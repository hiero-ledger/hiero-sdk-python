import os
import sys
from dotenv import load_dotenv

from hedera_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenFreezeTransaction,
    Network,
    TokenId,
)

load_dotenv() 

def freeze_token():
    network = Network(network='testnet')  
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    freeze_key = PrivateKey.from_string(os.getenv('FREEZE_KEY'))
    token_id = TokenId.from_string(os.getenv('TOKEN_ID'))
    account_id = AccountId.from_string(os.getenv('FREEZE_ACCOUNT_ID'))

    client.set_operator(operator_id, operator_key)

    transaction = (
        TokenFreezeTransaction()
        .set_token_id(token_id)
        .set_account(account_id)
        .freeze_with(client)
        .sign(freeze_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt is not None and receipt.status == 'SUCCESS':
            print(f"Token freeze successful")
        else:
            print(f"Token freeze failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Token freeze failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    freeze_token() 