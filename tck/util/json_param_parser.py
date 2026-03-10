from tck.param.common_tx_param import CommonTransactionParams


def parse_session_id(params: dict) -> str:
  session_id = params.get("sessionId")
  
  if isinstance(session_id, str) and session_id != "":
    return session_id
    
  raise ValueError("sessionId is required and must be a non-empty string")


def parse_common_transaction_params(params: dict) -> CommonTransactionParams | None:
  common_params = params.get("commonTransactionParams")
  if common_params is None:
    return None
  
  return CommonTransactionParams.from_dict(params.get("commonTransactionParams"))

