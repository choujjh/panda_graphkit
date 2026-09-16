"""Panda GraphKit public API with lazily loaded graph components."""

from importlib import import_module

__all__ = [
    "AttributeType", "Graph", "Operation", "Signature", "Parameter",
    "Associativity", "Backend", "MockBackend", "ExpressionResult",
    "build_expression",
]


def __getattr__(name: str):
    """Load graph API objects only when they are requested."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".graph", __name__), name)
    globals()[name] = value
    return value
