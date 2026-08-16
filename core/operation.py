"""Operation descriptor used to register callable graph operations.

An `Operation` bundles a name and one or more `Signature` objects that
describe the allowed input shapes and types for the operation. These
are lightweight dataclasses used by validation and dispatch logic.
"""

from dataclasses import dataclass
from .signature import Signature


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
        return f"Operation(name: {self.name} - num signatures: {len(self.signatures)})"
