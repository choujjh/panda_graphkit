from . import attribute_types
from . import operation
from typing import Callable, Union


class Graph:
    # Directed acyclic graph for computation nodes and data flow

    def __init__(self):
        self.nodes = {}
        self.connections = {}
        self._operation_counters = {}  # Track count per operation name

    def add_node(
        self, name: str = None, operation_=None, node: "Node" = None
    ) -> "Node":
        # Return node if already in graph
        if node is not None:
            name = node.name
        if name in self.nodes.keys():
            if isinstance(node, BackendNode):
                return self.nodes[name]

        if node is not None:
            self.nodes[node.name] = node
            return node
        if isinstance(operation_, operation.Operation) and operation_ is not None:
            # Increment counter for this name
            if name not in self._operation_counters:
                self._operation_counters[name] = 1
            else:
                self._operation_counters[name] += 1

            node_name = f"{name}{self._operation_counters[name]}"
            node = Node(node_name, operation_)
            self.nodes[node_name] = node
            return node

    def get_next_numeric_name(self, name):
        if name not in self._operation_counters:
            self._operation_counters[name] = 1
        else:
            self._operation_counters[name] += 1

        return f"{name}{self._operation_counters[name]}"

    def connect(self, source: "OutputPort", destination: "InputPort"):
        connection = Connection(source, destination)
        self.connections[connection] = connection
        pass

    def disconnect(self, destination: Union["InputPort", "Connection"]):
        pass

    def get_node_dependencies(self, node: "Node") -> list["Node"]:
        # Get upstream nodes
        pass

    def get_dependent_nodes(self, node: "Node") -> list["Node"]:
        # Get downstream nodes
        pass

    def topological_sort(self) -> list["Node"]:
        # Sort nodes by execution order
        pass


class Port:
    """Base class for input and output ports on a node.

    Attributes:
        name: The port name.
        type_: The AttributeType of this port.
        node: The Node this port belongs to.
    """

    def __init__(self, name: str, type_: attribute_types.AttributeType, node: "Node"):
        self.name = name
        self.type_ = type_
        self.node = node

    def __str__(self):
        return f"{type(self).__name__}(name: {self.name}, type: {self.type_.name}, node:{self.node.name})"


class InputPort(Port):
    """An input port that receives data from another node's output.

    Attributes:
        connection: The Connection feeding into this port (or None if unconnected).
    """

    def __init__(self, name: str, type_: attribute_types.AttributeType, node: "Node"):
        super().__init__(name, type_, node)
        self.connection = None


class OutputPort(Port):
    """An output port that produces data for other nodes."""

    pass


class BackendInputPort(InputPort):
    def __init__(self, name, type_, node, attribute_list: list = []):
        super().__init__(name, type_, node)
        self.attribute_list = attribute_list

    def __str__(self):
        curr_str = super().__str__()
        curr_str = curr_str.replace(")", f"attrs: {self.attribute_list})")

        return curr_str


class BackendOutputPort(OutputPort):
    def __init__(self, name, type_, node, attribute_list: list = []):
        super().__init__(name, type_, node)
        self.attribute_list = attribute_list

    def __str__(self):
        curr_str = super().__str__()
        curr_str = curr_str.replace(")", f"attrs: {self.attribute_list})")

        return curr_str


class Node:
    # Computation node wrapping an Operation
    _id_counter = 0
    _modify_attr_name = True
    _input_port_type = InputPort
    _output_port_type = OutputPort

    def __init__(self, name: str, operation: operation.Operation):
        self.id = Node._id_counter
        Node._id_counter += 1
        self.name = name
        self.operation = operation
        self.inputs = {}
        self.outputs = {}
        self._port_counters = {}

    def add_input(
        self, type_: attribute_types.AttributeType, name: str = None
    ) -> "InputPort":
        return self._add_port(
            name if name is not None else "input", type_, self._input_port_type
        )

    def add_output(
        self, type_: attribute_types.AttributeType, name: str = None
    ) -> "OutputPort":
        return self._add_port(
            name if name is not None else "output", type_, self._output_port_type
        )

    def _add_port(
        self, name: str, type_: attribute_types.AttributeType, port_type: Callable
    ) -> "Port":
        if self._modify_attr_name:
            if name not in self._port_counters:
                self._port_counters[name] = 1
            else:
                self._port_counters[name] += 1

            name = f"{name}{self._port_counters[name]}"

        port_map = self.outputs
        if port_type == InputPort:
            port_map = self.inputs
        port = port_type(name, type_, self)
        port_map[name] = port
        return port

    def __repr__(self):
        lines = [f"{type(self).__name__}(id: {self.id}, name: {self.name}):"]

        for port_type, port_dict in zip(
            ["inputs", "outputs"], [self.inputs, self.outputs]
        ):
            lines.append(f"  {port_type}:")
            for input in port_dict.values():
                lines.append(f"    {input}")

        return "\n".join(lines)


class ConstNode(Node):
    def __init__(self, name, type_: attribute_types.AttributeType, value):
        super().__init__(name, None)
        self.value = value
        self.output_port = self.add_output(type_=type_)


class BackendNode(Node):
    _modify_attr_name = False
    _input_port_type = BackendInputPort
    _output_port_type = BackendOutputPort

    def __init__(self, name):
        super().__init__(name, None)


class Connection:
    def __init__(self, source: OutputPort, destination: InputPort):
        # Type compatibility check
        if not self._types_compatible(source.type_, destination.type_):
            raise TypeError(
                f"Cannot connect {source.type_} (from {source.name}) "
                f"to {destination.type_} (to {destination.name})"
            )

        self.source = source
        self.destination = destination
        self.destination.connection = self

    def _types_compatible(
        self,
        source_type: attribute_types.AttributeType,
        destination_type: attribute_types.AttributeType,
    ) -> bool:
        return source_type.is_compatable(destination_type)

    def __repr__(self):
        return f"{self.source} -> {self.destination}"
