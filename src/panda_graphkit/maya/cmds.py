"""Forward Maya commands while converting Node/Attr inputs and results.

Import with ``from panda_graphkit.maya import cmds``. Returned strings that
resolve to scene nodes or attributes become wrappers, including ordinary text
that happens to match a scene name. Use maya.cmds for unchanged return values.
"""

from functools import lru_cache, wraps

from maya import cmds as maya_cmds

from .node_wrapper import Node, Attr, wrap_node


def _convert(value, converter):
    """Convert individual values recursively, preserving container types."""
    if isinstance(value, list):
        return [_convert(item, converter) for item in value]
    if isinstance(value, tuple):
        return tuple(_convert(item, converter) for item in value)
    if isinstance(value, dict):
        return {key: _convert(item, converter) for key, item in value.items()}
    return converter(value)


def _unwrap(value):
    """Turn node and attribute wrappers into names accepted by Maya."""
    if isinstance(value, (Node, Attr)):
        return str(value)
    return value


def _wrap(value):
    """Resolve node/attribute names, leaving other results unchanged."""
    if not isinstance(value, str):
        return value

    # Keep everything after the first dot for compound and array attributes.
    node_name, separator, attr_name = value.partition(".")
    node = wrap_node(node_name)
    if node is None:
        return value
    if not separator:
        return node

    # Components such as cube.vtx[0] contain dots too, but aren't attributes.
    try:
        return node[attr_name]
    except AttributeError:
        return value


# Remember forwarding functions by name, not the results of Maya commands.
@lru_cache(maxsize=None)
def __getattr__(name):
    """Create a forwarding function when a command is accessed on this module."""
    command = getattr(maya_cmds, name)
    if not callable(command):
        return command

    # Preserve the original command's name and documentation for inspection.
    @wraps(command)
    def wrapped(*args, **kwargs):
        result = command(
            *_convert(args, _unwrap),
            **_convert(kwargs, _unwrap),
        )
        return _convert(result, _wrap)

    return wrapped
