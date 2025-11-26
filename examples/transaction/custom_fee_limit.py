"""
Example: Using CustomFeeLimit with a revenue-generating topic.

- Creates a topic that charges a fixed custom fee per message.
- Submits a message with a CustomFeeLimit specifying how much the payer is
  willing to pay in custom fees for that message.
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Hbar,
    Network,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
    CustomFixedFee,
)
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit


def setup_client():
    """Initialize client and operator from .env file."""
    load_dotenv()

    try:
        if "OPERATOR_ID" not in os.environ or "OPERATOR_KEY" not in os.environ:
            raise Exception(
                "Environment variables OPERATOR_ID or OPERATOR_KEY are missing."
            )

        operator_id = AccountId.from_string(os.environ["OPERATOR_ID"])
        operator_key = PrivateKey.from_string(os.environ["OPERATOR_KEY"])

        # Default to testnet if NETWORK is not set
        network_name = os.environ.get("NETWORK", "testnet")
        client = Client(Network(network_name))

        client.set_operator(operator_id, operator_key)
        print(f"Operator set: {operator_id}")

        return client, operator_id
    except Exception as e:
        print(f"Error setting up client: {e}")
        sys.exit(1)


def main():
    #  Setup Client
    client, operator_id = setup_client()

    # Create a revenue-generating topic with a custom fee
    print("\nCreating a topic with a fixed custom fee per message...")

    # Charge 1 HBAR to the operator for every message
    custom_fee = CustomFixedFee(
        amount=Hbar(1).to_tinybars(),
        fee_collector_account_id=operator_id,
    )

    try:
        topic_tx = TopicCreateTransaction()
        topic_tx.set_custom_fees([custom_fee])

        # execute() returns the receipt
        topic_receipt = topic_tx.execute(client)

        topic_id = topic_receipt.topic_id
        print(f"Topic created successfully: {topic_id}")
        print("This topic charges a fixed fee of 1 HBAR per message.")
    except Exception as e:
        print(f"Failed to create topic: {e}")
        return

    # Submit a message with a Custom Fee Limit
    print("\nSubmitting a message with a CustomFeeLimit...")

    # We are willing to pay up to 2 HBAR in custom fees for this message
    limit_fee = CustomFixedFee(
        amount=Hbar(2).to_tinybars(),
        fee_collector_account_id=operator_id,
    )

    fee_limit = CustomFeeLimit()
    fee_limit.set_payer_id(operator_id)
    fee_limit.add_custom_fee(limit_fee)

    print(
        f"Setting fee limit: max {limit_fee.amount} tinybars "
        f"in custom fees for payer {operator_id}"
    )

    try:
        submit_tx = TopicMessageSubmitTransaction()
        submit_tx.set_topic_id(topic_id)
        submit_tx.set_message("Hello Hedera with Fee Limits!")

        # Ensure the base transaction fee is high enough
        submit_tx.transaction_fee = Hbar(5).to_tinybars()

        # Attach the custom fee limit to the transaction
        submit_tx.set_custom_fee_limits([fee_limit])

        submit_receipt = submit_tx.execute(client)

        print("Message submitted successfully!")
        print(f"Transaction status: {submit_receipt.status}")
    except Exception as e:
        print(f"Transaction failed: {e}")

    print("\nExample complete.")


if __name__ == "__main__":
    main()
