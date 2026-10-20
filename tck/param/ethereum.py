"""TCK request parameter models for the ethereum-transaction endpoint."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import parse_common_transaction_params, parse_session_id


@dataclass
class CreateEthereumTransactionParams(BaseTransactionParams):
    """Parameters for createEthereumTransaction.

    Extends BaseTransactionParams to include common transaction parameters.
    """

    ethereumData: str | None = None
    callDataFileId: str | None = None
    maxGasAllowance: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateEthereumTransactionParams:
        return cls(
            ethereumData=params.get("ethereumData"),
            callDataFileId=params.get("callDataFileId"),
            maxGasAllowance=params.get("maxGasAllowance"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
