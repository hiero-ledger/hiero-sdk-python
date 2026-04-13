"""TCK RPC handlers for account-related endpoints."""

from __future__ import annotations

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_info import AccountInfo
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.account import CreateAccountParams, GetAccountInfoParams
from tck.response.account import (
    CreateAccountResponse,
    GetAccountInfoResponse,
    StakingInfoResponse,
    TokenRelationshipResponse,
)
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string


def _build_create_account_transaction(params: CreateAccountParams) -> AccountCreateTransaction:
    transaction = AccountCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.key is not None:
        transaction.set_key_without_alias(get_key_from_string(params.key))

    if params.initialBalance is not None:
        transaction.set_initial_balance(Hbar.from_tinybars(params.initialBalance))

    if params.receiverSignatureRequired is not None:
        transaction.set_receiver_signature_required(params.receiverSignatureRequired)

    if params.maxAutoTokenAssociations is not None:
        transaction.set_max_automatic_token_associations(params.maxAutoTokenAssociations)

    if params.stakedAccountId is not None:
        transaction.set_staked_account_id(AccountId.from_string(params.stakedAccountId))

    if params.stakedNodeId is not None:
        transaction.set_staked_node_id(params.stakedNodeId)

    if params.declineStakingReward is not None:
        transaction.set_decline_staking_reward(params.declineStakingReward)

    if params.memo is not None:
        transaction.set_account_memo(params.memo)

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(params.autoRenewPeriod)

    if params.alias is not None:
        transaction.set_alias(params.alias)

    return transaction


@rpc_method("createAccount")
def create_account(params: CreateAccountParams) -> CreateAccountResponse:
    """Create a new account using TCK createAccount parameters."""
    client = get_client(params.sessionId)

    transaction = _build_create_account_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    account_id = ""
    if receipt.status == ResponseCode.SUCCESS:
        account_id = str(receipt.account_id)

    return CreateAccountResponse(account_id, ResponseCode(receipt.status).name)


def _enum_name(value) -> str | None:
    if value is None:
        return None
    return getattr(value, "name", str(value))


def _serialize_key(key) -> str | None:
    if key is None:
        return None

    to_string_der = getattr(key, "to_string_der", None)
    if callable(to_string_der):
        return to_string_der()

    return key.to_bytes().hex()


def _to_staking_info_response(info: AccountInfo) -> StakingInfoResponse:
    if info.staking_info is None:
        return StakingInfoResponse(
            declineStakingReward=False,
            pendingReward="0",
            stakedToMe="0",
        )

    staking_info = info.staking_info
    return StakingInfoResponse(
        declineStakingReward=staking_info.decline_reward,
        stakePeriodStart=str(staking_info.stake_period_start)
        if staking_info.stake_period_start is not None
        else None,
        pendingReward=str(staking_info.pending_reward.to_tinybars())
        if staking_info.pending_reward is not None
        else "0",
        stakedToMe=str(staking_info.staked_to_me.to_tinybars())
        if staking_info.staked_to_me is not None
        else "0",
        stakedAccountId=str(staking_info.staked_account_id)
        if staking_info.staked_account_id is not None
        else None,
        stakedNodeId=str(staking_info.staked_node_id)
        if staking_info.staked_node_id is not None
        else None,
    )


def _to_token_relationships_response(info: AccountInfo) -> dict[str, TokenRelationshipResponse]:
    token_relationships_response: dict[str, TokenRelationshipResponse] = {}

    for relationship in info.token_relationships:
        token_id = str(relationship.token_id) if relationship.token_id is not None else None
        if token_id is None:
            continue

        token_relationships_response[token_id] = TokenRelationshipResponse(
            tokenId=token_id,
            symbol=relationship.symbol,
            balance=str(relationship.balance) if relationship.balance is not None else "0",
            kycStatus=_enum_name(relationship.kyc_status),
            freezeStatus=_enum_name(relationship.freeze_status),
            decimals=str(relationship.decimals) if relationship.decimals is not None else None,
            automaticAssociation=relationship.automatic_association,
        )

    return token_relationships_response


def _build_account_info_response(info: AccountInfo) -> GetAccountInfoResponse:
    return GetAccountInfoResponse(
        accountId=str(info.account_id) if info.account_id is not None else None,
        contractAccountId=info.contract_account_id or "",
        isDeleted=bool(info.is_deleted),
        proxyAccountId="",
        proxyReceived=str(info.proxy_received.to_tinybars())
        if info.proxy_received is not None
        else "0",
        key=_serialize_key(info.key),
        balance=str(info.balance.to_tinybars()) if info.balance is not None else "0",
        sendRecordThreshold="0",
        receiveRecordThreshold="0",
        isReceiverSignatureRequired=bool(info.receiver_signature_required),
        expirationTime=str(info.expiration_time) if info.expiration_time is not None else None,
        autoRenewPeriod=str(info.auto_renew_period.seconds)
        if info.auto_renew_period is not None
        else "0",
        tokenRelationships=_to_token_relationships_response(info),
        accountMemo=info.account_memo or "",
        ownedNfts=str(info.owned_nfts) if info.owned_nfts is not None else "0",
        maxAutomaticTokenAssociations=str(info.max_automatic_token_associations)
        if info.max_automatic_token_associations is not None
        else "0",
        aliasKey="",
        ledgerId="",
        ethereumNonce="0",
        stakingInfo=_to_staking_info_response(info),
    )


@rpc_method("getAccountInfo")
def get_account_info(params: GetAccountInfoParams) -> GetAccountInfoResponse:
    """Query account info and map SDK fields to the TCK response contract."""
    client = get_client(params.sessionId)

    query = AccountInfoQuery().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)
    if params.accountId is not None:
        query.set_account_id(AccountId.from_string(params.accountId))

    info = query.execute(client)
    return _build_account_info_response(info)
