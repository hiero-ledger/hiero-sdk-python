from __future__ import annotations

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.hbar import Hbar
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


def _build_account_info_response(info) -> GetAccountInfoResponse:
    staking_info_response = None
    if info.staking_info:
        staking_info_response = StakingInfoResponse(
            declineStakingReward=info.staking_info.decline_staking_reward,
            stakePeriodStart=str(info.staking_info.stake_period_start)
            if info.staking_info.stake_period_start
            else None,
            pendingReward=str(info.staking_info.pending_reward.to_tinybars())
            if info.staking_info.pending_reward
            else None,
            stakedToMe=str(info.staking_info.staked_to_me.to_tinybars()) if info.staking_info.staked_to_me else None,
            stakedAccountId=str(info.staking_info.staked_account_id) if info.staking_info.staked_account_id else None,
            stakedNodeId=str(info.staking_info.staked_node_id) if info.staking_info.staked_node_id else None,
        )

    token_relationships_response = []
    if info.token_relationships:
        for rel in info.token_relationships:
            token_relationships_response.append(
                TokenRelationshipResponse(
                    tokenId=str(rel.token_id) if rel.token_id else None,
                    symbol=rel.symbol,
                    balance=str(rel.balance) if rel.balance is not None else None,
                    kycStatus=str(rel.kyc_status) if rel.kyc_status is not None else None,
                    freezeStatus=str(rel.freeze_status) if rel.freeze_status is not None else None,
                    decimals=str(rel.decimals) if rel.decimals is not None else None,
                    automaticAssociation=rel.automatic_association,
                )
            )

    return GetAccountInfoResponse(
        accountId=str(info.account_id) if info.account_id else None,
        contractAccountId=info.contract_account_id,
        isDeleted=info.is_deleted,
        proxyReceived=str(info.proxy_received.to_tinybars()) if info.proxy_received else None,
        key=info.key.to_bytes().hex() if info.key else None,
        balance=str(info.balance.to_tinybars()) if info.balance else None,
        isReceiverSignatureRequired=info.receiver_signature_required,
        expirationTime=str(info.expiration_time) if info.expiration_time else None,
        autoRenewPeriod=str(info.auto_renew_period.seconds) if info.auto_renew_period else None,
        tokenRelationships=token_relationships_response if token_relationships_response else None,
        accountMemo=info.account_memo,
        ownedNfts=str(info.owned_nfts) if info.owned_nfts is not None else None,
        maxAutomaticTokenAssociations=str(info.max_automatic_token_associations)
        if info.max_automatic_token_associations is not None
        else None,
        stakingInfo=staking_info_response,
    )


@rpc_method("getAccountInfo")
def get_account_info(params: GetAccountInfoParams) -> GetAccountInfoResponse:
    client = get_client(params.sessionId)

    query = AccountInfoQuery()
    if params.accountId:
        query.set_account_id(AccountId.from_string(params.accountId))

    info = query.execute(client)
    return _build_account_info_response(info)
