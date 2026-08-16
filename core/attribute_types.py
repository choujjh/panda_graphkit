"""Attribute and node type definitions used by operations and signatures.

This module provides a small nominal type system used to describe
input/output kinds foroperations (Number, Vector, Bool, etc.). Use these
types in `Signature` and validation logic.
"""


class AttributeType:
    """A simple nominal type with optional parent for subtyping.

    `is_a` can be used to test whether a type is equal to or a
    subtype of another by following the `parent` chain.
    """

    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent

    def is_a(self, other):
        current = self

        if not isinstance(other, AttributeType):
            return False

        while current is not None:
            if current == other:
                return True
            current = current.parent

        return False

    def is_compatable(self, other):
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
        return self.name

    def __eq__(self, other):
        if not isinstance(other, AttributeType):
            return False
        return self.name == other.name and self.parent == other.parent


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
]
