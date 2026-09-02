from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_create_transaction import ScheduleCreateTransaction
from hiero_sdk_python.schedule.schedule_delete_transaction import ScheduleDeleteTransaction
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.errors import JsonRpcError
from tck.handlers.account import _build_create_account_transaction
from tck.handlers.allowance import _build_approve_allowance_transaction
from tck.handlers.registry import rpc_method
from tck.handlers.token import _build_burn_token_transaction, _build_mint_token_transaction
from tck.handlers.topic import _build_create_topic_transaction, _build_topic_message_submit_transaction
from tck.handlers.transfer import _build_transfer_transaction
from tck.param.account import CreateAccountParams
from tck.param.allowance import ApproveAllowanceParams
from tck.param.base import BaseTransactionParams
from tck.param.common import CommonTransactionParams
from tck.param.schedule import CreateScheduleParams, DeleteScheduleParams, ScheduledTransactionParams
from tck.param.token import BurnTokenParams, MintTokenParams
from tck.param.topic import CreateTopicParams, TopicMessageSubmitParams
from tck.param.transfer import TransferCryptoParams
from tck.response.schedule import CreateScheduleResponse, DeleteScheduleResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string
from tck.util.param_utils import to_int


# Maps a scheduled transaction method name to its params class and builder.
# "submitMessage" is the name used by the TCK inside scheduledTransaction, while
# "submitTopicMessage" is the top-level JSON-RPC method name; both are accepted.
_SCHEDULABLE: dict[str, tuple[type[BaseTransactionParams], Callable[[Any], Transaction]]] = {
    "createAccount": (CreateAccountParams, _build_create_account_transaction),
    "transferCrypto": (TransferCryptoParams, _build_transfer_transaction),
    "submitMessage": (TopicMessageSubmitParams, _build_topic_message_submit_transaction),
    "submitTopicMessage": (TopicMessageSubmitParams, _build_topic_message_submit_transaction),
    "burnToken": (BurnTokenParams, _build_burn_token_transaction),
    "mintToken": (MintTokenParams, _build_mint_token_transaction),
    "approveAllowance": (ApproveAllowanceParams, _build_approve_allowance_transaction),
    "createTopic": (CreateTopicParams, _build_create_topic_transaction),
}


def _apply_schedulable_common_params(transaction: Transaction, common: CommonTransactionParams | None) -> None:
    """Apply the common params that survive into a SchedulableTransactionBody.

    A SchedulableTransactionBody carries only transactionFee and memo, so the rest of
    apply_common_params() would be silently discarded: transactionId and
    validTransactionDuration are not part of the body, and signers would freeze and sign a
    transaction that is never submitted. Schedule signers belong on the outer
    ScheduleCreateTransaction, which create_schedule() already handles.
    """
    if common is None:
        return

    if common.maxTransactionFee is not None:
        transaction.transaction_fee = int(common.maxTransactionFee)

    if common.memo is not None:
        transaction.set_transaction_memo(common.memo)


def _build_scheduled_transaction(params: ScheduledTransactionParams, session_id: str) -> Transaction:
    """Build the inner transaction that a schedule wraps."""
    schedulable = _SCHEDULABLE.get(params.method)
    if schedulable is None:
        raise JsonRpcError.invalid_params_error(f"Unsupported scheduled transaction method: {params.method}")

    params_class, build_transaction = schedulable

    # The inner params object carries no sessionId of its own, so inherit the outer one.
    inner_json = dict(params.params)
    inner_json["sessionId"] = session_id

    try:
        inner_params = cast(BaseTransactionParams, params_class.parse_json_params(inner_json))
    except (TypeError, ValueError) as e:
        raise JsonRpcError.invalid_params_error(str(e)) from e

    transaction = build_transaction(inner_params)
    _apply_schedulable_common_params(transaction, inner_params.commonTransactionParams)

    return transaction


def _build_create_schedule_transaction(params: CreateScheduleParams) -> ScheduleCreateTransaction:
    """Build a ScheduleCreateTransaction from TCK params."""
    transaction = ScheduleCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.scheduledTransaction is not None:
        transaction.set_scheduled_transaction(
            _build_scheduled_transaction(params.scheduledTransaction, params.sessionId)
        )

    if params.memo is not None:
        transaction.set_schedule_memo(params.memo)

    if params.adminKey is not None:
        transaction.set_admin_key(get_key_from_string(params.adminKey))

    if params.payerAccountId is not None:
        # Passed through unchecked so an empty string surfaces as an SDK error.
        transaction.set_payer_account_id(AccountId.from_string(params.payerAccountId))

    if params.expirationTime is not None:
        transaction.set_expiration_time(Timestamp(seconds=to_int(params.expirationTime), nanos=0))

    if params.waitForExpiry is not None:
        transaction.set_wait_for_expiry(params.waitForExpiry)

    return transaction


def _build_delete_schedule_transaction(params: DeleteScheduleParams) -> ScheduleDeleteTransaction:
    """Builds a ScheduleDeleteTransaction from the provided parameters."""
    transaction = ScheduleDeleteTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.scheduleId is not None:
        transaction.set_schedule_id(ScheduleId.from_string(params.scheduleId))

    return transaction


@rpc_method("createSchedule")
def create_schedule(params: CreateScheduleParams) -> CreateScheduleResponse:
    """Create a schedule."""
    client = get_client(params.sessionId)

    transaction = _build_create_schedule_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    schedule_id = ""
    scheduled_transaction_id = None
    if receipt.status == ResponseCode.SUCCESS:
        if receipt.schedule_id is not None:
            schedule_id = str(receipt.schedule_id)
        if receipt.scheduled_transaction_id is not None:
            scheduled_transaction_id = str(receipt.scheduled_transaction_id)

    return CreateScheduleResponse(schedule_id, scheduled_transaction_id, ResponseCode(receipt.status).name)


@rpc_method("deleteSchedule")
def delete_schedule(params: DeleteScheduleParams) -> DeleteScheduleResponse:
    """Handles the deleteSchedule JSON-RPC request."""

    client = get_client(params.sessionId)
    transaction = _build_delete_schedule_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt = response.get_receipt(client, validate_status=True)

    return DeleteScheduleResponse(status=ResponseCode(receipt.status).name)
