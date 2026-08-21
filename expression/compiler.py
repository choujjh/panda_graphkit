"""Compile analyzed expression ASTs into optimized computation graphs."""

from . import ast
from core import graph, operation
from backend import base
from backend.base import BackendNodeOptimization
from core import attribute_types
import operations.math as ops_math


class Compiler:
    """Build and optimize a graph from a semantically analyzed AST."""

    def __init__(self, backend: base.Backend):
        """Initialize a compiler using the given backend."""
        self.graph_ = graph.Graph()
        self.variables = {}
        self.backend = backend

    def compile(self, ast_node: ast.ASTNode, prefix: str, name: str):
        """Compile an AST, optimize its graph, and normalize its names."""
        self.ast_to_graph(ast_node, prefix, name)
        self.optimize_graph(prefix, name)
        self.graph_.clean_names()

    def ast_to_graph(self, ast_node: ast.ASTNode, prefix: str, name: str) -> graph.Port:
        """Convert one AST node and its children into graph ports."""
        nice_name = f"{name}_" if name != "" else ""
        full_prefix = f"{prefix}_{nice_name}"

        if isinstance(ast_node, ast.Assignment):
            if isinstance(ast_node.target, ast.AttributeAccess):
                input_port = self._attribute_access_to_graph(
                    ast_node.target, as_output_port=False
                )
                output_port = self.ast_to_graph(ast_node.value, prefix, name)

                self.graph_.connect(output_port, input_port)
                return output_port

            if isinstance(ast_node.target, ast.Identifier):
                name = ast_node.target.name
                output_port = self.ast_to_graph(ast_node.value, prefix, name)
                self.variables[ast_node.target.name] = output_port
                return output_port

        if isinstance(ast_node, ast.AttributeAccess):
            port = self._attribute_access_to_graph(ast_node=ast_node)

            return port

        if isinstance(ast_node, ast.BinaryOperation):
            left_port = self.ast_to_graph(ast_node.left, prefix, name)
            right_port = self.ast_to_graph(ast_node.right, prefix, name)

            node = self.graph_.add_node(
                f"{full_prefix}{ast_node.operation_.name}", ast_node.operation_
            )

            # add ports
            left_input = ast_node.left
            right_input = ast_node.right
            for input, port in zip([left_input, right_input], [left_port, right_port]):
                input_port = node.add_input(type_=input.type_)
                self.graph_.connect(port, input_port)
            output = node.add_output(type_=ast_node.type_)

            return output

        if isinstance(ast_node, ast.FunctionCall):
            node = self.graph_.add_node(
                f"{full_prefix}{ast_node.function.name}", ast_node.operation_
            )

            for attribute in ast_node.arguments:
                child_port = self.ast_to_graph(attribute, prefix, name)
                input_port = node.add_input(attribute.type_)

                self.graph_.connect(child_port, input_port)

            output = node.add_output(type_=ast_node.type_)

            return output

        if isinstance(ast_node, ast.Identifier):
            if ast_node.name not in self.variables:
                raise RuntimeError(f"variable {ast_node.name} not assigned before use")
            return self.variables[ast_node.name]

        if isinstance(ast_node, ast.Literal):
            node = self.graph_.add_node(
                node=graph.ConstNode(
                    name=self.graph_.get_next_numeric_name(
                        f"{ast_node.type_.name}Const"
                    ),
                    type_=ast_node.type_,
                    value=ast_node.value,
                )
            )
            port = node.output_port

            return port

        if isinstance(ast_node, ast.Program):
            first_node = None
            for node in ast_node.statments:
                first_node = self.ast_to_graph(node, prefix, name)
            return first_node

        raise ValueError(f"ast node type not supported: {ast_node}")

    def _attribute_access_to_graph(
        self, ast_node: ast.AttributeAccess, as_output_port=True
    ) -> graph.Port:
        """Convert a backend attribute access into an input or output port."""
        name = ast_node.node.name

        node = self.graph_.add_node(node=graph.BackendNode(name=name))

        attributes = []
        for attribute in ast_node.attributes:
            if isinstance(attribute, ast.Literal):
                attributes.append(attribute.value)
            elif isinstance(attribute, ast.Identifier):
                attributes.append(attribute.name)
        name = "".join([f"[{x}]" for x in attributes])

        port = None
        if as_output_port:
            port = node.add_output(type_=ast_node.type_, name=name)
            port.attribute_list = attributes
        else:
            port = node.add_input(type_=ast_node.type_, name=name)
            port.attribute_list = attributes

        return port

    def optimize_graph(self, prefix: str, name: str):
        """Repeatedly apply backend optimization passes to the graph."""
        changed = True
        iterations = 0
        while changed and iterations < 300:
            iterations += 1
            changed = False

            for (
                backend_node_optimize
            ) in self.backend.resolve_backend_node_optimization():
                changed |= self._flatten_operation(backend_node_optimize, prefix, name)

                changed |= self._eliminate_identity_operations()

            changed |= self._combine_constants()

    def _flatten_operation(
        self, backend_node_optimize: BackendNodeOptimization, prefix: str, name: str
    ) -> bool:
        """Flatten chains of compatible operations into one operation node."""
        nice_name = f"{name}_" if name != "" else ""
        full_prefix = f"{prefix}_{nice_name}"

        changed = False
        deleted_nodes = []
        replaced_ops = backend_node_optimize.checked_ops
        merge_op = backend_node_optimize.operand

        for node in list(self.graph_.get_nodes()):
            top_node = self.graph_.get_upstream_node(
                node, lambda x: x.operation in replaced_ops
            )
            if (
                node in deleted_nodes
                or node.operation not in replaced_ops
                or top_node == node
            ):
                continue
            dest_connections = self.graph_.output_dest_ports(top_node)
            output_port_type = list(top_node.outputs.values())[0].type_
            nodes, output_ports = self._traverse_flatten_nodes(top_node, replaced_ops)
            if len(nodes) == 1:
                continue

            deleted_nodes.extend(nodes)
            changed = True
            for curr_node in nodes:
                self.graph_.delete_node(curr_node)

            added_node = self.graph_.add_node(
                name=f"{full_prefix}{merge_op.name}", operation_=merge_op
            )
            for output_port in output_ports:
                added_input = added_node.add_input(output_port.type_)
                self.graph_.connect(output_port, added_input)

            dest_port = added_node.add_output(output_port_type)
            for dest in dest_connections:
                self.graph_.connect(dest_port, dest)

        return changed

    def _traverse_flatten_nodes(
        self,
        node: graph.Node,
        operations: list[operation.Operation],
        types_: attribute_types.AttributeType = None,
    ) -> tuple[list[graph.Node], list[graph.OutputPort]]:
        """Collect a compatible operation chain and its external inputs."""
        nodes = list()
        output_ports = list()

        if types_ is None:
            output_types = node.output_types
            if len(output_types) != 1:
                return [node], []
            types_ = node.output_types[0]

        for input_port in self.graph_.input_src_ports(node):
            if input_port.node.operation in operations:
                child_nodes, child_output_ports = self._traverse_flatten_nodes(
                    input_port.node, operations, types_
                )
                nodes.extend(child_nodes)
                output_ports.extend(child_output_ports)
            else:
                output_ports.append(input_port)

        nodes.append(node)

        return nodes, output_ports

    def _eliminate_identity_operations(self) -> bool:
        """Remove identity constants and collapse resulting single-input nodes."""
        changed = False
        deleted_nodes = []
        for node in list(self.graph_.get_nodes()):
            if node in deleted_nodes:
                continue
            identity_val = None
            for backend_optimize in self.backend.resolve_backend_node_optimization():
                if node.operation in backend_optimize.checked_ops:
                    identity_val = backend_optimize.identity_value
            if identity_val is None:
                continue

            for input_port in list(node.inputs.values()):
                if input_port.connection is None:
                    continue
                source_port = input_port.connection.source
                source_node = input_port.connection.source.node

                if isinstance(source_node, graph.ConstNode):
                    if source_node.value == identity_val:
                        changed = True
                        self.graph_.delete_port(input_port)
                        if len(list(source_port.connections.values())) == 0:
                            deleted_nodes.append(source_node)
                            self.graph_.delete_node(source_node)

            changed |= self.graph_.collapse_single_input_node(node)

        return changed

    def _combine_constants(self) -> bool:
        """Evaluate operations whose inputs are all compile-time constants."""
        changed = False
        deleted_nodes = []
        for node in list(self.graph_.get_nodes()):
            if node in deleted_nodes:
                continue
            input_connections = [
                x.connection
                for x in list(node.inputs.values())
                if x.connection is not None
            ]
            input_connections = [
                x
                for x in input_connections
                if isinstance(x.source.node, graph.ConstNode)
            ]

            if len(input_connections) <= 1:
                continue

            val = None
            type_ = attribute_types.infer_return_type(
                [x.source.type_ for x in input_connections]
            )

            constructor = self.backend.resolve_constructor(node.operation.name)
            # if it's a constructed data type
            if constructor is not None:
                if len(input_connections) not in constructor.num_elements:
                    continue

                changed = True
                val = [x.source.node.value for x in input_connections]
                val = constructor.math_class.from_values(*val)

                type_ = constructor.attr_type
            else:
                for connection in input_connections:
                    if val is None:
                        val = connection.source.node.value
                    elif node.operation in (ops_math.ADD, ops_math.SUM):
                        val = val + connection.source.node.value
                    elif node.operation in (ops_math.MULTIPLY, ops_math.PRODUCT):
                        val = val * connection.source.node.value

            for connection in input_connections:
                deleted_nodes.append(connection.source.node)
                self.graph_.disconnect(connection)
                self.graph_.delete_port(connection.destination)
                if (
                    len(list(self.graph_.output_dest_ports(connection.source.node)))
                    == 0
                ):
                    self.graph_.delete_node(connection.source.node)

            new_const = self.graph_.add_node(
                node=graph.ConstNode(
                    self.graph_.get_next_numeric_name(f"{type_.name}Const"),
                    type_=type_,
                    value=val,
                )
            )
            input_port = node.add_input(type_=type_)
            self.graph_.connect(new_const.output_port, input_port)

            self.graph_.collapse_single_input_node(node)

        return changed