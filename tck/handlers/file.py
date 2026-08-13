from __future__ import annotations

from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.errors import JsonRpcError
from tck.handlers.registry import rpc_method
from tck.param.file import CreateFileParams, DeleteFileParams
from tck.response.file import CreateFileResponse, DeleteFileResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string
from tck.util.param_utils import to_int


def _build_create_file_transaction(params: CreateFileParams) -> FileCreateTransaction:
    transaction = FileCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.keys is not None:
        transaction.set_keys([get_key_from_string(key) for key in params.keys])

    if params.contents is not None:
        transaction.set_contents(params.contents)

    if params.expirationTime is not None:
        expiration_time = to_int(params.expirationTime)
        if expiration_time is None:
            raise JsonRpcError.invalid_params_error("expirationTime must be an integer")
        transaction.set_expiration_time(Timestamp(seconds=expiration_time, nanos=0))

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
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    file_id = ""
    if receipt.status == ResponseCode.SUCCESS and receipt.file_id is not None:
        file_id = str(receipt.file_id)

    return CreateFileResponse(file_id, ResponseCode(receipt.status).name)


@rpc_method("deleteFile")
def delete_file(params: DeleteFileParams) -> DeleteFileResponse:
    """Delete a file."""
    client = get_client(params.sessionId)

    transaction = FileDeleteTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.fileId is not None:
        transaction.set_file_id(FileId.from_string(params.fileId))
    else:
        # The JS reference leaves fileId unset and lets the node reject it, but
        # the Python SDK raises ValueError("Missing required FileID") locally
        # before the transaction is built. Send an explicit 0.0.0 so the request
        # reaches the network, which resolves it to INVALID_FILE_ID -- matching
        # the spec's expectation for an omitted fileId.
        transaction.set_file_id(FileId(0, 0, 0))

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return DeleteFileResponse(ResponseCode(receipt.status).name)
