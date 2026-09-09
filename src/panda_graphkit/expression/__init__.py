"""Expression package: lexer, parser, and AST node definitions.

This package contains the components required to tokenize, parse,
and represent expression source code as an abstract syntax tree
(AST) for further processing.
"""

from .builder import ExpressionResult, build_expression

__all__ = ["ExpressionResult", "build_expression"]
