"""Function signature and parameter descriptions for operations.

Provides small frozen dataclasses used to declare operation inputs
and outputs for validation and dispatch.
"""

from dataclasses import dataclass
from .attribute_types import AttributeType


@dataclass(frozen=True)
class Parameter:
    """Describe a single parameter of an operation signature.

    Attributes:
        name: Parameter name.
        type: Expected `GraphType` of the parameter.
        variadict: Whether this parameter accepts a variable number of values.
        min_count: Minimum number of values when `variadict` is True.
    """
    name:str
    type: AttributeType
    variadict: bool = False
    min_count: int = 1


@dataclass(frozen=True)
class Signature:
    """Describe a particular callable signature for an operation.

    Attributes:
        inputs: Sequence of `Parameter` objects describing expected inputs.
        output: Expected `GraphType` of the result.
    """
    inputs: list[Parameter]
    output: AttributeType