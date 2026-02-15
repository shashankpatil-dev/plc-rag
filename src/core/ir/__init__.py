"""
Intermediate Representation (IR) Module

This module provides the core data structures that serve as the single source
of truth between CSV input and L5X output. All IR structures are deterministic
and do not involve AI/LLM processing.
"""

from src.core.ir.ir_builder import (
    Rung,
    Routine,
    Program,
    L5XProject,
    RoutineType,
    TagType
)

__all__ = [
    'Rung',
    'Routine',
    'Program',
    'L5XProject',
    'RoutineType',
    'TagType'
]
