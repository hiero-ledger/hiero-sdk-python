"""TCK RPC handlers for token-related endpoints."""

from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_airdrop_claim import TokenClaimAirdropTransaction
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_info import TokenInfo
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.custom_fee import CustomFeeParams, FixedFeeParams
from tck.param.token import (
    AirdropTokenParams,
    AssociateTokenParams,
    ClaimTokenParams,
    CreateTokenParams,
    DeleteTokenParams,
    FreezeTokenParams,
    GetTokenInfoParams,
    GrantTokenKycParams,
    MintTokenParams,
    PauseTokenParams,
    RejectTokenParams,
    RevokeTokenKycParams,
)
from tck.response.token import (
    AirdropTokenResponse,
    AssociateTokenResponse,
    ClaimTokenResponse,
    CreateTokenResponse,
    CustomFeeResponse,
    DeleteTokenResponse,
    FreezeTokenResponse,
    GetTokenInfoResponse,
    GrantTokenKycResponse,
    MintTokenResponse,
    PauseTokenResponse,
    RejectTokenResponse,
    RevokeTokenKycResponse,
)
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string
from tck.util.param_utils import to_int


def _parse_hex(value: str, field_name: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a hex-encoded string, got {value!r}") from exc


def _build_fixed_fee(params: FixedFeeParams) -> CustomFixedFee:
    fee = CustomFixedFee(amount=to_int(params.amount))
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
            numerator=to_int(params.fractionalFee.numerator),
            denominator=to_int(params.fractionalFee.denominator),
            min_amount=to_int(params.fractionalFee.minimumAmount),
            max_amount=to_int(params.fractionalFee.maximumAmount),
            assessment_method=assessment_method,
        )
    elif params.royaltyFee is not None:
        fallback_fee = _build_fixed_fee(params.royaltyFee.fallbackFee) if params.royaltyFee.fallbackFee else None
        fee = CustomRoyaltyFee(
            numerator=to_int(params.royaltyFee.numerator),
            denominator=to_int(params.royaltyFee.denominator),
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
        transaction.set_initial_supply(to_int(params.initialSupply))

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
        transaction.set_max_supply(to_int(params.maxSupply))

    if params.freezeDefault is not None:
        transaction.set_freeze_default(params.freezeDefault)

    if params.expirationTime is not None:
        transaction.set_expiration_time(Timestamp(seconds=to_int(params.expirationTime), nanos=0))

    if params.autoRenewAccountId is not None:
        transaction.set_auto_renew_account_id(AccountId.from_string(params.autoRenewAccountId))

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(Duration(seconds=to_int(params.autoRenewPeriod)))

    if params.metadata is not None:
        transaction.set_metadata(params.metadata.encode())

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
        transaction.set_amount(to_int(params.amount))

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


def _build_grant_token_kyc_transaction(params: GrantTokenKycParams) -> TokenGrantKycTransaction:
    """Build a TokenGrantKycTransaction from TCK params."""
    transaction = TokenGrantKycTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)
    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    if params.accountId is not None:
        transaction.set_account_id(AccountId.from_string(params.accountId))
    return transaction


def _build_revoke_token_kyc_transaction(params: RevokeTokenKycParams) -> TokenRevokeKycTransaction:
    """Build a TokenRevokeKycTransaction from TCK params."""
    transaction = TokenRevokeKycTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)
    if params.tokenId is not None:
        transaction.set_token_id(TokenId.from_string(params.tokenId))

    if params.accountId is not None:
        transaction.set_account_id(AccountId.from_string(params.accountId))
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


@rpc_method("grantTokenKyc")
def grant_token_kyc(params: GrantTokenKycParams) -> GrantTokenKycResponse:
    """Grant KYC to an account for a token using TCK grantTokenKyc parameters."""
    client = get_client(params.sessionId)

    transaction = _build_grant_token_kyc_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return GrantTokenKycResponse(status=ResponseCode(receipt.status).name)


@rpc_method("revokeTokenKyc")
def revoke_token_kyc(params: RevokeTokenKycParams) -> RevokeTokenKycResponse:
    """Revoke KYC from an account for a token using TCK revokeTokenKyc parameters."""
    client = get_client(params.sessionId)

    transaction = _build_revoke_token_kyc_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return RevokeTokenKycResponse(status=ResponseCode(receipt.status).name)


