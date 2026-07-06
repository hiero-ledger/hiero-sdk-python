from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.exceptions import ReceiptStatusError
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


@pytest.fixture
def file_id():
    """Returns a file_id for test."""
    return FileId.from_string("0.0.1")


@pytest.fixture
def account_id():
    """Returns an account_id for test."""
    return AccountId.from_string("0.0.9")


@pytest.fixture
def transaction_id():
    """Returns a transaction_id for test."""
    return TransactionId.from_string("0.0.9@1770911831.331000137")


def test_execute_waits_for_receipt_receipt():
    """Test execute return TransactionReceipt when wait_for_receipt is True (default)."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        # Default value of wait_for_receipt = True
        receipt = tx.execute(client, wait_for_receipt=True)

        assert isinstance(receipt, TransactionReceipt)
        assert receipt.status == ResponseCode.SUCCESS


def test_execute_without_wait_returns_transaction_response():
    """Test execute return TransactionResponse when wait_for_receipt is False."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        # Explicitly pass wait_for_receipt=False to get TransactionResponse
        response = tx.execute(client, wait_for_receipt=False)

        assert isinstance(response, TransactionResponse)
        assert response.transaction is tx
        assert response.node_id == tx.node_account_id
        assert response.validate_status is True


def test_execute_raises_error_when_validation_enabled_and_transaction_fails():
    """Test execute raises error for failing transactions when validate_status is True."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        with pytest.raises(ReceiptStatusError) as e:
            tx.execute(client, validate_status=True)

        assert e.value.status == ResponseCode.INVALID_SIGNATURE


def test_execute_returns_receipt_without_error_when_validation_disabled():
    """Test execute returns a receipt normally on failure when validate_status is False."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        receipt = tx.execute(client)

        assert receipt.status == ResponseCode.INVALID_SIGNATURE


def test_duplicate_signature_not_added():
    tx = TokenMintTransaction()
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1234)))
    tx.set_node_account_id(AccountId(0, 0, 3))
    tx.set_token_id(TokenId(0, 0, 1))
    tx.set_amount(100)
    key = PrivateKey.generate_ed25519()
    tx.freeze()
    tx.sign(key)
    tx.sign(key)
    assert tx._signature_map, "signature_map should not be empty after freeze+sign"  # ← ADD HERE
    body_bytes = next(iter(tx._signature_map.keys()))
    sig_pairs = tx._signature_map[body_bytes].sigPair
    assert len(sig_pairs) == 1, "Expected 1 signature for duplicate key"


def test_multiple_keys_still_work():
    tx = TokenMintTransaction()
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1234)))
    tx.set_node_account_id(AccountId(0, 0, 3))
    tx.set_token_id(TokenId(0, 0, 1))
    tx.set_amount(100)
    key1 = PrivateKey.generate_ed25519()
    key2 = PrivateKey.generate_ed25519()
    tx.freeze()
    tx.sign(key1)
    tx.sign(key2)
    assert tx._signature_map, "signature_map should not be empty after freeze+sign"
    body_bytes = next(iter(tx._signature_map.keys()))
    sig_pairs = tx._signature_map[body_bytes].sigPair
    assert len(sig_pairs) == 2, "Expected 2 signatures for different keys"
    pubkey_prefixes = {sp.pubKeyPrefix for sp in sig_pairs}
    expected_prefixes = {
        key1.public_key().to_bytes_raw(),
        key2.public_key().to_bytes_raw(),
    }
    assert pubkey_prefixes == expected_prefixes, "Signatures should match key1 and key2 exactly"


def test_same_size_for_identical_transactions(transaction_id, account_id):
    """Test two identical transactions should have the same size."""
    key = PrivateKey.generate()

    tx1 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    tx2 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    assert tx1.size == tx2.size


def test_signed_tx_have_larger_size(transaction_id, account_id):
    """Test signed Transaction should have larger size."""
    key = PrivateKey.generate()

    tx1 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
        .sign(PrivateKey.generate())
    )

    tx2 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    assert tx1.size > tx2.size


