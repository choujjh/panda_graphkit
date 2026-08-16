from . import ast
from core import graph


class Compiler:
    def __init__(self):
        self.graph = graph.Graph()
        self.variables = {}

    def ast_to_graph(self, ast_node: ast.ASTNode, prefix: str, name: str) -> graph.Port:
        nice_name = f"{name}_" if name != "" else ""
        full_prefix = f"{prefix}_{nice_name}"

        if isinstance(ast_node, ast.Assignment):
            if isinstance(ast_node.target, ast.AttributeAccess):
                input_port = self._attribute_access_to_graph(
                    ast_node.target, as_output_port=False
                )
                print(ast_node.target.node)
                output_port = self.ast_to_graph(ast_node.value, prefix, name)

                self.graph.connect(output_port, input_port)
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

            node = self.graph.add_node(
                f"{full_prefix}{ast_node.operation_.name}", ast_node.operation_
            )

            # add ports
            left_input = ast_node.left
            right_input = ast_node.right
            for input, port in zip([left_input, right_input], [left_port, right_port]):
                input_port = node.add_input(type_=input.type_)
                self.graph.connect(port, input_port)
            output = node.add_output(type_=ast_node.type_)

            return output

        if isinstance(ast_node, ast.FunctionCall):
            node = self.graph.add_node(
                f"{full_prefix}{ast_node.function.name}", ast_node.operation_
            )

            for attribute in ast_node.arguments:
                child_port = self.ast_to_graph(attribute, prefix, name)
                input_port = node.add_input(attribute.type_)

                self.graph.connect(child_port, input_port)

            output = node.add_output(type_=ast_node.type_)

            return output

        if isinstance(ast_node, ast.Identifier):
            if ast_node.name not in self.variables:
                raise RuntimeError(f"variable {ast_node.name} not assigned before use")
            return self.variables[ast_node.name]

        if isinstance(ast_node, ast.Literal):
            type_name = ast_node.type_.name.lower()
            name = f"{full_prefix}{type_name}Const"

            node = self.graph.add_node(
                node=graph.ConstNode(
                    name=self.graph.get_next_numeric_name(name),
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
        name = ast_node.node.name

        node = self.graph.add_node(node=graph.BackendNode(name=name))

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

    # TODO
    # sum for multiple adds?
    # attribute types, is_compatable_type
