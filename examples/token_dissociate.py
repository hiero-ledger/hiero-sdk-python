import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    Network,
    AccountId,
    PrivateKey,
    TokenId,
    TokenDissociateTransaction,
)

load_dotenv()

def dissociate_token(): #Single token
    network = Network(network='testnet')
    client = Client(network)

    recipient_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    recipient_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    token_id = TokenId.from_string('TOKEN_ID')

    client.set_operator(recipient_id, recipient_key)

    transaction = (
        TokenDissociateTransaction()
        .set_account_id(recipient_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(recipient_key)
    )

    try:
        receipt = transaction.execute(client)
        print("Token dissociation successful.")
    except Exception as e:
        print(f"Token dissociation failed: {str(e)}")
        sys.exit(1)

def dissociate_tokens():  # Multiple tokens
    network = Network(network='testnet')
    client = Client(network)

    recipient_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    recipient_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    token_ids = [TokenId.from_string('TOKEN_ID_1'), TokenId.from_string('TOKEN_ID_2')]  

    client.set_operator(recipient_id, recipient_key)

    transaction = (
        TokenDissociateTransaction()
        .set_account_id(recipient_id)
    )

    for token_id in token_ids:
        transaction.add_token_id(token_id)

    transaction = (
        transaction
        .freeze_with(client)
        .sign(recipient_key)
    )

    try:
        receipt = transaction.execute(client)
        print("Token dissociations successful.")
    except Exception as e:
        print(f"Token dissociations failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    dissociate_token()       # For single token dissociation
    # dissociate_tokens()    # For multiple token dissociation