def test_tx_with_larger_content_should_have_larger_tx_body(transaction_id, account_id):
    """Test transaction with larger content should have larger transaction body."""
    tx1 = (
        FileCreateTransaction()
        .set_contents("smallBody")
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    tx2 = (
        FileCreateTransaction()
        .set_contents("veryLargeBody")
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    assert tx1.body_size < tx2.body_size


def test_tx_without_optional_fields_should_have_smaller_tx_body(transaction_id, account_id):
    """Test transaction with without optional fields should have smaller transaction body."""
    key = PrivateKey.generate()
    tx1 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    tx2 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .set_alias(PrivateKey.generate_ecdsa().public_key().to_evm_address())
        .set_transaction_valid_duration(10)
        .freeze()
    )

    assert tx1.body_size < tx2.body_size


def test_file_append_chunk_tx_should_return_list_of_body_sizes(file_id, account_id, transaction_id):
    """Test file append tx should return array of body sizes for multi-chunk transaction."""
    chunk_size = 1024
    content = "a" * (chunk_size * 3)

    tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_chunk_size(chunk_size)
        .set_contents(content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 3


def test_file_append_single_chunk_tx_return_list_of_len_one(file_id, account_id, transaction_id):
    """Test file append tx should return array of one size for single-chunk transaction."""
    content = "small_content"
    tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 1


def test_message_submit_chunk_tx_should_return_list_of_body_sizes(topic_id, account_id, transaction_id):
    """Test topic message submit tx should return array of body sizes for multi-chunk transaction."""
    chunk_size = 1024
    message = "a" * (chunk_size * 3)

    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_chunk_size(chunk_size)
        .set_message(message)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 3
    assert tx._current_chunk_index == 0


def test_message_submit_single_chunk_tx_return_list_of_len_one(topic_id, account_id, transaction_id):
    """Test topic message submit tx should return array of one size for single-chunk transaction."""
    message = "small_content"
    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message(message)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 1


def test_tx_with_no_content_should_return_single_body_chunk(file_id, account_id, transaction_id):
    """Test should return single body chunk for transaction with no content."""
    tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(" ")
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 1


def test_chunked_tx_return_proper_sizes(file_id, account_id, transaction_id):
    """Test should return proper sizes for FileAppend transactions when chunking occurs."""
    large_content = "a" * 2048

    large_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(large_content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    large_size = large_tx.size

    small_content = "a" * 512

    small_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(small_content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    small_size = small_tx.size

    # Size should be greater than single chunk size
    assert large_size > 1024
    # The larger chunked transaction should be bigger than the single-chunk transaction
    assert large_size > small_size
    assert large_tx._current_chunk_index == 0


def test_chunked_tx_differ_size_if_chunk_are_not_equal(topic_id, account_id, transaction_id):
    """Test that the last chunk's size is different from the full chunks if the chunk size is not even."""
    chunk_size = 1024
    message = "a" * (chunk_size + 512)

    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_chunk_size(chunk_size)
        .set_message(message)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert len(sizes) == 2
    # The first chunk should be larger than the second because it carries more message data
    assert sizes[0] > sizes[1]


def test_high_volume_defaults_to_false():
    """Test that high_volume defaults to False."""
    transaction = AccountCreateTransaction()

    assert transaction.high_volume is False


def test_high_volume_can_be_serialized(mock_client):
    """Test that high_volume is preserved during serialization/deserialization."""

    transaction = AccountCreateTransaction().set_key_without_alias(PrivateKey.generate_ed25519()).set_high_volume(True)

    transaction.freeze_with(mock_client)

    transaction_bytes = transaction.to_bytes()
    transaction_from_bytes = Transaction.from_bytes(transaction_bytes)

    assert isinstance(transaction_from_bytes, AccountCreateTransaction)
    assert transaction_from_bytes.high_volume is True


def test_high_volume_cannot_change_after_freeze(transaction_id, account_id):
    """Test that high_volume cannot be modified after freezing."""
    transaction = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519())
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_high_volume(True)


def test_high_volume_is_included_in_protobuf_output(
    transaction_id,
    account_id,
):
    """Test that high_volume is correctly serialized into protobuf output."""

    # Test with high_volume=True
    transaction = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519())
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .set_high_volume(True)
        .freeze()
    )

    assert transaction._transaction_body_bytes

    body_bytes = next(iter(transaction._transaction_body_bytes.values()))

    body = transaction_pb2.TransactionBody()
    body.ParseFromString(body_bytes)

    assert body.high_volume is True

    # Test with high_volume=False
    transaction_false = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519())
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .set_high_volume(False)
        .freeze()
    )

    body_bytes_false = next(iter(transaction_false._transaction_body_bytes.values()))

    body_false = transaction_pb2.TransactionBody()
    body_false.ParseFromString(body_bytes_false)

    assert body_false.high_volume is False


def test_transaction_fee_accepts_hbar():
    """Test that transaction_fee accepts an Hbar value and stores it as tinybars."""
    tx = AccountCreateTransaction()

    tx.transaction_fee = Hbar(1)

    assert tx._transaction_fee == Hbar(1).to_tinybars()


def test_transaction_fee_rejects_bool():
    """Test transaction_fee rejects boolean values."""
    tx = AccountCreateTransaction()

    with pytest.raises(TypeError, match="fee must be of type Hbar or int"):
        tx.transaction_fee = True


def test_transaction_fee_rejects_invalid_type():
    """Test transaction_fee rejects invalid types."""
    tx = AccountCreateTransaction()

    with pytest.raises(TypeError, match="fee must be of type Hbar or int"):
        tx.transaction_fee = "100"


def test_transaction_fee_rejects_negative_int():
    """Test transaction_fee rejects negative integer values."""
    tx = AccountCreateTransaction()

    with pytest.raises(ValueError, match="fee must be greater than or equal to 0"):
        tx.transaction_fee = -1


