from unittest.mock import MagicMock
import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.transaction_pb2 import AtomicBatchTransactionBody
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.transaction.batch_transaction import BatchTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

pytestmark = pytest.mark.unit

@pytest.fixture
def batch_key():
    """Return a generated batch key."""
    return PrivateKey.generate()

@pytest.fixture
def transaction(mock_client, mock_account_ids, batch_key):
    """Return a transfer transaction with optional batch_key and freeze."""
    sender_id, receiver_id, _, _, _ = mock_account_ids
    key = batch_key

    def _make_tx(batch_key=True, freeze=True):
        tx = (
            TransferTransaction()
            .add_hbar_transfer(account_id=sender_id, amount=-1)
            .add_hbar_transfer(account_id=receiver_id, amount=1)
        )

        if batch_key:
            tx.set_batch_key(key)
        if freeze:
            tx.freeze_with(mock_client)

        return tx
    return _make_tx


def test_constructor_without_params():
    """Test create batch transaction without constructor params."""
    batch_tx = BatchTransaction()
    assert batch_tx.inner_transactions is not  None
    assert len(batch_tx.inner_transactions) == 0


def test_constructor_with_params(transaction):
    """Test create batch transaction with constructor params."""
    inner_tx = [transaction(batch_key=True, freeze=True)]
    batch_tx = BatchTransaction(inner_transactions=inner_tx)

    assert batch_tx.inner_transactions is not None
    assert len(batch_tx.inner_transactions) == 1
    assert isinstance(batch_tx.inner_transactions[0], TransferTransaction)

def test_constructor_rejects_transaction_without_batch_key(transaction):
    """Test create batch transaction should raise error if an inner transaction has no batch key."""
    # Single Inner Transaction
    inner_tx1 = [transaction(batch_key=False, freeze=True)]
    with pytest.raises(ValueError, match='Batch key needs to be set'):
        BatchTransaction(inner_transactions=inner_tx1)

    # Multiple Inner Transaction
    inner_tx2 = [
        transaction(batch_key=True, freeze=True),
        transaction(batch_key=False, freeze=True)
    ]
    with pytest.raises(ValueError, match='Batch key needs to be set'):
        BatchTransaction(inner_transactions=inner_tx2)

def test_constructor_rejects_unfrozen_transaction(transaction):
    """Test create batch transaction should raise error if an inner transaction is not frozen."""
    # Single Inner Transaction
    inner_tx1 = [transaction(batch_key=True, freeze=False)]
    with pytest.raises(ValueError, match='Transaction must be frozen.'):
        BatchTransaction(inner_transactions=inner_tx1)
    
    # Multiple Inner Transaction
    inner_tx2 = [
        transaction(batch_key=True, freeze=True),
        transaction(batch_key=True, freeze=False)
    ]
    with pytest.raises(ValueError, match='Transaction must be frozen.'):
        BatchTransaction(inner_transactions=inner_tx2)

def test_constructor_rejects_blacklisted_transaction_types(mock_client, batch_key, transaction):
    """Test create batch transaction reject freeze transaction and batch transaction as inner transactions."""
    # FreezeTransaction
    inner_tx1 = [
        FreezeTransaction()
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    ]
    with pytest.raises(ValueError, match='Transaction type FreezeTransaction is not allowed in a batch transaction.'):
        BatchTransaction(inner_transactions=inner_tx1)

    # BatchTransaction
    inner_tx2 = [
        BatchTransaction(inner_transactions=[transaction(batch_key=True, freeze=True)])
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    ]
    with pytest.raises(ValueError, match='Transaction type BatchTransaction is not allowed in a batch transaction.'):
        BatchTransaction(inner_transactions=inner_tx2)

def test_set_inner_transaction_method(transaction):
    """Test set_inner_transactions method set's the inner_transactions."""
    inner_tx = [transaction(batch_key=True, freeze=True)]

    batch_tx = BatchTransaction()
    assert batch_tx.inner_transactions is not None
    assert len(batch_tx.inner_transactions) == 0

    batch_tx.set_inner_transactions(inner_tx)
    assert len(batch_tx.inner_transactions) == 1
    assert isinstance(batch_tx.inner_transactions[0], TransferTransaction)

