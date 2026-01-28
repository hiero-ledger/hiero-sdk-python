from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import (
    TransactionReceipt as TransactionReceiptProto,
)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (
    TransactionResponse as TransactionResponseProto,
)
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services.transaction_pb2 import AtomicBatchTransactionBody
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.transaction.batch_transaction import BatchTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_tx(mock_client, mock_account_ids):
    """Return a factory that builds a TransferTransaction with optional batch_key and freeze."""
    sender_id, receiver_id, _, _, _ = mock_account_ids

    def _make_tx(batch_key=None, freeze=True):
        tx = (
            TransferTransaction()
            .add_hbar_transfer(account_id=sender_id, amount=-1)
            .add_hbar_transfer(account_id=receiver_id, amount=1)
        )

        if batch_key is not None:
            tx.set_batch_key(batch_key)
        if freeze:
            tx.freeze_with(mock_client)
        return tx

    return _make_tx


def test_constructor_without_params_creates_empty_inner_transactions():
    """Test create batch transaction without constructor params."""
    batch_tx = BatchTransaction()
    assert (
        batch_tx.inner_transactions is not None
    ), "inner_transactions should not be none"
    assert (
        len(batch_tx.inner_transactions) == 0
    ), "inner_transactions should be empty by default"


def test_constructor_with_params_accepts_valid_inner_transactions(mock_tx):
    """Test create batch transaction with constructor params."""
    inner_tx = [
        mock_tx(batch_key=PrivateKey.generate(), freeze=True),
        mock_tx(batch_key=PrivateKey.generate(), freeze=True),
    ]
    batch_tx = BatchTransaction(inner_transactions=inner_tx)

    assert batch_tx.inner_transactions is not None
    assert len(batch_tx.inner_transactions) == len(inner_tx)
    assert all(isinstance(t, TransferTransaction) for t in batch_tx.inner_transactions)


def test_constructor_rejects_transaction_without_batch_key(mock_tx):
    """Test create batch transaction should raise error if an inner transaction has no batch key."""
    inner_tx1 = [mock_tx(batch_key=None, freeze=True)]
    with pytest.raises(ValueError, match="Batch key needs to be set"):
        BatchTransaction(inner_transactions=inner_tx1)

    # multiple inner: first valid, second missing batch key
    inner_tx2 = [
        mock_tx(batch_key=PrivateKey.generate(), freeze=True),
        mock_tx(batch_key=None, freeze=True),
    ]
    with pytest.raises(ValueError, match="Batch key needs to be set"):
        BatchTransaction(inner_transactions=inner_tx2)


def test_constructor_rejects_unfrozen_transaction(mock_tx):
    """Test create batch transaction should raise error if an inner transaction is not frozen."""
    # single unfrozen
    inner_tx1 = [mock_tx(batch_key=PrivateKey.generate(), freeze=False)]
    with pytest.raises(ValueError, match="Transaction must be frozen"):
        BatchTransaction(inner_transactions=inner_tx1)

    # multiple: one frozen, one unfrozen
    inner_tx2 = [
        mock_tx(batch_key=PrivateKey.generate(), freeze=True),
        mock_tx(batch_key=PrivateKey.generate(), freeze=False),
    ]
    with pytest.raises(ValueError, match="Transaction must be frozen"):
        BatchTransaction(inner_transactions=inner_tx2)


def test_constructor_rejects_blacklisted_transaction_types(mock_client, mock_tx):
    """Test create batch transaction reject freeze transaction and batch transaction as inner transactions."""
    batch_key = PrivateKey.generate()

    # FreezeTransaction is not allowed
    inner_tx1 = [FreezeTransaction().set_batch_key(batch_key).freeze_with(mock_client)]
    with pytest.raises(
        ValueError,
        match="Transaction type FreezeTransaction is not allowed in a batch transaction",
    ):
        BatchTransaction(inner_transactions=inner_tx1)

    # BatchTransaction as an inner transaction is not allowed
    inner_tx2 = [
        BatchTransaction(inner_transactions=[mock_tx(batch_key=batch_key, freeze=True)])
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    ]
    with pytest.raises(
        ValueError,
        match="Transaction type BatchTransaction is not allowed in a batch transaction",
    ):
        BatchTransaction(inner_transactions=inner_tx2)


def test_set_inner_transactions_valid_param(mock_tx):
    """Test set_inner_transactions method set's the inner_transactions."""
    batch_key = PrivateKey.generate()
    batch_tx = BatchTransaction()

    inner_tx = [mock_tx(batch_key=batch_key, freeze=True)]
    batch_tx.set_inner_transactions(inner_tx)
    assert len(batch_tx.inner_transactions) == 1
    assert isinstance(batch_tx.inner_transactions[0], TransferTransaction)


