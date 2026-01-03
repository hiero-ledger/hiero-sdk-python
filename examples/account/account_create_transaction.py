

import sys
from hiero_sdk_python import (
    Client,
    PrivateKey,
    AccountCreateTransaction,
    ResponseCode,
)


def create_new_account(client: Client) -> None:
    
    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()

    # Get the operator key from the client for signing
    operator_key = client.operator_private_key

    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(100000000)  # 1 HBAR in tinybars
        .set_account_memo("My new account")
    )

    try:
        # Explicit signing with key retrieved from client
        receipt = transaction.freeze_with(client).sign(operator_key).execute(client)
        print(f"Transaction status: {receipt.status}")

        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise Exception(f"Transaction failed with status: {status_message}")

        new_account_id = receipt.account_id
        if new_account_id is not None:
            print(f"✅ Account creation successful. New Account ID: {new_account_id}")
            print(f"   New Account Private Key: {new_account_private_key.to_string()}")
            print(f"   New Account Public Key: {new_account_public_key.to_string()}")
        else:
            raise Exception(
                "AccountID not found in receipt.  Account may not have been created."
            )

    except Exception as e:
        print(f"❌ Account creation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    client = Client.from_env()
    print(f"Operator: {client.operator_account_id}")
    create_new_account(client)
    client.close()