def test_set_inner_transaction_method_invalid_params(transaction, mock_client, batch_key):
    """Test set_inner_transactions method with invalid params."""
    batch_tx = BatchTransaction()
    
    # Without batch_key
    inner_tx1 = [transaction(batch_key=False, freeze=True)]

    with pytest.raises(ValueError, match="Batch key needs to be set."):
        batch_tx.set_inner_transactions(inner_tx1)
    
    # Without freeze
    inner_tx2 = [transaction(batch_key=True, freeze=False)]
    
    with pytest.raises(ValueError, match="Transaction must be frozen."):
        batch_tx.set_inner_transactions(inner_tx2)

    # Freeze Transaction
    inner_tx3 = [
        FreezeTransaction()
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    ]
    
    with pytest.raises(ValueError, match='Transaction type FreezeTransaction is not allowed in a batch transaction.'):
        batch_tx.set_inner_transactions(inner_tx3)

    # BatchTransaction
    inner_tx4 = [
        BatchTransaction(inner_transactions=[transaction(batch_key=True, freeze=True)])
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    ]
    with pytest.raises(ValueError, match='Transaction type BatchTransaction is not allowed in a batch transaction.'):
        batch_tx.set_inner_transactions(inner_tx4)

def test_add_inner_transaction_method(transaction):
    """Test add_inner_transaction method adds a inner_transactions."""
    transaction = transaction(batch_key=True, freeze=True)

    batch_tx = BatchTransaction()
    assert batch_tx.inner_transactions is not None
    assert len(batch_tx.inner_transactions) == 0

    batch_tx.add_inner_transaction(transaction)
    assert len(batch_tx.inner_transactions) == 1
    assert isinstance(batch_tx.inner_transactions[0], TransferTransaction)

def test_add_inner_transaction_method_invalid_params(transaction, mock_client, batch_key):
    """Test add_inner_transaction method with invalid params"""
    batch_tx = BatchTransaction()
    
    # Without batch_key
    inner_tx1 = transaction(batch_key=False, freeze=True)

    with pytest.raises(ValueError, match="Batch key needs to be set."):
        batch_tx.add_inner_transaction(inner_tx1)
    
    # Without freeze
    inner_tx2 = transaction(batch_key=True, freeze=False)
    
    with pytest.raises(ValueError, match="Transaction must be frozen."):
        batch_tx.add_inner_transaction(inner_tx2)

    # Freeze Transaction
    inner_tx3 = (
        FreezeTransaction()
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    )
    
    with pytest.raises(ValueError, match='Transaction type FreezeTransaction is not allowed in a batch transaction.'):
        batch_tx.add_inner_transaction(inner_tx3)

    # BatchTransaction
    inner_tx4 = (
        BatchTransaction(inner_transactions=[transaction(batch_key=True, freeze=True)])
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    )
    with pytest.raises(ValueError, match='Transaction type BatchTransaction is not allowed in a batch transaction.'):
        batch_tx.add_inner_transaction(inner_tx4)

def test_get_transaction_ids_method(transaction):
    """Test get_transaction_ids methods returns transaction_ids."""
    batch_tx = BatchTransaction()
    assert len(batch_tx.get_inner_transactions_ids()) == 0

    transaction = transaction(batch_key=True, freeze=True)
    batch_tx.add_inner_transaction(transaction)
    tx_ids = batch_tx.get_inner_transactions_ids()

    assert len(tx_ids) == 1
    assert isinstance(tx_ids[0], TransactionId)

def test_build_batch_transaction(mock_account_ids, batch_key, mock_client):
    """Test building a batch transaction body with valid parameters."""
    sender_id, receiver_id, node_id, _, _ = mock_account_ids

    inner_tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id, amount=1)
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    )

    # Check inner_transaction fields
    assert inner_tx.node_account_id == AccountId(0,0,0)
    assert inner_tx.batch_key is not None
    assert inner_tx.batch_key == batch_key

    # Check outer_transaction
    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(inner_tx)
    )
    batch_tx.operator_account_id = sender_id
    batch_tx.node_account_id = node_id

    body = batch_tx._build_proto_body()

    assert body is not None
    assert isinstance(body, AtomicBatchTransactionBody)

    assert len(body.transactions) == 1
    assert body.transactions[0] == inner_tx._make_request().signedTransactionBytes

def test_sign_transaction(mock_client, transaction):
    """Test signing the batch transaction with a private key."""
    batch_tx = BatchTransaction()
    batch_tx.set_inner_transactions([transaction(batch_key=True, freeze=True)])

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    batch_tx.freeze_with(mock_client)

    batch_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = batch_tx._transaction_body_bytes[node_id]

    assert len(batch_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = batch_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b'public_key'
    assert sig_pair.ed25519 == b'signature'

def test_to_proto(mock_client, transaction):
    """Test converting the batch transaction to protobuf format after signing."""
    batch_tx = BatchTransaction()
    batch_tx.set_inner_transactions([transaction(batch_key=True, freeze=True)])

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    batch_tx.freeze_with(mock_client)

    batch_tx.sign(private_key)
    proto = batch_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0

