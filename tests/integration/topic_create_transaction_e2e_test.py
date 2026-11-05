from __future__ import annotations

import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.transaction.transaction import Transaction
from tests.integration.utils import IntegrationTestEnv


topic_memo = "Python SDK created topic"


@pytest.mark.integration
def test_integration_topic_create_transaction_can_execute():
    env = IntegrationTestEnv()

    try:
        transaction = TopicCreateTransaction()

        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
        )

        transaction = TopicCreateTransaction(memo=topic_memo, admin_key=env.client.operator_private_key.public_key())

        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
        )

        topic_id = receipt.topic_id
        assert topic_id is not None

        topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert topic_info is not None

        assert topic_info.memo == topic_memo
        assert topic_info.sequence_number == 0

        assert isinstance(topic_info.admin_key, PublicKey)
        assert env.client.operator_private_key.public_key().to_bytes_raw() == topic_info.admin_key.to_bytes_raw()

        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)

        delete_transaction.freeze_with(env.client)
        receipt = delete_transaction.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Topic deletion failed with status: {ResponseCode(receipt.status).name}"
        )
    finally:
        env.close()


@pytest.mark.integration
def test_integration_topic_create_with_private_key():
    """Test creating a topic with PrivateKey directly (not PublicKey)."""
    env = IntegrationTestEnv()

    try:
        # Generate a new private key for the admin key
        admin_private_key = PrivateKey.generate_ed25519()
        admin_public_key = admin_private_key.public_key()

        # Create topic with PrivateKey
        transaction = TopicCreateTransaction(memo="Topic with PrivateKey", admin_key=admin_private_key)

        # Sign with the admin key (required when admin_key is set)
        transaction.freeze_with(env.client)
        transaction.sign(admin_private_key)
        receipt = transaction.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
        )

        topic_id = receipt.topic_id
        assert topic_id is not None

        # Query the topic and verify the admin key matches the public key
        topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert topic_info is not None
        assert topic_info.admin_key is not None

        assert isinstance(topic_info.admin_key, PublicKey)
        assert topic_info.admin_key.to_bytes_raw() == admin_public_key.to_bytes_raw(), (
            "Admin key on network should match the public key derived from PrivateKey"
        )

        # Clean up
        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        delete_transaction.freeze_with(env.client)
        delete_transaction.sign(admin_private_key)  # Sign with admin key for deletion
        delete_receipt = delete_transaction.execute(env.client)
        assert delete_receipt.status == ResponseCode.SUCCESS
    finally:
        env.close()


@pytest.mark.integration
def test_integration_topic_create_non_custodial_workflow():
    """
    Test the non-custodial workflow where:
    1. Operator builds a TX using only a PublicKey
    2. Operator gets the transaction bytes
    3. User (with the PrivateKey) signs the bytes
    4. Operator executes the signed transaction
    """
    env = IntegrationTestEnv()

    try:
        # 1. SETUP: Create a new key pair for the "user"
        user_private_key = PrivateKey.generate_ed25519()
        user_public_key = user_private_key.public_key()

        # =================================================================
        # STEP 1 & 2: OPERATOR (CLIENT) BUILDS THE TRANSACTION
        # =================================================================

        tx = (
            TopicCreateTransaction()
            .set_memo("NonCustodialTopic")
            .set_admin_key(user_public_key)  # <-- The new feature!
            .freeze_with(env.client)
        )

        tx_bytes = tx.to_bytes()

        # =================================================================
        # STEP 3: USER (SIGNER) SIGNS THE TRANSACTION
        # =================================================================

        tx_from_bytes = Transaction.from_bytes(tx_bytes)
        tx_from_bytes.sign(user_private_key)

        # =================================================================
        # STEP 4: OPERATOR (CLIENT) EXECUTES THE SIGNED TX
        # =================================================================

        receipt = tx_from_bytes.execute(env.client)

        assert receipt is not None
        topic_id = receipt.topic_id
        assert topic_id is not None

        # PROOF: Query the new topic and check if the admin key matches
        topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert topic_info.admin_key is not None

        # This is the STRONG assertion:
        assert isinstance(topic_info.admin_key, PublicKey)
        assert topic_info.admin_key.to_bytes_raw() == user_public_key.to_bytes_raw(), (
            "Admin key on network should match the PublicKey used in transaction"
        )

        # Clean up
        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        delete_transaction.freeze_with(env.client)
        delete_transaction.sign(user_private_key)  # Sign with admin key for deletion
        delete_receipt = delete_transaction.execute(env.client)
        assert delete_receipt.status == ResponseCode.SUCCESS
    finally:
        env.close()


