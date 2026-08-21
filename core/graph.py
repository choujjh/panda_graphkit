"""Directed graph primitives for computation nodes, ports, and connections."""

from . import attribute_types
from . import operation
from typing import Callable, Union
import re


class Graph:
    """Store computation nodes and the connections that carry their data."""

    def __init__(self):
        """Create an empty graph with no nodes or connections."""
        self.nodes = {}
        self.connections = {}
        self._node_name_counters = {}  # Track count per operation name

    def add_node(
        self, name: str = None, operation_=None, node: "Node" = None
    ) -> "Node":
        """Add a node or operation node and return the stored node."""
        # Return node if already in graph
        if node is not None:
            name = node.name
        if name in self.nodes:
            if isinstance(node, BackendNode):
                return self.nodes[name]

        if node is not None:
            self.nodes[node.name] = node
            return node
        if name is None:
            name = operation_.name
        if isinstance(operation_, operation.Operation) and operation_ is not None:
            # Increment counter for this name
            name = self.get_next_numeric_name(name)

            node = Node(name, operation_)
            self.nodes[name] = node
            return node

    def output_dest_ports(self, node: "Node") -> list["InputPort"]:
        """Return input ports connected to outputs of ``node``."""
        output_ports = []
        for output in node.outputs.values():
            connections = list(output.connections.values())
            output_ports.extend([x.destination for x in connections])

        return output_ports

    def output_nodes(self, node: "Node") -> list["Node"]:
        """Return nodes receiving output from ``node``."""
        output_ports = self.output_dest_ports(node)

        return [x.node for x in output_ports]

    def input_src_ports(self, node: "Node") -> list["OutputPort"]:
        """Return output ports connected to inputs of ``node``."""
        input_ports = []
        for input in node.inputs.values():
            connection = input.connection
            if connection is not None:
                input_ports.append(connection.source)

        return input_ports

    def input_nodes(self, node: "Node") -> list["Node"]:
        """Return nodes supplying inputs to ``node``."""
        input_ports = self.input_src_ports(node)

        return [x for x in input_ports.node]

    def get_upstream_node(
        self, node: "Node", predicate: Callable, same_type: bool = True
    ):
        """Walk upstream while nodes satisfy a predicate and type constraints."""
        current = node
        node_type = node.output_types
        if len(node_type) != 1:
            return current
        node_type = node_type[0]
        while True:
            output_nodes = self.output_nodes(current)
            if len(output_nodes) != 1:
                break
            output_node = output_nodes[0]
            output_types = output_node.output_types
            if same_type:
                if not len(output_types) == 1 and node_type.is_compatable(
                    output_types[0]
                ):
                    break
                if any(
                    not node_type.is_compatable(input_port.type_)
                    for input_port in output_node.inputs.values()
                ):
                    break
            if not predicate(output_node):
                break
            current = output_nodes[0]

        return current

    def get_next_numeric_name(self, name):
        """Return the next unique numbered name for a base name."""
        if name not in self._node_name_counters:
            self._node_name_counters[name] = 1
        else:
            self._node_name_counters[name] += 1

        return f"{name}{self._node_name_counters[name]}"

    def connect(self, source: "OutputPort", destination: "InputPort"):
        """Connect an output port to an input port."""
        connection = Connection(source, destination)
        self.connections[connection] = connection
        pass

    def disconnect(
        self,
        destination: Union["InputPort", "OutputPort", "Connection", str],
        force=False,
    ):
        """Remove connections associated with a port, connection, or key."""
        disconnects = []
        if isinstance(destination, InputPort):
            if destination.connection is not None:
                disconnects = [destination.connection]
        elif isinstance(destination, OutputPort):
            disconnects.extend(destination.connections.values())
        elif isinstance(destination, str):
            if destination not in self.connections:
                raise KeyError(f"{destination} key not found in connections")
        elif isinstance(destination, Connection):
            disconnects = [destination]

        for connection in disconnects:
            if force or connection in self.connections:
                connection.source.connections.pop(connection)
                connection.destination.connection = None
            if connection in self.connections:
                self.connections.pop(connection)

    def delete_node(self, node: "Node"):
        """Remove a node and force-disconnect all of its ports."""
        if node.name in self.nodes:
            for input in node.inputs.values():
                if input is not None:
                    self.disconnect(input, force=True)
            for output in node.outputs.values():
                if output != [None]:
                    self.disconnect(output, force=True)
            self.nodes.pop(node.name)

    def delete_port(self, port: "Port"):
        """Remove a port and any connections attached to it."""
        if isinstance(port, InputPort):
            if port.connection is not None:
                self.disconnect(port.connection)
            port.node.inputs.pop(port.name)
        elif isinstance(port, OutputPort):
            if port.connection is not None:
                for connection in port.connections.values():
                    self.disconnect(connection)
            port.node.outputs.pop(port.name)

    def collapse_single_input_node(self, node: "Node"):
        """Replace a single-input operation with its upstream source."""
        if isinstance(node, (ConstNode, BackendNode)):
            return False

        input_ports = self.input_src_ports(node)
        output_ports = self.output_dest_ports(node)

        if len(input_ports) == 1:
            self.delete_node(node)
            for output_port in output_ports:
                self.connect(input_ports[0], output_port)
            return True
        return False

    def get_nodes(self) -> list["Node"]:
        """Return all nodes currently stored in the graph."""
        return list(self.nodes.values())

    def clean_names(self):
        """Renumber node and port names after graph transformations."""
        self._node_name_counters = {}

        for node in self.get_nodes():
            strip_name = re.sub(r"\d+$", "", node.name)

            node.clean_port_names()

            self.nodes.pop(node.name)
            node.name = self.get_next_numeric_name(strip_name)
            self.nodes[node.name] = node

    def print_graph(self):
        """Print a human-readable representation of the graph."""
        print("-" * 45)
        print("Nodes")
        for node in self.get_nodes():
            print(f"  {node.name}: {node}")
            for port_type, port_list in zip(
                ["input", "output"],
                [list(node.inputs.values()), list(node.outputs.values())],
            ):
                print(f"    {port_type}")
                for port in port_list:
                    if isinstance(port, OutputPort):
                        for x in port.connections.values():
                            print(f"      {x} - ({port.type_.name})")
                    elif isinstance(port, InputPort):
                        print(f"      {port.name}: {port}")

        print("Connection")
        for connection in self.connections.values():
            print(f"  {connection}")

        print("Node Name Counters")
        for key, value in self._node_name_counters.items():
            print(f"  {key}: {value}")