def test_set_inner_transactions_invalid_param(mock_tx, mock_client):
    """Test set_inner_transactions method with invalid params."""
    batch_key = PrivateKey.generate()
    batch_tx = BatchTransaction()

    # no batch key
    with pytest.raises(ValueError, match="Batch key needs to be set"):
        batch_tx.set_inner_transactions([mock_tx(batch_key=None, freeze=True)])

    # not frozen
    with pytest.raises(ValueError, match="Transaction must be frozen"):
        batch_tx.set_inner_transactions([mock_tx(batch_key=batch_key, freeze=False)])

    # FreezeTransaction not allowed
    with pytest.raises(
        ValueError,
        match="Transaction type FreezeTransaction is not allowed in a batch transaction",
    ):
        batch_tx.set_inner_transactions(
            [FreezeTransaction().set_batch_key(batch_key).freeze_with(mock_client)]
        )

    # BatchTransaction not allowed
    nested_batch = BatchTransaction(
        inner_transactions=[mock_tx(batch_key=batch_key, freeze=True)]
    )
    nested_batch.set_batch_key(batch_key)
    nested_batch.freeze_with(mock_client)
    with pytest.raises(
        ValueError,
        match="Transaction type BatchTransaction is not allowed in a batch transaction",
    ):
        batch_tx.set_inner_transactions([nested_batch])


def test_add_inner_transaction_valid_param(mock_tx, mock_client):
    """Test add_inner_transaction method adds a inner_transactions."""
    batch_key = PrivateKey.generate()
    batch_tx = BatchTransaction()

    # can add a valid inner tx
    tx = mock_tx(batch_key=batch_key, freeze=True)
    batch_tx.add_inner_transaction(tx)
    assert len(batch_tx.inner_transactions) == 1
    assert batch_tx.inner_transactions[0].batch_key == batch_key


def test_add_inner_transaction_method_invalid_param(mock_tx, mock_client):
    """Test add_inner_transaction method with invalid params."""
    batch_key = PrivateKey.generate()
    batch_tx = BatchTransaction()

    # without batch key
    with pytest.raises(ValueError, match="Batch key needs to be set"):
        batch_tx.add_inner_transaction(mock_tx(batch_key=None, freeze=True))

    # not frozen
    with pytest.raises(ValueError, match="Transaction must be frozen"):
        batch_tx.add_inner_transaction(mock_tx(batch_key=batch_key, freeze=False))

    # FreezeTransaction
    with pytest.raises(
        ValueError,
        match="Transaction type FreezeTransaction is not allowed in a batch transaction",
    ):
        batch_tx.add_inner_transaction(
            FreezeTransaction().set_batch_key(batch_key).freeze_with(mock_client)
        )

    # BatchTransaction
    nested_batch = BatchTransaction(
        inner_transactions=[mock_tx(batch_key=batch_key, freeze=True)]
    )
    nested_batch.set_batch_key(batch_key)
    nested_batch.freeze_with(mock_client)
    with pytest.raises(
        ValueError,
        match="Transaction type BatchTransaction is not allowed in a batch transaction",
    ):
        batch_tx.add_inner_transaction(nested_batch)


def test_get_inner_transactions_ids_returns_transaction_ids(mock_tx):
    """Test get_transaction_ids methods returns transaction_ids."""
    batch_key = PrivateKey.generate()
    batch_tx = BatchTransaction()
    assert (
        batch_tx.get_inner_transaction_ids() == []
    ), "No inner transactions should return an empty list"

    transaction = mock_tx(batch_key=batch_key, freeze=True)
    batch_tx.add_inner_transaction(transaction)
    tx_ids = batch_tx.get_inner_transaction_ids()

    assert len(tx_ids) == 1
    assert isinstance(tx_ids[0], TransactionId)


def test_build_batch_transaction_body(mock_account_ids, mock_client):
    """Test building a batch transaction body with valid parameters."""
    sender_id, receiver_id, node_id, _, _ = mock_account_ids
    batch_key = PrivateKey.generate()

    inner_tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender_id, amount=-1)
        .add_hbar_transfer(account_id=receiver_id, amount=1)
        .set_batch_key(batch_key)
        .freeze_with(mock_client)
    )

    # verify inner transaction fields
    assert inner_tx.node_account_id == AccountId(0, 0, 0)
    assert inner_tx.batch_key == batch_key

    batch_tx = BatchTransaction().add_inner_transaction(inner_tx)
    batch_tx.operator_account_id = sender_id
    batch_tx.node_account_id = node_id

    body = batch_tx._build_proto_body()

    assert isinstance(body, AtomicBatchTransactionBody)
    assert len(body.transactions) == 1
    assert body.transactions[0] == inner_tx._make_request().signedTransactionBytes


