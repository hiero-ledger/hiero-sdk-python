from __future__ import annotations

from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.file import CreateFileParams
from tck.response.file import CreateFileResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string


def _build_create_file_transaction(params: CreateFileParams) -> FileCreateTransaction:
    transaction = FileCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.keys is not None:
        transaction.set_keys([get_key_from_string(key) for key in params.keys])

    if params.contents is not None:
        transaction.set_contents(params.contents)

    if params.expirationTime is not None:
        transaction.set_expiration_time(Timestamp(seconds=params.expirationTime, nanos=0))

    if params.memo is not None:
        transaction.set_file_memo(params.memo)

    return transaction


@rpc_method("createFile")
def create_file(params: CreateFileParams) -> CreateFileResponse:
    """Create a file."""
    client = get_client(params.sessionId)

    transaction = _build_create_file_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=False)

    file_id = ""
    if receipt.status == ResponseCode.SUCCESS and receipt.file_id is not None:
        file_id = str(receipt.file_id)

    return CreateFileResponse(file_id, ResponseCode(receipt.status).name)
