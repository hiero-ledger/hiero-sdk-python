from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import (
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
    to_int,
)


@dataclass
class CreateAccountParams(BaseTransactionParams):
    key: str | None = None
    initialBalance: int | None = None
    receiverSignatureRequired: bool | None = None
    maxAutoTokenAssociations: int | None = None
    stakedAccountId: str | None = None
    stakedNodeId: int | None = None
    declineStakingReward: bool | None = None
    memo: str | None = None
    autoRenewPeriod: int | None = None
    alias: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateAccountParams:
        return cls(
            key=params.get("key"),
            initialBalance=to_int(params.get("initialBalance")),
            receiverSignatureRequired=to_bool(params.get("receiverSignatureRequired")),
            maxAutoTokenAssociations=to_int(params.get("maxAutoTokenAssociations")),
            stakedAccountId=params.get("stakedAccountId"),
            stakedNodeId=to_int(params.get("stakedNodeId")),
            declineStakingReward=to_bool(params.get("declineStakingReward")),
            memo=params.get("memo"),
            autoRenewPeriod=to_int(params.get("autoRenewPeriod")),
            alias=params.get("alias"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