def test_batchify_sets_required_fields(mock_account_ids, mock_client):
    """Test batchifiy method set required fields."""
    sender, receiver, _, _, _ = mock_account_ids
    batch_key = PrivateKey.generate()

    tx = (
        TransferTransaction()
        .add_hbar_transfer(sender, -1)
        .add_hbar_transfer(receiver, 1)
        .batchify(mock_client, batch_key)
    )

    assert (
        tx._transaction_body_bytes is not None
    ), "batchify should set _transaction_body_bytes"
    assert tx.batch_key == batch_key
    assert tx.node_account_id == AccountId(
        0, 0, 0
    ), "node_account_id for batched tx should be 0.0.0"


def test_round_trip_to_bytes_and_back_preserves_inner_transactions(
    mock_account_ids, mock_client
):
    """Test round trip of converting transaction to_bytes and from_bytes."""
    sender, receiver, _, _, _ = mock_account_ids
    batch_key = PrivateKey.generate()

    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(sender, -1)
        .add_hbar_transfer(receiver, 1)
        .batchify(mock_client, batch_key)
    )

    batch_tx = (
        BatchTransaction()
        .add_inner_transaction(transfer_tx)
        .freeze_with(mock_client)
        .sign(batch_key)
    )

    batch_tx_bytes = batch_tx.to_bytes()
    assert batch_tx_bytes and len(batch_tx_bytes) > 0

    new_batch_tx = Transaction.from_bytes(batch_tx_bytes)
    assert isinstance(new_batch_tx, BatchTransaction)
    assert batch_tx.transaction_id == new_batch_tx.transaction_id
    assert len(batch_tx.inner_transactions) == len(new_batch_tx.inner_transactions)

    inner_tx = new_batch_tx.inner_transactions[0]
    assert isinstance(inner_tx, TransferTransaction)
    assert inner_tx.transaction_id == transfer_tx.transaction_id


def test_sign_transaction(mock_client, mock_tx):
    """Test signing the batch transaction with a private key."""
    batch_tx = BatchTransaction()
    batch_tx.set_inner_transactions(
        [mock_tx(batch_key=PrivateKey.generate(), freeze=True)]
    )

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    batch_tx.freeze_with(mock_client)
    batch_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = batch_tx._transaction_body_bytes[node_id]

    assert (
        body_bytes in batch_tx._signature_map
    ), "signature map must contain an entry for the tx body bytes"
    sig_pairs = batch_tx._signature_map[body_bytes].sigPair
    assert len(sig_pairs) == 1
    sig_pair = sig_pairs[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, mock_tx):
    """Test converting the batch transaction to protobuf format after signing."""
    batch_tx = BatchTransaction()
    batch_tx.set_inner_transactions(
        [mock_tx(batch_key=PrivateKey.generate(), freeze=True)]
    )

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    batch_tx.freeze_with(mock_client)
    batch_tx.sign(private_key)
    proto = batch_tx._to_proto()

    assert getattr(
        proto, "signedTransactionBytes", None
    ), "proto must include signedTransactionBytes"
    assert len(proto.signedTransactionBytes) > 0


def test_batch_transaction_execute_successful(mock_account_ids, mock_client):
    """Test that a batch transaction executes and returns a success receipt."""
    sender, receiver, _, _, _ = mock_account_ids
    batch_key = PrivateKey.generate()

    # Precheck OK response
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Receipt indicating success
    mock_receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)

    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto,
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        transaction = (
            BatchTransaction()
            .add_inner_transaction(
                TransferTransaction()
                .add_hbar_transfer(sender, -1)
                .add_hbar_transfer(receiver, 1)
                .batchify(mock_client, batch_key)
            )
            .freeze_with(client)
            .sign(batch_key)
        )

        receipt = transaction.execute(client)
        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Transaction should have succeeded, got {receipt.status}"


def test_batch_key_accepts_public_key(mock_account_ids):
    """Test that batch_key can accept PublicKey (not just PrivateKey)."""
    sender, receiver, _, _, _ = mock_account_ids

    # Generate a key pair
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    # Test using PublicKey as batch_key
    tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender, amount=-1)
        .add_hbar_transfer(account_id=receiver, amount=1)
        .set_batch_key(public_key)  # Using PublicKey instead of PrivateKey
    )

    # Verify batch_key was set correctly
    assert tx.batch_key == public_key
    assert isinstance(tx.batch_key, type(public_key))


