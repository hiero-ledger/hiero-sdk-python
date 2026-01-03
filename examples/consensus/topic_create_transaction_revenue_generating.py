"""
Revenue Generating Topics Example

This example demonstrates how to create and use revenue generating topics with custom fees.
It covers:
1. Creating accounts (Alice, Bob)
2. Creating topics with Hbar fees
3. Submitting messages with custom fee limits
4. Updating topics with token fees
5. Using fee exempt keys
6. Verifying fee collection

Run with:
uv run examples/consensus/topic_create_transaction_revenue_generating.py
python examples/consensus/topic_create_transaction_revenue_generating.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    CryptoGetAccountBalanceQuery,
    CustomFeeLimit,
    CustomFixedFee,
    Hbar,
    Network,
    PrivateKey,
    ResponseCode,
    TokenAssociateTransaction,
    TokenCreateTransaction,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
    TopicUpdateTransaction,
    TransferTransaction,
)

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def create_account(client, name, initial_balance=Hbar(10)):
    """Create a test account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(initial_balance)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    account_id = receipt.account_id
    print(f"{name} account created with id: {account_id}")

    return account_id, account_private_key


def create_revenue_generating_topic(client, custom_fees):
    """Create a revenue generating topic with custom fees"""
    receipt = (
        TopicCreateTransaction()
        .set_admin_key(client.operator_private_key.public_key())
        .set_fee_schedule_key(client.operator_private_key.public_key())
        .set_custom_fees(custom_fees)
        .set_memo("python sdk revenue generating topic")
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Topic creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    topic_id = receipt.topic_id
    print(f"Topic created: {topic_id}")
    return topic_id


def submit_message_with_custom_fee_limit(client, topic_id, custom_fee_limit):
    """Submit a message to a topic with custom fee limit"""
    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message("message")
        .add_custom_fee_limit(custom_fee_limit)
    )
    tx.transaction_fee = Hbar(2).to_tinybars()
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Message submission failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print("Message submitted successfully")
    return receipt


def submit_message_without_custom_fee_limit(client, topic_id):
    """Submit a message to a topic without custom fee limit"""
    tx = TopicMessageSubmitTransaction().set_message("message").set_topic_id(topic_id)
    tx.transaction_fee = Hbar(2).to_tinybars()
    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Message submission failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print("Message submitted successfully")
    return receipt


def get_account_balance(client, account_id):
    """Get the balance of an account"""
    balance = CryptoGetAccountBalanceQuery(account_id).execute(client)
    return balance


