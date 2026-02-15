"""
L5X Assembler

Merges the skeleton XML with generated routine logic.
Replaces placeholders with actual ladder logic rungs.

This is a deterministic operation (no AI involved).
"""

from typing import Dict
from src.utils.logger import logger


class L5XAssembler:
    """
    Assembles final L5X file from skeleton and generated routines

    Takes the skeleton (with placeholders) and generated rungs,
    and produces the complete L5X file.
    """

    def assemble(
        self,
        skeleton: str,
        routine_logic: Dict[str, str]
    ) -> str:
        """
        Assemble complete L5X from skeleton and generated routines

        Args:
            skeleton: L5X skeleton with placeholders
            routine_logic: Dict mapping routine name to generated rungs

        Returns:
            Complete L5X XML string
        """
        logger.info(f"Assembling L5X with {len(routine_logic)} routines")

        l5x = skeleton

        # Replace each placeholder with generated logic
        for routine_name, rungs in routine_logic.items():
            placeholder = f"<!-- LOGIC_PLACEHOLDER_{routine_name} -->"

            if placeholder not in l5x:
                logger.warning(f"Placeholder not found for routine: {routine_name}")
                continue

            # Replace placeholder with rungs
            l5x = l5x.replace(placeholder, rungs)

            logger.debug(f"  ✅ Inserted rungs for {routine_name}")

        # Check for unfilled placeholders
        remaining_placeholders = l5x.count("LOGIC_PLACEHOLDER_")

        if remaining_placeholders > 0:
            logger.warning(f"⚠️  {remaining_placeholders} placeholder(s) not filled")

        logger.info("✅ Assembly complete")

        return l5x


def assemble_l5x(skeleton: str, routine_logic: Dict[str, str]) -> str:
    """
    Convenience function to assemble L5X

    Args:
        skeleton: L5X skeleton with placeholders
        routine_logic: Dict mapping routine name to generated rungs

    Returns:
        Complete L5X XML string
    """
    assembler = L5XAssembler()
    return assembler.assemble(skeleton, routine_logic)