def _build_airdrop_token_transaction(params: AirdropTokenParams) -> TokenAirdropTransaction:
    """Build a TokenAirdropTransaction from TCK params."""
    tx = TokenAirdropTransaction()
    tx.set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenTransfers is None:
        return tx

    for entry in params.tokenTransfers:
        ## Token Transfer
        if entry.token is not None:
            token = entry.token

            token_id = TokenId.from_string(token.tokenId)
            account = AccountId.from_string(token.accountId)

            if token.decimals is not None:
                decimals = int(token.decimals)

                if entry.approved:
                    tx.add_approved_token_transfer_with_decimals(token_id, account, int(token.amount), decimals)
                else:
                    tx.add_token_transfer_with_decimals(token_id, account, int(token.amount), decimals)
            else:
                if entry.approved:
                    tx.add_approved_token_transfer(token_id, account, int(token.amount))
                else:
                    tx.add_token_transfer(token_id, account, int(token.amount))

        ## NFT Transfer
        elif entry.nft is not None:
            nft = entry.nft

            nft_id = NftId(TokenId.from_string(nft.tokenId), int(nft.serialNumber))

            sender = AccountId.from_string(nft.senderAccountId)
            receiver = AccountId.from_string(nft.receiverAccountId)

            if entry.approved:
                tx.add_approved_nft_transfer(nft_id, sender, receiver)
            else:
                tx.add_nft_transfer(nft_id, sender, receiver)

    return tx


@rpc_method("airdropToken")
def airdrop_token(params: AirdropTokenParams) -> AirdropTokenResponse:
    """Airdrop tokens using TCK airdropToken parameters."""
    client = get_client(params.sessionId)

    tx = _build_airdrop_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(tx, client)

    receipt = tx.execute(client, wait_for_receipt=False).get_receipt(
        client,
        validate_status=True,
    )

    return AirdropTokenResponse(status=ResponseCode(receipt.status).name)


def _build_claim_token_transaction(params: ClaimTokenParams) -> TokenClaimAirdropTransaction:
    """Build a TokenClaimAirdropTransaction from TCK params."""
    transaction = TokenClaimAirdropTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    sender_id = AccountId.from_string(params.senderAccountId)
    receiver_id = AccountId.from_string(params.receiverAccountId)
    token_id = TokenId.from_string(params.tokenId)

    if params.serialNumbers:
        for serial_number in params.serialNumbers:
            transaction.add_pending_airdrop_id(
                PendingAirdropId(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    nft_id=NftId(token_id=token_id, serial_number=int(serial_number)),
                )
            )
    else:
        transaction.add_pending_airdrop_id(
            PendingAirdropId(
                sender_id=sender_id,
                receiver_id=receiver_id,
                token_id=token_id,
            )
        )

    return transaction


@rpc_method("claimToken")
def claim_token(params: ClaimTokenParams) -> ClaimTokenResponse:
    """Claim pending token airdrops using TCK claimToken parameters."""
    client = get_client(params.sessionId)

    transaction = _build_claim_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return ClaimTokenResponse(status=ResponseCode(receipt.status).name)


def _serialize_key(key) -> str | None:
    """Serialize a key to its DER-encoded hex string representation."""
    if key is None:
        return ""
    return key.to_string_der()


def _serialize_custom_fee(fee: CustomFee) -> CustomFeeResponse:
    """Serialize a CustomFee to a CustomFeeResponse."""
    response = CustomFeeResponse()

    if fee.fee_collector_account_id is not None:
        aid = fee.fee_collector_account_id
        response.feeCollectorAccountId = {
            "realm": str(aid.realm),
            "shard": str(aid.shard),
            "num": str(aid.num),
        }
    response.feeCollectorsExempt = fee.all_collectors_are_exempt

    if isinstance(fee, CustomFixedFee):
        fixed_fee_dict: dict = {"amount": str(fee.amount)}
        if fee.denominating_token_id is not None:
            fixed_fee_dict["denominatingTokenId"] = str(fee.denominating_token_id)
        response.fixedFee = fixed_fee_dict
    elif isinstance(fee, CustomFractionalFee):
        response.fractionalFee = {
            "numerator": str(fee.numerator),
            "denominator": str(fee.denominator),
            "minimumAmount": str(fee.min_amount),
            "maximumAmount": str(fee.max_amount),
            "assessmentMethod": "inclusive" if fee.assessment_method == FeeAssessmentMethod.INCLUSIVE else "exclusive",
        }
    elif isinstance(fee, CustomRoyaltyFee):
        royalty_fee_dict: dict = {
            "numerator": str(fee.numerator),
            "denominator": str(fee.denominator),
        }
        if fee.fallback_fee is not None:
            fallback: dict = {"amount": str(fee.fallback_fee.amount)}
            if fee.fallback_fee.denominating_token_id is not None:
                fallback["denominatingTokenId"] = str(fee.fallback_fee.denominating_token_id)
            royalty_fee_dict["fallbackFee"] = fallback
        response.royaltyFee = royalty_fee_dict

    return response


def _map_pause_status(pause_status: TokenPauseStatus) -> bool | None:
    """Map TokenPauseStatus enum to TCK boolean representation."""
    if pause_status == TokenPauseStatus.PAUSED:
        return True
    if pause_status == TokenPauseStatus.UNPAUSED:
        return False
    return None


