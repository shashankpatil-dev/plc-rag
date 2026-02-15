"""
RAG Pipeline for L5X Generation

Complete workflow: CSV → Retrieval → Generation → Validation
"""
from typing import Optional, Dict, Any
from pathlib import Path
from src.api.models.csv_models import MachineLogic, ParsedCSV
from src.core.parser.csv_parser import parse_csv_file, parse_csv_bytes
from src.core.rag.retriever import get_retriever
from src.core.rag.generator import get_generator
from src.core.rag.embedder import get_embedder
from src.core.templates.prompts import create_generation_prompt, create_refinement_prompt
from src.core.rag.validator import validate_l5x
from src.utils.logger import logger


class L5XGenerationResult:
    """Result from L5X generation pipeline"""

    def __init__(
        self,
        machine_name: str,
        l5x_code: str,
        success: bool,
        similar_count: int = 0,
        error: Optional[str] = None,
        iterations: Optional[list] = None,
        is_valid: bool = False,
        validation_issues: Optional[list] = None
    ):
        self.machine_name = machine_name
        self.l5x_code = l5x_code
        self.success = success
        self.similar_count = similar_count
        self.error = error
        self.iterations = iterations or []
        self.is_valid = is_valid
        self.validation_issues = validation_issues or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "machine_name": self.machine_name,
            "l5x_code": self.l5x_code,
            "success": self.success,
            "similar_count": self.similar_count,
            "error": self.error,
            "iterations": self.iterations,
            "is_valid": self.is_valid,
            "validation_issues": [
                issue.to_dict() if hasattr(issue, 'to_dict') else issue
                for issue in self.validation_issues
            ]
        }


