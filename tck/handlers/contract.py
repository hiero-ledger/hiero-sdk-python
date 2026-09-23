from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_bytecode_query import ContractBytecodeQuery
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info import ContractInfo
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.contract.contract_update_transaction import ContractUpdateTransaction
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.errors import JsonRpcError
from tck.handlers.registry import rpc_method
from tck.param.contract import (
    ContractByteCodeQueryParams,
    ContractCallQueryParams,
    ContractInfoQueryParams,
    CreateContractParams,
    UpdateContractParams,
)
from tck.response.contract import (
    ContractByteCodeResponse,
    ContractCallResponse,
    ContractInfoResponse,
    CreateContractResponse,
    StakingInfoResponse,
    UpdateContractResponse,
)
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string, key_to_string
from tck.util.param_utils import decode_hex, to_int
from tck.util.transaction_utils import execute_validated


INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def _require_int64(value: str, name: str) -> int:
    """Parse an int64 JSON-RPC param transported as a string.

    Python ints are unbounded, so enforce the wire type's int64 range here
    (gas, initialBalance, autoRenewPeriod, stakedNodeId, expirationTime); boundary values
    themselves are valid and left for the network to judge.
    """
    parsed = to_int(value)
    if parsed is None:
        raise JsonRpcError.invalid_params_error(f"{name} must be an integer")
    if not INT64_MIN <= parsed <= INT64_MAX:
        raise JsonRpcError.invalid_params_error(f"{name} must fit in an int64")
    return parsed


def _require_int32(value: int, name: str) -> int:
    """Validate an int32 JSON-RPC parameter."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise JsonRpcError.invalid_params_error(f"{name} must be an integer")
    if not INT32_MIN <= value <= INT32_MAX:
        raise JsonRpcError.invalid_params_error(f"{name} must fit in an int32")
    return value


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

    # The SDK's staking-target setters clear each other (the fields share the
    # protobuf staked_id oneof), so if both are supplied the one applied last
    # (stakedNodeId) wins, matching the JS TCK server.
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


def _build_update_contract_transaction(params: UpdateContractParams) -> ContractUpdateTransaction:
    """
    Maps updateContract JSON-RPC params onto a ContractUpdateTransaction.

    Only supplied params are applied, SDK defaults remain intact.
    """

    transaction = ContractUpdateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.contractId is not None:
        transaction.set_contract_id(ContractId.from_string(params.contractId))

    if params.adminKey is not None:
        transaction.set_admin_key(get_key_from_string(params.adminKey))

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(Duration(_require_int64(params.autoRenewPeriod, "autoRenewPeriod")))

    if params.expirationTime is not None:
        transaction.set_expiration_time(
            Timestamp(
                seconds=_require_int64(params.expirationTime, "expirationTime"),
                nanos=0,
            )
        )
    if params.memo is not None:
        transaction.set_contract_memo(params.memo)

    if params.autoRenewAccountId is not None:
        transaction.set_auto_renew_account_id(AccountId.from_string(params.autoRenewAccountId))

    if params.maxAutomaticTokenAssociations is not None:
        transaction.set_max_automatic_token_associations(
            _require_int32(
                params.maxAutomaticTokenAssociations,
                "maxAutomaticTokenAssociations",
            )
        )

    if params.stakedAccountId is not None:
        transaction.set_staked_account_id(AccountId.from_string(params.stakedAccountId))

    if params.stakedNodeId is not None:
        transaction.set_staked_node_id(_require_int64(params.stakedNodeId, "stakedNodeId"))

    if params.declineStakingReward is not None:
        transaction.set_decline_reward(params.declineStakingReward)

    return transaction


@rpc_method("createContract")
def create_contract(params: CreateContractParams) -> CreateContractResponse:
    """Create a smart contract."""
    client = get_client(params.sessionId)

    transaction = _build_create_contract_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    receipt = execute_validated(transaction, client)

    contract_id = ""
    if receipt.contract_id is not None:
        contract_id = str(receipt.contract_id)

    return CreateContractResponse(contract_id, ResponseCode(receipt.status).name)


def _build_contract_call_query(params: ContractCallQueryParams) -> ContractCallQuery:
    """Build ContractCallQuery from ContractCallQueryParams."""
    query = ContractCallQuery().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.contractId is not None:
        query.set_contract_id(ContractId.from_string(params.contractId))

    if params.gas is not None:
        query.set_gas(to_int(params.gas))

    if params.functionParameters is not None:
        query.set_function_parameters(bytes.fromhex(params.functionParameters))

    if params.maxResultSize is not None:
        query.set_max_result_size(to_int(params.maxResultSize))

    if params.senderAccountId is not None:
        query.set_sender(AccountId.from_string(params.senderAccountId))

    return query


@rpc_method("contractCallQuery")
def contract_call_query(params: ContractCallQueryParams) -> ContractCallResponse:
    """Contract call query."""
    client = get_client(params.sessionId)

    query = _build_contract_call_query(params)

    result: ContractFunctionResult = query.execute(client)
    return ContractCallResponse(
        contractId=str(result.contract_id),
        evmAddress=str(result.evm_address),
        errorMessage=result.error_message,
        gasUsed=result.gas_used,
        logs=result.log_info,
        gas=result.gas_available,
        hbarAmount=result.amount,
        senderAccountId=str(result.sender_id),
        signerNonce=result.signer_nonce,
        rawResult=result.contract_call_result.hex(),
    )


@rpc_method("updateContract")
def update_contract(params: UpdateContractParams) -> UpdateContractResponse:
    """Update a smart contract."""
    client = get_client(params.sessionId)

    transaction = _build_update_contract_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return UpdateContractResponse(status=ResponseCode(receipt.status).name)


@rpc_method("contractByteCodeQuery")
def contract_byte_code_query(params: ContractByteCodeQueryParams) -> ContractByteCodeResponse:
    """Get a smart contract's runtime bytecode as a hexadecimal string."""
    client = get_client(params.sessionId)

    query = ContractBytecodeQuery().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.contractId is not None:
        query.set_contract_id(ContractId.from_string(params.contractId))

    if params.queryPayment is not None:
        query.set_query_payment(Hbar.from_tinybars(int(params.queryPayment)))

    if params.maxQueryPayment is not None:
        query.set_max_query_payment(Hbar.from_tinybars(int(params.maxQueryPayment)))

    bytecode = query.execute(client)

    return ContractByteCodeResponse(
        contractId=str(query.contract_id),
        # A contract with no bytecode omits the field, matching the JS TCK server.
        bytecode=("0x" + bytecode.hex()) if bytecode else None,
    )


