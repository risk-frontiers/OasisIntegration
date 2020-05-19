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
