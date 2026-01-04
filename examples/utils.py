def info_to_dict(info):
    """
    Convert an AccountInfo object into a dictionary of serializable strings.
    Useful for pretty-printing information in examples.
    """
    out = {}

    for name in dir(info):
        if name.startswith("_"):
            continue

        try:
            val = getattr(info, name)
        except Exception as error:
            out[name] = f"Error retrieving value: {error}"
            continue

        if callable(val):
            continue

        out[name] = str(val)

    return out
