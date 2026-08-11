"""Predefined mathematical operations available to the graphkit.

This module defines `Operation` instances (signatures, names) for
common math functions such as `sin`, `cos`, `add`, `multiply`, and
`power`. These objects describe expected argument types and are used
by downstream validation and dispatch.
"""

import core.graph_types as graph_types
from core.signature import Parameter, Signature
from core.operation import Operation

SIN = Operation(
    name="sin",
    signatures=(
        Signature(
            Parameter("value", graph_types.NUMBER),
            )
    )
)

COS = Operation(
    name="cos",
    signatures=(
        Signature(
            Parameter("value", graph_types.NUMBER),
        )
    )
)

REMAP = Operation(
    name="remap",
    signatures=(
        Signature(
            Parameter("input_min", graph_types.NUMBER),
            Parameter("input_max", graph_types.NUMBER),
            Parameter("output_min", graph_types.NUMBER),
            Parameter("output_max", graph_types.NUMBER),
            Parameter("value", graph_types.NUMBER),
        )
    )
)

ADD = Operation(
    name="add",
    signatures=(
        Signature(
            Parameter("value", graph_types.NUMBER, variadict=True, min_count=2)
        ),
        Signature(
            Parameter("value", graph_types.VECTOR, variadict=True, min_count=2)
        ),
        Signature(
            Parameter("value1", graph_types.NUMBER),
            Parameter("value2", graph_types.VECTOR)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.NUMBER)
        )
    )
)

SUBTRACT = Operation(
    name="subtract",
    signatures=(
        Signature(
            Parameter("value1", graph_types.NUMBER),
            Parameter("value2", graph_types.NUMBER)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.VECTOR)
        ),
        Signature(
            Parameter("value1", graph_types.NUMBER),
            Parameter("value2", graph_types.VECTOR)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.NUMBER)
        )
    )
)

MULTIPLY = Operation(
    name="multiply",
    signatures=(
        Signature(
            Parameter("value", graph_types.NUMBER, variadict=True, min_count=2)
        ),
        Signature(
            Parameter("value1", graph_types.NUMBER),
            Parameter("value2", graph_types.VECTOR)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.NUMBER)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.VECTOR)
        )
    )
)

DIVIDE = Operation(
    name="divide",
    signatures=(
        Signature(
            Parameter("value1", graph_types.NUMBER),
            Parameter("value2", graph_types.NUMBER)
        ),
        Signature(
            Parameter("value1", graph_types.NUMBER),
            Parameter("value2", graph_types.VECTOR)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.NUMBER)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.VECTOR)
        )
    )
)

POWER = Operation(
    name="power",
    signatures=(
        Signature(
            Parameter("value1", graph_types.NUMBER),
            Parameter("value2", graph_types.NUMBER)
        ),
        Signature(
            Parameter("value1", graph_types.VECTOR),
            Parameter("value2", graph_types.NUMBER)
        )
    )
)