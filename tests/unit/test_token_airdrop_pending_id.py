from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
import pytest

from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId

pytestmark = pytest.mark.unit

def test_pending_airdrop_id_constructor(mock_account_ids):
    """Test PendingAirdropId constructor with various params"""
    sender_id, receiver_id, _, token_id_1, token_id_2 = mock_account_ids
    nft_id = NftId(token_id=token_id_2, serial_number=10)

    # Test with token_id
    token_pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        token_id=token_id_1
    )

    assert token_pending_airdrop_id.sender_id == sender_id
    assert token_pending_airdrop_id.receiver_id == receiver_id
    assert token_pending_airdrop_id.token_id == token_id_1
    assert token_pending_airdrop_id.nft_id == None

    #Test wit nft_id
    nft_pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        nft_id=nft_id
    )

    assert nft_pending_airdrop_id.sender_id == sender_id
    assert nft_pending_airdrop_id.receiver_id == receiver_id
    assert nft_pending_airdrop_id.token_id == None
    assert nft_pending_airdrop_id.nft_id == nft_id

def test_pending_airdrop_id_constructor_for_invalid_param(mock_account_ids):
    """Test PendingAirdropId constructor for invalid params"""
    sender_id, receiver_id, _, token_id_1, token_id_2 = mock_account_ids
    nft_id = NftId(token_id=token_id_2, serial_number=10)

    #Both token_id and nft_id not provide:
    with pytest.raises(ValueError, match="Exactly one of 'token_id' or 'nft_id' must be required."):
        PendingAirdropId(
            sender_id=sender_id,
            receiver_id=receiver_id
        )

    #Bot token_id and nft is provided:
    with pytest.raises(ValueError, match="Exactly one of 'token_id' or 'nft_id' must be required."):
        PendingAirdropId(
            sender_id=sender_id,
            receiver_id=receiver_id,
            token_id=token_id_1,
            nft_id=nft_id
        )

def test_convert_to_proto(mock_account_ids):
    """Test PendingAirdropId _to_proto() method"""
    sender_id, receiver_id, _, token_id_1, token_id_2 = mock_account_ids
    nft_id = NftId(token_id=token_id_2, serial_number=10)

    # Test with token_id
    token_pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        token_id=token_id_1
    )

    token_proto = token_pending_airdrop_id._to_proto()
    assert token_proto.sender_id.shardNum == sender_id.shard
    assert token_proto.sender_id.realmNum == sender_id.realm
    assert token_proto.sender_id.accountNum == sender_id.num
    assert token_proto.receiver_id.shardNum== receiver_id.shard
    assert token_proto.receiver_id.realmNum == receiver_id.realm
    assert token_proto.receiver_id.accountNum == receiver_id.num
    assert token_proto.fungible_token_type.shardNum == token_id_1.shard
    assert token_proto.fungible_token_type.realmNum == token_id_1.realm
    assert token_proto.fungible_token_type.tokenNum == token_id_1.num
    assert token_proto.HasField("non_fungible_token") == False

    # Test with nft_id
    nft_pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        nft_id=nft_id
    )

    nft_proto = nft_pending_airdrop_id._to_proto()
    assert nft_proto.sender_id.shardNum == sender_id.shard
    assert nft_proto.sender_id.realmNum == sender_id.realm
    assert nft_proto.sender_id.accountNum == sender_id.num
    assert nft_proto.receiver_id.shardNum== receiver_id.shard
    assert nft_proto.receiver_id.realmNum == receiver_id.realm
    assert nft_proto.receiver_id.accountNum == receiver_id.num
    assert nft_proto.non_fungible_token.serial_number == 10
    assert nft_proto.non_fungible_token.token_ID.shardNum == token_id_2.shard
    assert nft_proto.non_fungible_token.token_ID.realmNum == token_id_2.realm
    assert nft_proto.non_fungible_token.token_ID.tokenNum == token_id_2.num
    assert nft_proto.HasField("fungible_token_type") == False

def test_from_proto(mock_account_ids):
    """Test PendingAirdropId _from_proto() method"""
    sender_id, receiver_id, _, token_id_1, token_id_2 = mock_account_ids
    nft_id = NftId(token_id=token_id_2, serial_number=10)

    # Test with token_id
    token_pending_airdrop_proto = basic_types_pb2.PendingAirdropId(
        sender_id=AccountId._to_proto(sender_id),
        receiver_id=AccountId._to_proto(receiver_id),
        fungible_token_type=TokenId._to_proto(token_id_1),
        non_fungible_token=None
    )

    token_pending_airdrop_id = PendingAirdropId._from_proto(token_pending_airdrop_proto)

    assert token_pending_airdrop_id.sender_id.shard == sender_id.shard
    assert token_pending_airdrop_id.sender_id.realm == sender_id.realm
    assert token_pending_airdrop_id.sender_id.num == sender_id.num
    assert token_pending_airdrop_id.receiver_id.shard == receiver_id.shard
    assert token_pending_airdrop_id.receiver_id.realm == receiver_id.realm
    assert token_pending_airdrop_id.receiver_id.num == receiver_id.num
    assert token_pending_airdrop_id.token_id.shard == token_id_1.shard
    assert token_pending_airdrop_id.token_id.realm == token_id_1.realm
    assert token_pending_airdrop_id.token_id.num == token_id_1.num
    assert token_pending_airdrop_id.nft_id == None

    # Test with nft_id
    nft_pending_airdrop_proto = basic_types_pb2.PendingAirdropId(
        sender_id=AccountId._to_proto(sender_id),
        receiver_id=AccountId._to_proto(receiver_id),
        fungible_token_type=None,
        non_fungible_token=NftId._to_proto(nft_id)
    )

    nft_pending_airdrop_id = PendingAirdropId._from_proto(nft_pending_airdrop_proto)

    assert nft_pending_airdrop_id.sender_id.shard == sender_id.shard
    assert nft_pending_airdrop_id.sender_id.realm == sender_id.realm
    assert nft_pending_airdrop_id.sender_id.num == sender_id.num
    assert nft_pending_airdrop_id.receiver_id.shard == receiver_id.shard
    assert nft_pending_airdrop_id.receiver_id.realm == receiver_id.realm
    assert nft_pending_airdrop_id.receiver_id.num == receiver_id.num
    assert nft_pending_airdrop_id.nft_id.serial_number == 10
    assert nft_pending_airdrop_id.nft_id.token_id.shard == token_id_2.shard
    assert nft_pending_airdrop_id.nft_id.token_id.realm == token_id_2.realm
    assert nft_pending_airdrop_id.nft_id.token_id.num == token_id_2.num
    assert nft_pending_airdrop_id.token_id == None