class Port:
    """Base class for input and output ports on a node.

    Attributes:
        name: The port name.
        type_: The AttributeType of this port.
        node: The Node this port belongs to.
    """

    def __init__(self, name: str, type_: attribute_types.AttributeType, node: "Node"):
        """Create a port attached to a node with the given type."""
        self.name = name
        self.type_ = type_
        self.node = node

    def __str__(self):
        """Return a compact description of this port and its owner node."""
        return f"{type(self).__name__}(name: {self.name}, type: {self.type_.name}, node:{self.node.name})"


class InputPort(Port):
    """An input port that receives data from another node's output.

    Attributes:
        connection: The Connection feeding into this port (or None if unconnected).
    """

    def __init__(self, name: str, type_: attribute_types.AttributeType, node: "Node"):
        """Create an input port with no incoming connection."""
        super().__init__(name, type_, node)
        self.connection = None


class OutputPort(Port):
    """An output port that produces data for other nodes."""

    def __init__(self, name, type_, node):
        """Create an output port with no outgoing connections."""
        super().__init__(name, type_, node)
        self.connections = {}


class BackendInputPort(InputPort):
    """Input port that also stores a backend attribute path."""

    def __init__(self, name, type_, node, attribute_list: list = []):
        """Create a backend input port for an attribute path."""
        super().__init__(name, type_, node)
        self.attribute_list = attribute_list

    def __str__(self):
        """Return the port description including backend attributes."""
        curr_str = super().__str__()
        curr_str = curr_str.replace(")", f"attrs: {self.attribute_list})")

        return curr_str


class BackendOutputPort(OutputPort):
    """Output port that also stores a backend attribute path."""

    def __init__(self, name, type_, node, attribute_list: list = []):
        """Create a backend output port for an attribute path."""
        super().__init__(name, type_, node)
        self.attribute_list = attribute_list

    def __str__(self):
        """Return the port description including backend attributes."""
        curr_str = super().__str__()
        curr_str = curr_str.replace(")", f"attrs: {self.attribute_list})")

        return curr_str


