from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.topic import CreateTopicCustomFeeParams, CreateTopicParams
from tck.response.topic import CreateTopicResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string


def _build_custom_fee(custom_fee_params: CreateTopicCustomFeeParams) -> CustomFixedFee:
    custom_fee = CustomFixedFee()

    if custom_fee_params.feeCollectorAccountId == "":
        # Keep TCK behavior: explicitly empty collector should surface as internal error.
        raise ValueError("feeCollectorAccountId cannot be empty")

    if custom_fee_params.feeCollectorAccountId is not None:
        custom_fee.set_fee_collector_account_id(AccountId.from_string(custom_fee_params.feeCollectorAccountId))

    if custom_fee_params.feeCollectorsExempt:
        custom_fee.set_all_collectors_are_exempt(custom_fee_params.feeCollectorsExempt)

    if custom_fee_params.fixedFee is not None:
        if custom_fee_params.fixedFee.amount is not None:
            custom_fee.amount = custom_fee_params.fixedFee.amount

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

    if params.autoRenewAccountId is None and client is not None and client.operator_account_id is not None:
        transaction.set_auto_renew_account(client.operator_account_id)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    topic_id = ""
    if receipt.status == ResponseCode.SUCCESS and receipt.topic_id is not None:
        topic_id = str(receipt.topic_id)

    return CreateTopicResponse(topic_id, ResponseCode(receipt.status).name)
