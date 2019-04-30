
def str_to_int(string):
    """
    Parses a string number into an integer, optionally converting to a float
    and rounding down.

    Some LVM values may come with a comma instead of a dot to define decimals.
    This function normalizes a comma into a dot
    """
    try:
        integer = float(string.replace(',', '.'))
    except AttributeError:
        # this might be a integer already, so try to use it, otherwise raise
        # the original exception
        if isinstance(string, (int, float)):
            integer = string
        else:
            raise

    return int(integer)
