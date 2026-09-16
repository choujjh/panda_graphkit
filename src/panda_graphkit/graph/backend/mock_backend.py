"""Minimal test backend implementation for development and testing.

This module provides a stubbed backend implementation that assigns
default attribute types for testing purposes.
"""

from __future__ import annotations
from ..core import AttributeType, INT, FLOAT, VECTOR2, VECTOR3, BOOL, MATRIX4

from .base import Backend
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..expression import ast


class MockBackend(Backend):
    """Minimal concrete implementation of Backend for tests and scaffolding.

    Maps attribute names to corresponding AttributeTypes for testing
    purposes. Provides basic type resolution without a real graph system.
    """

    def resolve_attribute_type(
        self, node: ast.Identifier, attributes: list[ast.Identifier]
    ) -> AttributeType:
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
            "int": INT,
            "float": FLOAT,
            "vector2": VECTOR2,
            "vector3": VECTOR3,
            "bool": BOOL,
            "matrix4": MATRIX4,
        }

        for key, value in return_dict.items():
            if last_attr.name.startswith(key):
                return value

        raise SyntaxError(
            f"{node}.{''.join(['[{x}]' for x in attributes])} attribute type not found"
        )

    def _create_nodes(self, graph):
        """Create backend nodes for a graph in the mock implementation."""
        pass

    def _create_connections(self, graph, node_dict):
        """Connect mock graph nodes without any real backend dependency."""
        pass
