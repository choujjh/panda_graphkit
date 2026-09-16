"""Predefined mathematical operations available to the graphkit.

This module defines `Operation` instances (signatures, names) for
common math functions such as `sin`, `cos`, `add`, `multiply`, and
`power`. These objects describe expected argument types and are used
by downstream validation and dispatch.
"""

from ..core import Associativity, Operation
from ..signatures import math as sig_math

__all__ = (
    "SIN",
    "ACOS",
    "COS",
    "REMAP",
    "DIST",
    "ADD",
    "SUM",
    "SUBTRACT",
    "MULTIPLY",
    "PRODUCT",
    "DIVIDE",
    "POWER",
    "VECTOR",
    "MATRIX",
)

SIN = Operation(
    name="sin",
    signatures=sig_math.N_O_F_SIG,
)
ACOS = Operation(
    name="acos",
    signatures=sig_math.N_O_F_SIG,
)
COS = Operation(
    name="cos",
    signatures=sig_math.N_O_F_SIG,
)

REMAP = Operation(
    name="remap",
    signatures=sig_math.N5_O_N_SIG.replace_names(
        "input_min", "input_max", "output_min", "output_max", "value", "output"
    ),
)

DIST = Operation(
    name="dist",
    signatures=(
        sig_math.M_M_O_N_SIG,
        sig_math.V_V_O_N_SIG,
    ),
)

ADD = Operation(
    name="add",
    aliases="+",
    infix={"+": (10, Associativity.LEFT)},
    signatures=(
        sig_math.N_N_O_N_SIG.replace(commutative=True),
        sig_math.V_V_O_V_SIG.replace(commutative=True),
        sig_math.N_V_O_V_SIG.replace(commutative=True),
        sig_math.V_N_O_V_SIG.replace(commutative=True),
    ),
)

SUM = Operation(
    name="sum",
    signatures=(
        sig_math.NV_O_N_SIG.replace(commutative=True),
        sig_math.NUVV_O_V_SIG.replace(commutative=True),
        sig_math.MV_O_M_SIG.replace(commutative=True),
    ),
)

SUBTRACT = Operation(
    name="subtract",
    aliases="-",
    infix={"-": (10, Associativity.LEFT)},
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.V_V_O_V_SIG,
        sig_math.N_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
    ),
)

MULTIPLY = Operation(
    name="mult",
    aliases="*",
    infix={"*": (20, Associativity.LEFT)},
    signatures=(
        sig_math.N_N_O_N_SIG.replace(commutative=True),
        sig_math.V_V_O_V_SIG.replace(commutative=True),
        sig_math.M_M_O_M_SIG,
        sig_math.N_V_O_V_SIG.replace(commutative=True),
        sig_math.V_N_O_V_SIG.replace(commutative=True),
        sig_math.M_V_O_V_SIG,
    ),
)

PRODUCT = Operation(
    name="product",
    signatures=(
        sig_math.NV_O_N_SIG.replace(commutative=True),
        sig_math.MV_O_M_SIG,
        sig_math.NUVV_O_V_SIG.replace(commutative=True),
    ),
)

DIVIDE = Operation(
    name="div",
    aliases="/",
    infix={"/": (20, Associativity.LEFT)},
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.N_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
        sig_math.V_V_O_V_SIG,
    ),
)

POWER = Operation(
    name="pow",
    aliases=("**", "^"),
    infix={"**": (30, Associativity.RIGHT), "^": (30, Associativity.RIGHT)},
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.V_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
    ),
)

VECTOR = Operation(
    name="vector",
    signatures=(
        sig_math.N_N_O_V_SIG,
        sig_math.N_N_N_O_V_SIG,
        sig_math.N4_O_V_SIG,
    ),
)

MATRIX = Operation(
    name="matrix",
    signatures=sig_math.N16_O_M_SIG,
)