def _map_token_type(token_type: TokenType | None) -> str | None:
    """Map TokenType enum to TCK string representation."""
    if token_type is None:
        return None
    mapping = {
        TokenType.FUNGIBLE_COMMON: "FUNGIBLE_COMMON",
        TokenType.NON_FUNGIBLE_UNIQUE: "NON_FUNGIBLE_UNIQUE",
    }
    return mapping.get(token_type)


def _map_supply_type(supply_type: SupplyType | None) -> str | None:
    """Map SupplyType enum to TCK string representation."""
    if supply_type is None:
        return None
    mapping = {
        SupplyType.INFINITE: "INFINITE",
        SupplyType.FINITE: "FINITE",
    }
    return mapping.get(supply_type)


def _map_freeze_status(freeze_status: TokenFreezeStatus) -> bool | None:
    """Map TokenFreezeStatus enum to TCK boolean representation."""
    if freeze_status == TokenFreezeStatus.FROZEN:
        return True
    if freeze_status == TokenFreezeStatus.UNFROZEN:
        return False
    return None


def _map_kyc_status(kyc_status: TokenKycStatus) -> bool | None:
    """Map TokenKycStatus enum to TCK boolean representation."""
    if kyc_status == TokenKycStatus.GRANTED:
        return True
    if kyc_status == TokenKycStatus.REVOKED:
        return False
    return None


def _build_token_info_response(info: TokenInfo) -> GetTokenInfoResponse:
    """Build a GetTokenInfoResponse from a TokenInfo object."""
    # Serialize custom fees
    custom_fees = [_serialize_custom_fee(fee) for fee in info.custom_fees] if info.custom_fees else []

    return GetTokenInfoResponse(
        tokenId=str(info.token_id) if info.token_id else None,
        name=info.name or "",
        symbol=info.symbol or "",
        decimals=info.decimals,
        totalSupply=str(info.total_supply) if info.total_supply is not None else "0",
        treasuryAccountId=str(info.treasury) if info.treasury else None,
        adminKey=_serialize_key(info.admin_key),
        kycKey=_serialize_key(info.kyc_key),
        freezeKey=_serialize_key(info.freeze_key),
        pauseKey=_serialize_key(info.pause_key),
        wipeKey=_serialize_key(info.wipe_key),
        supplyKey=_serialize_key(info.supply_key),
        feeScheduleKey=_serialize_key(info.fee_schedule_key),
        metadataKey=_serialize_key(info.metadata_key),
        defaultFreezeStatus=_map_freeze_status(info.default_freeze_status),
        defaultKycStatus=_map_kyc_status(info.default_kyc_status),
        pauseStatus=_map_pause_status(info.pause_status),
        isDeleted=info.is_deleted,
        autoRenewAccountId=str(info.auto_renew_account) if info.auto_renew_account else None,
        autoRenewPeriod=str(info.auto_renew_period.seconds) if info.auto_renew_period else None,
        expirationTime=str(info.expiry.seconds) if info.expiry else None,
        tokenMemo=info.memo if info.memo is not None else "",
        customFees=custom_fees,
        tokenType=_map_token_type(info.token_type),
        supplyType=_map_supply_type(info.supply_type),
        maxSupply=str(info.max_supply) if info.max_supply is not None else "0",
        metadata=info.metadata.hex() if info.metadata else "",
        ledgerId=info.ledger_id.hex() if info.ledger_id else "",
    )


@rpc_method("getTokenInfo")
def get_token_info(params: GetTokenInfoParams) -> GetTokenInfoResponse:
    """Query token info using TCK getTokenInfo parameters."""
    client = get_client(params.sessionId)

    query = TokenInfoQuery().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.tokenId is not None:
        query.set_token_id(TokenId.from_string(params.tokenId))

    if params.queryPayment is not None:
        query.set_query_payment(Hbar.from_tinybars(int(params.queryPayment)))

    if params.maxQueryPayment is not None:
        query.set_max_query_payment(Hbar.from_tinybars(int(params.maxQueryPayment)))

    info = query.execute(client)
    return _build_token_info_response(info)


def _build_reject_token_transaction(
    params: RejectTokenParams,
) -> TokenRejectTransaction:
    transaction = TokenRejectTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.ownerId is not None:
        transaction.set_owner_id(AccountId.from_string(params.ownerId))

    if params.serialNumbers is not None and params.tokenIds is not None:
        nft_ids = []

        for token_id in params.tokenIds:
            nft_ids.extend(
                NftId(TokenId.from_string(token_id), int(serial_number)) for serial_number in params.serialNumbers
            )

        transaction.set_nft_ids(nft_ids)

    elif params.tokenIds is not None:
        transaction.set_token_ids([TokenId.from_string(token) for token in params.tokenIds])

    return transaction


@rpc_method("rejectToken")
def reject_token(params: RejectTokenParams) -> RejectTokenResponse:
    client = get_client(params.sessionId)

    transaction = _build_reject_token_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt = response.get_receipt(client, validate_status=True)

    return RejectTokenResponse(
        status=ResponseCode(receipt.status).name,
    )
