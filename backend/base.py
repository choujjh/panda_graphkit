"""Abstract base class for graph operation backends.

This module defines the Backend ABC which provides the interface for
resolving operations and attributes. Concrete implementations should
provide operation and attribute resolution for specific graph systems.
"""

from abc import ABC, abstractmethod

import core.attribute_types as attribute_types
import core.operation as operation
import operations.math as math
import expression.ast as ast


class Backend(ABC):
    """Abstract base class for graph operation backends.

    Provides an interface for resolving operation names to Operation
    objects and resolving attribute chains to AttributeType. Subclasses
    should implement resolve_attribute for their specific graph system.

    Attributes:
        supported_operations_map: Dict mapping operation names to Operation
            objects for the operations this backend supports.
    """

    """
    @classmethod
    def _get_operations_map(cls):
        if not hasattr(cls, '_operations_map_cache'):
            import operations.math as math
            cls._operations_map_cache = {
                "+": math.ADD,
                "-": math.SUBTRACT,
                "*": math.MULTIPLY,
                "/": math.DIVIDE,
                "**": math.POWER,
                "^": math.POWER,
                "sin": math.SIN,
                "cos": math.COS,
                "remap": math.REMAP,
                "add": math.ADD,
                "subtract": math.SUBTRACT,
                "mult": math.MULTIPLY,
                "div": math.DIVIDE,
                "pwr": math.POWER,
            }
        return cls._operations_map_cache

    supported_operations_map = property(lambda self: self._get_operations_map())
    """

    supported_operations_map = {
        "+": math.ADD,
        "-": math.SUBTRACT,
        "*": math.MULTIPLY,
        "/": math.DIVIDE,
        "**": math.POWER,
        "^": math.POWER,
        "sin": math.SIN,
        "cos": math.COS,
        "remap": math.REMAP,
        "add": math.ADD,
        "subtract": math.SUBTRACT,
        "mult": math.MULTIPLY,
        "div": math.DIVIDE,
        "pwr": math.POWER,
    }

    @abstractmethod
    def resolve_attribute(
        self, node: ast.Identifier, attributes: list[ast.Identifier]
    ) -> attribute_types.AttributeType:
        """Resolve the type of an attribute access on a node.

        Args:
            node: The base node being accessed.
            attributes: A list of attribute identifiers being accessed.

        Returns:
            The resolved `AttributeType` of the final attribute in the chain.
        """
        raise NotImplementedError

    def resolve_operation(self, operation_name: str) -> operation.Operation:
        """Resolve an operation name to its corresponding `Operation` object.

        Args:
            operation_name: The name of the operation (e.g., "+", "sin").

        Returns:
            The corresponding `Operation` object.

        Raises:
            ValueError: If the operation name is not supported.
        """
        if operation_name in self.supported_operations_map:
            curr_operation = self.supported_operations_map[operation_name]
            return curr_operation
        else:
            raise ValueError(f"Unsupported operation: {operation_name}")
