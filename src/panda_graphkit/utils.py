"""Shared small types used across graphkit modules."""

from enum import Enum


class Associativity(Enum):
    """Direction in which operators of equal precedence group."""

    LEFT = "left"
    RIGHT = "right"

def nested_to_dict(data, indexes=(), depth=0, max_depth=300):
    result = {}
    if depth >= max_depth:
        return {}
    for i, value in enumerate(data):
        current_index = indexes + (i,)

        if isinstance(value, list):
            result.update(nested_to_dict(value, current_index, depth + 1))
        else:
            result[current_index] = value

    return result

def kwarg_to_dict(**kwarg_dict):
    """returns keyword arguments as a dictionary"""
    return kwarg_dict