def test_batchify_with_public_key(mock_client, mock_account_ids):
    """Test that batchify method accepts PublicKey."""
    sender, receiver, _, _, _ = mock_account_ids

    # Generate a key pair
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    # Test using PublicKey in batchify
    tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender, amount=-1)
        .add_hbar_transfer(account_id=receiver, amount=1)
        .batchify(mock_client, public_key)  # Using PublicKey
    )

    # Verify batch_key was set and transaction was frozen
    assert tx.batch_key == public_key
    assert tx._transaction_body_bytes  # Should be frozen


def test_batch_transaction_with_public_key_inner_transactions(
    mock_client, mock_account_ids
):
    """Test BatchTransaction can accept inner transactions with PublicKey batch_keys."""
    sender, receiver, _, _, _ = mock_account_ids

    # Generate key pairs
    batch_key1 = PrivateKey.generate_ed25519()
    public_key1 = batch_key1.public_key()

    batch_key2 = PrivateKey.generate_ecdsa()
    public_key2 = batch_key2.public_key()

    # Create inner transactions with PublicKey batch_keys
    inner_tx1 = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender, amount=-1)
        .add_hbar_transfer(account_id=receiver, amount=1)
        .set_batch_key(public_key1)
        .freeze_with(mock_client)
    )

    inner_tx2 = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender, amount=-1)
        .add_hbar_transfer(account_id=receiver, amount=1)
        .set_batch_key(public_key2)
        .freeze_with(mock_client)
    )

    # BatchTransaction should accept these inner transactions
    batch_tx = BatchTransaction(inner_transactions=[inner_tx1, inner_tx2])

    assert len(batch_tx.inner_transactions) == 2
    assert batch_tx.inner_transactions[0].batch_key == public_key1
    assert batch_tx.inner_transactions[1].batch_key == public_key2


def test_batch_key_mixed_private_and_public_keys(mock_client, mock_account_ids):
    """Test that BatchTransaction can handle inner transactions with mixed PrivateKey and PublicKey."""
    sender, receiver, _, _, _ = mock_account_ids

    # Generate keys
    private_key = PrivateKey.generate_ed25519()
    public_key = PrivateKey.generate_ecdsa().public_key()

    # Inner transaction with PrivateKey
    inner_tx1 = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender, amount=-1)
        .add_hbar_transfer(account_id=receiver, amount=1)
        .set_batch_key(private_key)
        .freeze_with(mock_client)
    )

    # Inner transaction with PublicKey
    inner_tx2 = (
        TransferTransaction()
        .add_hbar_transfer(account_id=sender, amount=-1)
        .add_hbar_transfer(account_id=receiver, amount=1)
        .set_batch_key(public_key)
        .freeze_with(mock_client)
    )

    # BatchTransaction should accept mixed key types
    batch_tx = BatchTransaction(inner_transactions=[inner_tx1, inner_tx2])

    assert len(batch_tx.inner_transactions) == 2
    assert isinstance(batch_tx.inner_transactions[0].batch_key, PrivateKey)
    assert isinstance(batch_tx.inner_transactions[1].batch_key, type(public_key))


def test_set_batch_key_with_private_key():
    """Test that batch_key can be set with PrivateKey."""
    private_key = PrivateKey.generate_ed25519()
    transaction = TransferTransaction()

    result = transaction.set_batch_key(private_key)

    assert transaction.batch_key == private_key
    assert result == transaction  # Check method chaining


def test_set_batch_key_with_public_key():
    """Test that batch_key can be set with PublicKey."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()
    transaction = TransferTransaction()

    result = transaction.set_batch_key(public_key)

    assert transaction.batch_key == public_key
    assert result == transaction  # Check method chaining


def test_batch_key_type_annotation():
    """Test that batch_key accepts both PrivateKey and PublicKey types."""
    transaction = TransferTransaction()

    # Test with PrivateKey
    private_key = PrivateKey.generate_ecdsa()
    transaction.set_batch_key(private_key)
    assert isinstance(transaction.batch_key, PrivateKey)

    # Test with PublicKey
    public_key = private_key.public_key()
    transaction.set_batch_key(public_key)
    assert isinstance(transaction.batch_key, PublicKey)


def test_batch_key_none_by_default():
    """Test that batch_key is None by default."""
    transaction = TransferTransaction()
    assert transaction.batch_key is None
