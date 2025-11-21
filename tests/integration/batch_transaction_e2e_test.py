import datetime
import pytest
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.system.freeze_type import FreezeType
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.batch_transaction import BatchTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import env

def create_account_tx(key, client):
    """Helper transaction to create an account."""
    account_receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(1)
        .execute(client)
    ) 

    return account_receipt.account_id

batch_key = PrivateKey.generate()

def test_batch_transaction_can_execute(env):
    """Test can create and execute batch transaction."""
    receiver_id = create_account_tx(PrivateKey.generate().public_key(), env.client)

    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id=env.operator_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id, amount=1)
        .batchify(env.client, batch_key)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(transfer_tx)
        .freeze_with(env.client)
        .sign(batch_key)
    )

    batch_receipt = batch_tx.execute(env.client)

    assert batch_receipt.status == ResponseCode.SUCCESS

    # Inner Transaction Receipt
    transfer_tx_id = batch_tx.get_inner_transaction_ids()[0]
    transfer_tx_receipt = (
        TransactionGetReceiptQuery()
        .set_transaction_id(transfer_tx_id)
        .execute(env.client)
    )

    assert transfer_tx_receipt.status == ResponseCode.SUCCESS

def test_batch_transaction_can_execute_from_bytes(env):
    """Test can create and execute batch transaction from bytes."""
    receiver_id = create_account_tx(PrivateKey.generate().public_key(), env.client)

    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id=env.operator_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id, amount=1)
        .batchify(env.client, batch_key)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(transfer_tx)
        .freeze_with(env.client)
        .sign(batch_key)
    )

    # Convert to bytes
    batch_bytes = batch_tx.to_bytes()
    # Build from bytes
    batch_tx_from_bytes = BatchTransaction.from_bytes(batch_bytes)
    batch_receipt = batch_tx_from_bytes.execute(env.client)

    assert batch_receipt.status == ResponseCode.SUCCESS

    # Inner Transaction Receipt
    transfer_tx_id = batch_tx_from_bytes.get_inner_transaction_ids()[0]
    transfer_tx_receipt = (
        TransactionGetReceiptQuery()
        .set_transaction_id(transfer_tx_id)
        .execute(env.client)
    )

    assert transfer_tx_receipt.status == ResponseCode.SUCCESS

def test_batch_transaction_can_execute_large_batch(env):
    """Test can execute a large batch transaction"""
    batch_tx = BatchTransaction()
    
    receiver_id = create_account_tx(PrivateKey.generate().public_key(), env.client)

    for _ in range(20):
        transfer_tx = (
            TransferTransaction()
            .add_hbar_transfer(account_id=env.operator_id, amount=-1)
            .add_hbar_transfer(account_id=receiver_id, amount=1)
            .batchify(env.client, batch_key)
        )

        batch_tx.add_inner_transaction(transfer_tx)

    batch_tx.freeze_with(env.client)
    batch_tx.sign(batch_key)

    batch_receipt = batch_tx.execute(env.client)

    assert batch_receipt.status == ResponseCode.SUCCESS
    
    # Inner Transaction Receipt
    for tx_id in batch_tx.get_inner_transaction_ids():
        transfer_tx_receipt = (
            TransactionGetReceiptQuery()
            .set_transaction_id(tx_id)
            .execute(env.client)
        )
    
    assert transfer_tx_receipt.status == ResponseCode.SUCCESS

def test_batch_transaction_without_inner_transactions(env):
    """Test batch transaction with empty inner transaction's list should raise an error."""
    with pytest.raises(ValueError, match="BatchTransaction requires at least one inner transaction."):
        (
            BatchTransaction()
            .freeze_with(env.client)
            .sign(batch_key)
            .execute(env.client)
        )

def test_batch_transaction_with_blacklisted_inner_transaction(env):
    """Test batch transaction with blacklisted inner transaction should raise an error."""
    # Freeze Transaction
    freeze_tx = (
        FreezeTransaction()
        .set_file_id(FileId.from_string("4.5.6"))
        .set_file_hash(bytes.fromhex('1723904587120938954702349857'))
        .set_start_time(Timestamp.generate())
        .set_freeze_type(FreezeType.FREEZE_ONLY)
        .batchify(env.client, batch_key)
    )

    with pytest.raises(ValueError, match="Transaction type FreezeTransaction is not allowed in a batch transaction"):
        (
            BatchTransaction()
            .add_inner_transaction(freeze_tx)
            .freeze_with(env.client)
            .sign(batch_key)
            .execute(env.client)
        )

    # Batch Transaction
    account_tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate().public_key())
        .set_initial_balance(1)
        .batchify(env.client, batch_key)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(account_tx)
        .batchify(env.client, batch_key)
    )

    with pytest.raises(ValueError, match="Transaction type BatchTransaction is not allowed in a batch transaction"):
        (
            BatchTransaction()
            .add_inner_transaction(batch_tx)
            .freeze_with(env.client)
            .sign(batch_key)
            .execute(env.client)
        )

