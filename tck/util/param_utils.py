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


def to_bool(value) -> bool | None:
    """Helper to convert value to bool."""
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value) if value is not None else None