class Node:
    """Represent a computation operation and its input and output ports."""

    _id_counter = 0
    _modify_attr_name = True
    _input_port_type = InputPort
    _output_port_type = OutputPort

    def __init__(self, name: str, operation: operation.Operation):
        """Create a node with a unique id and no ports."""
        self.id = Node._id_counter
        Node._id_counter += 1
        self.name = name
        self.operation = operation
        self.inputs = {}
        self.outputs = {}
        self._port_counters = {}

    @property
    def output_types(self) -> list[attribute_types.AttributeType]:
        """Return the types of all output ports on this node."""
        output_ports = list(self.outputs.values())
        if len(output_ports) == 0:
            return []
        return [x.type_ for x in output_ports]

    def add_input(
        self, type_: attribute_types.AttributeType, name: str = None
    ) -> "InputPort":
        """Add and return an input port, optionally with a custom name."""
        return self._add_port(
            name if name is not None else "input", type_, self._input_port_type
        )

    def add_output(
        self, type_: attribute_types.AttributeType, name: str = None
    ) -> "OutputPort":
        """Add and return an output port, optionally with a custom name."""
        return self._add_port(
            name if name is not None else "output", type_, self._output_port_type
        )

    def clean_port_names(self):
        """Renumber repeated input and output port names."""
        self._port_counters = {}
        for key, node in list(self.inputs.items()):
            stripped_name = re.sub(r"\d+$", "", node.name)
            if node.name == stripped_name:
                continue
            self.inputs.pop(key)
            node.name = self.get_next_numeric_port_name(stripped_name)
            self.inputs[node.name] = node
        for key, node in list(self.outputs.items()):
            stripped_name = re.sub(r"\d+$", "", node.name)
            if node.name == stripped_name:
                continue
            self.outputs.pop(key)
            node.name = self.get_next_numeric_port_name(stripped_name)
            self.outputs[node.name] = node

    def _add_port(
        self, name: str, type_: attribute_types.AttributeType, port_type: Callable
    ) -> "Port":
        """Create, register, and return a port of the requested type."""
        name = self.get_next_numeric_port_name(name)
        port_map = self.outputs
        if port_type == InputPort:
            port_map = self.inputs
        port = port_type(name, type_, self)
        port_map[name] = port
        return port

    def get_next_numeric_port_name(self, name: str) -> str:
        """Return the next unique numbered name for a port base name."""
        if not self._modify_attr_name:
            return name

        if name not in self._port_counters:
            self._port_counters[name] = 1
        else:
            self._port_counters[name] += 1

        name = f"{name}{self._port_counters[name]}"

        return name

    def __repr__(self):
        """Return a representation containing node identity and port types."""
        inputs = [f"({x.type_}){x.name}" for x in self.inputs.values()]
        outputs = [f"({x.type_}){x.name}" for x in self.outputs.values()]

        return f"{type(self).__name__}(NAME: {self.name}, ID: {self.id}, INPUTS: [{','.join(inputs)}], OUTPUTS: [{','.join(outputs)}])"


class ConstNode(Node):
    """Node representing a compile-time constant value."""

    def __init__(self, name, type_: attribute_types.AttributeType, value):
        """Create a constant node and its single output port."""
        super().__init__(name, None)
        self.value = value
        self.output_port = self.add_output(type_=type_)

    def __repr__(self):
        """Return the node representation including the constant value."""
        rep = super().__repr__()
        rep = rep.replace("INPUTS:", f"VAL: {self.value}, INPUTS:")
        return rep

    def clean_port_names(self):
        """Leave constant port names unchanged."""
        pass


class BackendNode(Node):
    """Node representing a value resolved from a backend attribute."""

    _modify_attr_name = False
    _input_port_type = BackendInputPort
    _output_port_type = BackendOutputPort

    def __init__(self, name):
        """Create a backend node with the given attribute owner name."""
        super().__init__(name, None)

    def clean_port_names(self):
        """Leave backend attribute port names unchanged."""
        pass


class Connection:
    """Link one output port to one compatible input port."""

    def __init__(self, source: OutputPort, destination: InputPort):
        """Create and register a typed connection between two ports."""
        # Type compatibility check
        if not source.type_.is_compatable(destination.type_):
            raise TypeError(
                f"Cannot connect {source.type_} (from {source.name}) "
                f"to {destination.type_} (to {destination.name})"
            )

        self.source = source
        self.source.connections[self] = self
        self.destination = destination
        self.destination.connection = self

    def __repr__(self):
        """Return the source-to-destination connection path."""
        return f"{self.source.node.name}[{self.source.name}] -> {self.destination.node.name}[{self.destination.name}]"
