"""Predefined mathematical operations available to the graphkit.

This module defines `Operation` instances (signatures, names) for
common math functions such as `sin`, `cos`, `add`, `multiply`, and
`power`. These objects describe expected argument types and are used
by downstream validation and dispatch.
"""

import core.attribute_types as attribute_types
from core.signature import Parameter, Signature
from core.operation import Operation

SIN = Operation(
    name="sin",
    signatures=(
        Signature(
            inputs=[Parameter("value", attribute_types.NUMBER)],
            output=attribute_types.NUMBER,
        ),
    ),
)

COS = Operation(
    name="cos",
    signatures=(
        Signature(
            inputs=[Parameter("value", attribute_types.NUMBER)],
            output=attribute_types.NUMBER,
        ),
    ),
)

REMAP = Operation(
    name="remap",
    signatures=(
        Signature(
            inputs=[
                Parameter("input_min", attribute_types.NUMBER),
                Parameter("input_max", attribute_types.NUMBER),
                Parameter("output_min", attribute_types.NUMBER),
                Parameter("output_max", attribute_types.NUMBER),
                Parameter("value", attribute_types.NUMBER),
            ],
            output=attribute_types.NUMBER,
        ),
    ),
)

ADD = Operation(
    name="add",
    signatures=(
        Signature(
            inputs=[
                Parameter("value", attribute_types.NUMBER, variadict=True, min_count=2)
            ],
            output=attribute_types.NUMBER,
        ),
        Signature(
            inputs=[
                Parameter("value", attribute_types.VECTOR, variadict=True, min_count=2)
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.NUMBER),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.VECTOR,
        ),
    ),
)

SUBTRACT = Operation(
    name="subtract",
    signatures=(
        Signature(
            inputs=[
                Parameter("value1", attribute_types.NUMBER),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.NUMBER,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.NUMBER),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.VECTOR,
        ),
    ),
)

MULTIPLY = Operation(
    name="mult",
    signatures=(
        Signature(
            inputs=[
                Parameter("value", attribute_types.NUMBER, variadict=True, min_count=2)
            ],
            output=attribute_types.NUMBER,
        ),
        Signature(
            inputs=[
                Parameter("value", attribute_types.VECTOR, variadict=True, min_count=2)
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value", attribute_types.MATRIX4, variadict=True, min_count=2)
            ],
            output=attribute_types.MATRIX4,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.NUMBER),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.MATRIX4),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
    ),
)

DIVIDE = Operation(
    name="div",
    signatures=(
        Signature(
            inputs=[
                Parameter("value1", attribute_types.NUMBER),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.NUMBER,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.NUMBER),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.VECTOR,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.VECTOR),
            ],
            output=attribute_types.VECTOR,
        ),
    ),
)

POWER = Operation(
    name="pow",
    signatures=(
        Signature(
            inputs=[
                Parameter("value1", attribute_types.NUMBER),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.NUMBER,
        ),
        Signature(
            inputs=[
                Parameter("value1", attribute_types.VECTOR),
                Parameter("value2", attribute_types.NUMBER),
            ],
            output=attribute_types.VECTOR,
        ),
    ),
)

__all__ = [
    "SIN",
    "COS",
    "REMAP",
    "ADD",
    "SUBTRACT",
    "MULTIPLY",
    "DIVIDE",
    "POWER",
]