def test_batch_transaction_with_invalid_batch_key(env):
    """Test invalid batch key set to inner transaction should raise error."""
    invalid_batch_key = PrivateKey.generate()
    receiver_id = create_account_tx(PrivateKey.generate().public_key(), env.client)

    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id=env.operator_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id, amount=1)
        .batchify(env.client, invalid_batch_key)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(transfer_tx)
        .freeze_with(env.client)
        .sign(batch_key)
    )

    batch_receipt = batch_tx.execute(env.client)

    assert batch_receipt.status == ResponseCode.INVALID_SIGNATURE

def test_batch_transaction_can_execute_with_different_batch_key(env):
    """Test can execute batch transaction with different batch keys."""
    batch_key1 = PrivateKey.generate()
    batch_key2 = PrivateKey.generate()
    batch_key3 = PrivateKey.generate()

    receiver_id1 = create_account_tx(PrivateKey.generate().public_key(), env.client)
    transfer_tx1 = (
        TransferTransaction()
        .add_hbar_transfer(account_id=env.operator_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id1, amount=1)
        .batchify(env.client, batch_key1)
    )

    receiver_id2 = create_account_tx(PrivateKey.generate().public_key(), env.client)
    transfer_tx2 = (
        TransferTransaction()
        .add_hbar_transfer(account_id=env.operator_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id2, amount=1)
        .batchify(env.client, batch_key2)
    )

    receiver_id3 = create_account_tx(PrivateKey.generate().public_key(), env.client)
    transfer_tx3 = (
        TransferTransaction()
        .add_hbar_transfer(account_id=env.operator_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id3, amount=1)
        .batchify(env.client, batch_key3)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(transfer_tx1)
        .add_inner_transaction(transfer_tx2)
        .add_inner_transaction(transfer_tx3)
        .freeze_with(env.client)
        .sign(batch_key1)
        .sign(batch_key2)
        .sign(batch_key3)
    )

    batch_receipt = batch_tx.execute(env.client)

    assert batch_receipt.status == ResponseCode.SUCCESS

    # Inner Transaction Receipt
    for transfer_tx_id in batch_tx.get_inner_transaction_ids():
        transfer_tx_receipt = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transfer_tx_id)
            .execute(env.client)
        )
        assert transfer_tx_receipt.status == ResponseCode.SUCCESS

def test_execute_transaction_fail_when_batchified(env):
    """Test transaction should fail when batchified but not part of a batch."""
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate().public_key())
        .set_initial_balance(1)
        .batchify(env.client, batch_key)
    )

    with pytest.raises(ValueError, match="Cannot execute batchified transaction outside of BatchTransaction."):
        tx.execute(env.client)

def test_successful_inner_transactions_should_incur_fees_even_though_one_fails(env):
    """Test successful inner transaction should incur fees even though one failed."""
    initial_balance = (
        AccountInfoQuery(account_id=env.operator_id).execute(env.client).balance
    )

    tx1 = (
        AccountCreateTransaction()
        .set_key(PrivateKey.generate().public_key())
        .set_initial_balance(1)
        .batchify(env.client, batch_key)
    )

    tx2 = (
        AccountCreateTransaction()
        .set_key(PrivateKey.generate().public_key())
        .set_initial_balance(1)
        .batchify(env.client, batch_key)
    )

    # Invalid Tx
    tx3 = (
        AccountCreateTransaction()
        .set_key(PrivateKey.generate().public_key())
        .set_initial_balance(1)
        .set_receiver_signature_required(True)
        .batchify(env.client, batch_key)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(tx1)
        .add_inner_transaction(tx2)
        .add_inner_transaction(tx3)
        .freeze_with(env.client)
        .sign(batch_key)
    )

    batch_receipt = batch_tx.execute(env.client)
    assert batch_receipt.status == ResponseCode.INNER_TRANSACTION_FAILED

    final_balance = (
        AccountInfoQuery(account_id=env.operator_id).execute(env.client).balance
    )

    assert initial_balance > final_balance

def test_batch_transaction_with_inner_schedule_transaction(env):
    """Test batch_transaction with inner schedule transaction raise error."""
    receiver_key = PrivateKey.generate()
    receiver_id = create_account_tx(receiver_key.public_key(), env.client)

    schedule_create_tx = (
        TransferTransaction()
        .add_hbar_transfer(receiver_id, -1)
        .add_hbar_transfer(env.operator_id, 1)
        .schedule()
    )

    current_time = datetime.datetime.now()
    future_expiration = Timestamp.from_date(current_time + datetime.timedelta(seconds=30))

    (
        schedule_create_tx.set_payer_account_id(receiver_id)
        .set_schedule_memo("test schedule create transaction")
        .set_expiration_time(future_expiration)
        .set_wait_for_expiry(True)
        .set_batch_key(batch_key)
        .freeze_with(env.client)
        .sign(receiver_key)
        .sign(env.operator_key)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(schedule_create_tx)
        .freeze_with(env.client)
        .sign(batch_key)
    )

    batch_receipt = batch_tx.execute(env.client)
    assert batch_receipt.status == ResponseCode.BATCH_TRANSACTION_IN_BLACKLIST
