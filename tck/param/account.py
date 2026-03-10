from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.json_param_parser import parse_common_transaction_params, parse_session_id


@dataclass
class CreateAccountParams(BaseTransactionParams):
  key: str | None = None
  initialBalance: str | None = None
  receiverSignatureRequired: bool | None = None
  maxAutoTokenAssociations: int | None = None
  stakedAccountId: str | None = None
  stakedNodeId: str | None = None
  declineStakingReward: bool | None = None
  memo: str | None = None
  autoRenewPeriod: str | None = None
  alias: str | None = None

  @classmethod
  def from_dict(cls, params: dict) -> "CreateAccountParams":
    initial_balance = params.get("initialBalance")
    staked_node_id = params.get("stakedNodeId")
    receiver_signature_required = params.get("receiverSignatureRequired")
    max_auto_association = params.get("maxAutoTokenAssociations")

    print("creaing object")
    print(parse_common_transaction_params(params))

    obj =  cls(
      key=params.get("key"),
      initialBalance=int(initial_balance) if initial_balance else None,
      receiverSignatureRequired=eval(receiver_signature_required) if receiver_signature_required else None,
      maxAutoTokenAssociations=int(max_auto_association) if max_auto_association else None,
      stakedAccountId=params.get("stakedAccountId"),
      stakedNodeId=int(staked_node_id) if staked_node_id else None,
      declineStakingReward=params.get("declineStakingReward"),
      memo=params.get("memo"),
      autoRenewPeriod=params.get("autoRenewPeriod"),
      alias=params.get("alias"),
      sessionId=parse_session_id(params),
    )

    print("Object done")
    return obj
