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


def setup_client() -> tuple[Client, AccountId]:
    """Initialize client and operator from .env file."""
    load_dotenv()

    if "OPERATOR_ID" not in os.environ or "OPERATOR_KEY" not in os.environ:
        print("Environment variables OPERATOR_ID or OPERATOR_KEY are missing.")
        sys.exit(1)

    try:
        operator_id = AccountId.from_string(os.environ["OPERATOR_ID"])
        operator_key = PrivateKey.from_string(os.environ["OPERATOR_KEY"])
    except Exception as e:  # noqa: BLE001
        print(f"Failed to parse OPERATOR_ID or OPERATOR_KEY: {e}")
        sys.exit(1)

    network_name = os.environ.get("NETWORK", "testnet")

    try:
        client = Client(Network(network_name))
    except Exception as e:
        print(f"Failed to create client for network '{network_name}': {e}")
        sys.exit(1)

    client.set_operator(operator_id, operator_key)
    print(f"Operator set: {operator_id}")

    return client, operator_id


def create_revenue_generating_topic(client: Client, operator_id: AccountId):
    """
    Create a topic that charges a fixed custom fee per message.

    The topic charges 1 HBAR (in tinybars) to the operator account for every message.
    """
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

        return topic_id
    except Exception as e:   # noqa: BLE001
        print(f"Failed to create topic: {e}")
        return None


def submit_message_with_custom_fee_limit(
    client: Client, topic_id, operator_id: AccountId
) -> None:
    """
    Submit a message to the topic with a CustomFeeLimit applied.

    The CustomFeeLimit caps the total custom fees the payer is willing to pay
    for this message at 2 HBAR.
    """
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

        # Ensure the base transaction fee is high enough to cover processing
        submit_tx.transaction_fee = Hbar(5).to_tinybars()

        # Attach the custom fee limit to the transaction
        submit_tx.set_custom_fee_limits([fee_limit])

        submit_receipt = submit_tx.execute(client)

        print("Message submitted successfully!")
        print(f"Transaction status: {submit_receipt.status}")
    except Exception as e:    # noqa: BLE001
        print(f"Transaction failed: {e}")


def main() -> None:
    client, operator_id = setup_client()

    topic_id = create_revenue_generating_topic(client, operator_id)
    if topic_id is None:
        return

    submit_message_with_custom_fee_limit(client, topic_id, operator_id)

    print("\nExample complete.")


if __name__ == "__main__":
    main()
