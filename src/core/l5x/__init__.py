"""
L5X Generation Module

This module handles L5X (Rockwell/Allen-Bradley) XML file generation.

Components:
- skeleton_generator: Creates valid XML structure with placeholders
- routine_generator: Fills routines with ladder logic using LLM
- assembler: Merges skeleton + generated routines
- validator: Validates final L5X output
"""

from src.core.l5x.skeleton_generator import (
    generate_skeleton,
    SkeletonGenerator
)

__all__ = [
    'generate_skeleton',
    'SkeletonGenerator'
]
