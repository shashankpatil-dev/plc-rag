"""
Complete L5X Generation Pipeline

End-to-end pipeline: CSV → IR → Skeleton → Generation → Assembly → Validation → L5X

This is the main entry point for generating L5X files from CSV input.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from src.core.parser.csv_parser import parse_csv_file
from src.core.parser.csv_to_ir import csv_to_ir
from src.core.l5x.skeleton_generator import generate_skeleton
from src.core.l5x.routine_generator import RoutineBatchGenerator
from src.core.l5x.assembler import assemble_l5x
from src.core.l5x.validator import validate_l5x
from src.core.rag.generator import LLMGenerator
from src.utils.logger import logger


class L5XGenerationPipeline:
    """
    Complete CSV → L5X generation pipeline

    This orchestrates all the steps needed to convert a CSV file
    into a complete, validated L5X file.
    """

    def __init__(self, llm_generator: Optional[LLMGenerator] = None):
        """
        Initialize pipeline

        Args:
            llm_generator: Optional LLM generator (creates default if None)
        """
        self.llm = llm_generator or LLMGenerator()
        self.batch_generator = RoutineBatchGenerator(self.llm)
        logger.info("L5X generation pipeline initialized")

    def generate_from_csv(
        self,
        csv_content: str,
        project_name: Optional[str] = None,
        style_profile: Optional[str] = None,
        validate_output: bool = True
    ) -> Dict[str, Any]:
        """
        Generate L5X from CSV content

        Args:
            csv_content: CSV file content
            project_name: Optional project name
            style_profile: Optional coding style guidelines
            validate_output: Whether to validate final output (default: True)

        Returns:
            Dict with L5X content and generation statistics
        """
        logger.info("=" * 60)
        logger.info("Starting L5X Generation Pipeline")
        logger.info("=" * 60)

        # Step 1: Parse CSV
        logger.info("\n[1/6] Parsing CSV...")
        parsed_csv = parse_csv_file(csv_content)
        logger.info(f"✅ Parsed {parsed_csv.total_machines} machine(s)")

        # Step 2: Convert to IR
        logger.info("\n[2/6] Converting to IR...")
        ir_project = csv_to_ir(parsed_csv, project_name)
        logger.info(
            f"✅ IR created: {ir_project.program_count} programs, "
            f"{ir_project.total_routines} routines, {ir_project.total_rungs} rungs"
        )

        # Step 3: Generate skeleton
        logger.info("\n[3/6] Generating skeleton...")
        skeleton = generate_skeleton(ir_project)
        logger.info(f"✅ Skeleton: {len(skeleton):,} characters")

        # Step 4: Generate routines with LLM
        logger.info(f"\n[4/6] Generating {ir_project.total_routines} routines with Claude Sonnet...")

        all_routines = []
        for program in ir_project.programs:
            all_routines.extend(program.routines)

        routine_logic = self.batch_generator.generate_all_routines(
            routines=all_routines,
            style_profile=style_profile
        )

        success_count = sum(
            1 for rungs in routine_logic.values()
            if "GENERATION_FAILED" not in rungs
        )

        logger.info(f"✅ Generated {success_count}/{len(all_routines)} routines")

        # Step 5: Assemble final L5X
        logger.info("\n[5/6] Assembling L5X...")
        final_l5x = assemble_l5x(skeleton, routine_logic)
        logger.info(f"✅ Final L5X: {len(final_l5x):,} characters")

        # Step 6: Validate (if enabled)
        validation_result = None
        if validate_output:
            logger.info("\n[6/6] Validating L5X...")
            validation_result = validate_l5x(final_l5x, ir_project)

            if validation_result['valid']:
                logger.info("✅ Validation passed")
            else:
                logger.warning(f"⚠️  Validation issues: {validation_result['issues']}")

            if validation_result['warnings']:
                logger.warning(f"⚠️  Warnings: {validation_result['warnings']}")

        # Compile statistics
        statistics = {
            'csv_machines': parsed_csv.total_machines,
            'ir_programs': ir_project.program_count,
            'ir_routines': ir_project.total_routines,
            'ir_rungs': ir_project.total_rungs,
            'ir_tags': len(ir_project.tags),
            'skeleton_size': len(skeleton),
            'final_size': len(final_l5x),
            'routines_generated': success_count,
            'routines_failed': len(all_routines) - success_count,
            'estimated_cost_usd': ir_project.estimated_generation_cost,
        }

        if validation_result:
            statistics['validation'] = validation_result

        logger.info("\n" + "=" * 60)
        logger.info("Pipeline Complete")
        logger.info("=" * 60)
        logger.info(f"✅ Generated L5X: {statistics['final_size']:,} bytes")
        logger.info(f"✅ Estimated cost: ${statistics['estimated_cost_usd']:.2f}")

        return {
            'l5x_content': final_l5x,
            'ir_project': ir_project,
            'statistics': statistics,
            'validation': validation_result
        }

    def generate_from_file(
        self,
        csv_file_path: str,
        output_path: Optional[str] = None,
        project_name: Optional[str] = None,
        style_profile: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate L5X from CSV file

        Args:
            csv_file_path: Path to CSV file
            output_path: Optional path to save L5X file
            project_name: Optional project name
            style_profile: Optional style guidelines

        Returns:
            Generation result dict
        """
        logger.info(f"Reading CSV from: {csv_file_path}")

        # Read CSV file
        with open(csv_file_path, 'r') as f:
            csv_content = f.read()

        # Generate L5X
        result = self.generate_from_csv(
            csv_content=csv_content,
            project_name=project_name,
            style_profile=style_profile
        )

        # Save to file if output path provided
        if output_path:
            logger.info(f"Saving L5X to: {output_path}")

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result['l5x_content'])

            logger.info(f"✅ Saved: {output_file}")
            result['output_file'] = str(output_file)

        return result


def generate_l5x_from_csv(
    csv_content: str,
    project_name: Optional[str] = None,
    llm_generator: Optional[LLMGenerator] = None
) -> str:
    """
    Convenience function to generate L5X from CSV

    Args:
        csv_content: CSV content string
        project_name: Optional project name
        llm_generator: Optional LLM generator

    Returns:
        L5X XML string
    """
    pipeline = L5XGenerationPipeline(llm_generator)
    result = pipeline.generate_from_csv(csv_content, project_name)
    return result['l5x_content']
