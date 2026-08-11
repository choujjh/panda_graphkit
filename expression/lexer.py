from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    
    # literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # keywords
    CLAMP = auto()
    SIN = auto()
    COS = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    EQUAL = auto()
    POWER = auto()

    # Punctuation
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_SQR_BRACKET = auto()
    RIGHT_SQR_BRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    NEWLINE = auto()
    PERIOD = auto()

    EOF = auto()


_OPERATORS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "^": TokenType.CARET,
    "**": TokenType.POWER,
}
_OPERATOR_START_STRING = "".join(set([char[0] for char in _OPERATORS.keys()]))
_PUNCTUATION = {
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "[": TokenType.LEFT_SQR_BRACKET,
    "]": TokenType.RIGHT_SQR_BRACKET,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    ".": TokenType.PERIOD,
    "=": TokenType.EQUAL,
}
FUNCTIONS = {
    "clamp": TokenType.CLAMP,
    "sin": TokenType.SIN,
    "cos": TokenType.COS,
}


@dataclass(frozen=True)
class Token:
    """ Token class

    Args:
        type_: TokenType
        value: str
    """
    type_: TokenType
    value: str

    def __str__(self):
        return f"Type: {self.type_.name}, Value: {self.value}"


class Tokenizer:
    """ Takes a string and tokenizes it
    """
    def __init__(self, source):
        self.source = source
        self.source_len = len(source) if source is not None else 0
        self.current = 0
        self.row = 0
        self.column = 0

    def tokenize(self) -> list[TokenType]:
        tokens = []
        while not self._at_end():
            self._skip_whitespace()

            if self._at_end():
                break
            value = self._next_token()
            tokens.append(value)

        tokens.append(Token(TokenType.EOF, ""))

        return tokens

    def _next_token(self):
        char = self._advance()
        if char == ":" or char == "|" or char.isalpha():
            return self._identifier()

        if char.isdigit():
            return self._number()
        
        if char in "\r\n":
            self.row += 1
            self.column = 0
            return Token(type_=TokenType.NEWLINE, value="")

        if char in _OPERATOR_START_STRING:
            return self._operator(char)

        if char in _PUNCTUATION.keys():
            return Token(type_=_PUNCTUATION[char], value=char)

        self._raise_value_error(char)

    def _match(self, expected_char: str):
        if self._at_end():
            return False
        if self._peek() != expected_char:
            return False

        self._advance()
        return True

    def _identifier(self):
        """Creates and returns Identifier Token"""

        start = self.current - 1
        while not self._at_end():
            char = self._peek()
            if not (char in "|:_" or char.isalnum()):
                break
            self._advance()

        value = self.source[start : self.current]
        if value in FUNCTIONS.keys():
            return Token(type_=FUNCTIONS[value], value=value)
        return Token(type_=TokenType.IDENTIFIER, value=value)

    def _number(self):
        """Creates and returns number Token"""

        start = self.current - 1
        while not self._at_end():
            char = self._peek()
            if not (char == "." or char.isdigit()):
                break
            self._advance()

        value = self.source[start : self.current]
        return Token(type_=TokenType.NUMBER, value=value)

    def _operator(self, char):
        if char == "*":
            if self._match("*"):
                return Token(TokenType.POWER, "**")
            return Token(TokenType.STAR, "*")

        if char in _OPERATORS.keys():
            return Token(_OPERATORS[char], char)

        self._raise_value_error(char)

    def _skip_whitespace(self):
        """Places pointer at next character thats not a whitespace. 
        doesn't skip whitelines"""
        while not self._at_end():
            char = self._peek()
            if char in "\r\n":
                break
            if not char.isspace():
                break
            self._advance()

    def _skip_new_lines(self):
        """Places pointer at next character thats not a new line"""
        while not self._at_end():
            char = self._peek()
            if char in "\r\n":
                self._advance()
            else:
                break

    def _advance(self):
        """Returns character at current pointer and advances pointer"""

        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def _peek(self):
        """Returns character at current pointer"""

        char = self.source[self.current]
        return char

    def _at_end(self):
        """At end of source"""

        return self.current >= self.source_len

    def _raise_value_error(self, char: str):
        """Raises Value Error"""
        column = self.column
        if self.current != 0 and char == self.source[self.current - 1]:
            column -= 1
        raise ValueError(
            f"Unexpected Character: '{char}' at row {self.row} col {column}"
        )