def create_fungible_token(
    client,
    treasury_id,
    treasury_key,
    initial_supply=100,
):
    """Create a fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("revenue-generating token")
        .set_token_symbol("RGT")
        .set_decimals(8)
        .set_admin_key(treasury_key)
        .set_supply_key(treasury_key)
        .set_treasury_account_id(treasury_id)
        .set_initial_supply(initial_supply)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"Token created: {token_id}")
    return token_id


def associate_token_with_account(client, account_id, token_id, account_key):
    """Associate a token with an account"""
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Token association failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print("Token associated successfully")


def transfer_tokens(client, token_id, from_account_id, to_account_id, amount):
    """Transfer tokens between accounts"""
    receipt = (
        TransferTransaction()
        .add_token_transfer(token_id, from_account_id, -amount)
        .add_token_transfer(token_id, to_account_id, amount)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Transferred {amount} tokens successfully")


def update_topic_custom_fees(client, topic_id, custom_fees):
    """Update topic custom fees"""
    receipt = (
        TopicUpdateTransaction()
        .set_topic_id(topic_id)
        .set_custom_fees(custom_fees)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Topic update failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Topic updated with new custom fees")


def update_topic_fee_exempt_keys(client, topic_id, fee_exempt_keys):
    """Update topic fee exempt keys"""
    receipt = (
        TopicUpdateTransaction()
        .set_topic_id(topic_id)
        .set_fee_exempt_keys(fee_exempt_keys)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Topic update failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Topic updated with fee exempt keys")


def test_hbar_fee_flow(
    client, topic_id, alice_id, alice_key, operator_id, operator_key
):
    """Test Steps 3-4: Submit message with custom fee limit and verify Hbar fee collection"""
    print("Submitting a message as Alice to the topic")
    alice_balance_before = get_account_balance(client, alice_id)
    fee_collector_balance_before = get_account_balance(client, operator_id)

    custom_fee_limit = (
        CustomFeeLimit()
        .set_payer_id(alice_id)
        .add_custom_fee(
            CustomFixedFee().set_hbar_amount(Hbar(2))  # Bigger than topic fee of 1 Hbar
        )
    )

    # Set operator to Alice for message submission
    client.set_operator(alice_id, alice_key)
    submit_message_with_custom_fee_limit(client, topic_id, custom_fee_limit)
    # Reset operator back to original
    client.set_operator(operator_id, operator_key)

    # Verify fee collection
    print("Verifying fee collection...")
    alice_balance_after = get_account_balance(client, alice_id)
    fee_collector_balance_after = get_account_balance(client, operator_id)

    print(f"Alice account Hbar balance before: {alice_balance_before.hbars}")
    print(f"Alice account Hbar balance after: {alice_balance_after.hbars}")
    print(
        f"Fee collector account Hbar balance before: {fee_collector_balance_before.hbars}"
    )
    print(
        f"Fee collector account Hbar balance after: {fee_collector_balance_after.hbars}"
    )


def setup_token_and_update_topic(
    client, topic_id, alice_id, alice_key, operator_id, operator_key
):
    """Test Steps 5-6: Create token, transfer to Alice, and update topic with token fee"""
    print("Creating a token")
    token_id = create_fungible_token(client, operator_id, operator_key)

    associate_token_with_account(client, alice_id, token_id, alice_key)

    # Transfer token to Alice
    print("Transferring the token to Alice")
    transfer_tokens(client, token_id, operator_id, alice_id, 1)

    # Update topic to have token fee
    print("Updating the topic to have a custom fee of the token")
    custom_token_fee = (
        CustomFixedFee()
        .set_amount_in_tinybars(1)
        .set_denominating_token_id(token_id)
        .set_fee_collector_account_id(operator_id)
    )

    update_topic_custom_fees(client, topic_id, [custom_token_fee])
    return token_id


def test_token_fee_flow(
    client, topic_id, token_id, alice_id, alice_key, operator_id, operator_key
):
    """Test Steps 7-8: Submit message without custom fee limit and verify token fee collection"""
    print("Submitting a message as Alice to the topic")
    alice_balance_before = get_account_balance(client, alice_id)
    fee_collector_balance_before = get_account_balance(client, operator_id)

    # Set operator to Alice for message submission
    client.set_operator(alice_id, alice_key)
    submit_message_without_custom_fee_limit(client, topic_id)
    # Reset operator back to original
    client.set_operator(operator_id, operator_key)

    # Verify token fee collection
    print("Verifying token fee collection...")
    alice_balance_after = get_account_balance(client, alice_id)
    fee_collector_balance_after = get_account_balance(client, operator_id)

    print(f"Alice account Hbar balance before: {alice_balance_before.hbars}")
    print(
        f"Alice account Token balance before:"
        f"{alice_balance_before.token_balances.get(token_id, 0)}"
    )
    print(f"Alice account Hbar balance after: {alice_balance_after.hbars}")
    print(
        f"Alice account Token balance after:"
        f"{alice_balance_after.token_balances.get(token_id, 0)}"
    )
    print(
        f"Fee collector account Token balance before:"
        f"{fee_collector_balance_before.token_balances.get(token_id, 0)}"
    )
    print(
        f"Fee collector account Token balance after:"
        f"{fee_collector_balance_after.token_balances.get(token_id, 0)}"
    )


def test_fee_exempt_flow(client, topic_id, token_id, operator_id, operator_key):
    """Test Steps 9-12: Create Bob, update fee exempt keys, and verify Bob isn't charged"""
    print("Creating account - Bob")
    bob_id, bob_key = create_account(client, "Bob")

    # Update topic's fee exempt keys and add Bob's public key
    print("Updating the topic's fee exempt keys and add Bob's public key")
    update_topic_fee_exempt_keys(client, topic_id, [bob_key.public_key()])

    # Submit message with Bob without specifying max custom fee amount
    print("Submitting a message as Bob to the topic")
    bob_balance_before = get_account_balance(client, bob_id)

    client.set_operator(bob_id, bob_key)  # Set operator to Bob for message submission
    submit_message_without_custom_fee_limit(client, topic_id)
    client.set_operator(operator_id, operator_key)  # Reset operator back to original

    # Verify Bob was not debited the fee amount
    print("Verifying Bob was not charged fees...")
    bob_balance_after = get_account_balance(client, bob_id)

    print(f"Bob account Hbar balance before: {bob_balance_before.hbars}")
    print(
        f"Bob account Token balance before:"
        f"{bob_balance_before.token_balances.get(token_id, 0)}"
    )
    print(f"Bob account Hbar balance after: {bob_balance_after.hbars}")
    print(
        f"Bob account Token balance after:"
        f"{bob_balance_after.token_balances.get(token_id, 0)}"
    )


def revenue_generating_topics():
    """
    Demonstrates revenue generating topics functionality by:
    1. Creating Alice account
    2. Creating a topic with Hbar custom fee
    3. Submitting message with custom fee limit
    4. Verifying fee collection
    5. Creating fungible token and transferring some to Alice
    6. Updating topic to have token custom fee
    7. Submitting message, paid by Alice, without specifying max custom fee amount
    8. Verifying token fee collection
    9. Creating Bob account
    10. Updating topic's fee exempt keys and add Bob's public key
    11. Submitting message, paid by Bob, without specifying max custom fee amount
    12. Verifying Bob was not debited the fee amount
    """
    client = setup_client()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    # STEP 1: Create Alice account
    print("Creating account - Alice")
    alice_id, alice_key = create_account(client, "Alice")

    # STEP 2: Create a topic with Hbar custom fee
    print("Creating a topic with hbar custom fee")
    custom_hbar_fee = (
        CustomFixedFee()
        .set_hbar_amount(Hbar(1))
        .set_fee_collector_account_id(operator_id)
    )

    topic_id = create_revenue_generating_topic(client, [custom_hbar_fee])

    # STEPS 3-4: Test Hbar fee flow
    test_hbar_fee_flow(client, topic_id, alice_id, alice_key, operator_id, operator_key)

    # STEPS 5-6: Setup token and update topic
    token_id = setup_token_and_update_topic(
        client, topic_id, alice_id, alice_key, operator_id, operator_key
    )

    # STEPS 7-8: Test token fee flow
    test_token_fee_flow(
        client, topic_id, token_id, alice_id, alice_key, operator_id, operator_key
    )

    # STEPS 9-12: Test fee exempt flow
    test_fee_exempt_flow(client, topic_id, token_id, operator_id, operator_key)


if __name__ == "__main__":
    revenue_generating_topics()
