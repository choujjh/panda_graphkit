"""Core package: graph types, signatures, and operation definitions.

Provides the foundational types and small data classes used by the
rest of the library (type system, operation signatures, and
operation descriptors).
"""

from .attribute_types import (
    AttributeType,
    NUMBER,
    INT,
    FLOAT,
    VECTOR,
    VECTOR2,
    VECTOR3,
    BOOL,
    MATRIX4,
    STRING,
    infer_return_type,
)
from .graph import (
    Graph,
    Port,
    InputPort,
    OutputPort,
    BackendInputPort,
    BackendOutputPort,
    Node,
    ConstNode,
    BackendNode,
    Connection,
)
from .math import Vector as MathVector, Matrix as MathMatrix
from .operation import Operation, Signature, Parameter, check_signature


__all__ = [
    "AttributeType",
    "NUMBER",
    "INT",
    "FLOAT",
    "VECTOR",
    "VECTOR2",
    "VECTOR3",
    "BOOL",
    "MATRIX4",
    "STRING",
    "infer_return_type",
    "Graph",
    "Port",
    "InputPort",
    "OutputPort",
    "BackendInputPort",
    "BackendOutputPort",
    "Node",
    "ConstNode",
    "BackendNode",
    "Connection",
    "MathVector",
    "MathMatrix",
    "Operation",
    "Signature",
    "Parameter",
    "check_signature",
]
