"""Recursive descent parser for the expression language.

This module exposes `Parser`, which transforms a list of lexical
`Token` objects (from `expression.lexer`) into an AST composed of the
node classes defined in `expression.ast`.

The parser implements operator precedence and supports function
calls, attribute access, indexing, unary and binary operators, and
assignment statements.
"""

from .lexer import TokenType, Token
from . import ast

class Parser:
    """Parse a token stream into an `ast.Program`.

    Usage: construct with a token list and call `parse()` to return an
    `ast.Program` representing the top-level statements.
    """

    PRECEDENCE = {
        TokenType.PLUS: 10,
        TokenType.MINUS: 10,
        TokenType.STAR: 20,
        TokenType.SLASH: 20,
        TokenType.CARET: 30,
        TokenType.POWER: 30,
    }

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.token_len = len(tokens) if tokens is not None else 0
        self.current = 0

    def parse(self) -> ast.Program:
        """Parse the token list and return an `ast.Program`.

        This consumes tokens until EOF, collecting top-level statements.
        Newlines and semicolons are treated as statement separators.
        """
        statements = []
        while not self._at_end():
            while self._match(TokenType.NEWLINE, TokenType.SEMICOLON):
                pass

            statement = self._assignment()
            if statement is not None:
                statements.append(statement)

            if not self._at_end():

                if not self._match(
                    TokenType.NEWLINE,
                    TokenType.SEMICOLON
                ):
                    raise SyntaxError(
                        "Expected newline or ';' after statement"
                    )

        return ast.Program(statements)

    def _assignment(self) -> ast.ASTNode:
        """Parse an assignment or an expression.

        If an `=` follows the initial expression, this produces an
        `ast.Assignment` node. Otherwise returns the parsed expression.
        """
        target = self._expression()
        if self._match(TokenType.EQUAL, "="):
            value = self._expression()

            return ast.Assignment(
                target=target,
                value=value
            )
        return target

    def _expression(self, min_precedence=0) -> ast.ASTNode:
        """Parse an expression using precedence climbing.

        `min_precedence` is used to implement operator precedence and
        left/right associativity. Returns an AST node for the
        expression.
        """
        left = self._unary()

        while True:
            operator = self._peek()
            precedence = self.PRECEDENCE.get(operator.type_, -1)

            if precedence < min_precedence:
                break

            self._advance()
            next_precedence = precedence + 1
            if operator.type_ in [TokenType.CARET, TokenType.POWER]:
                next_precedence = precedence
            right = self._expression(next_precedence)
            left = ast.BinaryOperation(
                operation=operator.value,
                left=left,
                right=right
            )

        return left

    def _unary(self) -> ast.ASTNode:
        """Handle unary `+` and `-` operators, falling back to postfix.

        Returns an `ast.UnaryOperation` if a leading plus/minus is
        present; otherwise returns the result of `_post_fix()`.
        """
        if self._match(TokenType.PLUS) or self._match(TokenType.MINUS):
            operator = self._previous()
            operand = self._post_fix()

            return ast.UnaryOperation(operator=operator.value, operand=operand)

        return self._post_fix()

    def _post_fix(self) -> ast.ASTNode:
        """Handle postfix constructs: function calls and attribute/index access.

        This first parses a primary expression and then consumes any
        sequence of calls (`(...)`) or attribute/index accesses
        (`.name` / `[expr]`). Returns an appropriate AST node.
        """
        token = self._primary()
        attributes = []

        if isinstance(token, ast.Identifier) and self._match(TokenType.LEFT_PAREN):
            while True:
                value = self._expression()
                attributes.append(value)
                if not self._match(TokenType.COMMA):
                    break
                if self._peek().type_ is TokenType.RIGHT_PAREN:
                    break
            self._expect(TokenType.RIGHT_PAREN)

            return ast.FunctionCall(
                function=token,
                arguments=attributes
            )

        while isinstance(token, ast.Identifier):
            if self._match(TokenType.PERIOD):
                self._expect(TokenType.IDENTIFIER)
                attributes.append(ast.Identifier(self._previous().value))
            elif self._match(TokenType.LEFT_SQR_BRACKET):
                node = self._expression()
                self._expect(TokenType.RIGHT_SQR_BRACKET)

                self._flatten_attribute_access(node, attributes)
            else:
                break
        if attributes:
            return ast.AttributeAccess(token, attributes)

        return token

    def _primary(self) -> ast.ASTNode:
        """Parse a primary expression: identifier, number, or parenthesized.

        Returns an AST node corresponding to the primary. Raises
        `SyntaxError` on unexpected tokens.
        """
        token = self._advance()

        if token.type_ is TokenType.IDENTIFIER:
            return ast.Identifier(token.value)

        if token.type_ is TokenType.NUMBER:
            return ast.NumberLiteral(float(token.value))

        if token.type_ is TokenType.LEFT_PAREN:
            node = self._expression()
            self._expect(TokenType.RIGHT_PAREN)

            return node

        raise SyntaxError(f"Unexpected token: {token.type_}")

    def _flatten_attribute_access(self, node: ast.ASTNode, attributes):
        """Flatten a nested `AttributeAccess` into the attribute list.

        This helper converts nested attribute/index expressions into a
        flat list used by `AttributeAccess` nodes.
        """
        if isinstance(node, ast.AttributeAccess):
            attributes.append(node.node)
            attributes.extend(node.attributes)
        else:
            attributes.append(node)

    def _peek(self) -> Token:
        """Return the next token without consuming it."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        """Consume and return the next token from the token stream."""
        token = self.tokens[self.current]
        self.current += 1
        return token

    def _match(self, *expected_token):
        """If the next token matches any `expected_token`, consume it.

        Accepts one or more `TokenType` values. Returns `True` when a
        match occurred and the token was consumed.
        """
        if self._at_end():
            return False
        token = self._peek()
        if any(token.type_ is x for x in expected_token if isinstance(x, TokenType)):
            self._advance()
            return True
        return False

    def _expect(self, expected_token: TokenType):
        """Assert the next token is `expected_token` and consume it.

        Raises `ValueError` with a helpful message if the expectation
        is not met or if the stream ends unexpectedly.
        """
        if self._at_end():
            self.raise_value_error()
        if self._peek().type_ is not expected_token:
            self.raise_value_error()
        self._advance()

    def _at_end(self):
        """Return True if there are no more non-EOF tokens to consume."""
        return self.current >= self.token_len or self._peek().type_ is TokenType.EOF

    def raise_value_error(self):
        """Raise a `ValueError` describing the unexpected token at cursor."""
        raise ValueError(f"Unexpected Token: {self.tokens[self.current]}")
