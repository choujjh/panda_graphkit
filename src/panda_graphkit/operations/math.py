"""Predefined mathematical operations available to the graphkit.

This module defines `Operation` instances (signatures, names) for
common math functions such as `sin`, `cos`, `add`, `multiply`, and
`power`. These objects describe expected argument types and are used
by downstream validation and dispatch.
"""

from ..core import Operation
from ..signatures import math as sig_math

__all__ = (
    "SIN",
    "COS",
    "REMAP",
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
    signatures=(sig_math.N_O_F_SIG,),
)

COS = Operation(
    name="cos",
    signatures=(sig_math.N_O_F_SIG,),
)

REMAP = Operation(
    name="remap",
    signatures=(sig_math.N5_O_N_SIG,),
)

ADD = Operation(
    name="add",
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.V_V_O_V_SIG,
        sig_math.N_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
    ),
)

SUM = Operation(
    name="sum",
    signatures=(
        sig_math.NV_O_N_SIG,
        sig_math.VV_O_V_SIG,
        sig_math.MV_O_M_SIG,
    ),
)

SUBTRACT = Operation(
    name="subtract",
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.V_V_O_V_SIG,
        sig_math.N_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
    ),
)

MULTIPLY = Operation(
    name="mult",
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.V_V_O_V_SIG,
        sig_math.M_M_O_M_SIG,
        sig_math.N_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
        sig_math.M_V_O_V_SIG,
    ),
)

PRODUCT = Operation(
    name="product",
    signatures=(
        sig_math.NV_O_N_SIG,
        sig_math.VV_O_V_SIG,
        sig_math.M_V_O_V_SIG,
    ),
)

DIVIDE = Operation(
    name="div",
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.N_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
        sig_math.V_V_O_V_SIG,
    ),
)

POWER = Operation(
    name="pow",
    signatures=(
        sig_math.N_N_O_N_SIG,
        sig_math.V_V_O_V_SIG,
        sig_math.V_N_O_V_SIG,
    ),
)

VECTOR = Operation(
    name="vector",
    signatures=(
        sig_math.N_N_O_V,
        sig_math.N_N_N_O_V,
        sig_math.N4_O_V,
    ),
)

MATRIX = Operation(
    name="matrix",
    signatures=(sig_math.N16_O_M,),
)
