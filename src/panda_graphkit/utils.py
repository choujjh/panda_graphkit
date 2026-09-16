"""Shared utility functions used across graphkit modules."""

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
