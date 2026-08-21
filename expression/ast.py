"""Abstract syntax tree (AST) node definitions for the expression language.

This module defines simple dataclass-based node types used by the
parser to represent expressions and statements. It also provides a
`print_ast` utility for a human-readable tree dump useful during
development and debugging.
"""

from dataclasses import dataclass
import core.attribute_types as attribute_types


@dataclass(kw_only=True)
class ASTNode:
    """Base class for all AST node types.

    Subclass this to represent specific AST constructs. Instances are
    plain dataclasses and carry no behaviour beyond their fields.
    """

    type_: attribute_types.AttributeType | None = None
    operation_: attribute_types.AttributeType | None = None


@dataclass
class Identifier(ASTNode):
    """An identifier, e.g. variable or function name.

    Attributes:
        name: The identifier name as a string.
    """

    name: str


@dataclass
class AttributeAccess(ASTNode):
    """Accessing attributes or indexing on a base node.

    Examples include `obj.attr` and `arr[0]` (indexing is represented
    by nested AST nodes in `attributes`).
    """

    node: ASTNode
    attributes: list[ASTNode]


@dataclass
class Literal(ASTNode):
    """A numeric literal.

    Attributes:
        value: Numeric value (float) parsed from source.
    """

    value: str


@dataclass
class BinaryOperation(ASTNode):
    """A binary operation node, such as addition or multiplication.

    Attributes:
        operation: The operator symbol as a string (e.g. '+').
        left: Left operand node.
        right: Right operand node.
    """

    operation: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOperation(ASTNode):
    """A unary operation node, such as negation.

    Attributes:
        operator: Operator symbol (e.g. '-').
        operand: Operand node.
    """

    operator: str
    operand: ASTNode


@dataclass
class FunctionCall(ASTNode):
    """A function call expression.

    Attributes:
        function: Expression evaluating to the callable being invoked.
        arguments: List of argument AST nodes.
    """

    function: Identifier
    arguments: list[ASTNode]


@dataclass
class Assignment(ASTNode):
    """An assignment statement node.

    Attributes:
        target: LHS of the assignment (identifier or attribute access).
        value: RHS expression to assign.
    """

    target: ASTNode
    value: ASTNode


@dataclass
class Program(ASTNode):
    """A container node representing a sequence of statements.

    Attributes:
        statments: List of top-level AST nodes (statements).
    """

    statments: list[ASTNode]


def print_ast(node: ASTNode, indent="", is_last=True):
    """Print a visual tree representation of an AST node.

    This helper is useful for debugging. It prints the node and its
    children using a simple ASCII tree format.

    Args:
        node: The root AST node to print.
        indent: Internal use only; prefix string for the current level.
        is_last: Internal use only; whether this node is the last child.
    """
    connector = "└── " if is_last else "├── "
    print_prefix = f"{indent}{connector}"
    next_indent = f"{indent}{'    ' if is_last else '│   '}"

    type_label = f" type={node.type_}" if node.type_ is not None else ""
    operation = (
        f" operation={node.operation_.name}" if node.operation_ is not None else ""
    )

    if isinstance(node, Identifier):
        print(f"{print_prefix}Identifier:{node.name}{type_label}{operation}")

    elif isinstance(node, Literal):
        print(f"{print_prefix}Literal:{node.value}{type_label}{operation}")

    elif isinstance(node, UnaryOperation):
        print(f"{print_prefix}Unary:{node.operator}{type_label}{operation}")
        print_ast(node.operand, indent=next_indent, is_last=True)

    elif isinstance(node, FunctionCall):
        print(f"{print_prefix}Function{type_label}{operation}")
        print_ast(node.function, indent=next_indent, is_last=False)
        for index, arg in enumerate(node.arguments):
            is_last = index >= len(node.arguments) - 1
            print_ast(arg, next_indent, is_last=is_last)

    elif isinstance(node, BinaryOperation):
        print(f"{print_prefix}BinaryOperation:{node.operation}{type_label}{operation}")
        print_ast(node.left, indent=next_indent, is_last=False)
        print_ast(node.right, indent=next_indent, is_last=True)

    elif isinstance(node, Assignment):
        print(f"{print_prefix}Assignment{type_label}{operation}")
        print_ast(node.target, indent=next_indent, is_last=False)
        print_ast(node.value, indent=next_indent, is_last=True)

    elif isinstance(node, AttributeAccess):
        print(f"{print_prefix}AttributeAccess{type_label}{operation}")
        print_ast(node.node, indent=next_indent, is_last=False)
        for index, arg in enumerate(node.attributes):
            is_last = index >= len(node.attributes) - 1
            print_ast(arg, next_indent, is_last=is_last)

    elif isinstance(node, Program):
        print(f"{print_prefix}Program{type_label}{operation}")
        for index, arg in enumerate(node.statments):
            is_last = index >= len(node.statments) - 1
            print_ast(arg, next_indent, is_last=is_last)