def test_transaction_default_max_fee(account_id):
    """Test default transaction fee is set if no transaction fee is set."""
    tx = TopicMessageSubmitTransaction()
    tx.set_node_account_id(AccountId(0, 0, 3))
    tx.operator_account_id = account_id

    tx_body = tx.build_base_transaction_body()

    assert tx_body is not None
    assert tx_body.transactionFee == Hbar(2).to_tinybars()


def test_build_transaction_body():
    """Test that build_transaction_body create transaction body with basic fields."""
    tx = TransferTransaction()
    transaction_body = tx.build_base_transaction_body()

    assert transaction_body is not None
    assert transaction_body.high_volume == False
    assert transaction_body.transactionValidDuration == Duration(120)._to_proto()
    # TODO: Should be change to 2hbar in future.
    # Since the deault fee for AbstractTokenTransfer can be remove, a default_fee is now updated to 2-hbar
    assert transaction_body.transactionFee == Hbar(1).to_tinybars()

    assert not transaction_body.HasField("transactionID")
    assert not transaction_body.HasField("nodeAccountID")


def test_set_node_account_id_updates_node_account_ids():
    """Test that setting a single node account ID updates node_account_ids."""
    tx = TransferTransaction().set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))

    account_node_id1 = AccountId(0, 0, 3)
    tx.set_node_account_id(account_node_id1)

    assert tx.node_account_ids == [account_node_id1]
    assert tx.node_account_id == account_node_id1  # Deprecated

    # Test backward compatibility
    node_account_id2 = AccountId(0, 0, 4)
    tx.node_account_id = node_account_id2

    assert tx.node_account_ids == [node_account_id2]
    assert tx.node_account_id == node_account_id2  # Deprecated


def test_set_node_account_ids_updates_node_account_ids():
    """Test that setting a node account ID list updates node_account_ids."""
    tx = TransferTransaction().set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))

    node_account_ids1 = [AccountId(0, 0, 3), AccountId(0, 0, 4)]
    tx.set_node_account_ids(node_account_ids1)

    assert tx.node_account_ids == node_account_ids1
    assert tx.node_account_id == node_account_ids1[0]  # Deprecated, will return 1st element of list

    # Test property setter
    node_account_ids2 = [AccountId(0, 0, 5), AccountId(0, 0, 6)]
    tx.node_account_ids = node_account_ids2

    assert tx.node_account_ids == node_account_ids2
    assert tx.node_account_id == node_account_ids2[0]  # Deprecated, will return 1st element of list


def test_freeze_transaction_sets_transaction_id_and_node_ids():
    """Test that freeze() preserves the transaction ID and builds body bytes for all node IDs."""
    tx_id = TransactionId.generate(AccountId(0, 0, 1))
    node_account_ids = [AccountId(0, 0, 3), AccountId(0, 0, 4)]

    tx = TransferTransaction().set_transaction_id(tx_id).set_node_account_ids(node_account_ids).freeze()

    assert tx.transaction_id == tx_id
    assert tx.node_account_ids == node_account_ids

    assert len(tx._transaction_body_bytes) == 1
    assert set(tx._transaction_body_bytes.keys()) == {tx_id}

    for node_id in node_account_ids:
        body_bytes = tx._transaction_body_bytes[tx_id][node_id]
        assert body_bytes is not None
        assert len(body_bytes) > 0


def test_freeze_with_sets_transaction_id_and_node_ids_from_client(mock_client):
    """Test that freeze_with() populates the transaction ID and node IDs from the client."""
    tx = TransferTransaction().freeze_with(mock_client)
    expected_node_ids = [node._account_id for node in mock_client.network.nodes]
    
    # Generated when freeze with using clinet
    expected_transaction_ids = tx._transaction_ids

    assert tx.transaction_id is not None
    assert tx.node_account_ids == expected_node_ids

    assert len(tx._transaction_body_bytes) == len(expected_node_ids)
    assert set(tx._transaction_body_bytes.keys()) == set(expected_transaction_ids)

    for node_id in expected_node_ids:
        body_bytes = tx._transaction_body_bytes[expected_transaction_ids[0]][node_id]
        assert body_bytes is not None
        assert len(body_bytes) > 0


# Deprecated, Only to test backward compatibility.
def test_freeze_transaction_sets_transaction_id_and_node_id():
    """Test that freeze() with a single node account ID builds the transaction body."""
    tx_id = TransactionId.generate(AccountId(0, 0, 1))
    node_account_id = AccountId(0, 0, 3)

    tx = TransferTransaction().set_transaction_id(tx_id).set_node_account_id(node_account_id).freeze()

    assert tx.transaction_id == tx_id
    assert tx._transaction_ids == [tx_id]
    assert tx.node_account_id == node_account_id

    assert len(tx._transaction_body_bytes) == 1
    assert set(tx._transaction_body_bytes.keys()) == {tx_id}
    assert set(tx._transaction_body_bytes[tx_id].keys()) == {node_account_id}

    body_bytes = tx._transaction_body_bytes[tx_id][node_account_id]
    assert body_bytes is not None
    assert len(body_bytes) > 0
