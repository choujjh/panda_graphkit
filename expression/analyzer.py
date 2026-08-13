"""Type analysis and semantic checking for expression AST nodes.

This module provides the `Analyzer` class which traverses an AST and
performs type checking, type inference, and semantic validation. It
resolves operations and attributes using the backend, and infers
numeric return types based on input argument types.
"""

import expression.ast as ast
import core.attribute_types as attribute_types
import core.operation as operation
import backend.base as base


class Analyzer:
    """Analyzes and type-checks expression AST nodes.

    The analyzer traverses an AST and assigns type information to nodes,
    validates operations against their signatures, and infers types for
    function calls and binary operations.

    Attributes:
        backend: The backend used to resolve operations and attributes.
        variables: Dict mapping variable names to their AST nodes for lookup.
    """

    def __init__(self, backend: base.Backend):
        """Initialize the analyzer with a backend.

        Args:
            backend: The backend to use for resolving operations and attributes.
        """
        self.backend = backend
        self.variables = {}

    def analyze(self, node):
        """Analyze an AST node and assign type information.

        Dispatches to specialized analysis methods based on node type
        (literals, binary operations, function calls, etc.).

        Args:
            node: An AST node to analyze.

        Returns:
            The inferred type of the node.

        Raises:
            NameError: If an undefined variable is referenced.
            TypeError: If the node type is unsupported.
        """
        if isinstance(node, ast.Literal):
            return self.analyze_literal(node)

        if isinstance(node, ast.BinaryOperation):
            return self.analyze_binary(node)

        if isinstance(node, ast.FunctionCall):
            return self.analyze_function_call(node)

        if isinstance(node, ast.Identifier):
            if node.name in self.variables:
                node.type_ = self.variables[node.name].type_
                return node.type_
            else:
                raise NameError(f"Undefined variable: {node.name}")

        if isinstance(node, ast.AttributeAccess):
            return self.analyze_attribute_access(node)

        if isinstance(node, ast.Assignment):
            return self.analyze_assignment(node)

        if isinstance(node, ast.Program):
            return self.analyze_program(node)

        raise TypeError(f"Unsupported AST node: {type(node).__name__}")

    def analyze_literal(self, node: ast.Literal):
        """Analyze a literal node and determine its type.

        Infers the type based on the Python value (int, float, str).
        For numeric strings, determines if they are INT or FLOAT.

        Args:
            node: A Literal AST node.

        Raises:
            TypeError: If the literal type cannot be determined.
        """
        value = node.value

        str_type = attribute_types.STRING
        float_type = attribute_types.FLOAT
        int_type = attribute_types.INT

        if isinstance(value, int):
            node.type_ = int_type
        if isinstance(value, float):
            node.type_ = float_type

        if isinstance(value, str):
            if len(value) == 0:
                node.type_ = str_type
            if value[0] not in "-+":
                node.type_ = str_type
            decimal_count = value.count(".")
            if decimal_count > 1:
                node.type_ = str_type
            for char in value[1:]:
                if not char.isdigit() and char != ".":
                    node.type_ = str_type
            if decimal_count == 1 and value.find(".") != len(value) - 1:
                node.type_ = float_type
            else:
                node.type_ = int_type

        if node.type_ is None:
            raise TypeError(f"Unsupported literal type: {type(node.value).__name__}")

    def analyze_binary(self, node: ast.BinaryOperation):
        """Analyze a binary operation node.

        Recursively analyzes left and right operands, resolves the operation
        from the backend, and checks if the operand types match a signature.

        Args:
            node: A BinaryOperation AST node.

        Returns:
            The inferred return type of the operation.
        """
        self.analyze(node.left)
        self.analyze(node.right)

        left_type = node.left.type_
        right_type = node.right.type_

        operation = self.backend.resolve_operation(node.operation)

        signature_check = self.check_signature(operation, [left_type, right_type])
        if signature_check is not None:
            node.type_ = signature_check

        return node.type_

    def analyze_function_call(self, node: ast.FunctionCall):
        """Analyze a function call node.

        Recursively analyzes all arguments, resolves the function name to
        an operation from the backend, and checks if argument types match
        a signature.

        Args:
            node: A FunctionCall AST node.

        Returns:
            The inferred return type of the function.

        Raises:
            TypeError: If the function is not an Identifier.
        """
        for argument in node.arguments:
            self.analyze(argument)

        if isinstance(node.function, ast.Identifier):
            operation = self.backend.resolve_operation(node.function.name)
        else:
            raise TypeError(
                f"Unsupported function type: {type(node.function).__name__}"
            )

        signature_check = self.check_signature(
            operation, [arg.type_ for arg in node.arguments]
        )
        if signature_check is not None:
            node.type_ = signature_check

        return node.type_

    def analyze_attribute_access(self, node: ast.AttributeAccess):
        """Analyze an attribute access node.

        Uses the backend to resolve the type of an attribute chain
        (e.g., obj.attr1.attr2) and assigns it to the node.

        Args:
            node: An AttributeAccess AST node.
        """
        type_ = self.backend.resolve_attribute(node.node, node.attributes)
        node.type_ = type_

    def analyze_assignment(self, node: ast.Assignment):
        """Analyze an assignment node.

        Analyzes the right-hand side value, stores the binding in the
        variables dict if assigning to an identifier, and assigns the
        value's type to the assignment node.

        Args:
            node: An Assignment AST node.
        """
        self.analyze(node.value)
        if isinstance(node.target, ast.Identifier):
            target_name = node.target.name
            self.variables[target_name] = node.value
        if isinstance(node.target, ast.AttributeAccess):
            self.backend.resolve_attribute(node.target.node, node.target.attributes)

        node.type_ = node.value.type_

    def analyze_program(self, node: ast.Program):
        """Analyze a program node containing multiple statements.

        Recursively analyzes each statement in the program.

        Args:
            node: A Program AST node.
        """
        for statement in node.statments:
            self.analyze(statement)

    def check_signature(
        self,
        operation: operation.Operation,
        arg_types: list[attribute_types.AttributeType],
    ) -> attribute_types.AttributeType:
        """Check if argument types match a signature in the operation.

        Iterates through operation signatures and tests if the provided
        argument types match via subtype checking (is_a). Handles both
        variadic and fixed-arity parameters.

        Args:
            operation: The Operation to check signatures for.
            arg_types: List of argument types to match against signatures.

        Returns:
            The return type of the matching signature. For numeric returns,
            infers the most specific numeric type (INT/FLOAT).

        Raises:
            TypeError: If no matching signature is found.
        """
        for signature in operation.signatures:
            first_input = signature.inputs[0] if signature.inputs else None
            if (
                first_input
                and first_input.variadict
                and len(arg_types) >= first_input.min_count
            ):
                if all(arg_type.is_a(first_input.type_) for arg_type in arg_types):
                    if signature.output in [attribute_types.NUMBER]:
                        return self.infer_numeric_return_type(arg_types)
                    return signature.output
            if len(arg_types) == len(signature.inputs):
                if all(
                    arg_type.is_a(param.type_)
                    for arg_type, param in zip(arg_types, signature.inputs)
                ):
                    if signature.output in [attribute_types.NUMBER]:
                        return self.infer_numeric_return_type(arg_types)
                    return signature.output

        raise TypeError(
            f"No matching signature found for operation '{operation.name}' with argument types {arg_types}"
        )

    def infer_numeric_return_type(
        self, type_list: list[attribute_types.AttributeType]
    ) -> attribute_types.AttributeType:
        """Infer the most specific numeric return type from argument types.

        Returns FLOAT if any argument is FLOAT, INT if all are INT,
        otherwise NUMBER.

        Args:
            type_list: List of argument types.

        Returns:
            The inferred numeric return type (INT, FLOAT, or NUMBER).
        """
        if any(type_list.is_a(attribute_types.FLOAT) for type_list in type_list):
            return attribute_types.FLOAT
        if all(type_list.is_a(attribute_types.INT) for type_list in type_list):
            return attribute_types.INT
        return attribute_types.NUMBER
