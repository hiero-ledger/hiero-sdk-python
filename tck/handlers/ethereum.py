from __future__ import annotations

from hiero_sdk_python.contract.ethereum_transaction import EthereumTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.errors import JsonRpcError
from tck.handlers.registry import rpc_method
from tck.param.ethereum import CreateEthereumTransactionParams
from tck.response.ethereum import CreateEthereumTransactionResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.param_utils import decode_hex, to_int


INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def _require_int64(value: str, name: str) -> int:
    """Parse and validate a string as an int64."""
    parsed = to_int(value)
    if parsed is None:
        raise JsonRpcError.invalid_params_error(f"{name} must be an integer")
    if not INT64_MIN <= parsed <= INT64_MAX:
        raise JsonRpcError.invalid_params_error(f"{name} must fit in an int64")
    return parsed


def _build_create_ethereum_transaction(
    params: CreateEthereumTransactionParams,
) -> EthereumTransaction:
    """Build an EthereumTransaction from JSON-RPC params."""
    transaction = EthereumTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.ethereumData is not None:
        transaction.set_ethereum_data(decode_hex(params.ethereumData))

    if params.callDataFileId is not None:
        transaction.set_call_data_file_id(FileId.from_string(params.callDataFileId))

    if params.maxGasAllowance is not None:
        transaction.set_max_gas_allowed(_require_int64(params.maxGasAllowance, "maxGasAllowance"))

    return transaction


@rpc_method("createEthereumTransaction")
def create_ethereum_transaction(
    params: CreateEthereumTransactionParams,
) -> CreateEthereumTransactionResponse:
    """Execute an Ethereum-formatted transaction."""
    client = get_client(params.sessionId)

    transaction = _build_create_ethereum_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)
    contract_id = ""
    if receipt.status == ResponseCode.SUCCESS and receipt.contract_id is not None:
        contract_id = str(receipt.contract_id)

    return CreateEthereumTransactionResponse(contract_id, ResponseCode(receipt.status).name)
