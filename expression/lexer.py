"""Lexer for the expression language used by panda_graphkit.

This module provides a simple tokenizer that converts a source
string into a stream of `Token` instances. It recognizes identifiers,
numbers, strings, operators, punctuation, and newlines.

The primary entrypoint is `Tokenizer.tokenize()` which returns a list
of `Token` objects ending with an `EOF` token.
"""

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Enumeration of all token types produced by the tokenizer.

    Token types include literals, operators, punctuation, and special
    markers like `NEWLINE` and `EOF`.
    """

    # literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

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


@dataclass(frozen=True)
class Token:
    """Token class

    Args:
        type_: TokenType
        value: str
    """

    type_: TokenType
    value: str

    def __str__(self):
        return f"Type: {self.type_.name}, Value: {self.value}"


class Tokenizer:
    """Convert a source string into a sequence of `Token` objects.

    The tokenizer scans the input character-by-character and groups
    characters into tokens recognized by the grammar. It does not
    perform parsing or semantic analysis; it only produces token
    objects describing the lexical elements.

    Args:
        source: The input string to tokenize. If `None`, an empty
            sequence is produced.
    """

    def __init__(self, source):
        self.source = source
        self.source_len = len(source) if source is not None else 0
        self.current = 0
        self.row = 0
        self.column = 0

    def tokenize(self) -> list[TokenType]:
        """Tokenize the entire source and return a list of `Token`.

        The returned list always ends with an `EOF` token.
        """
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
        """Read and return the next token from the input stream.

        This is the core dispatch that examines the next character and
        delegates to specialized routines for identifiers, numbers,
        operators, and punctuation.
        """
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
        """Conditionally consume `expected_char` from the input.

        Returns `True` and advances the cursor if the next character
        matches `expected_char`. Otherwise returns `False` and leaves
        the cursor unchanged.
        """
        if self._at_end():
            return False
        if self._peek() != expected_char:
            return False

        self._advance()
        return True

    def _identifier(self):
        """Consume characters for an identifier and return an IDENTIFIER token.

        Identifiers may contain letters, digits, and the characters
        `|`, `:`, and `_`.
        """

        start = self.current - 1
        while not self._at_end():
            char = self._peek()
            if not (char in "|:_" or char.isalnum()):
                break
            self._advance()

        value = self.source[start : self.current]

        return Token(type_=TokenType.IDENTIFIER, value=value)

    def _number(self):
        """Consume characters for a number literal and return a NUMBER token.

        Supports integer and floating-point formats using `.` as the
        decimal separator. This routine does not validate numeric ranges.
        """

        start = self.current - 1
        while not self._at_end():
            char = self._peek()
            if not (char == "." or char.isdigit()):
                break
            self._advance()

        value = self.source[start : self.current]
        return Token(type_=TokenType.NUMBER, value=value)

    def _operator(self, char):
        """Return an operator token starting with `char`.

        Handles multi-character operators such as `**` for power.
        Raises `ValueError` for unknown operator starts.
        """
        if char == "*":
            if self._match("*"):
                return Token(TokenType.POWER, "**")
            return Token(TokenType.STAR, "*")

        if char in _OPERATORS.keys():
            return Token(_OPERATORS[char], char)

        self._raise_value_error(char)

    def _skip_whitespace(self):
        """Advance the cursor past horizontal whitespace (not newlines).

        This stops at `\r`/`\n` so that blank lines are preserved as
        `NEWLINE` tokens by other logic.
        """
        while not self._at_end():
            char = self._peek()
            if char in "\r\n":
                break
            if not char.isspace():
                break
            self._advance()

    def _advance(self):
        """Return the current character and advance the input cursor by one.

        Updates internal `column` tracking and returns the consumed
        character. Caller must ensure not at end before invoking.
        """

        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def _peek(self):
        """Return the character at the current cursor without consuming it."""

        char = self.source[self.current]
        return char

    def _at_end(self):
        """Return True when the input cursor has reached the end."""

        return self.current >= self.source_len

    def _raise_value_error(self, char: str):
        """Raise a `ValueError` describing an unexpected character.

        The message includes the current row and column for easier
        debugging of lexical errors.
        """
        column = self.column
        if self.current != 0 and char == self.source[self.current - 1]:
            column -= 1
        raise ValueError(
            f"Unexpected Character: '{char}' at row {self.row} col {column}"
        )
