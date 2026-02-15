"""
LLM Generator for L5X Code Generation

Uses Gemini or OpenAI to generate PLC L5X code from CSV logic patterns.
Supports RAG-based generation with retrieved examples.
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import time
from src.config.settings import get_settings
from src.utils.logger import logger

settings = get_settings()


class LLMGenerator:
    """
    LLM-based code generator for PLC L5X files

    Supports:
    - OpenRouter (access to Claude, GPT-4, Gemini, Llama, etc.)
    - Gemini (Google's models)
    - OpenAI (GPT models)
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize LLM generator

        Args:
            model: Optional model override (uses settings default if None)
        """
        self.provider = settings.llm_provider

        if self.provider == "gemini":
            if not settings.google_api_key:
                raise ValueError("GOOGLE_API_KEY not set in environment")

            genai.configure(api_key=settings.google_api_key)

            # Use provided model or default from settings
            self.model = model or settings.google_model

            logger.info(f"Initialized Gemini LLM with model: {self.model}")

        elif self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")

            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = model or settings.openai_model

            logger.info(f"Initialized OpenAI LLM with model: {self.model}")

        elif self.provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY not set in environment")

            # OpenRouter uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url
            )
            self.model = model or settings.openrouter_model

            logger.info(f"Initialized OpenRouter LLM with model: {self.model}")

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Generate text using the LLM

        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative). Uses settings default if None.
            max_tokens: Maximum tokens to generate. Uses settings default if None.

        Returns:
            Generated text
        """
        # Use settings defaults if not provided
        if temperature is None:
            temperature = settings.generation_temperature
        if max_tokens is None:
            max_tokens = settings.max_generation_tokens

        logger.info(f"Generating with {self.provider} (temp={temperature}, max_tokens={max_tokens})")

        if self.provider == "gemini":
            return self._generate_gemini(prompt, temperature, max_tokens)
        elif self.provider == "openai":
            return self._generate_openai(prompt, temperature, max_tokens)
        elif self.provider == "openrouter":
            # OpenRouter uses OpenAI-compatible API
            return self._generate_openai(prompt, temperature, max_tokens)

        raise NotImplementedError(f"Generation not implemented for {self.provider}")

    def _generate_gemini(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using Gemini with retry logic"""
        # Log prompt size
        prompt_size = len(prompt)
        logger.info(f"Prompt size: {prompt_size:,} characters ({prompt_size/1024:.1f} KB)")

        # Reduce max tokens if too high (Gemini has limits)
        if max_tokens > 8192:
            logger.warning(f"Reducing max_tokens from {max_tokens} to 8192 for Gemini")
            max_tokens = 8192

        # Configure generation settings
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": 0.95,
            "top_k": 40,
        }

        # Retry logic with exponential backoff
        max_retries = settings.generation_max_retries

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    logger.info(f"Retry attempt {attempt}/{max_retries} after {wait_time}s wait...")
                    time.sleep(wait_time)

                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries + 1})...")

                # Create model with timeout configuration
                model = genai.GenerativeModel(
                    model_name=self.model,
                    generation_config=generation_config
                )

                # Generate (Gemini SDK handles timeout internally)
                response = model.generate_content(prompt)

                if not response.text:
                    logger.error("Gemini returned empty response")
                    raise ValueError("LLM returned empty response")

                logger.info(f"Generated {len(response.text)} characters")
                return response.text

            except google_exceptions.DeadlineExceeded as e:
                logger.warning(f"Attempt {attempt + 1} timed out")
                if attempt == max_retries:
                    logger.error(f"All {max_retries + 1} attempts failed due to timeout")
                    # Try with reduced prompt on last attempt
                    if prompt_size > 50000:
                        logger.info("Prompt too large, try reducing similar examples count")
                    raise TimeoutError(
                        f"Gemini API timed out after {max_retries + 1} attempts. "
                        f"Prompt size: {prompt_size} chars. Try reducing similar examples or using a smaller model."
                    ) from e
            except google_exceptions.ResourceExhausted as e:
                logger.error("Gemini rate limit exceeded")
                if attempt == max_retries:
                    raise ValueError("Gemini rate limit exceeded. Please try again later.") from e
                # Wait longer for rate limits
                wait_time = min(10 * (2 ** attempt), 60)
                logger.info(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Gemini generation error: {e}")
                raise

        raise RuntimeError("Should not reach here")

    def _generate_openai(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert PLC programmer specializing in Rockwell/Allen-Bradley systems and L5X file generation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        generated_text = response.choices[0].message.content

        if not generated_text:
            logger.error("OpenAI returned empty response")
            raise ValueError("LLM returned empty response")

        logger.info(f"Generated {len(generated_text)} characters")
        return generated_text

    def generate_l5x(
        self,
        machine_name: str,
        csv_logic: str,
        similar_examples: List[Dict[str, Any]],
        prompt_template: str,
        temperature: float = 0.1
    ) -> str:
        """
        Generate L5X code for a machine using RAG

        Args:
            machine_name: Name of the machine
            csv_logic: Structured description of the CSV logic
            similar_examples: List of similar examples from retrieval
            prompt_template: The prompt template to use
            temperature: Generation temperature

        Returns:
            Generated L5X XML code
        """
        logger.info(f"Generating L5X for machine: {machine_name}")

        # Build complete prompt with context
        full_prompt = prompt_template.format(
            machine_name=machine_name,
            csv_logic=csv_logic,
            similar_examples=self._format_examples(similar_examples)
        )

        # Generate
        l5x_code = self.generate(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=8000  # L5X files can be large
        )

        return l5x_code

    def _format_examples(self, examples: List[Dict[str, Any]]) -> str:
        """
        Format similar examples for the prompt

        Args:
            examples: List of retrieval results

        Returns:
            Formatted string for prompt
        """
        if not examples:
            return "No similar examples available."

        formatted = []
        for i, example in enumerate(examples[:3], 1):  # Top 3 examples
            formatted.append(f"\n### Example {i} (Similarity: {example.get('similarity_score', 0):.2f})")
            formatted.append(f"Machine: {example.get('machine_name', 'Unknown')}")
            formatted.append(f"States: {example.get('metadata', {}).get('state_count', 'N/A')}")
            formatted.append(f"Interlocks: {example.get('metadata', {}).get('interlock_count', 'N/A')}")

            # Add L5X preview if available
            l5x_preview = example.get('metadata', {}).get('l5x_preview')
            if l5x_preview:
                formatted.append(f"\nL5X Preview:\n```xml\n{l5x_preview[:500]}...\n```")

        return "\n".join(formatted)


def get_generator(model: Optional[str] = None) -> LLMGenerator:
    """
    Get an LLM generator instance

    Args:
        model: Optional model override

    Returns:
        Initialized LLMGenerator
    """
    return LLMGenerator(model=model)
