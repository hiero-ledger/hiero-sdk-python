"""TCK RPC handlers for token-related endpoints."""

from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.token import (
    AssociateTokenParams,
    CreateTokenParams,
    DeleteTokenParams,
    FreezeTokenParams,
    MintTokenParams,
    PauseTokenParams,
)
from tck.response.token import (
    AssociateTokenResponse,
    CreateTokenResponse,
    DeleteTokenResponse,
    FreezeTokenResponse,
    MintTokenResponse,
    PauseTokenResponse,
)
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string


def _build_create_token_transaction(params: CreateTokenParams) -> TokenCreateTransaction:
    """Build a TokenCreateTransaction from TCK params."""
    transaction = TokenCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.name is not None:
        transaction.set_token_name(params.name)

    if params.symbol is not None:
        transaction.set_token_symbol(params.symbol)

    if params.decimals is not None:
        transaction.set_decimals(params.decimals)

    if params.initialSupply is not None:
        transaction.set_initial_supply(int(params.initialSupply))

    if params.treasuryAccountId is not None:
        transaction.set_treasury_account_id(AccountId.from_string(params.treasuryAccountId))

    if params.adminKey is not None:
        transaction.set_admin_key(get_key_from_string(params.adminKey))

    if params.kycKey is not None:
        transaction.set_kyc_key(get_key_from_string(params.kycKey))

    if params.freezeKey is not None:
        transaction.set_freeze_key(get_key_from_string(params.freezeKey))

    if params.wipeKey is not None:
        transaction.set_wipe_key(get_key_from_string(params.wipeKey))

    if params.supplyKey is not None:
        transaction.set_supply_key(get_key_from_string(params.supplyKey))

    if params.pauseKey is not None:
        transaction.set_pause_key(get_key_from_string(params.pauseKey))

    if params.feeScheduleKey is not None:
        transaction.set_fee_schedule_key(get_key_from_string(params.feeScheduleKey))

    if params.metadataKey is not None:
        transaction.set_metadata_key(get_key_from_string(params.metadataKey))

    if params.memo is not None:
        transaction.set_memo(params.memo)

    if params.tokenType is not None:
        if params.tokenType == "ft":
            transaction.set_token_type(TokenType.FUNGIBLE_COMMON)
        elif params.tokenType == "nft":
            transaction.set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)

    if params.supplyType is not None:
        if params.supplyType == "infinite":
            transaction.set_supply_type(SupplyType.INFINITE)
        elif params.supplyType == "finite":
            transaction.set_supply_type(SupplyType.FINITE)

    if params.maxSupply is not None:
        transaction.set_max_supply(int(params.maxSupply))

    if params.freezeDefault is not None:
        transaction.set_freeze_default(params.freezeDefault)

    if params.expirationTime is not None:
        transaction.set_expiration_time(Timestamp(seconds=int(params.expirationTime), nanos=0))

    if params.autoRenewAccountId is not None:
        transaction.set_auto_renew_account_id(AccountId.from_string(params.autoRenewAccountId))

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(Duration(seconds=int(params.autoRenewPeriod)))

    if params.metadata is not None:
        transaction.set_metadata(bytes.fromhex(params.metadata) if params.metadata else b"")

    return transaction


@rpc_method("createToken")
def create_token(params: CreateTokenParams) -> CreateTokenResponse:
    """Create a token using TCK createToken parameters."""
    client = get_client(params.sessionId)

    transaction = _build_create_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    token_id = str(receipt.token_id) if receipt.token_id else ""

    return CreateTokenResponse(
        tokenId=token_id,
        status=ResponseCode(receipt.status).name,
    )


def _build_mint_token_transaction(params: MintTokenParams) -> TokenMintTransaction:
    """Build a TokenMintTransaction from TCK params."""
    transaction = TokenMintTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    if params.amount is not None:
        transaction.set_amount(int(params.amount))

    if params.metadata is not None:
        # metadata is a list of hex-encoded strings
        metadata_bytes = [bytes.fromhex(m) for m in params.metadata]
        transaction.set_metadata(metadata_bytes)

    return transaction


@rpc_method("mintToken")
def mint_token(params: MintTokenParams) -> MintTokenResponse:
    """Mint tokens using TCK mintToken parameters."""
    client = get_client(params.sessionId)

    transaction = _build_mint_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    serial_numbers = [str(s) for s in receipt.serial_numbers] if receipt.serial_numbers else []

    return MintTokenResponse(
        newTotalSupply=str(receipt._receipt_proto.newTotalSupply),
        serialNumbers=serial_numbers,
        status=ResponseCode(receipt.status).name,
    )


def _build_associate_token_transaction(params: AssociateTokenParams) -> TokenAssociateTransaction:
    """Build a TokenAssociateTransaction from TCK params."""
    transaction = TokenAssociateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.accountId is not None:
        transaction.set_account_id(AccountId.from_string(params.accountId))

    if params.tokenIds is not None:
        token_ids = [TokenId.from_string(tid) for tid in params.tokenIds]
        transaction.set_token_ids(token_ids)

    return transaction


@rpc_method("associateToken")
def associate_token(params: AssociateTokenParams) -> AssociateTokenResponse:
    """Associate tokens with an account using TCK associateToken parameters."""
    client = get_client(params.sessionId)

    transaction = _build_associate_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return AssociateTokenResponse(status=ResponseCode(receipt.status).name)


@rpc_method("deleteToken")
def delete_token(params: DeleteTokenParams) -> DeleteTokenResponse:
    """Delete a token using TCK deleteToken parameters."""
    client = get_client(params.sessionId)

    transaction = TokenDeleteTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return DeleteTokenResponse(status=ResponseCode(receipt.status).name)


@rpc_method("freezeToken")
def freeze_token(params: FreezeTokenParams) -> FreezeTokenResponse:
    """Freeze a token for an account using TCK freezeToken parameters."""
    client = get_client(params.sessionId)

    transaction = TokenFreezeTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    if params.accountId is not None:
        transaction.set_account_id(AccountId.from_string(params.accountId))

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return FreezeTokenResponse(status=ResponseCode(receipt.status).name)


@rpc_method("pauseToken")
def pause_token(params: PauseTokenParams) -> PauseTokenResponse:
    """Pause a token using TCK pauseToken parameters."""
    client = get_client(params.sessionId)

    transaction = TokenPauseTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return PauseTokenResponse(status=ResponseCode(receipt.status).name)
