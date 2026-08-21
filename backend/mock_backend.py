"""Minimal test backend implementation for development and testing.

This module provides a stubbed backend implementation that assigns
default attribute types for testing purposes.
"""

from expression import ast
from core import attribute_types

from .base import Backend


class MockBackend(Backend):
    """Minimal concrete implementation of Backend for tests and scaffolding.

    Maps attribute names to corresponding AttributeTypes for testing
    purposes. Provides basic type resolution without a real graph system.
    """

    def resolve_attribute_type(
        self, node: ast.Identifier, attributes: list[ast.Identifier]
    ) -> attribute_types.AttributeType:
        """Return a default attribute type based on the attribute name.

        Matches the last attribute name against known type prefixes
        (int, float, vector2, vector3, bool, matrix4).

        Args:
            node: The base node (unused in stub implementation).
            attributes: List of attribute identifiers to resolve.

        Returns:
            The corresponding AttributeType for the matched prefix.
        """
        last_attr = attributes[-1] if attributes else "float"

        return_dict = {
            "int": attribute_types.INT,
            "float": attribute_types.FLOAT,
            "vector2": attribute_types.VECTOR2,
            "vector3": attribute_types.VECTOR3,
            "bool": attribute_types.BOOL,
            "matrix4": attribute_types.MATRIX4,
        }

        for key, value in return_dict.items():
            if last_attr.name.startswith(key):
                return value

        raise SyntaxError(
            f"{node}.{''.join(['[{x}]' for x in attributes])} attribute type not found"
        )
