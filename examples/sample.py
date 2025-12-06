import os
from dotenv import load_dotenv
from hiero_sdk_python import AccountId, Client,Network, PrivateKey



from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()

def main():
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    key = PrivateKey.generate_ecdsa()
    pub_key = key.public_key()
    evm_address= pub_key.to_evm_address()

    receipt = (
        AccountCreateTransaction()
        .set_key_with_alias(pub_key)
        .set_account_memo("Demo account")
        .freeze_with(client)
        .execute(client)
    )

    print(receipt.account_id)
    print(f"Evm address: {evm_address}")

    receipt = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -1)
        .add_hbar_transfer(AccountId.from_evm_address(evm_address), 1)
        .freeze_with(client)
        .execute(client)
    )

    print(ResponseCode(receipt.status).name)

if __name__ == "__main__":
    main()