class RAGPipeline:
    """
    Complete RAG pipeline for L5X generation

    Workflow:
    1. Parse CSV to extract machine logic
    2. Retrieve similar machines from vector DB
    3. Build prompt with context
    4. Generate L5X code using LLM
    5. Return results
    """

    def __init__(self):
        """Initialize RAG pipeline"""
        self.retriever = get_retriever()
        self.generator = get_generator()
        self.embedder = get_embedder()
        logger.info("Initialized RAG Pipeline")

    def generate_from_csv(
        self,
        csv_content: str,
        machine_index: int = 0,
        n_similar: int = 3
    ) -> L5XGenerationResult:
        """
        Generate L5X from CSV content

        Args:
            csv_content: CSV file content
            machine_index: Which machine to generate (default: first)
            n_similar: Number of similar examples to retrieve

        Returns:
            L5XGenerationResult
        """
        try:
            # Step 1: Parse CSV
            logger.info("Step 1: Parsing CSV...")
            parsed = parse_csv_file(csv_content)

            if parsed.total_machines == 0:
                return L5XGenerationResult(
                    machine_name="Unknown",
                    l5x_code="",
                    success=False,
                    error="No machines found in CSV"
                )

            # Get target machine
            if machine_index >= parsed.total_machines:
                return L5XGenerationResult(
                    machine_name="Unknown",
                    l5x_code="",
                    success=False,
                    error=f"Machine index {machine_index} out of range (found {parsed.total_machines} machines)"
                )

            machine = parsed.machines[machine_index]
            logger.info(f"Target machine: {machine.name}")

            # Step 2: Retrieve similar examples
            logger.info(f"Step 2: Retrieving {n_similar} similar machines...")
            similar = self.retriever.retrieve_similar(
                machine=machine,
                n_results=n_similar
            )

            logger.info(f"Found {len(similar)} similar machines")

            # Step 3: Build context
            logger.info("Step 3: Building generation context...")
            csv_logic = self._format_machine_logic(machine)
            similar_examples = self._format_similar_examples(similar)

            # Step 4: Generate L5X
            logger.info("Step 4: Generating L5X code...")

            # Try detailed template first
            prompt = create_generation_prompt(
                machine_name=machine.name,
                csv_logic=csv_logic,
                similar_examples=similar_examples,
                template="detailed"
            )

            # Check prompt size and fallback to simple template if too large
            MAX_PROMPT_SIZE = 100000  # ~100KB character limit
            if len(prompt) > MAX_PROMPT_SIZE:
                logger.warning(
                    f"Prompt too large ({len(prompt)} chars), "
                    f"falling back to simple template without examples"
                )
                prompt = create_generation_prompt(
                    machine_name=machine.name,
                    csv_logic=csv_logic,
                    similar_examples="",  # Skip examples for simple template
                    template="simple"
                )

            l5x_code = self.generator.generate(
                prompt=prompt
                # Uses settings defaults: temperature=0.1, max_tokens=8192
            )

            # Clean up generated code (remove markdown if present)
            l5x_code = self._clean_generated_code(l5x_code)

            logger.info(f"Successfully generated L5X ({len(l5x_code)} characters)")

            return L5XGenerationResult(
                machine_name=machine.name,
                l5x_code=l5x_code,
                success=True,
                similar_count=len(similar)
            )

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            import traceback
            traceback.print_exc()

            return L5XGenerationResult(
                machine_name="Unknown",
                l5x_code="",
                success=False,
                error=str(e)
            )

    def generate_with_refinement(
        self,
        csv_content: str,
        machine_index: int = 0,
        n_similar: int = 3,
        max_iterations: int = 3
    ) -> L5XGenerationResult:
        """
        Generate L5X with iterative refinement to fix validation issues

        Args:
            csv_content: CSV file content
            machine_index: Which machine to generate (default: first)
            n_similar: Number of similar examples to retrieve
            max_iterations: Maximum refinement iterations (default: 3)

        Returns:
            L5XGenerationResult with iteration history
        """
        logger.info(f"Starting L5X generation with refinement (max {max_iterations} iterations)")

        # Step 1: Generate initial L5X
        result = self.generate_from_csv(
            csv_content=csv_content,
            machine_index=machine_index,
            n_similar=n_similar
        )

        if not result.success:
            return result

        iterations = []
        current_l5x = result.l5x_code
        best_l5x = current_l5x
        best_error_count = float('inf')

        # Step 2: Validate and refine iteratively
        for iteration in range(max_iterations):
            logger.info(f"Refinement iteration {iteration + 1}/{max_iterations}")

            # Validate current L5X
            is_valid, issues = validate_l5x(current_l5x)

            # Count errors
            errors = [i for i in issues if i.severity == "error"]
            error_count = len(errors)

            # Track iteration
            iteration_data = {
                "iteration": iteration + 1,
                "is_valid": is_valid,
                "error_count": error_count,
                "warning_count": len([i for i in issues if i.severity == "warning"]),
                "info_count": len([i for i in issues if i.severity == "info"]),
                "issues": [issue.to_dict() for issue in issues]
            }
            iterations.append(iteration_data)

            logger.info(f"  Validation: {'VALID' if is_valid else 'INVALID'} "
                       f"({error_count} errors)")

            # Update best result
            if error_count < best_error_count:
                best_l5x = current_l5x
                best_error_count = error_count
                logger.info(f"  New best result (errors: {error_count})")

            # If valid or no errors, we're done
            if is_valid or error_count == 0:
                logger.info("✓ L5X is valid! Refinement complete.")
                return L5XGenerationResult(
                    machine_name=result.machine_name,
                    l5x_code=current_l5x,
                    success=True,
                    similar_count=result.similar_count,
                    iterations=iterations,
                    is_valid=True,
                    validation_issues=issues
                )

            # Build refinement prompt
            logger.info(f"  Attempting to fix {error_count} error(s)...")
            issues_text = "\n".join([
                f"- {issue.severity.upper()}: {issue.message} ({issue.location})"
                for issue in errors[:5]  # Top 5 errors
            ])

            refinement_prompt = create_refinement_prompt(
                original_l5x=current_l5x,
                issues=issues_text
            )

            # Check prompt size for refinement
            if len(refinement_prompt) > 150000:  # 150KB limit for refinement
                logger.warning(
                    f"Refinement prompt too large ({len(refinement_prompt)} chars), "
                    f"truncating L5X to critical sections"
                )
                # Truncate L5X but keep header and problematic sections
                truncated_l5x = current_l5x[:50000] + "\n... [TRUNCATED] ..."
                refinement_prompt = create_refinement_prompt(
                    original_l5x=truncated_l5x,
                    issues=issues_text
                )

            # Generate refined L5X
            try:
                refined_l5x = self.generator.generate(
                    prompt=refinement_prompt,
                    max_tokens=8192  # Explicit limit for refinement
                )

                # Clean up
                refined_l5x = self._clean_generated_code(refined_l5x)
                current_l5x = refined_l5x

            except TimeoutError as e:
                logger.error(f"  Refinement timed out: {e}")
                logger.info("  Continuing with current best L5X")
                break
            except Exception as e:
                logger.error(f"  Refinement failed: {e}")
                break

        # Return best result even if not perfect
        logger.warning(f"Refinement complete after {len(iterations)} iterations. "
                      f"Best result has {best_error_count} errors.")

        # Final validation of best result
        is_valid, final_issues = validate_l5x(best_l5x)

        return L5XGenerationResult(
            machine_name=result.machine_name,
            l5x_code=best_l5x,
            success=True,
            similar_count=result.similar_count,
            iterations=iterations,
            is_valid=is_valid,
            validation_issues=final_issues
        )

    def generate_all(
        self,
        csv_content: str,
        n_similar: int = 3
    ) -> Dict[str, L5XGenerationResult]:
        """
        Generate L5X for all machines in CSV

        Args:
            csv_content: CSV file content
            n_similar: Number of similar examples per machine

        Returns:
            Dictionary mapping machine names to results
        """
        results = {}

        # Parse CSV
        parsed = parse_csv_file(csv_content)

        logger.info(f"Generating L5X for {parsed.total_machines} machines...")

        for i, machine in enumerate(parsed.machines):
            logger.info(f"Processing machine {i+1}/{parsed.total_machines}: {machine.name}")

            result = self.generate_from_csv(
                csv_content=csv_content,
                machine_index=i,
                n_similar=n_similar
            )

            results[machine.name] = result

        return results

    def _format_machine_logic(self, machine: MachineLogic) -> str:
        """Format machine logic for the prompt"""
        lines = [
            f"Machine: {machine.name}",
            f"Total States: {machine.state_count}",
            f"State Cycle: {' → '.join(map(str, machine.cycle_path))}",
            f"Unique Interlocks: {', '.join(machine.all_interlocks[:15])}",  # First 15
            "",
            "State Definitions:",
        ]

        for state in machine.states:
            interlock_str = ', '.join(state.interlocks) if state.interlocks else "None"
            lines.append(
                f"  Step {state.step}: {state.description}\n"
                f"    - Interlocks: {interlock_str}\n"
                f"    - Condition: {state.condition}\n"
                f"    - Next Step: {state.next_step}"
            )

        return "\n".join(lines)

    def _format_similar_examples(self, similar_results: list) -> str:
        """Format similar examples for the prompt"""
        if not similar_results:
            return "No similar examples found in database."

        lines = ["Found similar machines in database:"]

        for i, result in enumerate(similar_results[:3], 1):  # Top 3
            lines.append(
                f"\n{i}. {result.machine_name} (Similarity: {result.similarity_score:.2f})\n"
                f"   - States: {result.metadata.get('state_count', 'N/A')}\n"
                f"   - Interlocks: {result.metadata.get('interlock_count', 'N/A')}\n"
                f"   - Source: {result.metadata.get('source_csv', 'N/A')}"
            )

            # Add L5X preview if available
            l5x_preview = result.metadata.get('l5x_preview')
            if l5x_preview:
                lines.append(f"   - L5X structure reference available")

        return "\n".join(lines)

    def _clean_generated_code(self, code: str) -> str:
        """Clean up generated L5X code"""
        # Remove markdown code blocks if present
        if "```xml" in code:
            # Extract content between ```xml and ```
            parts = code.split("```xml")
            if len(parts) > 1:
                code = parts[1].split("```")[0].strip()

        elif "```" in code:
            # Generic code block
            parts = code.split("```")
            if len(parts) > 1:
                code = parts[1].strip()

        # Remove any leading/trailing whitespace
        code = code.strip()

        return code


def get_pipeline() -> RAGPipeline:
    """
    Get a RAG pipeline instance

    Returns:
        Initialized RAGPipeline
    """
    return RAGPipeline()
