from __future__ import annotations


def parse_session_id(params: dict) -> str:
    """Parse sessionId from the json rpc params."""
    session_id = params.get("sessionId")

    if isinstance(session_id, str) and session_id != "":
        return session_id

    raise ValueError("sessionId is required and must be a non-empty string")


def parse_common_transaction_params(params: dict):
    """Parse the commonTransactionParams form json the rpc params."""
    from tck.param.common import CommonTransactionParams

    common_params = params.get("commonTransactionParams")
    if common_params is None:
        return None

    return CommonTransactionParams.parse_json_params(params.get("commonTransactionParams"))


def to_int(value) -> int | None:
    """Helper to convert value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def non_empty_string_or_none(value: str | None) -> str | None:
    """Trim string values; convert blank strings to None."""
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    return cleaned if cleaned else None


def non_empty_string_list(values) -> list[str] | None:
    """Trim list entries and remove empty-string items."""
    if values is None:
        return None

    cleaned_values: list[str] = []
    for value in values:
        cleaned = non_empty_string_or_none(value)
        if cleaned is not None:
            cleaned_values.append(cleaned)

    return cleaned_values


def to_bool(value) -> bool | None:
    """Helper to convert value to bool."""
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value) if value is not None else None
