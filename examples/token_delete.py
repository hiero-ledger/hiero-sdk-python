import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenDeleteTransaction,
    Network,
    TokenId,
)

load_dotenv()

def delete_token():
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    admin_key = PrivateKey.from_string_ed25519(os.getenv('ADMIN_KEY'))
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
        if receipt and receipt.status == 'SUCCESS':
            print("Token deletion successful.")
        else:
            print("Token deletion failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Token deletion failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    delete_token()
