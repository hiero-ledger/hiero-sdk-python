import pytest

from hiero_sdk_python.tokens.token_nft_info import TokenNftInfo
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import token_get_nft_info_pb2, timestamp_pb2, basic_types_pb2

pytestmark = pytest.mark.unit

# This test uses fixture (mock_account_ids,nft_id) as parameter
def test_token_nft_info_constructor(mock_account_ids, nft_id):
    """Test the TokenNftInfo constructor with various parameters"""
    # Create test data
    account_id, spender_id, _, _, _ = mock_account_ids
    creation_time = 1623456789
    metadata = b"test metadata"
    
    # Test with all parameters
    token_nft_info = TokenNftInfo(
        nft_id=nft_id,
        account_id=account_id,
        creation_time=creation_time,
        metadata=metadata,
        spender_id=spender_id
    )
    
    # Verify all fields were set correctly
    assert token_nft_info.nft_id == nft_id
    assert token_nft_info.account_id == account_id
    assert token_nft_info.creation_time == creation_time
    assert token_nft_info.metadata == metadata
    assert token_nft_info.spender_id == spender_id
    
    # Test with default parameters
    empty_token_nft_info = TokenNftInfo()
    assert empty_token_nft_info.nft_id is None
    assert empty_token_nft_info.account_id is None
    assert empty_token_nft_info.creation_time is None
    assert empty_token_nft_info.metadata is None
    assert empty_token_nft_info.spender_id is None

def test_from_proto():
    """Test creating a TokenNftInfo from a protobuf object"""
    # Create a mock protobuf
    proto = token_get_nft_info_pb2.TokenNftInfo(
        nftID=basic_types_pb2.NftID(
            token_ID=basic_types_pb2.TokenID(
                shardNum=0,
                realmNum=0,
                tokenNum=123
            ),
            serial_number=456
        ),
        accountID=basic_types_pb2.AccountID(
            shardNum=0,
            realmNum=0,
            accountNum=789
        ),
        creationTime=timestamp_pb2.Timestamp(seconds=1623456789),
        metadata=b"test metadata",
        spender_id=basic_types_pb2.AccountID(
            shardNum=0,
            realmNum=0,
            accountNum=101112
        )
    )
    
    # Create TokenNftInfo from proto
    token_nft_info = TokenNftInfo._from_proto(proto)
    
    # Verify fields
    assert token_nft_info.nft_id.token_id.shard == 0
    assert token_nft_info.nft_id.token_id.realm == 0
    assert token_nft_info.nft_id.token_id.num == 123
    assert token_nft_info.nft_id.serial_number == 456
    
    assert token_nft_info.account_id.shard == 0
    assert token_nft_info.account_id.realm == 0
    assert token_nft_info.account_id.num == 789
    
    assert token_nft_info.creation_time == 1623456789
    assert token_nft_info.metadata == b"test metadata"
    
    assert token_nft_info.spender_id.shard == 0
    assert token_nft_info.spender_id.realm == 0
    assert token_nft_info.spender_id.num == 101112

# This test uses fixture (mock_account_ids, nft_id) as parameter
def test_to_proto(mock_account_ids, nft_id):
    """Test converting TokenNftInfo to a protobuf object"""
    account_id, spender_id, _, _, _ = mock_account_ids
    creation_time = 1623456789
    metadata = b"test metadata"
    
    # Create TokenNftInfo instance
    token_nft_info = TokenNftInfo(
        nft_id=nft_id,
        account_id=account_id,
        creation_time=creation_time,
        metadata=metadata,
        spender_id=spender_id
    )
    
    # Convert to protobuf
    proto = token_nft_info._to_proto()
    
    # Verify protobuf fields
    assert proto.nftID.token_ID.shardNum == nft_id.token_id.shard
    assert proto.nftID.token_ID.realmNum == nft_id.token_id.realm
    assert proto.nftID.token_ID.tokenNum == nft_id.token_id.num
    assert proto.nftID.serial_number == nft_id.serial_number
    
    assert proto.accountID.shardNum == account_id.shard
    assert proto.accountID.realmNum == account_id.realm
    assert proto.accountID.accountNum == account_id.num
    
    assert proto.creationTime.seconds == creation_time
    assert proto.metadata == metadata
    
    assert proto.spender_id.shardNum == spender_id.shard
    assert proto.spender_id.realmNum == spender_id.realm
    assert proto.spender_id.accountNum == spender_id.num

# This test uses fixture (mock_account_ids, nft_id) as parameter
def test_str_representation(mock_account_ids, nft_id):
    """Test the string representation of TokenNftInfo"""
    account_id, spender_id, _, _, _ = mock_account_ids
    creation_time = 1623456789
    metadata = b"test metadata"
    
    # Create TokenNftInfo instance
    token_nft_info = TokenNftInfo(
        nft_id=nft_id,
        account_id=account_id,
        creation_time=creation_time,
        metadata=metadata,
        spender_id=spender_id
    )
    
    # Get string representation
    string_repr = str(token_nft_info)
    
    # Verify string contains all important fields
    assert str(nft_id) in string_repr
    assert str(account_id) in string_repr
    assert str(creation_time) in string_repr
    assert str(metadata) in string_repr
    assert str(spender_id) in string_repr 