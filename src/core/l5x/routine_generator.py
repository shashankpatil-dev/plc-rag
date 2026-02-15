"""
Routine-Level LLM Generator

Generates ladder logic rungs for individual routines using Claude Sonnet.
This is the ONLY place where AI/LLM is used in the generation pipeline.

Key Design Principles:
- One routine = One LLM call (chunked generation)
- Strict prompts (generate ONLY rungs, no XML structure)
- RAG retrieval for similar examples
- Style profile enforcement
- Retry logic with validation
- Token budget per routine (~2,500 tokens)
"""

from typing import List, Dict, Optional, Any
from src.core.ir.ir_builder import Routine, Rung, RoutineType
from src.core.rag.generator import LLMGenerator
from src.core.knowledge.embedder import EmbeddingGenerator
from src.core.knowledge.vector_store import get_vector_store
from src.utils.logger import logger


class RoutineGenerator:
    """
    Generates ladder logic for a single routine using LLM

    This class is responsible for:
    - Building focused prompts for routine generation
    - Calling Claude Sonnet via OpenRouter
    - Validating generated output
    - Retry logic on failures
    """

    def __init__(self, llm_generator: Optional[LLMGenerator] = None, use_rag: bool = True):
        """
        Initialize routine generator

        Args:
            llm_generator: Optional LLM generator instance (creates default if None)
            use_rag: Whether to use RAG retrieval for similar examples
        """
        self.llm = llm_generator or LLMGenerator()
        self.use_rag = use_rag

        # Initialize RAG components if enabled
        if use_rag:
            try:
                self.embedder = EmbeddingGenerator()
                self.vector_store = get_vector_store()
                self.collection = self.vector_store.client.get_collection("plc_client_routines")
                logger.info(f"Routine generator initialized with {self.llm.provider} + RAG")
            except Exception as e:
                logger.warning(f"RAG not available: {e}. Continuing without RAG.")
                self.use_rag = False
        else:
            logger.info(f"Routine generator initialized with {self.llm.provider} (no RAG)")

    def generate_routine(
        self,
        routine: Routine,
        style_profile: Optional[str] = None,
        similar_examples: Optional[List[str]] = None,
        max_retries: int = 2,
        n_similar: int = 3
    ) -> str:
        """
        Generate ladder logic rungs for a single routine

        Args:
            routine: IR Routine structure with rungs to generate
            style_profile: Optional coding style guidelines
            similar_examples: Optional list of similar routine examples from RAG
            max_retries: Number of retry attempts on failure

        Returns:
            Generated L5X rungs as XML string

        Raises:
            ValueError: If generation fails after all retries
        """
        logger.info(f"Generating routine: {routine.name} ({routine.rung_count} rungs)")

        # Retrieve similar examples from RAG if enabled and not provided
        if self.use_rag and similar_examples is None:
            similar_examples = self._retrieve_similar_routines(routine, n_similar)

        # Build prompt
        prompt = self._build_prompt(routine, style_profile, similar_examples)

        # Log prompt size for debugging
        prompt_size = len(prompt)
        logger.debug(f"Prompt size: {prompt_size:,} characters")

        # Attempt generation with retries
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries}")

                # Generate rungs
                generated_rungs = self.llm.generate(
                    prompt=prompt,
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=2500   # Per routine token budget
                )

                # Validate output
                validation = self._validate_rungs(generated_rungs, routine)

                if validation['valid']:
                    logger.info(f"✅ Successfully generated {routine.name}")
                    return generated_rungs
                else:
                    logger.warning(f"Validation failed: {validation['issues']}")

                    if attempt < max_retries:
                        # Try again with stricter constraints
                        prompt = self._build_stricter_prompt(
                            routine,
                            style_profile,
                            similar_examples,
                            previous_issues=validation['issues']
                        )
                    else:
                        raise ValueError(
                            f"Validation failed after {max_retries + 1} attempts: "
                            f"{validation['issues']}"
                        )

            except Exception as e:
                logger.error(f"Generation failed on attempt {attempt + 1}: {e}")

                if attempt == max_retries:
                    raise ValueError(
                        f"Failed to generate routine {routine.name} after "
                        f"{max_retries + 1} attempts: {e}"
                    )

        raise RuntimeError("Should not reach here")

    def _build_prompt(
        self,
        routine: Routine,
        style_profile: Optional[str],
        similar_examples: Optional[List[str]]
    ) -> str:
        """
        Build generation prompt for a routine

        Creates a strict, focused prompt that instructs the LLM to generate
        ONLY ladder logic rungs without any XML structure.
        """
        # System instructions (strict constraints)
        system_prompt = """You are a PLC ladder logic generator. Your task is to generate ONLY ladder logic rungs in L5X XML format.

CRITICAL RULES:
1. Generate ONLY <Rung> elements - nothing else
2. DO NOT generate: XML headers, <Routine> tags, <RLLContent> tags, or any wrapper elements
3. Each rung must have: Number, Comment, and valid ladder logic
4. Use standard Rockwell/Allen-Bradley instructions: XIC, XIO, OTE, OTL, OTU, TON, CTU
5. Ladder logic must be syntactically correct for Studio 5000

OUTPUT FORMAT (example):
<Rung Number="0" Type="N">
  <Comment>
    <![CDATA[Check emergency stop]]>
  </Comment>
  <Text>
    <![CDATA[XIO(EStop)OTE(Safety_OK);]]>
  </Text>
</Rung>
"""

        # Style guidelines
        style_section = ""
        if style_profile:
            style_section = f"\nCODING STYLE REQUIREMENTS:\n{style_profile}\n"
        else:
            style_section = """
CODING STYLE REQUIREMENTS:
- Tag naming: PascalCase with underscores (e.g., Motor_Run, Safety_OK)
- Comments: Clear, concise descriptions
- Rung numbering: Sequential starting from 0
- Logic: Simple and maintainable
"""

        # Similar examples section
        examples_section = ""
        if similar_examples:
            examples_section = "\nSIMILAR EXAMPLES FROM KNOWLEDGE BASE:\n"
            for i, example in enumerate(similar_examples[:3], 1):
                examples_section += f"\nExample {i}:\n{example}\n"
        else:
            examples_section = """
EXAMPLE RUNG FORMAT:
<Rung Number="0" Type="N">
  <Comment>
    <![CDATA[Start motor when button pressed and safety clear]]>
  </Comment>
  <Text>
    <![CDATA[XIC(Start_Button)XIC(Safety_Clear)OTE(Motor_Run);]]>
  </Text>
</Rung>
"""

        # Routine specification
        routine_spec = f"""
GENERATE RUNGS FOR THIS ROUTINE:
Routine Name: {routine.name}
Routine Type: {routine.type.display_name}
Number of Rungs: {routine.rung_count}

LOGIC REQUIREMENTS:
"""

        # Add each rung's requirements
        for rung in routine.rungs:
            routine_spec += f"""
Rung {rung.number}: {rung.comment}
  Condition: {rung.condition}
  Action: {rung.action}
  Tags: {', '.join(rung.tags_used)}
  Safety Critical: {rung.safety_critical}
"""

        # Assembly instructions
        assembly_instructions = """
OUTPUT INSTRUCTIONS:
Generate EXACTLY {rung_count} rung(s) following the L5X format shown above.
Each rung must implement the logic requirements specified.
Use proper ladder logic instructions (XIC for examine closed, XIO for examine open, OTE for output).
Include clear comments for each rung.
Do NOT include any text outside the <Rung> elements.

BEGIN OUTPUT:
""".format(rung_count=routine.rung_count)

        # Combine all sections
        full_prompt = (
            system_prompt +
            style_section +
            examples_section +
            routine_spec +
            assembly_instructions
        )

        return full_prompt

    def _build_stricter_prompt(
        self,
        routine: Routine,
        style_profile: Optional[str],
        similar_examples: Optional[List[str]],
        previous_issues: List[str]
    ) -> str:
        """
        Build a stricter prompt after validation failure

        Adds additional constraints based on previous issues.
        """
        base_prompt = self._build_prompt(routine, style_profile, similar_examples)

        # Add corrections based on previous issues
        corrections = "\n\nCORRECTIONS NEEDED (previous attempt had these issues):\n"
        for issue in previous_issues:
            corrections += f"- {issue}\n"

        corrections += "\nPlease generate again with these corrections applied.\n"

        return base_prompt + corrections

    def _validate_rungs(self, generated_rungs: str, routine: Routine) -> Dict[str, Any]:
        """
        Validate generated rungs

        Checks:
        - Contains <Rung> elements
        - No invalid XML wrapper elements
        - Correct number of rungs
        - Valid XML syntax
        """
        issues = []

        # Check for invalid wrapper elements
        invalid_wrappers = ['<Routine', '<RLLContent', '<?xml', '<RSLogix5000Content']
        for wrapper in invalid_wrappers:
            if wrapper in generated_rungs:
                issues.append(f"Contains invalid wrapper element: {wrapper}")

        # Check for <Rung> elements
        rung_count = generated_rungs.count('<Rung')
        if rung_count == 0:
            issues.append("No <Rung> elements found in output")
        elif rung_count != routine.rung_count:
            issues.append(
                f"Wrong number of rungs: expected {routine.rung_count}, got {rung_count}"
            )

        # Check XML validity (basic)
        try:
            import xml.etree.ElementTree as ET
            # Wrap in a root element for parsing
            wrapped = f"<Root>{generated_rungs}</Root>"
            ET.fromstring(wrapped)
        except ET.ParseError as e:
            issues.append(f"Invalid XML: {e}")

        # Check for required elements in each rung
        if '<Comment>' not in generated_rungs:
            issues.append("Missing <Comment> elements in rungs")

        if '<Text>' not in generated_rungs:
            issues.append("Missing <Text> elements (ladder logic)")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'rung_count': rung_count
        }

    def _retrieve_similar_routines(self, routine: Routine, n_similar: int = 3) -> List[str]:
        """
        Retrieve similar routines using RAG

        This method queries the ChromaDB knowledge base for similar routines
        based on the routine's metadata, type, and rung descriptions.

        Args:
            routine: Routine to find similar examples for
            n_similar: Number of similar routines to retrieve

        Returns:
            List of similar routine texts
        """
        if not self.use_rag:
            return []

        try:
            # Build query from routine metadata
            query_parts = []

            # Add routine type
            query_parts.append(f"{routine.type.display_name} routine")

            # Add description if available
            if routine.description:
                query_parts.append(routine.description)

            # Add rung descriptions from first 3 rungs
            for rung in routine.rungs[:3]:
                if rung.comment:
                    query_parts.append(rung.comment)

            query_text = " ".join(query_parts)

            logger.info(f"RAG query: {query_text[:100]}...")

            # Create embedding for query
            query_embedding = self.embedder.embed_text(query_text)

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_similar
            )

            # Extract documents (similar routine texts)
            similar_routines = results['documents'][0] if results['documents'] else []
            distances = results['distances'][0] if results['distances'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []

            # Log retrieval results
            logger.info(f"Retrieved {len(similar_routines)} similar routines:")
            for i, (meta, dist) in enumerate(zip(metadatas, distances), 1):
                logger.info(f"  {i}. {meta.get('routine_name', 'Unknown')} (distance: {dist:.4f})")

            return similar_routines

        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []


class RoutineBatchGenerator:
    """
    Generates multiple routines in sequence

    Handles generation for an entire program or project.
    """

    def __init__(self, llm_generator: Optional[LLMGenerator] = None):
        """Initialize batch generator"""
        self.routine_gen = RoutineGenerator(llm_generator)

    def generate_all_routines(
        self,
        routines: List[Routine],
        style_profile: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, str]:
        """
        Generate all routines in a list

        Args:
            routines: List of routines to generate
            style_profile: Optional coding style
            progress_callback: Optional callback for progress updates

        Returns:
            Dict mapping routine name to generated rungs
        """
        results = {}
        total = len(routines)

        logger.info(f"Generating {total} routines...")

        for i, routine in enumerate(routines, 1):
            logger.info(f"[{i}/{total}] Generating {routine.name}...")

            try:
                # Generate routine
                rungs = self.routine_gen.generate_routine(
                    routine=routine,
                    style_profile=style_profile,
                    similar_examples=None  # TODO: Add RAG retrieval here
                )

                results[routine.name] = rungs

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i, total, routine.name)

            except Exception as e:
                logger.error(f"Failed to generate {routine.name}: {e}")
                # Continue with other routines
                results[routine.name] = f"<!-- GENERATION_FAILED: {e} -->"

        logger.info(f"✅ Generated {len(results)}/{total} routines")

        return results


def generate_routine(
    routine: Routine,
    llm_generator: Optional[LLMGenerator] = None,
    style_profile: Optional[str] = None
) -> str:
    """
    Convenience function to generate a single routine

    Args:
        routine: Routine to generate
        llm_generator: Optional LLM generator
        style_profile: Optional style guidelines

    Returns:
        Generated rungs as XML string
    """
    generator = RoutineGenerator(llm_generator)
    return generator.generate_routine(routine, style_profile)
