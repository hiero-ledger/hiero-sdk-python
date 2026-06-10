from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.util.param_utils import parse_session_id, to_bool


@dataclass
class HbarTransferParams:
    accountId: str | None = None
    evmAddress: str | None = None
    amount: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict[str, object]) -> HbarTransferParams:
        return cls(accountId=params.get("accountId"), evmAddress=params.get("evmAddress"), amount=params.get("amount"))


@dataclass
class TokenTransferParams:
    tokenId: str | None = None
    accountId: str | None = None
    amount: str | None = None
    decimals: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict[str, object]) -> TokenTransferParams:
        return cls(
            tokenId=params.get("tokenId"),
            accountId=params.get("accountId"),
            amount=params.get("amount"),
            decimals=params.get("decimals"),
        )


@dataclass
class NftTransferParams:
    tokenId: str | None = None
    serialNumber: str | None = None
    senderAccountId: str | None = None
    receiverAccountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict[str, object]) -> NftTransferParams:
        return cls(
            tokenId=params.get("tokenId"),
            serialNumber=params.get("serialNumber"),
            senderAccountId=params.get("senderAccountId"),
            receiverAccountId=params.get("receiverAccountId"),
        )


@dataclass
class TransferParams:
    hbar: HbarTransferParams | None = None
    token: TokenTransferParams | None = None
    nft: NftTransferParams | None = None
    approved: bool | None = None

    @classmethod
    def parse_json_params(cls, params: dict[str, object]) -> TransferParams:
        return cls(
            hbar=HbarTransferParams.parse_json_params(params["hbar"]) if params.get("hbar") is not None else None,
            token=TokenTransferParams.parse_json_params(params["token"]) if params.get("token") is not None else None,
            nft=NftTransferParams.parse_json_params(params["nft"]) if params.get("nft") is not None else None,
            approved=to_bool(params.get("approved")) if "approved" in params else None,
        )


@dataclass
class TransferCryptoParams(BaseTransactionParams):
    transfers: list[TransferParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> TransferCryptoParams:
        transfers_raw = params.get("transfers")

        return cls(
            sessionId=parse_session_id(params),
            commonTransactionParams=params.get("commonTransactionParams"),
            transfers=[TransferParams.parse_json_params(t) for t in transfers_raw] if transfers_raw else None,
        )
