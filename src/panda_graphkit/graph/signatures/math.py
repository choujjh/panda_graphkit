"""Signatures for scalar, vector, and matrix mathematical operations."""

from ..core import Signature, Parameter, NUMBER, FLOAT, VECTOR, MATRIX4

# FLOAT -> F
# NUMBER -> N
# INTEGER -> I
# VECTOR -> V
# MATRIX -> M
# NUMBER Variadict -> NV
# INTEGER Variadict -> IV
# VECTOR Variadict -> VV
# MATRIX Variadict -> MV
# *number* denotes repeat ie. 16 -> repeated 16 times
# OUTPUT -> O
# OR/UNION -> U

__all__ = [
    "N_O_F_SIG",
    "N5_O_N_SIG",
    "N_N_O_N_SIG",
    "V_V_O_V_SIG",
    "N_V_O_V_SIG",
    "V_N_O_V_SIG",
    "NV_O_N_SIG",
    "VV_O_V_SIG",
    "MV_O_M_SIG",
    "M_M_O_M_SIG",
    "M_V_O_V_SIG",
    "N4_O_V_SIG",
    "N_N_N_O_V_SIG",
    "N16_O_M_SIG",
    "M_M_O_N_SIG",
    "V_V_O_N_SIG",
]


N_O_F_SIG = Signature(
    inputs=Parameter("value", NUMBER), outputs=Parameter("output", FLOAT)
)

N5_O_N_SIG = Signature(
    inputs=(
        Parameter("value1", NUMBER),
        Parameter("value2", NUMBER),
        Parameter("value3", NUMBER),
        Parameter("value4", NUMBER),
        Parameter("value5", NUMBER),
    ),
    outputs=Parameter("output", NUMBER),
)

N_N_O_N_SIG = Signature(
    inputs=(
        Parameter("value1", NUMBER),
        Parameter("value2", NUMBER),
    ),
    outputs=Parameter("output", NUMBER),
)
V_V_O_V_SIG = Signature(
    inputs=(
        Parameter("value1", VECTOR),
        Parameter("value2", VECTOR),
    ),
    outputs=Parameter("output", VECTOR),
)
N_V_O_V_SIG = Signature(
    inputs=(
        Parameter("value1", NUMBER),
        Parameter("value2", VECTOR),
    ),
    outputs=Parameter("output", VECTOR),
)
V_N_O_V_SIG = Signature(
    inputs=(
        Parameter("value1", VECTOR),
        Parameter("value2", NUMBER),
    ),
    outputs=Parameter("output", VECTOR),
)
NV_O_N_SIG = Signature(
    inputs=Parameter("value", NUMBER, variadict=True, min_count=2),
    outputs=Parameter("output", NUMBER),
)
VV_O_V_SIG = Signature(
    inputs=Parameter("value", VECTOR, variadict=True, min_count=2),
    outputs=Parameter("output", VECTOR),
)
NUVV_O_V_SIG = Signature(
    inputs=Parameter("value", (NUMBER, VECTOR), variadict=True, min_count=2),
    outputs=Parameter("output", VECTOR),
)
MV_O_M_SIG = Signature(
    inputs=Parameter("value", MATRIX4, variadict=True, min_count=2),
    outputs=Parameter("output", MATRIX4),
)
M_M_O_M_SIG = Signature(
    inputs=(
        Parameter("value1", MATRIX4),
        Parameter("value2", MATRIX4),
    ),
    outputs=Parameter("output", MATRIX4),
)
M_V_O_V_SIG = Signature(
    inputs=(
        Parameter("value1", MATRIX4),
        Parameter("value2", VECTOR),
    ),
    outputs=Parameter("output", VECTOR),
)
N4_O_V_SIG = Signature(
    inputs=(
        Parameter("x", NUMBER),
        Parameter("y", NUMBER),
        Parameter("z", NUMBER),
        Parameter("w", NUMBER),
    ),
    outputs=Parameter("output", VECTOR),
)
N_N_O_V_SIG = Signature(
    inputs=(
        Parameter("x", NUMBER),
        Parameter("y", NUMBER),
    ),
    outputs=Parameter("output", VECTOR),
)
N_N_N_O_V_SIG = Signature(
    inputs=(
        Parameter("x", NUMBER),
        Parameter("y", NUMBER),
        Parameter("z", NUMBER),
    ),
    outputs=Parameter("output", VECTOR),
)
N16_O_M_SIG = Signature(
    inputs=(
        Parameter("cell00", NUMBER),
        Parameter("cell01", NUMBER),
        Parameter("cell02", NUMBER),
        Parameter("cell03", NUMBER),
        Parameter("cell10", NUMBER),
        Parameter("cell11", NUMBER),
        Parameter("cell12", NUMBER),
        Parameter("cell13", NUMBER),
        Parameter("cell20", NUMBER),
        Parameter("cell21", NUMBER),
        Parameter("cell22", NUMBER),
        Parameter("cell23", NUMBER),
        Parameter("cell30", NUMBER),
        Parameter("cell31", NUMBER),
        Parameter("cell32", NUMBER),
        Parameter("cell33", NUMBER),
    ),
    outputs=Parameter("output", MATRIX4),
)

M_M_O_N_SIG = Signature(
    inputs=(
        Parameter("input1", MATRIX4),
        Parameter("input2", MATRIX4)
    ),
    outputs=Parameter("output", NUMBER)
)
V_V_O_N_SIG = Signature(
    inputs=(
        Parameter("input1", VECTOR),
        Parameter("input2", VECTOR)
    ),
    outputs=Parameter("output", NUMBER)
)