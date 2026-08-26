"""Small vector and matrix value types used by graph operations."""

from __future__ import annotations
from dataclasses import dataclass

Number = int | float


@dataclass
class Vector:
    """Represent a four-component vector with homogeneous coordinate ``w``."""

    x: Number = 0
    y: Number = 0
    z: Number = 0
    w: Number = 1

    @classmethod
    def from_values(cls, *values: float) -> Vector:
        """Create a vector from exactly three or four scalar values."""
        if len(values) == 3:
            return cls(*values, 1)
        elif len(values) == 4:
            return cls(*values)

        raise ValueError("expected 3 or 4 values")

    def __add__(self, other: Vector | Number) -> Vector:
        """Add a scalar or vector component-wise."""
        if isinstance(other, Number):
            return Vector(
                self.x + other,
                self.y + other,
                self.z + other,
                1,
            )
        elif isinstance(other, Vector):
            return Vector(
                self.x + other.x,
                self.y + other.y,
                self.z + other.z,
                1,
            )
        if not isinstance(other, Vector):
            return NotImplemented

    def __radd__(self, other: Vector | Number) -> Vector:
        """Support scalar or vector addition with the vector on the right."""
        return self + other

    def __mul__(self, other: Number) -> Vector:
        """Multiply by a scalar or multiply two vectors component-wise."""
        if isinstance(other, Number):
            return Vector(
                self.x * other,
                self.y * other,
                self.z * other,
                1,
            )
        elif isinstance(other, Vector):
            return Vector(
                self.x * other.x,
                self.y * other.y,
                self.z * other.z,
                self.w * other.w,
            )
        if not isinstance(other, (int, float)):
            return NotImplemented

    def __rmul__(self, other: Number) -> Vector:
        """Support multiplication with the vector on the right."""
        return self * other


@dataclass
class Matrix:
    """Represent a four-by-four matrix stored as four vector rows."""

    rows: tuple[Vector, Vector, Vector, Vector]

    @classmethod
    def from_values(cls, *values: float):
        """Create a matrix from exactly sixteen scalar values."""
        if len(values) != 16:
            raise ValueError("Expected 16 values")

        vectors = tuple(Vector.from_values(*values[i : i + 4]) for i in range(0, 16, 4))

        return cls(vectors)

    def __getitem__(self, index: int) -> Vector:
        """Return the row at ``index``."""
        return self.rows[index]

    def __add__(self, other: Matrix) -> Matrix:
        """Add two matrices row by row."""
        if not isinstance(other, Matrix):
            return NotImplemented

        return Matrix(
            (
                self.rows[0] + other.rows[0],
                self.rows[1] + other.rows[1],
                self.rows[2] + other.rows[2],
                self.rows[3] + other.rows[3],
            )
        )

    def __mul__(
        self,
        other: Matrix | Vector,
    ) -> Matrix | Vector:
        """Multiply by a matrix, vector, or scalar."""
        # Matrix * Matrix
        if isinstance(other, Matrix):
            vectors = []
            for row in range(4):
                new_row = []
                for col in range(4):
                    value = 0
                    for i in range(4):
                        value += self.rows[row][i] * other.rows[i][col]
                    new_row.append(value)
                vectors.append(Vector(*new_row))

            return Matrix(vectors[0], vectors[1], vectors[2], vectors[3])

        # Matrix * Vector4
        if isinstance(other, Vector):
            vectors = []
            for row in range(4):
                for col in range(4):
                    value += self.rows[row][col] * other[col]

                vectors.append(value)

            return Vector(*vectors)

        # Matrix * scalar
        if isinstance(other, (int, float)):
            return Matrix(
                (
                    self.rows[0] * other,
                    self.rows[1] * other,
                    self.rows[2] * other,
                    self.rows[3] * other,
                )
            )
        return NotImplemented
