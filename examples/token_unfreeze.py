import os 
import sys 
from dotenv import load_dotenv

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.network import Network 
from hiero_sdk_python.tokens.token_id import TokenId 
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction

load_dotenv()

def unfreeze_token(): # Single Token
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    freeze_key = PrivateKey.from_string_ed25519(os.getenv('FREEZE_KEY'))
    token_id = TokenId.from_string(os.getenv('TOKEN_ID'))
    account_id = AccountId.from_string(os.getenv('FREEZE_ACCOUNT_ID'))

    client.set_operator(operator_id, operator_key)

    transaction = (
        TokenUnfreezeTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .freeze_with(client)
        .sign(freeze_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt is not None and receipt.status == "SUCCESS":
            print('Token unfreeze Successful')
        else: 
            print("Token freeze failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Token unfreeze failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    unfreeze_token() # For single token unfreeze