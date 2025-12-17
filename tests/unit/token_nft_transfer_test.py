from hiero_sdk_python.tokens.token_id import TokenId
import pytest

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer

pytestmark = pytest.mark.unit

def test_token_nft_transfer_constructor(mock_account_ids):
    """Test the TokenNftTransfer constructor with various parameters"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    serial_number = 789
    
    nft_transfer = TokenNftTransfer(
        token_id=token_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        serial_number=serial_number
    )
    
    # Verify all fields were set correctly
    
    assert nft_transfer.token_id == token_id
    assert nft_transfer.sender_id == sender_id
    assert nft_transfer.receiver_id == receiver_id
    assert nft_transfer.serial_number == serial_number
    assert nft_transfer.is_approved is False
    
    # Test with explicit is_approved=True
    approved_transfer = TokenNftTransfer(
        token_id=token_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        serial_number=serial_number,
        is_approved=True
    )
    
    assert nft_transfer.token_id == token_id
    assert approved_transfer.sender_id == sender_id
    assert approved_transfer.receiver_id == receiver_id
    assert approved_transfer.serial_number == serial_number
    assert approved_transfer.is_approved is True

def test_to_proto(mock_account_ids):
    """Test converting TokenNftTransfer to a protobuf object"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    serial_number = 789
    is_approved = True
    
    nft_transfer = TokenNftTransfer(
        token_id=token_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        serial_number=serial_number,
        is_approved=is_approved
    )
    
    # Convert to protobuf
    proto = nft_transfer._to_proto()
    
    # Verify protobuf fields
    assert proto.senderAccountID.shardNum == sender_id.shard
    assert proto.senderAccountID.realmNum == sender_id.realm
    assert proto.senderAccountID.accountNum == sender_id.num
    
    assert proto.receiverAccountID.shardNum == receiver_id.shard
    assert proto.receiverAccountID.realmNum == receiver_id.realm
    assert proto.receiverAccountID.accountNum == receiver_id.num
    
    assert proto.serialNumber == serial_number
    assert proto.is_approval is is_approved
    
def test_from_proto(mock_account_ids):
    """Test converting a protobuf object to a TokenNftTransfer"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    serial_number = 789
    is_approved = True
    
    proto = basic_types_pb2.TokenTransferList(
        token = TokenId._to_proto(token_id),
        nftTransfers= [basic_types_pb2.NftTransfer(
            senderAccountID=sender_id._to_proto(),
            receiverAccountID=receiver_id._to_proto(),
            serialNumber=serial_number,
            is_approval=is_approved
        )]
    )
    
    nft_transfer = TokenNftTransfer._from_proto(proto)
    
    assert nft_transfer[0].token_id == token_id
    assert nft_transfer[0].is_approved == is_approved
    assert nft_transfer[0].sender_id == sender_id
    assert nft_transfer[0].receiver_id == receiver_id
