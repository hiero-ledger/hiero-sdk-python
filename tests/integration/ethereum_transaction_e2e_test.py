"""
Integration tests for the EthereumTransaction class.
"""

import pytest
import rlp
from eth_keys import keys

from examples.contracts import CONTRACT_DEPLOY_GAS, STATEFUL_CONTRACT_BYTECODE
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.ethereum_transaction import EthereumTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_ethereum_transaction_with_contract_execution(env):
    """Test that a contract can be executed with an Ethereum transaction."""
    alias_private_key = _create_alias_account(env)

    contract_id = _create_contract(env)

    message = "Updated message bytes!".encode("utf-8")
    call_data_bytes = (
        ContractFunctionParameters("setMessage").add_bytes32(message).to_bytes()
    )

    # Ethereum transaction fields
    chain_id_bytes = bytes.fromhex("012a")
    max_priority_gas_bytes = bytes.fromhex("00")
    nonce_bytes = bytes.fromhex("00")
    max_gas_bytes = bytes.fromhex("d1385c7bf0")
    gas_limit_bytes = bytes.fromhex("0249f0")  # 150k
    value_bytes = bytes.fromhex("00")

    # Convert ContractId to 20-byte EVM address for the Ethereum transaction 'to' field
    contract_bytes = bytes.fromhex(contract_id.to_evm_address())

    # Get the call data bytes
    transaction_data = _get_call_data(
        chain_id_bytes,
        nonce_bytes,
        (max_priority_gas_bytes, max_gas_bytes, gas_limit_bytes),
        contract_bytes,
        value_bytes,
        call_data_bytes,
        alias_private_key,
    )

    receipt = (
        EthereumTransaction().set_ethereum_data(transaction_data).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Ethereum transaction failed with status: {ResponseCode(receipt.status).name}"

    info_query = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_function_parameters(ContractFunctionParameters("getMessage"))
        .set_gas(1000000)
        .execute(env.client)
    )

    assert (
        info_query.get_bytes32(0).rstrip(b"\x00") == message
    ), "Message should be updated"


