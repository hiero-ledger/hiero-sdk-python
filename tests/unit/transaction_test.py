import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction_id import TransactionId

pytestmark = pytest.mark.unit


@pytest.fixture
def file_id():
    """Returns a file_is for test."""
    return FileId.from_string("0.0.1")


@pytest.fixture
def account_id():
    """Returns an account_id for test."""
    return AccountId.from_string("0.0.9")


@pytest.fixture
def transaction_id():
    """Returns a transaction_id for test."""
    return TransactionId.from_string("0.0.9@1770911831.331000137")


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


def test_tx_without_optional_fields_should_have_smaller_tx_body(
    transaction_id, account_id
):
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


def test_chunk_tx_should_return_list_of_body_sizes(file_id, account_id, transaction_id):
    """Test should return array of body sizes for multi-chunk transaction."""
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


def test_single_chunk_tx_return_list_of_len_one(file_id, account_id, transaction_id):
    """Test should return array of one size for single-chunk transaction."""
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


def test_tx_with_no_content_should_return_single_body_chunk(
    file_id, account_id, transaction_id
):
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
