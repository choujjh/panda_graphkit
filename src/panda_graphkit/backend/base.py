"""Abstract base class for graph operation backends.

This module defines the Backend ABC which provides the interface for
resolving operations and attributes. Concrete implementations should
provide operation and attribute resolution for specific graph systems.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
from collections.abc import Iterator

from ..core import (
    AttributeType,
    MATRIX4,
    VECTOR,
    Operation,
    MathMatrix,
    MathVector,
    Signature,
    Graph,
    Node,
    Port,
    InputPort,
)
from ..operations import math as ops_math

if TYPE_CHECKING:
    from ..expression import ast


@dataclass(frozen=True)
class NodeMap:
    """Describe how a graph operation maps onto a backend node.

    The mapping keeps the operation signature, backend node name, and the
    attribute names used for input and output ports so graph connections can be
    materialized correctly on a specific backend.
    """

    operation_name: str
    signature: Signature
    mapped_node_type: str
    input_attributes: tuple[str]
    output_attributes: tuple[str]
    invert_input_indicies: bool = False
    node_init: dict[str:Any] = field(default_factory=dict)

    def attr_mapping(self) -> dict[str : dict[str : str | bool]]:
        """Map signature parameter names to backend attribute names.

        Returns:
            A mapping with ``input`` and ``output`` entries. Each parameter
            entry contains its backend name and whether it is variadic.

        Raises:
            ValueError: If signature and backend attribute counts differ.
        """
        for sig, attr in [
            (self.signature.inputs, self.input_attributes),
            (self.signature.outputs, self.output_attributes),
        ]:
            len_sig = len(sig)
            len_attr = len(attr)
            if len_sig != len_attr:
                raise ValueError(
                    f"attribute mapping len mismatch. signature is len {len_sig} and attribute identifiers is len {len_attr}"
                )
        attr_map = {}
        attr_map["input"] = {
            parm.name: {"name": input_name, "variadict": parm.variadict}
            for parm, input_name in zip(self.signature.inputs, self.input_attributes)
        }
        attr_map["output"] = {
            parm.name: {"name": output_name, "variadict": parm.variadict}
            for parm, output_name in zip(self.signature.outputs, self.output_attributes)
        }

        return attr_map

    def get_backend_attr_name(self, port: Port) -> list[str, int]:
        """Return the backend attribute path for a graph port.

        Variadic parameters are returned as an attribute name and the port's
        index. Fixed parameters are returned as a one-item attribute path.

        Args:
            port: Graph input or output port to resolve.

        Returns:
            A backend attribute path, or ``None`` when the port index is not
            mapped by this node map.
        """
        port_index = port.get_port_index()
        is_input_port = isinstance(port, InputPort)
        if self.invert_input_indicies:
            port_index = port.node.get_port_len(is_input_port) - port_index - 1
        attr_map = self.attr_mapping()["input" if is_input_port else "output"]
        attrs = self.input_attributes if is_input_port else self.output_attributes
        attr_list = list(attr_map.values())
        if len(attr_list) > 0 and attr_list[0]["variadict"]:
            return [attr_list[0]["name"], port_index]
        if port_index < len(attrs):
            return [attrs[port_index]]


@dataclass(frozen=True)
class OperationMap:
    """Group the backend node mappings for one graph operation.

    Each operation may have several valid backend node variants depending on the
    signature being used in the graph.
    """

    operation: Operation
    node_maps: tuple[NodeMap]

    def sig_map(self) -> dict[Signature : list[NodeMap]]:
        """Group node mappings by their operation signature.

        Returns:
            A dictionary whose keys are signatures and whose values preserve
            the node mappings registered for each signature.
        """
        ret_map = {}
        for node_map in self.node_maps:
            if node_map.signature not in ret_map.keys():
                ret_map[node_map.signature] = [node_map]
            else:
                ret_map[node_map.signature].append(node_map)
        return ret_map


@dataclass(frozen=True)
class BackendNodeOptimization:
    """Describe an optimization that combines compatible operations."""

    checked_ops: list[Operation]
    operand: Operation
    identity_value: Any


@dataclass(frozen=True)
class ConstructorOps:
    """Describe how a backend constructs a compound math value."""

    signature: Operation
    math_class: MathMatrix | MathVector
    attr_type: AttributeType
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
            math_class=MathVector,
            attr_type=VECTOR,
            num_elements=(3, 4),
        ),
        ops_math.MATRIX.name: ConstructorOps(
            signature=ops_math.MATRIX,
            math_class=MathMatrix,
            attr_type=MATRIX4,
            num_elements=(16),
        ),
    }

    @abstractmethod
    def resolve_attribute_type(
        self, node: ast.Identifier, attributes: list[ast.Identifier]
    ) -> AttributeType:
        """Resolve the type of an attribute access on a node.

        Args:
            node: The base node being accessed.
            attributes: A list of attribute identifiers being accessed.

        Returns:
            The resolved `AttributeType` of the final attribute in the chain.
        """
        raise NotImplementedError

    @abstractmethod
    def _create_nodes(self, graph: Graph) -> dict[Node:Any]:
        """Create backend nodes corresponding to graph nodes.

        Args:
            graph: Graph whose nodes should be materialized by the backend.

        Returns:
            A mapping from graph nodes or names to backend node data.
        """
        raise NotImplementedError

    @abstractmethod
    def _create_connections(self, graph: Graph, node_dict: dict[Node:Any]):
        """Create backend connections for the graph's registered edges.

        Args:
            graph: Graph containing the connections to materialize.
            node_dict: Backend node data returned by :meth:`_create_nodes`.
        """
        raise NotImplementedError

    def build_graph(self, graph: Graph):
        """Materialize graph nodes and then connect their backend attributes.

        Args:
            graph: Graph to build in the target backend.
        """
        node_dict = self._create_nodes(graph)
        self._create_connections(graph, node_dict)

    def resolve_operation(self, operation_name: str) -> Operation:
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
