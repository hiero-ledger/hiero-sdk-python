import pytest

from hiero_sdk_python.hapi.services.token_reject_pb2 import TokenReference, TokenRejectTransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, timestamp_pb2, transaction_get_receipt_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time
    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)

    tx_id = TransactionId(
        valid_start=tx_timestamp,
        account_id=account_id_proto
    )
    return tx_id

def test_build_transaction_body_with_token_ids(mock_account_ids):
    """Test building a token reject transaction body with token IDs."""
    account_id, owner_account_id, node_account_id, token_id, _ = mock_account_ids
    token_ids = [token_id]

    reject_tx = (
        TokenRejectTransaction()
        .set_owner_id(owner_account_id)
        .set_token_ids(token_ids)
    )

    reject_tx.transaction_id = generate_transaction_id(account_id)
    reject_tx.node_account_id = node_account_id

    transaction_body = reject_tx.build_transaction_body()

    assert transaction_body.tokenReject.owner.shardNum == owner_account_id.shard
    assert transaction_body.tokenReject.owner.realmNum == owner_account_id.realm
    assert transaction_body.tokenReject.owner.accountNum == owner_account_id.num

    assert len(transaction_body.tokenReject.rejections) == 1
    assert transaction_body.tokenReject.rejections[0].fungible_token.shardNum == token_id.shard
    assert transaction_body.tokenReject.rejections[0].fungible_token.realmNum == token_id.realm
    assert transaction_body.tokenReject.rejections[0].fungible_token.tokenNum == token_id.num

def test_build_transaction_body_with_nft_ids(mock_account_ids):
    """Test building a token reject transaction body with NFT IDs."""
    account_id, owner_account_id, node_account_id, token_id, _ = mock_account_ids

    # Create NftId instances
    nft_ids = [NftId(token_id=token_id, serial_number=1), NftId(token_id=token_id, serial_number=2)]

    reject_tx = ( 
        TokenRejectTransaction()
        .set_owner_id(owner_account_id)
        .set_nft_ids(nft_ids)
    )

    reject_tx.transaction_id = generate_transaction_id(account_id)
    reject_tx.node_account_id = node_account_id

    transaction_body = reject_tx.build_transaction_body()

    assert transaction_body.tokenReject.owner.shardNum == owner_account_id.shard
    assert transaction_body.tokenReject.owner.realmNum == owner_account_id.realm
    assert transaction_body.tokenReject.owner.accountNum == owner_account_id.num

    assert len(transaction_body.tokenReject.rejections) == 2

    # Check first NFT
    assert transaction_body.tokenReject.rejections[0].nft.token_ID.shardNum == token_id.shard
    assert transaction_body.tokenReject.rejections[0].nft.token_ID.realmNum == token_id.realm
    assert transaction_body.tokenReject.rejections[0].nft.token_ID.tokenNum == token_id.num
    assert transaction_body.tokenReject.rejections[0].nft.serial_number == 1

    # Check second NFT
    assert transaction_body.tokenReject.rejections[1].nft.token_ID.shardNum == token_id.shard
    assert transaction_body.tokenReject.rejections[1].nft.token_ID.realmNum == token_id.realm
    assert transaction_body.tokenReject.rejections[1].nft.token_ID.tokenNum == token_id.num
    assert transaction_body.tokenReject.rejections[1].nft.serial_number == 2

def test_constructor_with_parameters(mock_account_ids):
    """Test creating a token reject transaction with constructor parameters."""
    _, owner_account_id, _, token_id, _ = mock_account_ids
    token_ids = [token_id]
    nft_ids = [NftId(token_id=token_id, serial_number=1)]

    reject_tx = TokenRejectTransaction(
        owner_id=owner_account_id,
        token_ids=token_ids,
        nft_ids=nft_ids
    )

    assert reject_tx.owner_id == owner_account_id
    assert reject_tx.token_ids == token_ids
    assert reject_tx.nft_ids == nft_ids

