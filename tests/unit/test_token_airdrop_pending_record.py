from hiero_sdk_python.hapi.services import basic_types_pb2, transaction_record_pb2
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
import pytest

from hiero_sdk_python.tokens.token_airdrop_pending_record import PendingAirdropRecord

def test_pending_airdrop_record_constructor(mock_account_ids):
    """Test PendingAirdropRecord constructor with various params"""
    sender_id, receiver_id, _, token_id_1, token_id_2 = mock_account_ids
    nft_id = NftId(token_id=token_id_2, serial_number=10)
    amount = 1

    token_pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        token_id=token_id_1
    )

    nft_pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        nft_id=nft_id
    )

    #Pending airdrop id with token
    pending_airdrop_record_1 = PendingAirdropRecord(
        pending_airdrop_id=token_pending_airdrop_id,
        amount=amount
    )

    assert pending_airdrop_record_1.pending_airdrop_id == token_pending_airdrop_id
    assert pending_airdrop_record_1.amount == amount

    #Pending airdrop id with nft
    pending_airdrop_record_2 = PendingAirdropRecord(
        pending_airdrop_id=nft_pending_airdrop_id,
        amount=amount
    )

    assert pending_airdrop_record_2.pending_airdrop_id == nft_pending_airdrop_id
    assert pending_airdrop_record_2.amount == amount

def test_pending_airdrop_record_to_proto_for_fungible_token(mock_account_ids):
    """Test PendingAirdropRecord _to_proto() method for fungible token"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    amount = 1

    pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        token_id=token_id
    )

    #Pending airdrop id with token
    record = PendingAirdropRecord(
        pending_airdrop_id=pending_airdrop_id,
        amount=amount
    )
    proto = record._to_proto()

    assert proto.pending_airdrop_id.sender_id.shardNum == sender_id.shard
    assert proto.pending_airdrop_id.sender_id.realmNum == sender_id.realm
    assert proto.pending_airdrop_id.sender_id.accountNum == sender_id.num
    assert proto.pending_airdrop_id.receiver_id.shardNum== receiver_id.shard
    assert proto.pending_airdrop_id.receiver_id.realmNum == receiver_id.realm
    assert proto.pending_airdrop_id.receiver_id.accountNum == receiver_id.num
    assert proto.pending_airdrop_id.fungible_token_type.shardNum == token_id.shard
    assert proto.pending_airdrop_id.fungible_token_type.realmNum == token_id.realm
    assert proto.pending_airdrop_id.fungible_token_type.tokenNum == token_id.num
    assert proto.pending_airdrop_id.HasField("non_fungible_token") == False
    assert proto.pending_airdrop_value.amount == amount

def test_pending_airdrop_record_to_proto_for_nft(mock_account_ids):
    """Test PendingAirdropRecord _to_proto() method for nft"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    nft_id = NftId(token_id=token_id, serial_number=10)
    amount = 1

    pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        nft_id=nft_id
    )

    #Pending airdrop id with nft
    record = PendingAirdropRecord(
        pending_airdrop_id=pending_airdrop_id,
        amount=amount
    )
    proto = record._to_proto()

    assert proto.pending_airdrop_id.sender_id.shardNum == sender_id.shard
    assert proto.pending_airdrop_id.sender_id.realmNum == sender_id.realm
    assert proto.pending_airdrop_id.sender_id.accountNum == sender_id.num
    assert proto.pending_airdrop_id.receiver_id.shardNum== receiver_id.shard
    assert proto.pending_airdrop_id.receiver_id.realmNum == receiver_id.realm
    assert proto.pending_airdrop_id.receiver_id.accountNum == receiver_id.num
    assert proto.pending_airdrop_id.non_fungible_token.serial_number == 10
    assert proto.pending_airdrop_id.non_fungible_token.token_ID.shardNum == token_id.shard
    assert proto.pending_airdrop_id.non_fungible_token.token_ID.realmNum == token_id.realm
    assert proto.pending_airdrop_id.non_fungible_token.token_ID.tokenNum == token_id.num
    assert proto.pending_airdrop_id.HasField("fungible_token_type") == False
    assert proto.pending_airdrop_value.amount == amount


def test_pending_airdrop_record_from_proto_for_fungible_token(mock_account_ids):
    """Test PendingAirdropRecord _from_proto() method for fungible token"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    amount = 1

    pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        token_id=token_id
    )

    #Pending airdrop id with token
    proto = transaction_record_pb2.PendingAirdropRecord(
        pending_airdrop_id=pending_airdrop_id._to_proto(),
        pending_airdrop_value=basic_types_pb2.PendingAirdropValue(amount=amount)
    )

    record = PendingAirdropRecord._from_proto(proto=proto)

    assert record.pending_airdrop_id.sender_id.shard == sender_id.shard
    assert record.pending_airdrop_id.sender_id.realm == sender_id.realm
    assert record.pending_airdrop_id.sender_id.num == sender_id.num
    assert record.pending_airdrop_id.receiver_id.shard == receiver_id.shard
    assert record.pending_airdrop_id.receiver_id.realm == receiver_id.realm
    assert record.pending_airdrop_id.receiver_id.num == receiver_id.num
    assert record.pending_airdrop_id.token_id.shard == token_id.shard
    assert record.pending_airdrop_id.token_id.realm == token_id.realm
    assert record.pending_airdrop_id.token_id.num == token_id.num
    assert record.pending_airdrop_id.nft_id == None
    assert record.amount == amount

def test_pending_airdrop_record_from_proto_for_nft(mock_account_ids):
    """Test PendingAirdropRecord _from_proto() method for nft"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    nft_id = NftId(token_id=token_id, serial_number=10)
    amount = 1

    pending_airdrop_id = PendingAirdropId(
        sender_id=sender_id,
        receiver_id=receiver_id,
        nft_id=nft_id
    )

    #Pending airdrop id with nft
    proto = transaction_record_pb2.PendingAirdropRecord(
        pending_airdrop_id=pending_airdrop_id._to_proto(),
        pending_airdrop_value=basic_types_pb2.PendingAirdropValue(amount=amount)
    )

    record = PendingAirdropRecord._from_proto(proto=proto)

    assert record.pending_airdrop_id.sender_id.shard == sender_id.shard
    assert record.pending_airdrop_id.sender_id.realm == sender_id.realm
    assert record.pending_airdrop_id.sender_id.num == sender_id.num
    assert record.pending_airdrop_id.receiver_id.shard == receiver_id.shard
    assert record.pending_airdrop_id.receiver_id.realm == receiver_id.realm
    assert record.pending_airdrop_id.receiver_id.num == receiver_id.num
    assert record.pending_airdrop_id.nft_id.serial_number == 10
    assert record.pending_airdrop_id.nft_id.token_id.shard == token_id.shard
    assert record.pending_airdrop_id.nft_id.token_id.realm == token_id.realm
    assert record.pending_airdrop_id.nft_id.token_id.num == token_id.num
    assert record.pending_airdrop_id.token_id == None