@pytest.mark.integration
def test_integration_topic_create_with_ecdsa_private_key():
    """Test creating a topic with ECDSA PrivateKey."""
    env = IntegrationTestEnv()

    try:
        # Generate a new ECDSA private key for the admin key
        admin_private_key = PrivateKey.generate("ecdsa")
        admin_public_key = admin_private_key.public_key()

        # Create topic with ECDSA PrivateKey
        transaction = TopicCreateTransaction(memo="Topic with ECDSA PrivateKey", admin_key=admin_private_key)

        # Sign with the admin key (required when admin_key is set)
        transaction.freeze_with(env.client)
        transaction.sign(admin_private_key)
        receipt = transaction.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
        )

        topic_id = receipt.topic_id
        assert topic_id is not None

        # Query the topic and verify the admin key matches the public key
        topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert topic_info is not None
        assert topic_info.admin_key is not None

        assert isinstance(topic_info.admin_key, PublicKey)
        assert topic_info.admin_key.to_bytes_raw() == admin_public_key.to_bytes_raw(), (
            "Admin key on network should match the public key derived from ECDSA PrivateKey"
        )

        # Clean up
        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        delete_transaction.freeze_with(env.client)
        delete_transaction.sign(admin_private_key)  # Sign with admin key for deletion
        delete_receipt = delete_transaction.execute(env.client)
        assert delete_receipt.status == ResponseCode.SUCCESS
    finally:
        env.close()


@pytest.mark.integration
def test_serialize_topic_create_transaction_can_execute(env):
    """Verify restored create fileds and the resulting network topic."""
    topic_id = None

    try:
        submit_key = PrivateKey.generate_ed25519().public_key()
        exempt_key = PrivateKey.generate_ecdsa().public_key()
        period = Duration(7_776_000)
        fee = CustomFixedFee(amount=1, fee_collector_account_id=env.operator_id)

        transaction = TopicCreateTransaction(
            memo="Round-trip topic",
            admin_key=env.public_operator_key,
            submit_key=submit_key,
            auto_renew_period=period,
            auto_renew_account=env.operator_id,
            fee_schedule_key=env.public_operator_key,
            fee_exempt_keys=[exempt_key],
            custom_fees=[fee],
        )

        transaction.freeze_with(env.client)

        original_bytes = transaction.to_bytes()
        restored = Transaction.from_bytes(original_bytes)

        assert isinstance(restored, TopicCreateTransaction)
        assert restored.topic_memo == "Round-trip topic"
        assert restored.admin_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert restored.submit_key.to_proto_key() == submit_key.to_proto_key()
        assert restored.auto_renew_period == period
        assert restored.auto_renew_account == env.operator_id
        assert restored.fee_schedule_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert [key.to_proto_key() for key in restored.fee_exempt_keys] == [exempt_key.to_proto_key()]
        assert restored.custom_fees == [fee]
        assert restored.to_bytes() == original_bytes

        receipt = restored.execute(env.client)
        topic_id = receipt.topic_id

        assert receipt.status == ResponseCode.SUCCESS
        assert topic_id is not None

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert info.memo == "Round-trip topic"
        assert info.admin_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert info.submit_key.to_proto_key() == submit_key.to_proto_key()
        assert info.auto_renew_period == period
        assert info.auto_renew_account == env.operator_id
        assert info.fee_schedule_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert [key.to_proto_key() for key in info.fee_exempt_keys] == [exempt_key.to_proto_key()]
        assert info.custom_fees == [fee]
        assert info.sequence_number == 0

    finally:
        if topic_id is not None:
            receipt = TopicDeleteTransaction(topic_id=topic_id).execute(env.client)

            assert receipt.status == ResponseCode.SUCCESS