@pytest.mark.integration
def test_integration_ethereum_transaction_with_contract_call(env):
    """Test that a contract can be called with an Ethereum transaction."""
    alias_private_key = _create_alias_account(env)

    contract_id = _create_contract(env)

    call_data_bytes = ContractFunctionParameters("getMessage").to_bytes()

    # Ethereum transaction fields
    chain_id_bytes = bytes.fromhex("012a")
    max_priority_gas_bytes = bytes.fromhex("00")
    nonce_bytes = bytes.fromhex("00")
    max_gas_bytes = bytes.fromhex("d1385c7bf0")
    gas_limit_bytes = bytes.fromhex("0249f0")  # 150k
    value_bytes = bytes.fromhex("00")

    # Convert ContractId to 20-byte EVM address for the Ethereum transaction 'to' field
    contract_bytes = bytes.fromhex(contract_id.to_evm_address())

    # Get the call data bytes
    transaction_data = _get_call_data(
        chain_id_bytes,
        nonce_bytes,
        (max_priority_gas_bytes, max_gas_bytes, gas_limit_bytes),
        contract_bytes,
        value_bytes,
        call_data_bytes,
        alias_private_key,
    )

    receipt = (
        EthereumTransaction().set_ethereum_data(transaction_data).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Ethereum transaction failed with status: {ResponseCode(receipt.status).name}"

    record = (
        TransactionRecordQuery()
        .set_transaction_id(receipt.transaction_id)
        .execute(env.client)
    )
    assert (
        record.call_result.contract_call_result == b"Initial message from constructor"
    )


def test_integration_ethereum_transaction_jumbo_transaction(env):
    """Test that a jumbo transaction can be executed."""
    alias_private_key = _create_alias_account(env)

    contract_id = _create_contract(env)

    # Attempt to call the contract function `consumeLargeData` with a large payload of bytes
    call_data = ContractFunctionParameters("consumeLargeData").add_bytes(b"A" * 100_000)
    # Build call data bytes using ContractFunctionParameters
    call_data_bytes = call_data.to_bytes()

    # Prepare the required Ethereum transaction fields as bytes
    chain_id_bytes = bytes.fromhex("012a")
    max_priority_gas_bytes = bytes.fromhex("00")
    nonce_bytes = bytes.fromhex("00")
    max_gas_bytes = bytes.fromhex("d1385c7bf0")
    gas_limit_bytes = bytes.fromhex("3567E0")  # 3.5M
    value_bytes = bytes.fromhex("00")

    contract_bytes = bytes.fromhex(contract_id.to_evm_address())

    # Get the call data bytes
    transaction_data = _get_call_data(
        chain_id_bytes,
        nonce_bytes,
        (max_priority_gas_bytes, max_gas_bytes, gas_limit_bytes),
        contract_bytes,
        value_bytes,
        call_data_bytes,
        alias_private_key,
    )

    receipt = (
        EthereumTransaction().set_ethereum_data(transaction_data).execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Ethereum transaction failed with status: {ResponseCode(receipt.status).name}"


# pylint: disable=too-many-arguments, too-many-positional-arguments
def _get_call_data(
    chain_id: bytes,
    nonce: bytes,
    gas_params: tuple[bytes, bytes, bytes],
    contract_bytes: bytes,
    value: bytes,
    call_data_bytes: bytes,
    ecdsa_private_key: PrivateKey,
) -> bytes:
    """
    Create Ethereum transaction data with RLP encoding and ECDSA signature.

    This function creates an EIP-1559 transaction (type 2) with the provided parameters,
    signs it with the given ECDSA private key, and returns the complete transaction bytes.

    Args:
        chain_id: Chain ID as bytes
        nonce: Transaction nonce as bytes
        gas_params: Tuple of max priority fee per gas, max fee per gas, and gas limit as bytes
        contract_bytes: Contract address as bytes
        value: Transaction value as bytes
        call_data_bytes: Contract call data as bytes
        ecdsa_private_key: ECDSA private key for signing

    Returns:
        Complete transaction bytes with signature
    """

    # Create the transaction list without signature components
    # EIP-1559 transaction format:
    # [chainId, nonce, maxPriorityFeePerGas, maxFeePerGas, gasLimit, to, value, data, accessList]
    max_priority_gas, max_gas, gas_limit = gas_params

    transaction_list = [
        chain_id,
        nonce if nonce != b"\x00" else b"",
        max_priority_gas if max_priority_gas != b"\x00" else b"",
        max_gas if max_gas != b"\x00" else b"",
        gas_limit if gas_limit != b"\x00" else b"",
        contract_bytes if contract_bytes != b"\x00" else b"",
        value if value != b"\x00" else b"",
        call_data_bytes if call_data_bytes != b"\x00" else b"",
        [],  # empty access list
    ]

    # Encode the transaction
    message_bytes = rlp.encode(transaction_list)
    message_bytes = b"\x02" + message_bytes

    # Sign the transaction
    private_key_obj = keys.PrivateKey(ecdsa_private_key.to_bytes_ecdsa_raw())
    sig = private_key_obj.sign_msg(message_bytes)

    # Add the signature to the transaction
    signed_transaction_fields = transaction_list + [sig.v, sig.r, sig.s]
    signed_transaction_rlp = rlp.encode(signed_transaction_fields)

    return b"\x02" + signed_transaction_rlp


def _create_alias_account(env) -> PrivateKey:
    """
    Create an alias account for the ECDSA key and transfer HBAR to it.

    Args:
        env: The environment to use for the transfer transaction.

    Returns:
        The private key.
    """
    alias_private_key = PrivateKey.generate_ecdsa()

    alias_account_id = AccountId(
        shard=0, realm=0, num=0, alias_key=alias_private_key.public_key()
    )

    # Create a shallow account for the ECDSA key by transferring HBAR to the alias
    receipt = (
        TransferTransaction()
        .add_hbar_transfer(env.operator_id, -Hbar(5).to_tinybars())
        .add_hbar_transfer(alias_account_id, Hbar(5).to_tinybars())
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Transfer transaction failed with status: {ResponseCode(receipt.status).name}"

    return alias_private_key


def _create_contract(env) -> ContractId:
    """
    Create a contract.

    Returns:
        The contract ID.
    """
    # Create a file with the contract bytecode
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("file create with constructor params")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Create file failed with status: {ResponseCode(receipt.status).name}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Convert the message string to bytes32 format for the contract constructor.
    message = "Initial message from constructor".encode("utf-8")
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(ContractFunctionParameters().add_bytes32(message))
        .set_contract_memo("contract create with constructor params")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

    return contract_id
