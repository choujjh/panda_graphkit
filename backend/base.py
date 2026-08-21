"""Abstract base class for graph operation backends.

This module defines the Backend ABC which provides the interface for
resolving operations and attributes. Concrete implementations should
provide operation and attribute resolution for specific graph systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from collections.abc import Iterator

import core.attribute_types as attribute_types
import core.operation as operation
import core.math as core_math
import operations.math as ops_math
import expression.ast as ast


@dataclass(frozen=True)
class BackendNodeOptimization:
    """Describe an optimization that combines compatible operations."""

    checked_ops: list[operation.Operation]
    operand: operation.Operation
    identity_value: Any


@dataclass(frozen=True)
class ConstructorOps:
    """Describe how a backend constructs a compound math value."""

    signature: operation.Operation
    math_class: core_math.Matrix | core_math.Vector
    attr_type: attribute_types.AttributeType
    num_elements: tuple[int]


class Backend(ABC):
    """Abstract base class for graph operation backends.

    Provides an interface for resolving operation names to Operation
    objects and resolving attribute chains to AttributeType. Subclasses
    should implement resolve_attribute for their specific graph system.

    Attributes:
        supported_operations_map: Dict mapping operation names to Operation
            objects for the operations this backend supports.
    """

    supported_operations_map = {
        "+": ops_math.ADD,
        "-": ops_math.SUBTRACT,
        "*": ops_math.MULTIPLY,
        "/": ops_math.DIVIDE,
        "**": ops_math.POWER,
        "^": ops_math.POWER,
        ops_math.SIN.name: ops_math.SIN,
        ops_math.COS.name: ops_math.COS,
        ops_math.REMAP.name: ops_math.REMAP,
        ops_math.ADD.name: ops_math.ADD,
        ops_math.SUM.name: ops_math.SUM,
        ops_math.SUBTRACT.name: ops_math.SUBTRACT,
        ops_math.MULTIPLY.name: ops_math.MULTIPLY,
        ops_math.PRODUCT.name: ops_math.PRODUCT,
        ops_math.DIVIDE.name: ops_math.DIVIDE,
        ops_math.POWER.name: ops_math.POWER,
        ops_math.VECTOR.name: ops_math.VECTOR,
        ops_math.MATRIX.name: ops_math.MATRIX,
    }
    optimize_operations = [
        BackendNodeOptimization(
            checked_ops=[ops_math.ADD, ops_math.SUM],
            operand=ops_math.SUM,
            identity_value=0,
        ),
        BackendNodeOptimization(
            checked_ops=[ops_math.MULTIPLY, ops_math.PRODUCT],
            operand=ops_math.PRODUCT,
            identity_value=1,
        ),
    ]
    constructors = {
        ops_math.VECTOR.name: ConstructorOps(
            signature=ops_math.VECTOR,
            math_class=core_math.Vector,
            attr_type=attribute_types.VECTOR,
            num_elements=(3, 4),
        ),
        ops_math.MATRIX.name: ConstructorOps(
            signature=ops_math.MATRIX,
            math_class=core_math.Matrix,
            attr_type=attribute_types.MATRIX4,
            num_elements=(16),
        ),
    }

    @abstractmethod
    def resolve_attribute_type(
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

    def resolve_constructor(self, operation_name: str) -> ConstructorOps:
        """Return constructor metadata for an operation name, if registered."""
        if operation_name in self.constructors:
            curr_operation = self.constructors[operation_name]
            return curr_operation
        return None

    def resolve_backend_node_optimization(self) -> Iterator[BackendNodeOptimization]:
        """Yield the optimization rules supported by this backend."""
        for curr in self.optimize_operations:
            yield curr
