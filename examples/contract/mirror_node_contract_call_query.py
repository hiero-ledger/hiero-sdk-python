"""
Example demonstrating MirrorNodeContractCallQuery.

MirrorNodeContractCallQuery simulates a contract call on the mirror node
(eth_call semantics) and returns the raw ABI-encoded result. Unlike
ContractCallQuery it is free: there is no query payment and no consensus
node round trip.

This example:
1. Sets up a client with operator credentials
2. Deploys the StatefulContract (paid transactions, needed only for the demo)
3. Calls getMessage() through the mirror node, by contract ID
4. Calls getMessageAndOwner() through the mirror node, by EVM address
5. Decodes both results with ContractFunctionResult

The mirror node lags consensus by a few seconds. Until it imports a new
contract, calls to the contract's address return "0x" instead of failing,
so the example waits for the contract before querying it.

Usage:
    # Run from the project root directory
    uv run -m examples.contract.mirror_node_contract_call_query
    python -m examples.contract.mirror_node_contract_call_query
"""

import sys
import time

from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    ContractCreateTransaction,
    ContractFunctionParameters,
    ContractFunctionResult,
    FileCreateTransaction,
    MirrorNodeContractCallQuery,
    MirrorNodeError,
    ResponseCode,
)

from .contracts import CONTRACT_DEPLOY_GAS, STATEFUL_CONTRACT_BYTECODE


load_dotenv()

INITIAL_MESSAGE = b"Hello from the mirror node query"  # exactly 32 bytes


def setup_client() -> Client:
    """Set up the client from the environment."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def deploy_stateful_contract(client: Client):
    """Deploy StatefulContract with INITIAL_MESSAGE as its constructor argument."""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(client.operator_private_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .execute(client)
    )
    if file_receipt.status != ResponseCode.SUCCESS:
        print(f"File creation failed with status: {ResponseCode(file_receipt.status).name}")
        sys.exit(1)

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(client.operator_private_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_receipt.file_id)
        .set_constructor_parameters(ContractFunctionParameters().add_bytes32(INITIAL_MESSAGE))
        .execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Contract creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Deployed contract {receipt.contract_id}")
    return receipt.contract_id


def wait_for_contract_on_mirror_node(client: Client, contract_id, attempts: int = 15) -> None:
    """
    Wait until the mirror node has imported the contract.

    Until then, a call to the contract's address does not fail: it runs
    against an address with no code, so a call returns "0x" and a gas
    estimate is only the cost of a plain transfer. Poll a view function
    until it returns data.
    """
    query = MirrorNodeContractCallQuery().set_contract_id(contract_id).set_function("getMessage")
    for _ in range(attempts):
        try:
            if query.execute(client) != "0x":
                return
        except MirrorNodeError as error:
            print(f"Mirror node error while waiting: {error}")
        print("Waiting for the mirror node to import the contract...")
        time.sleep(2)

    print("The mirror node did not import the contract in time")
    sys.exit(1)


def mirror_node_contract_call_query():
    """Call view functions of a deployed contract through the mirror node."""
    client = setup_client()
    contract_id = deploy_stateful_contract(client)

    # 1. Call by contract ID. The sender is optional; set it when the
    #    function depends on msg.sender.
    wait_for_contract_on_mirror_node(client, contract_id)

    result_hex = (
        MirrorNodeContractCallQuery()
        .set_contract_id(contract_id)
        .set_sender(client.operator_account_id)
        .set_function("getMessage")
        .execute(client)
    )
    print(f"\ngetMessage() raw result: {result_hex}")

    # The result is ABI-encoded hex. Wrap the bytes in ContractFunctionResult
    # to decode it with the same getters as ContractCallQuery results.
    result = ContractFunctionResult(contract_call_result=bytes.fromhex(result_hex[2:]))
    print(f"Decoded message: {result.get_bytes32(0)}")

    # 2. Call by EVM address, without a contract ID.
    evm_address = "0x" + contract_id.to_evm_address()
    result_hex = (
        MirrorNodeContractCallQuery()
        .set_contract_evm_address(evm_address)
        .set_function("getMessageAndOwner")
        .execute(client)
    )
    message, owner = ContractFunctionResult(contract_call_result=bytes.fromhex(result_hex[2:])).get_result(
        ["bytes32", "address"]
    )
    print(f"\ngetMessageAndOwner() via {evm_address}")
    print(f"Message: {message}")
    print(f"Owner:   {owner}")

    client.close()


if __name__ == "__main__":
    mirror_node_contract_call_query()
