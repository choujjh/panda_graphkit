"""Attribute and node type definitions used by operations and signatures.

This module provides a small nominal type system used to describe
input/output kinds foroperations (Number, Vector, Bool, etc.). Use these
types in `Signature` and validation logic.
"""

from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Iterable


@dataclass(frozen=True)
class AttributeType:
    """A simple nominal type with optional parent for subtyping.

    `is_a` can be used to test whether a type is equal to or a
    subtype of another by following the `parent` chain.
    """

    name: str
    parent: AttributeType | None = None

    def is_a(self, other):
        """Return whether this type is equal to or derives from ``other``."""
        current = self

        if not isinstance(other, AttributeType):
            return False

        while current is not None:
            if current == other:
                return True
            current = current.parent

        return False

    def is_compatable(self, other):
        """Return whether both types belong to the same root type family."""
        if isinstance(other, Iterable):
            return any(self.is_compatable(x) for x in other)

        if not isinstance(other, AttributeType) or other is None:
            return False

        self_parent = self
        while self_parent.parent is not None:
            self_parent = self_parent.parent

        other_parent = other
        while other_parent.parent is not None:
            other_parent = other_parent.parent

        return self_parent == other_parent

    def __repr__(self):
        """Return the display name of the attribute type."""
        return self.name

    def __eq__(self, other):
        """Return whether two attribute types have matching names and parents."""
        if not isinstance(other, AttributeType):
            return False
        return self.name == other.name and self.parent == other.parent


def infer_return_type(type_list: list[AttributeType]) -> AttributeType:
    """Infer the most specific numeric return type from argument types.

    Returns FLOAT if any argument is FLOAT, INT if all are INT,
    otherwise NUMBER.

    Args:
        type_list: List of argument types.

    Returns:
        The inferred numeric return type (INT, FLOAT, or NUMBER).
    """
    if MATRIX4 in type_list:
        return MATRIX4
    if any(type_list.is_a(VECTOR) for type_list in type_list):
        return VECTOR
    if any(type_list.is_a(FLOAT) for type_list in type_list):
        return FLOAT
    if all(type_list.is_a(INT) for type_list in type_list):
        return INT
    return NUMBER

def types_is_compatable(types_a:tuple[AttributeType], types_b:tuple[AttributeType]):
    """Return whether a type or tuple of types is compatible with another type set.

    Args:
        types_a: Candidate type or tuple of types to compare.
        types_b: Type or tuple of types to check compatibility against.

    Returns:
        True when any candidate type is compatible with the target set.
    """
    if not isinstance(types_a, Iterable):
        types_a = [types_a]
    for type_a in types_a:
        if type_a.is_compatable(types_b):
            return True
    return False

# Common built-in types
NUMBER = AttributeType("Number")
INT = AttributeType("Int", parent=NUMBER)
FLOAT = AttributeType("Float", parent=NUMBER)
VECTOR = AttributeType("Vector")
VECTOR2 = AttributeType("Vector2", parent=VECTOR)
VECTOR3 = AttributeType("Vector3", parent=VECTOR)
BOOL = AttributeType("Bool")
MATRIX4 = AttributeType("Matrix4")
STRING = AttributeType("String")

__all__ = [
    "AttributeType",
    "NUMBER",
    "INT",
    "FLOAT",
    "VECTOR",
    "VECTOR2",
    "VECTOR3",
    "BOOL",
    "MATRIX4",
    "STRING",
    "infer_return_type",
    "types_is_compatable",
]
