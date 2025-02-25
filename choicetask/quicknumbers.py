def try_int(value, default=None, base=10):
    """
    Attempt to convert 'value' to an integer.

    Parameters:
      value: The value to convert (can be int, float, str, etc.).
      default: A value to return if conversion fails.
      base: Base for integer conversion (only used if 'value' is a string).

    Returns:
      The integer conversion of 'value' if possible;
      otherwise, returns 'default' if provided, or else the original value.
    """
    # If already an int, just return it.
    if isinstance(value, int):
        return value
    try:
        if isinstance(value, str):
            # Remove any surrounding whitespace.
            value = value.strip()
            # An empty string should be treated as a conversion failure.
            if not value:
                raise ValueError("Empty string")
            # Convert using the specified base.
            return int(value, base)
        else:
            # For non-string types, rely on Python's built-in int conversion.
            return int(value)
    except (ValueError, TypeError):
        return default if default is not None else value


def try_float(value, default=None):
    """
    Attempt to convert 'value' to a float.

    Parameters:
      value: The value to convert.
      default: A value to return if conversion fails.

    Returns:
      The float conversion of 'value' if possible;
      otherwise, returns 'default' if provided, or else the original value.
    """
    # If already a float, just return it.
    if isinstance(value, float):
        return value
    try:
        if isinstance(value, str):
            # Remove any surrounding whitespace.
            value = value.strip()
            if not value:
                raise ValueError("Empty string")
        # Convert using Python's built-in float conversion.
        return float(value)
    except (ValueError, TypeError):
        return default if default is not None else value


# Example usage:
if __name__ == "__main__":
    # try_int examples
    print(try_int(" 42 "))  # 42
    print(try_int("not a number", default=-1))  # -1
    print(try_int(3.0))  # 3
    print(try_int("101", base=2))  # 5 (binary 101 -> 5)

    # try_float examples
    print(try_float("3.1415"))  # 3.1415
    print(try_float("not a float", default=-1.0))  # -1.0
    print(try_float(10))  # 10.0
