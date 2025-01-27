import os
import sys
from dotenv import load_dotenv

from hedera_sdk_python.client.client import Client
from hedera_sdk_python.account.account_id import AccountId
from hedera_sdk_python.crypto.private_key import PrivateKey
from hedera_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hedera_sdk_python.client.network import Network
from hedera_sdk_python.tokens.token_id import TokenId

load_dotenv() 

def delete_token():
    network = Network(network='testnet')  
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    admin_key = PrivateKey.from_string(os.getenv('ADMIN_KEY'))
    token_id = TokenId.from_string(os.getenv('TOKEN_ID'))

    client.set_operator(operator_id, operator_key)

    transaction = (
        TokenDeleteTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(operator_key)
        .sign(admin_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt is not None and receipt.status == 'SUCCESS':
            print(f"Token deletion successful")
        else:
            print(f"Token deletion failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Token deletion failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    delete_token() 