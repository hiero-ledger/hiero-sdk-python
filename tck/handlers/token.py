"""TCK RPC handlers for token-related endpoints."""

from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
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
    CustomFeeParams,
    DeleteTokenParams,
    FixedFeeParams,
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


def _parse_required_int(value: str | None, field_name: str) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer string, got {value!r}") from exc


def _parse_hex(value: str, field_name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a hex-encoded string, got {value!r}") from exc


def _build_fixed_fee(params: FixedFeeParams) -> CustomFixedFee:
    fee = CustomFixedFee(amount=_parse_required_int(params.amount, "fixedFee.amount"))
    if params.denominatingTokenId is not None:
        fee.set_denominating_token_id(TokenId.from_string(params.denominatingTokenId))
    return fee


def _apply_custom_fee_common_fields(fee: CustomFee, params: CustomFeeParams) -> CustomFee:
    if params.feeCollectorAccountId == "":
        raise ValueError("feeCollectorAccountId cannot be empty")
    if params.feeCollectorAccountId is not None:
        fee.set_fee_collector_account_id(AccountId.from_string(params.feeCollectorAccountId))
    if params.feeCollectorsExempt is not None:
        fee.set_all_collectors_are_exempt(params.feeCollectorsExempt)
    return fee


def _build_custom_fee(params: CustomFeeParams) -> CustomFee:
    if params.fixedFee is not None:
        fee: CustomFee = _build_fixed_fee(params.fixedFee)
    elif params.fractionalFee is not None:
        assessment_methods = {
            "inclusive": FeeAssessmentMethod.INCLUSIVE,
            "exclusive": FeeAssessmentMethod.EXCLUSIVE,
        }
        try:
            assessment_method = assessment_methods[params.fractionalFee.assessmentMethod]
        except KeyError as exc:
            raise ValueError(
                "fractionalFee.assessmentMethod must be inclusive or exclusive, "
                f"got {params.fractionalFee.assessmentMethod!r}"
            ) from exc

        fee = CustomFractionalFee(
            numerator=_parse_required_int(params.fractionalFee.numerator, "fractionalFee.numerator"),
            denominator=_parse_required_int(params.fractionalFee.denominator, "fractionalFee.denominator"),
            min_amount=_parse_required_int(params.fractionalFee.minimumAmount, "fractionalFee.minimumAmount"),
            max_amount=_parse_required_int(params.fractionalFee.maximumAmount, "fractionalFee.maximumAmount"),
            assessment_method=assessment_method,
        )
    elif params.royaltyFee is not None:
        fallback_fee = _build_fixed_fee(params.royaltyFee.fallbackFee) if params.royaltyFee.fallbackFee else None
        fee = CustomRoyaltyFee(
            numerator=_parse_required_int(params.royaltyFee.numerator, "royaltyFee.numerator"),
            denominator=_parse_required_int(params.royaltyFee.denominator, "royaltyFee.denominator"),
            fallback_fee=fallback_fee,
        )
    else:
        raise ValueError("custom fee requires a fee type")

    return _apply_custom_fee_common_fields(fee, params)


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
        transaction.set_initial_supply(_parse_required_int(params.initialSupply, "initialSupply"))

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
        else:
            raise ValueError("tokenType must be ft or nft")

    if params.supplyType is not None:
        if params.supplyType == "infinite":
            transaction.set_supply_type(SupplyType.INFINITE)
        elif params.supplyType == "finite":
            transaction.set_supply_type(SupplyType.FINITE)
        else:
            raise ValueError("supplyType must be infinite or finite")

    if params.maxSupply is not None:
        transaction.set_max_supply(_parse_required_int(params.maxSupply, "maxSupply"))

    if params.freezeDefault is not None:
        transaction.set_freeze_default(params.freezeDefault)

    if params.expirationTime is not None:
        transaction.set_expiration_time(
            Timestamp(seconds=_parse_required_int(params.expirationTime, "expirationTime"), nanos=0)
        )

    if params.autoRenewAccountId is not None:
        transaction.set_auto_renew_account_id(AccountId.from_string(params.autoRenewAccountId))

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(
            Duration(seconds=_parse_required_int(params.autoRenewPeriod, "autoRenewPeriod"))
        )

    if params.metadata is not None:
        transaction.set_metadata(_parse_hex(params.metadata, "metadata"))

    if params.customFees is not None:
        transaction.set_custom_fees([_build_custom_fee(custom_fee) for custom_fee in params.customFees])

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
        transaction.set_amount(_parse_required_int(params.amount, "amount"))

    if params.metadata is not None:
        # metadata is a list of hex-encoded strings
        metadata_bytes = [_parse_hex(metadata, f"metadata[{index}]") for index, metadata in enumerate(params.metadata)]
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
        newTotalSupply=str(receipt.new_total_supply),
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


def _build_delete_token_transaction(params: DeleteTokenParams) -> TokenDeleteTransaction:
    """Build a TokenDeleteTransaction from TCK params."""
    transaction = TokenDeleteTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    return transaction


def _build_freeze_token_transaction(params: FreezeTokenParams) -> TokenFreezeTransaction:
    """Build a TokenFreezeTransaction from TCK params."""
    transaction = TokenFreezeTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    if params.accountId is not None:
        transaction.set_account_id(AccountId.from_string(params.accountId))

    return transaction


def _build_pause_token_transaction(params: PauseTokenParams) -> TokenPauseTransaction:
    """Build a TokenPauseTransaction from TCK params."""
    transaction = TokenPauseTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

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

    transaction = _build_delete_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return DeleteTokenResponse(status=ResponseCode(receipt.status).name)


@rpc_method("freezeToken")
def freeze_token(params: FreezeTokenParams) -> FreezeTokenResponse:
    """Freeze a token for an account using TCK freezeToken parameters."""
    client = get_client(params.sessionId)

    transaction = _build_freeze_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return FreezeTokenResponse(status=ResponseCode(receipt.status).name)


@rpc_method("pauseToken")
def pause_token(params: PauseTokenParams) -> PauseTokenResponse:
    """Pause a token using TCK pauseToken parameters."""
    client = get_client(params.sessionId)

    transaction = _build_pause_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return PauseTokenResponse(status=ResponseCode(receipt.status).name)
