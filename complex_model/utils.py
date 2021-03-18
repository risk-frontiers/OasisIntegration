# Simple centralised set of utilities to account for changes in Oasis.
# E.g. how datatypes are assigned to parsed OED columns


def is_integer(obj):
    try:
        int(obj)
        return True
    except ValueError:
        return False


def is_float(obj):
    try:
        float(obj)
        return True
    except ValueError:
        return False


def is_bool(obj):
    try:
        return isinstance(obj, bool)
    except ValueError:
        return False


def is_number(obj):
    return is_integer(obj) or is_float(obj)


def to_bool(obj):
    if isinstance(obj, int):
        return bool(obj)
    elif isinstance(obj, str):
        if obj.lower() in ['1', 'true', 'yes']:
            return True
        if obj.lower() in ['0', 'false', 'no']:
            return False
    raise TypeError("{0} is not a boolean value".format(obj))
