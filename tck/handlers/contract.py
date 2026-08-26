from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.errors import JsonRpcError
from tck.handlers.registry import rpc_method
from tck.param.contract import CreateContractParams
from tck.response.contract import CreateContractResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string
from tck.util.param_utils import decode_hex, to_int


INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def _require_int64(value: str, name: str) -> int:
    """Parse an int64 JSON-RPC param transported as a string.

    Python ints are unbounded, so enforce the wire type's int64 range here
    (gas, initialBalance, autoRenewPeriod, stakedNodeId); boundary values
    themselves are valid and left for the network to judge.
    """
    parsed = to_int(value)
    if parsed is None:
        raise JsonRpcError.invalid_params_error(f"{name} must be an integer")
    if not INT64_MIN <= parsed <= INT64_MAX:
        raise JsonRpcError.invalid_params_error(f"{name} must fit in an int64")
    return parsed


def _build_create_contract_transaction(params: CreateContractParams) -> ContractCreateTransaction:
    """Map createContract JSON-RPC params onto a ContractCreateTransaction.

    Only supplied params are applied, so SDK defaults stay intact.
    """
    transaction = ContractCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.adminKey is not None:
        transaction.set_admin_key(get_key_from_string(params.adminKey))

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(Duration(_require_int64(params.autoRenewPeriod, "autoRenewPeriod")))

    if params.gas is not None:
        transaction.set_gas(_require_int64(params.gas, "gas"))

    if params.autoRenewAccountId is not None:
        transaction.set_auto_renew_account_id(AccountId.from_string(params.autoRenewAccountId))

    if params.initialBalance is not None:
        transaction.set_initial_balance(_require_int64(params.initialBalance, "initialBalance"))

    # Order matters: when both bytecode sources are supplied, bytecodeFileId wins
    # (matches the JS TCK server; the setters clear each other).
    if params.initcode is not None:
        transaction.set_bytecode(decode_hex(params.initcode))

    if params.bytecodeFileId is not None:
        transaction.set_bytecode_file_id(FileId.from_string(params.bytecodeFileId))

    if params.stakedAccountId is not None:
        transaction.set_staked_account_id(AccountId.from_string(params.stakedAccountId))

    if params.stakedNodeId is not None:
        transaction.set_staked_node_id(_require_int64(params.stakedNodeId, "stakedNodeId"))

    if params.declineStakingReward is not None:
        transaction.set_decline_reward(params.declineStakingReward)

    if params.memo is not None:
        transaction.set_contract_memo(params.memo)

    if params.maxAutomaticTokenAssociations is not None:
        transaction.set_max_automatic_token_associations(params.maxAutomaticTokenAssociations)

    if params.constructorParameters is not None:
        transaction.set_constructor_parameters(decode_hex(params.constructorParameters))

    return transaction


@rpc_method("createContract")
def create_contract(params: CreateContractParams) -> CreateContractResponse:
    """Create a smart contract."""
    client = get_client(params.sessionId)

    transaction = _build_create_contract_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    contract_id = ""
    if receipt.status == ResponseCode.SUCCESS and receipt.contract_id is not None:
        contract_id = str(receipt.contract_id)

    return CreateContractResponse(contract_id, ResponseCode(receipt.status).name)
