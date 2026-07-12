"""TCK request parameter models for token endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from tck.param.base import BaseTransactionParams
from tck.param.custom_fee import CustomFeeParams
from tck.util.param_utils import (
    parse_common_transaction_params,
    parse_session_id,
    to_bool,
    to_int,
)


@dataclass
class CreateTokenParams(BaseTransactionParams):
    """Request parameters for the createToken endpoint."""

    name: str | None = None
    symbol: str | None = None
    decimals: int | None = None
    initialSupply: str | None = None
    treasuryAccountId: str | None = None
    adminKey: str | None = None
    kycKey: str | None = None
    freezeKey: str | None = None
    wipeKey: str | None = None
    supplyKey: str | None = None
    pauseKey: str | None = None
    feeScheduleKey: str | None = None
    metadataKey: str | None = None
    memo: str | None = None
    tokenType: str | None = None
    supplyType: str | None = None
    maxSupply: str | None = None
    freezeDefault: bool | None = None
    expirationTime: str | None = None
    autoRenewAccountId: str | None = None
    autoRenewPeriod: str | None = None
    metadata: str | None = None
    customFees: list[CustomFeeParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateTokenParams:
        """Parse JSON-RPC params into a CreateTokenParams instance."""
        custom_fees = params.get("customFees")
        if custom_fees is not None and not isinstance(custom_fees, list):
            raise ValueError("customFees must be a list")

        return cls(
            name=params.get("name"),
            symbol=params.get("symbol"),
            decimals=to_int(params.get("decimals")),
            initialSupply=params.get("initialSupply"),
            treasuryAccountId=params.get("treasuryAccountId"),
            adminKey=params.get("adminKey"),
            kycKey=params.get("kycKey"),
            freezeKey=params.get("freezeKey"),
            wipeKey=params.get("wipeKey"),
            supplyKey=params.get("supplyKey"),
            pauseKey=params.get("pauseKey"),
            feeScheduleKey=params.get("feeScheduleKey"),
            metadataKey=params.get("metadataKey"),
            memo=params.get("memo"),
            tokenType=params.get("tokenType"),
            supplyType=params.get("supplyType"),
            maxSupply=params.get("maxSupply"),
            freezeDefault=to_bool(params.get("freezeDefault")),
            expirationTime=params.get("expirationTime"),
            autoRenewAccountId=params.get("autoRenewAccountId"),
            autoRenewPeriod=params.get("autoRenewPeriod"),
            metadata=params.get("metadata"),
            customFees=(
                [CustomFeeParams.parse_json_params(custom_fee) for custom_fee in custom_fees]
                if custom_fees is not None
                else None
            ),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class MintTokenParams(BaseTransactionParams):
    """Request parameters for the mintToken endpoint."""

    tokenId: str | None = None
    amount: str | None = None
    metadata: list[str] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> MintTokenParams:
        """Parse JSON-RPC params into a MintTokenParams instance."""
        metadata = params.get("metadata")
        if metadata is not None and not isinstance(metadata, list):
            raise ValueError("metadata must be a list")
        if metadata is not None and any(not isinstance(value, str) for value in metadata):
            raise ValueError("each metadata item must be a string")

        return cls(
            tokenId=params.get("tokenId"),
            amount=params.get("amount"),
            metadata=metadata,
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class AssociateTokenParams(BaseTransactionParams):
    """Request parameters for the associateToken endpoint."""

    accountId: str | None = None
    tokenIds: list[str] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> AssociateTokenParams:
        """Parse JSON-RPC params into an AssociateTokenParams instance."""
        token_ids = params.get("tokenIds")
        if token_ids is not None and not isinstance(token_ids, list):
            raise ValueError("tokenIds must be a list")
        if token_ids is not None and any(not isinstance(token_id, str) for token_id in token_ids):
            raise ValueError("each tokenIds item must be a string")

        return cls(
            accountId=params.get("accountId"),
            tokenIds=token_ids,
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class DeleteTokenParams(BaseTransactionParams):
    """Request parameters for the deleteToken endpoint."""

    tokenId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> DeleteTokenParams:
        """Parse JSON-RPC params into a DeleteTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class FreezeTokenParams(BaseTransactionParams):
    """Request parameters for the freezeToken endpoint."""

    tokenId: str | None = None
    accountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> FreezeTokenParams:
        """Parse JSON-RPC params into a FreezeTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            accountId=params.get("accountId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class PauseTokenParams(BaseTransactionParams):
    """Request parameters for the pauseToken endpoint."""

    tokenId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> PauseTokenParams:
        """Parse JSON-RPC params into a PauseTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class RevokeKycTokenParams(BaseTransactionParams):
    """Request parameters for the revokeTokenKyc endpoint."""

    tokenId: str | None = None
    accountId: str | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> RevokeKycTokenParams:
        """Parse JSON-RPC params into a RevokeKycTokenParams instance."""
        return cls(
            tokenId=params.get("tokenId"),
            accountId=params.get("accountId"),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class AirdropTokenParams(BaseTransactionParams):
    """Request parameters for the airdropToken endpoint."""

    tokenTransfers: list | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> AirdropTokenParams:
        """Parse JSON-RPC params into an AirdropTokenParams instance."""
        from tck.param.transfer import TransferParams

        token_transfers_raw = params.get("tokenTransfers")

        return cls(
            tokenTransfers=(
                [TransferParams.parse_json_params(t) for t in token_transfers_raw]
                if token_transfers_raw is not None
                else None
            ),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class ClaimTokenParams(BaseTransactionParams):
    """Request parameters for the claimToken endpoint."""

    senderAccountId: str | None = None
    receiverAccountId: str | None = None
    tokenId: str | None = None
    serialNumbers: list[str] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> ClaimTokenParams:
        """Parse JSON-RPC params into a ClaimTokenParams instance."""
        serial_numbers = params.get("serialNumbers")
        if serial_numbers is not None and not isinstance(serial_numbers, list):
            raise ValueError("serialNumbers must be a list")
        if serial_numbers is not None and any(not isinstance(serial_number, str) for serial_number in serial_numbers):
            raise ValueError("each serialNumbers item must be a string")

        return cls(
            senderAccountId=params.get("senderAccountId"),
            receiverAccountId=params.get("receiverAccountId"),
            tokenId=params.get("tokenId"),
            serialNumbers=serial_numbers,
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )
