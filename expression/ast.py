from dataclasses import dataclass

@dataclass
class ASTNode:
    pass


@dataclass
class Identifier(ASTNode):
    name: str


@dataclass
class AttributeAccess(ASTNode):
    node: ASTNode
    attributes: list[ASTNode]


@dataclass
class NumberLiteral(ASTNode):
    value: float


@dataclass
class BinaryOperation(ASTNode):
    operation: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOperation(ASTNode):
    operator: str
    operand: ASTNode


@dataclass
class FunctionCall(ASTNode):
    function: ASTNode
    arguments: list[ASTNode]


@dataclass
class Assignment(ASTNode):
    target: ASTNode
    value: ASTNode


@dataclass
class Program(ASTNode):
    statments: list[ASTNode]


def print_ast(node: ASTNode, indent="", is_last=True):
    """"""
    connector = "└── " if is_last else "├── "
    print_prefix = f"{indent}{connector}"
    next_indent = f"{indent}{'    ' if is_last else '│   '}"
    if isinstance(node, Identifier):
        print(f"{print_prefix}Identifier:{node.name}")

    elif isinstance(node, NumberLiteral):
        print(f"{print_prefix}Number:{node.value}")

    elif isinstance(node, UnaryOperation):
        print(f"{print_prefix}Unary:{node.operator}")
        print_ast(node.operand, indent=next_indent, is_last=True)

    elif isinstance(node, FunctionCall):
        print(f"{print_prefix}Function")
        print_ast(node.function, indent=next_indent, is_last=False)
        for index, arg in enumerate(node.arguments):
            is_last = index >= len(node.arguments) - 1
            print_ast(arg, next_indent, is_last=is_last)

    elif isinstance(node, BinaryOperation):
        print(f"{print_prefix}BinaryOperation:{node.operation}")
        print_ast(node.left, indent=next_indent, is_last=False)
        print_ast(node.right, indent=next_indent, is_last=True)

    elif isinstance(node, Assignment):
        print(f"{print_prefix}Assignment")
        print_ast(node.target, indent=next_indent, is_last=False)
        print_ast(node.value, indent=next_indent, is_last=True)

    elif isinstance(node, AttributeAccess):
        print(f"{print_prefix}AttributeAccess")
        print_ast(node.node, indent=next_indent, is_last=False)
        for index, arg in enumerate(node.attributes):
            is_last = index >= len(node.attributes) - 1
            print_ast(arg, next_indent, is_last=is_last)
