"""Simple runtime graph type system used by operations and signatures.

This module provides a tiny `GraphType` class used to represent and
compare abstract data kinds (Number, Vector, Bool, etc.) and a set of
common built-in types used elsewhere in the project.
"""


class GraphType:
    """A simple nominal type with optional parent for subtyping.

    `is_a` can be used to test whether a type is equal to or a
    subtype of another by following the `parent` chain.
    """
    def __init__(self, name:str, parent=None):
        self.name = name
        self.parent = parent

    def is_a(self, other):
        current = self

        while current is not None:
            if current == other:
                return True

            current = current.parent

        return False

    def __repr__(self):
        return self.name


NUMBER = GraphType("Number")
INT = GraphType("Int", parent=NUMBER)
FLOAT = GraphType("Float", parent=NUMBER)
VECTOR = GraphType("Vector")
VECTOR2 = GraphType("Vector2", parent=VECTOR)
VECTOR3 = GraphType("Vector3", parent=VECTOR)
BOOL = GraphType("Bool")
MATRIX4 = GraphType("Bool")