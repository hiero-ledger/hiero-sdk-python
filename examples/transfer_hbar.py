import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
)

load_dotenv()

def transfer_hbar():
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    recipient_id = AccountId.from_string(os.getenv('RECIPIENT_ID'))
    client.set_operator(operator_id, operator_key)

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100000000)  # send 1 HBAR in tinybars
        .add_hbar_transfer(recipient_id, 100000000)
        .freeze_with(client)
    )

    transaction.sign(operator_key)

    try:
        receipt = transaction.execute(client)
        print("HBAR transfer successful.")
    except Exception as e:
        print(f"HBAR transfer failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    transfer_hbar()