def _map_to_contract_info_response(info: ContractInfo) -> ContractInfoResponse:
    """Map ContractInfo to ContractInfoResponse."""
    staking_info: StakingInfoResponse = None

    if info.staking_info is not None:
        staking = info.staking_info

        staking_info = StakingInfoResponse(
            declineStakingReward=staking.decline_reward,
            stakePeriodStart=str(staking.stake_period_start) if staking.stake_period_start is not None else None,
            pendingReward=str(staking.pending_reward.to_tinybars()) if staking.pending_reward is not None else None,
            stakedToMe=str(staking.staked_to_me.to_tinybars()) if staking.staked_to_me is not None else None,
            stakedAccountId=str(staking.staked_account_id) if staking.staked_account_id is not None else None,
            stakedNodeId=str(staking.staked_node_id) if staking.staked_node_id is not None else None,
        )

    return ContractInfoResponse(
        contractId=str(info.contract_id) if info.contract_id is not None else None,
        accountId=str(info.account_id) if info.account_id is not None else None,
        contractAccountId=info.contract_account_id,
        adminKey=key_to_string(info.admin_key),
        expirationTime=str(info.expiration_time) if info.expiration_time is not None else None,
        autoRenewPeriod=str(info.auto_renew_period.seconds) if info.auto_renew_period is not None else None,
        autoRenewAccountId=str(info.auto_renew_account_id) if info.auto_renew_account_id is not None else None,
        storage=str(info.storage) if info.storage is not None else None,
        contractMemo=info.contract_memo,
        balance=str(info.balance) if info.balance is not None else None,
        isDeleted=info.is_deleted,
        maxAutomaticTokenAssociations=str(info.max_automatic_token_associations)
        if info.max_automatic_token_associations is not None
        else None,
        ledgerId=info.ledger_id.hex() if info.ledger_id is not None else None,
        stakingInfo=staking_info,
    )


@rpc_method("contractInfoQuery")
def contract_info_query(params: ContractInfoQueryParams) -> ContractInfoResponse:
    """Contract info query."""
    client = get_client(params.sessionId)

    query = ContractInfoQuery().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.contractId is not None:
        query.set_contract_id(ContractId.from_string(params.contractId))

    if params.queryPayment is not None:
        query.set_query_payment(Hbar.from_tinybars(to_int(params.queryPayment)))

    if params.maxQueryPayment is not None:
        query.set_max_query_payment(Hbar.from_tinybars(to_int(params.maxQueryPayment)))

    result = query.execute(client)

    return _map_to_contract_info_response(result)
