"""Operation descriptor used to register callable graph operations.

An `Operation` bundles a name and one or more `Signature` objects that
describe the allowed input shapes and types for the operation. These
are lightweight dataclasses used by validation and dispatch logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections.abc import Iterable
from ..core import types_is_compatable
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
    types_: tuple[attribute_types.AttributeType]
    variadict: bool = False
    min_count: int = 1

    def __post_init__(self):
        """Normalize parameter types into a tuple for consistent validation."""
        if not isinstance(self.types_, tuple):
            curr_var = self.types_
            if not isinstance(curr_var, Iterable):
                curr_var = [curr_var]
            object.__setattr__(self, "types_", tuple(curr_var))

    def replace(
        self,
        name: str = None,
        types_: tuple[attribute_types.AttributeType] = None,
        variadict: bool = None,
        min_count: int = None,
    ):
        """Replaces fields for new copy of Parameter

        Args:
            name (str, optional): _description_. Defaults to None.
            types_ (tuple[attribute_types.AttributeType], optional): _description_. Defaults to None.
            variadict (bool, optional): _description_. Defaults to None.
            min_count (int, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        if name is None:
            name = self.name
        if types_ is None:
            types_ = self.types_
        if variadict is None:
            variadict = self.variadict
        if min_count is None:
            min_count = self.min_count
        return Parameter(name, types_, variadict, min_count)


@dataclass(frozen=True)
class Signature:
    """Describe a particular callable signature for an operation.

    Attributes:
        inputs: Sequence of `Parameter` objects describing expected inputs.
        output: Sequence of `Parameter` objects describing expected output.
        commutative: if signature's orders matter
    """

    inputs: tuple[Parameter]
    outputs: tuple[Parameter]
    commutative: bool = field(default=False, compare=False)

    def __repr__(self):
        """Return a readable representation of the signature shape."""
        inputs = []
        for input in self.inputs:
            input_types = "|".join([x.name for x in input.types_])
            if input.variadict:
                inputs.append(f"{input_types}(variadict)")
            else:
                inputs.append(input_types)
        outputs = []
        for output in self.outputs:
            output_types = "|".join([x.name for x in output.types_])
            if output.variadict:
                outputs.append(f"{output_types}(variadict)")
            else:
                outputs.append(output_types)

        return f"{inputs} -> {outputs}"

    def __post_init__(self):
        """Coerce the input and output parameter lists to tuples."""
        if not isinstance(self.inputs, tuple):
            curr_var = self.inputs
            if not isinstance(curr_var, Iterable):
                curr_var = [curr_var]
            object.__setattr__(self, "inputs", tuple(curr_var))
        if not isinstance(self.outputs, tuple):
            curr_var = self.outputs
            if not isinstance(curr_var, Iterable):
                curr_var = [curr_var]
            object.__setattr__(self, "outputs", tuple(curr_var))

    def replace(
        self,
        inputs: tuple[Parameter] = None,
        outputs: tuple[Parameter] = None,
        commutative: bool = None,
    )->Signature:
        """Replace Fields in Signature for copy of signature

        Args:
            inputs (tuple[Parameter], optional): Defaults to None.
            outputs (tuple[Parameter], optional): Defaults to None.
            commutative (bool, optional): Defaults to None.

        Returns:
            Signature:
        """
        if inputs is None:
            inputs = self.inputs
        if outputs is None:
            outputs = self.outputs
        if commutative is None:
            commutative = self.commutative
        return Signature(inputs, outputs, commutative)

    def replace_names(self, *names) -> Signature:
        """Replaces Parameter names

        Raises:
            ValueError:

        Returns:
            Signature:
        """
        if len(names) != len(self.inputs) + len(self.outputs):
            raise ValueError(
                f"Number of names ({len(names)}) does not match signature ({len(self.inputs) + len(self.outputs)})"
            )
        return Signature(
            inputs=tuple(
                parm.replace(name=name)
                for parm, name in zip(self.inputs, names[: len(self.inputs)])
            ),
            outputs=tuple(
                parm.replace(name=name)
                for parm, name in zip(self.outputs, names[len(self.inputs) :])
            ),
        )


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

    def __post_init__(self):
        """Normalize operation signatures to a tuple for consistent dispatch."""
        if not isinstance(self.signatures, tuple):
            curr_var = self.signatures
            if not isinstance(curr_var, Iterable):
                curr_var = [curr_var]
            object.__setattr__(self, "signatures", tuple(curr_var))


def check_signature(
    operation: Operation,
    arg_types: list[attribute_types.AttributeType] | Signature,
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
    out_attr_type, signature = match_signature(operation, arg_types)

    if out_attr_type is None and signature is None:
        raise TypeError(
            f"No matching signature found for operation '{operation.name}' with argument types {arg_types}"
        )

    return out_attr_type, signature


def match_signature(
    operation: Operation,
    arg_types: list[attribute_types.AttributeType] | Signature,
) -> tuple[attribute_types.AttributeType, Signature]:
    """tries to find a matching signature. returns None otherwise

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
    if isinstance(arg_types, Signature):
        arg_types = [x.types_ for x in arg_types.inputs]
    for signature in operation.signatures:
        first_input = signature.inputs[0] if signature.inputs else None
        if (
            first_input
            and first_input.variadict
            and len(arg_types) >= first_input.min_count
        ):
            if all(
                types_is_compatable(first_input.types_, arg_type)
                for arg_type in arg_types
            ):
                if signature.outputs[0] in [attribute_types.NUMBER]:
                    return attribute_types.infer_return_type(arg_types), signature
                return signature.outputs[0].types_[0], signature
        if len(arg_types) == len(signature.inputs):
            if all(
                types_is_compatable(arg_type, param.types_)
                for arg_type, param in zip(arg_types, signature.inputs)
            ):
                if signature.outputs[0] in [attribute_types.NUMBER]:
                    return attribute_types.infer_return_type(arg_types), signature
                return signature.outputs[0].types_[0], signature

    return None, None
