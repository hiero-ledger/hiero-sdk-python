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

    ec = AccountId.from_evm_address('0xe4904257d1df556813f4715d438eafd6069d3fb4')

    print(operator_id.__repr__())
    operator_id.populate_evm_address(client)
    print(operator_id.__repr__())

    print(ec.__repr__())
    print(ec.num)

    ec.populate_account_num(client)

    print(ec.__repr__())    
    print(ec.num)

if __name__ == "__main__":
    main()