def test_set_methods(mock_account_ids):
    """Test the set methods of TokenRejectTransaction."""
    _, owner_account_id, _, token_id, _ = mock_account_ids
    token_ids = [token_id]
    nft_ids = [NftId(token_id=token_id, serial_number=1)]

    reject_tx = TokenRejectTransaction()

    # Test method chaining
    tx_after_set = reject_tx.set_owner_id(owner_account_id)
    assert tx_after_set is reject_tx
    assert reject_tx.owner_id == owner_account_id

    tx_after_set = reject_tx.set_token_ids(token_ids)
    assert tx_after_set is reject_tx
    assert reject_tx.token_ids == token_ids

    tx_after_set = reject_tx.set_nft_ids(nft_ids)
    assert tx_after_set is reject_tx
    assert reject_tx.nft_ids == nft_ids

def test_set_methods_require_not_frozen(mock_account_ids, nft_id, mock_client):
    """Test the set methods of TokenRejectTransaction."""
    _, owner_account_id, _, token_id, _ = mock_account_ids
    token_ids = [token_id]
    nft_ids = [nft_id]

    reject_tx = TokenRejectTransaction()
    reject_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        reject_tx.set_owner_id(owner_account_id)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        reject_tx.set_token_ids(token_ids)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        reject_tx.set_nft_ids(nft_ids)

def test_reject_transaction_can_execute(mock_account_ids):
    """Test that a reject transaction can be executed successfully."""
    account_id, owner_account_id, _, token_id, _ = mock_account_ids
    token_ids = [token_id]

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for a successful token reject
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS
    )

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        transaction = (
            TokenRejectTransaction()
            .set_owner_id(owner_account_id)
            .set_token_ids(token_ids)
        )

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"

def test_reject_transaction_from_proto(mock_account_ids):
    """Test that a reject transaction can be created from a protobuf object."""
    _, owner_account_id, _, token_id, _ = mock_account_ids
    token_ids = [token_id]
    nft_ids = [NftId(token_id=token_id, serial_number=1)]

    # Create protobuf object with both fungible token and NFT rejections
    proto = TokenRejectTransactionBody(
        owner=owner_account_id._to_proto(),
        rejections=[
            TokenReference(fungible_token=token_id._to_proto(), nft=None),
            TokenReference(fungible_token=None, nft=nft_ids[0]._to_proto())
        ]
    )

    # Deserialize the protobuf object
    _from_proto = TokenRejectTransaction()._from_proto(proto)

    # Verify deserialized transaction matches original data
    assert _from_proto.owner_id == owner_account_id
    assert _from_proto.token_ids == token_ids
    assert _from_proto.nft_ids == nft_ids

    # Deserialize empty protobuf
    _from_proto = TokenRejectTransaction()._from_proto(TokenRejectTransactionBody())

    # Verify empty protobuf deserializes to empty/default values
    assert _from_proto.owner_id == AccountId()
    assert _from_proto.token_ids == []
    assert _from_proto.nft_ids == []
    
def test_build_scheduled_body_with_token_ids(mock_account_ids):
    """Test building a scheduled transaction body for token reject transaction with token IDs."""
    _, owner_account_id, _, token_id, _ = mock_account_ids
    token_ids = [token_id]
    
    reject_tx = TokenRejectTransaction()
    reject_tx.set_owner_id(owner_account_id)
    reject_tx.set_token_ids(token_ids)
    
    schedulable_body = reject_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenReject")
    assert schedulable_body.tokenReject.owner == owner_account_id._to_proto()
    assert len(schedulable_body.tokenReject.rejections) == 1
    assert schedulable_body.tokenReject.rejections[0].HasField("fungible_token")
    assert schedulable_body.tokenReject.rejections[0].fungible_token == token_id._to_proto()

def test_build_scheduled_body_with_nft_ids(mock_account_ids):
    """Test building a scheduled transaction body for token reject transaction with NFT IDs."""
    _, owner_account_id, _, token_id, _ = mock_account_ids
    nft_ids = [NftId(token_id=token_id, serial_number=1)]
    
    reject_tx = TokenRejectTransaction()
    reject_tx.set_owner_id(owner_account_id)
    reject_tx.set_nft_ids(nft_ids)

    schedulable_body = reject_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenReject")
    assert schedulable_body.tokenReject.owner == owner_account_id._to_proto()
    assert len(schedulable_body.tokenReject.rejections) == 1
    assert schedulable_body.tokenReject.rejections[0].HasField("nft")
    assert schedulable_body.tokenReject.rejections[0].nft.token_ID == token_id._to_proto()
    assert schedulable_body.tokenReject.rejections[0].nft.serial_number == 1
