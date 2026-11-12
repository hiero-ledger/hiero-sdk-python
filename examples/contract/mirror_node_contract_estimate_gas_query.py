"""
Example demonstrating MirrorNodeContractEstimateGasQuery.

MirrorNodeContractEstimateGasQuery asks the mirror node how much gas a
contract call needs, so a ContractExecuteTransaction can use that value
instead of a guessed set_gas(...). The estimate itself is free.

This example:
1. Sets up a client with operator credentials
2. Deploys the StatefulContract
3. Estimates the gas for setMessage(bytes32) through the mirror node
4. Executes setMessage with the estimated gas
5. Reads the new message back with MirrorNodeContractCallQuery

The mirror node lags consensus by a few seconds. Until it imports a new
contract, an estimate for it is only the cost of a plain transfer and is
too low, so the example waits for the contract before estimating.

Usage:
    # Run from the project root directory
    uv run -m examples.contract.mirror_node_contract_estimate_gas_query
    python -m examples.contract.mirror_node_contract_estimate_gas_query
"""

import sys
import time

from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    ContractCreateTransaction,
    ContractExecuteTransaction,
    ContractFunctionParameters,
    ContractFunctionResult,
    FileCreateTransaction,
    MirrorNodeContractCallQuery,
    MirrorNodeContractEstimateGasQuery,
    MirrorNodeError,
    ResponseCode,
)

from .contracts import CONTRACT_DEPLOY_GAS, STATEFUL_CONTRACT_BYTECODE


load_dotenv()

INITIAL_MESSAGE = b"Initial message from constructor"
NEW_MESSAGE = b"Message set with estimated gas!!"


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


def read_message(client: Client, contract_id) -> bytes:
    """Read the current message through the mirror node."""
    result_hex = MirrorNodeContractCallQuery().set_contract_id(contract_id).set_function("getMessage").execute(client)
    return ContractFunctionResult(contract_call_result=bytes.fromhex(result_hex[2:])).get_bytes32(0)


def mirror_node_contract_estimate_gas_query():
    """Estimate gas on the mirror node, then execute with that gas."""
    client = setup_client()
    contract_id = deploy_stateful_contract(client)

    # Set the sender when the function checks msg.sender, otherwise the
    # simulation may revert.
    # An estimate made before the mirror node imports the contract is too low.
    wait_for_contract_on_mirror_node(client, contract_id)

    gas = (
        MirrorNodeContractEstimateGasQuery()
        .set_contract_id(contract_id)
        .set_sender(client.operator_account_id)
        .set_function("setMessage", ContractFunctionParameters().add_bytes32(NEW_MESSAGE))
        .execute(client)
    )
    print(f"\nEstimated gas for setMessage(bytes32): {gas}")

    receipt = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_gas(gas)
        .set_function("setMessage", ContractFunctionParameters().add_bytes32(NEW_MESSAGE))
        .execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Contract execution failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    print(f"setMessage executed with gas {gas}: {ResponseCode(receipt.status).name}")

    # Wait for the mirror node to see the new state.
    for _ in range(15):
        message = read_message(client, contract_id)
        if message == NEW_MESSAGE:
            break
        time.sleep(2)
    else:
        print(f"The mirror node still returns the old message: {message}")
        sys.exit(1)
    print(f"Message read back from the mirror node: {message}")

    client.close()


if __name__ == "__main__":
    mirror_node_contract_estimate_gas_query()
