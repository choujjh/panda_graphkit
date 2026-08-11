from .lexer import TokenType, Token, FUNCTIONS
from . import ast

class Parser:
    function_calls = [TokenType.CLAMP, TokenType.SIN, TokenType.COS]
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
        statements = []
        while not self._at_end():
            while self._match(TokenType.NEWLINE, TokenType.SEMICOLON):
                pass

            print(self._peek())
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
        target = self._expression()
        if self._match(TokenType.EQUAL, "="):
            value = self._expression()

            return ast.Assignment(
                target=target,
                value=value
            )
        return target

    def _expression(self, min_precedence=0) -> ast.ASTNode:
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
        if self._match(TokenType.PLUS) or self._match(TokenType.MINUS):
            operator = self._previous()
            operand = self._post_fix()

            return ast.UnaryOperation(operator=operator.value, operand=operand)

        return self._post_fix()

    def _post_fix(self) -> ast.ASTNode:
        token = self._primary()
        attributes = []

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

        if isinstance(token, ast.FunctionCall):
            self._expect(TokenType.LEFT_PAREN)

            while True:
                value = self._expression()
                attributes.append(value)
                if not self._match(TokenType.COMMA):
                    break
                if self._peek().type_ is TokenType.RIGHT_PAREN:
                    break
            self._expect(TokenType.RIGHT_PAREN)

            token.arguments = attributes
            return token

        return token

    def _primary(self) -> ast.ASTNode:
        token = self._advance()

        if token.type_ is TokenType.IDENTIFIER:
            return ast.Identifier(token.value)

        if token.type_ is TokenType.NUMBER:
            return ast.NumberLiteral(float(token.value))

        if token.type_ is TokenType.LEFT_PAREN:
            node = self._expression()
            self._expect(TokenType.RIGHT_PAREN)

            return node

        if token.type_ in FUNCTIONS.values():
            return ast.FunctionCall(function=ast.Identifier(token.value), arguments=[])

        raise SyntaxError(f"Unexpected token: {token.type_}")

    def _flatten_attribute_access(self, node: ast.ASTNode, attributes):
        if isinstance(node, ast.AttributeAccess):
            attributes.append(node.node)
            attributes.extend(node.attributes)
        else:
            attributes.append(node)

    def _peek(self) -> Token:
        """looks at next token

        Returns:
            Token:
        """
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """gets previous token

        Returns:
            Token:
        """
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        """gets next token while consuming it

        Returns:
            Token:
        """
        token = self.tokens[self.current]
        self.current += 1
        return token

    def _match(self, *expected_token):
        """if next token matches token then consumes it

        Args:
            expected_token (TokenType):

        Returns:
            bool:
        """
        if self._at_end():
            return False
        token = self._peek()
        if any(token.type_ is x for x in expected_token if isinstance(x, TokenType)):
            self._advance()
            return True
        return False

    def _expect(self, expected_token: TokenType):
        """_expect _summary_

        Args:
            expected_token (TokenType): _description_

        Raises:
            ValueError: _description_
            ValueError: _description_
        """
        if self._at_end():
            self.raise_value_error()
        if self._peek().type_ is not expected_token:
            self.raise_value_error()
        self._advance()

    def _at_end(self):
        """returns if at end

        Returns:
            bool:
        """
        return self.current >= self.token_len or self._peek().type_ is TokenType.EOF

    def raise_value_error(self):
        """raises ValueError

        Raises:
            ValueError:
        """
        raise ValueError(f"Unexpected Token: {self.tokens[self.current]}")
