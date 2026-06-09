from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.custom_fee import CustomFeeLimitParams, CustomFeeParams
from tck.param.topic import CreateTopicParams, TopicMessageSubmitParams
from tck.response.topic import CreateTopicResponse, TopicMessageSubmitResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string


def _build_custom_fee(custom_fee_params: CustomFeeParams) -> CustomFixedFee:
    custom_fee = CustomFixedFee()

    if custom_fee_params.feeCollectorAccountId is not None:
        custom_fee.set_fee_collector_account_id(AccountId.from_string(custom_fee_params.feeCollectorAccountId))

    if custom_fee_params.feeCollectorsExempt:
        custom_fee.set_all_collectors_are_exempt(custom_fee_params.feeCollectorsExempt)

    if custom_fee_params.fixedFee is not None:
        if custom_fee_params.fixedFee.amount is not None:
            custom_fee.amount = int(custom_fee_params.fixedFee.amount)

        if custom_fee_params.fixedFee.denominatingTokenId:
            custom_fee.set_denominating_token_id(TokenId.from_string(custom_fee_params.fixedFee.denominatingTokenId))

    return custom_fee


def _build_create_topic_transaction(params: CreateTopicParams) -> TopicCreateTransaction:
    transaction = TopicCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.memo is not None:
        transaction.set_memo(params.memo)

    if params.adminKey is not None:
        transaction.set_admin_key(get_key_from_string(params.adminKey))

    if params.submitKey is not None:
        transaction.set_submit_key(get_key_from_string(params.submitKey))

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(params.autoRenewPeriod)

    if params.autoRenewAccountId is not None:
        transaction.set_auto_renew_account(AccountId.from_string(params.autoRenewAccountId))

    if params.feeScheduleKey is not None:
        transaction.set_fee_schedule_key(get_key_from_string(params.feeScheduleKey))

    if params.feeExemptKeys is not None:
        transaction.set_fee_exempt_keys([get_key_from_string(key) for key in params.feeExemptKeys])

    if params.customFees is not None:
        transaction.set_custom_fees([_build_custom_fee(custom_fee_params) for custom_fee_params in params.customFees])

    return transaction


@rpc_method("createTopic")
def create_topic(params: CreateTopicParams) -> CreateTopicResponse:
    client = get_client(params.sessionId)

    transaction = _build_create_topic_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    topic_id = ""
    if receipt.status == ResponseCode.SUCCESS and receipt.topic_id is not None:
        topic_id = str(receipt.topic_id)

    return CreateTopicResponse(topic_id, ResponseCode(receipt.status).name)


def _build_custom_fee_limit(params: CustomFeeLimitParams) -> CustomFeeLimit:
    """Build custom fee limit from params."""
    custom_fee_limit = CustomFeeLimit()

    if params.payerId is not None:
        custom_fee_limit.set_payer_id(AccountId.from_string(params.payerId))
    if params.fixedFees is not None:
        fixed_fees = []
        for fee in params.fixedFees:
            fixed_fee = CustomFixedFee()
            if fee.amount is not None:
                fixed_fee.set_amount_in_tinybars(int(fee.amount))

            if fee.denominatingTokenId is not None:
                fixed_fee.set_denominating_token_id(TokenId.from_string(fee.denominatingTokenId))

            fixed_fees.append(fixed_fee)

        custom_fee_limit.set_custom_fees(fixed_fees)
    return custom_fee_limit


def _build_topic_message_submit_transaction(params: TopicMessageSubmitParams) -> TopicMessageSubmitTransaction:
    """Build topic message submit transaction from params."""

    transaction = TopicMessageSubmitTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.topicId is not None:
        transaction.set_topic_id(TopicId.from_string(params.topicId))

    if params.message is not None:
        transaction.set_message(params.message)

    if params.maxChunks is not None:
        transaction.set_max_chunks(params.maxChunks)

    if params.chunkSize is not None:
        transaction.set_chunk_size(params.chunkSize)

    if params.customFeeLimits is not None:
        custom_fee_limits = [_build_custom_fee_limit(fee) for fee in params.customFeeLimits]

        transaction.set_custom_fee_limits(custom_fee_limits)

    return transaction


@rpc_method("submitTopicMessage")
def submit_topic_message(params: TopicMessageSubmitParams) -> TopicMessageSubmitResponse:
    """Submit message to a topic."""

    client = get_client(params.sessionId)

    transaction = _build_topic_message_submit_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return TopicMessageSubmitResponse(ResponseCode(receipt.status).name)
