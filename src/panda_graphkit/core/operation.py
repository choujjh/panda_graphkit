"""Operation descriptor used to register callable graph operations.

An `Operation` bundles a name and one or more `Signature` objects that
describe the allowed input shapes and types for the operation. These
are lightweight dataclasses used by validation and dispatch logic.
"""

from dataclasses import dataclass
from . import attribute_types


@dataclass(frozen=True)
class Parameter:
    """Describe a single parameter of an operation signature.

    Attributes:
        name: Parameter name.
        type: Expected `GraphType` of the parameter.
        variadict: Whether this parameter accepts a variable number of values.
        min_count: Minimum number of values when `variadict` is True.
    """

    name: str
    type_: attribute_types.AttributeType
    variadict: bool = False
    min_count: int = 1


@dataclass(frozen=True)
class Signature:
    """Describe a particular callable signature for an operation.

    Attributes:
        inputs: Sequence of `Parameter` objects describing expected inputs.
        output: Expected `GraphType` of the result.
    """

    inputs: tuple[Parameter]
    outputs: tuple[Parameter]

    def __repr__(self):
        inputs = []
        for input in self.inputs:
            if input.variadict:
                inputs.append(f"{input.type_.name}(variadict)")
            else:
                inputs.append(input.type_.name)
        outputs = []
        for output in self.outputs:
            if output.variadict:
                outputs.append(f"{output.type_.name}(variadict)")
            else:
                outputs.append(output.type_.name)

        return f"{inputs} -> {outputs}"


@dataclass(frozen=True)
class Operation:
    """Descriptor for a callable operation available to the graph.

    Attributes:
        name: Public name of the operation (e.g. 'sin').
        signatures: Tuple of `Signature` objects describing allowed inputs.
    """

    name: str
    signatures: tuple[Signature, ...]

    def __repr__(self):
        """Return a concise representation containing name and signature count."""
        return f"Operation(name: {self.name} - num signatures: {len(self.signatures)})"


def check_signature(
    operation: Operation,
    arg_types: list[attribute_types.AttributeType],
) -> tuple[attribute_types.AttributeType, Signature]:
    """Check if argument types match a signature in the operation.

    Iterates through operation signatures and tests if the provided
    argument types match via subtype checking (is_a). Handles both
    variadic and fixed-arity parameters.

    Args:
        operation: The Operation to check signatures for.
        arg_types: List of argument types to match against signatures.

    Returns:
        The return type of the matching signature. For numeric returns,
        infers the most specific numeric type (INT/FLOAT).
        returns the signature that matches

    Raises:
        TypeError: If no matching signature is found.
    """
    for signature in operation.signatures:
        first_input = signature.inputs[0] if signature.inputs else None
        if (
            first_input
            and first_input.variadict
            and len(arg_types) >= first_input.min_count
        ):
            if all(arg_type.is_compatable(first_input.type_) for arg_type in arg_types):
                if signature.outputs[0] in [attribute_types.NUMBER]:
                    return attribute_types.infer_return_type(arg_types), signature
                return signature.outputs[0].type_, signature
        if len(arg_types) == len(signature.inputs):
            if all(
                arg_type.is_compatable(param.type_)
                for arg_type, param in zip(arg_types, signature.inputs)
            ):
                if signature.outputs[0] in [attribute_types.NUMBER]:
                    return attribute_types.infer_return_type(arg_types), signature
                return signature.outputs[0].type_, signature

    raise TypeError(
        f"No matching signature found for operation '{operation.name}' with argument types {arg_types}"
    )
