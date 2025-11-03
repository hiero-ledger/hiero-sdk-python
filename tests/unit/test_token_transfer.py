import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.token_transfer_list import TokenTransferList

pytestmark = pytest.mark.unit

def test_token_transfer_constructor(mock_account_ids):
    """Test the TokenTransfer constructor with various parameters"""
    account_id, _, _, token_id, _ = mock_account_ids
    amount = 10
    expected_decimals = 1

    token_transfer = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=amount
    )
    assert token_transfer.token_id == token_id
    assert token_transfer.account_id == account_id
    assert token_transfer.amount == amount
    assert token_transfer.expected_decimals == None
    assert token_transfer.is_approved == False
    
    # Test with explicit excepted_decimals
    decimal_token_transfer = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=amount,
        expected_decimals=expected_decimals
    )
    assert decimal_token_transfer.token_id == token_id
    assert decimal_token_transfer.account_id == account_id
    assert decimal_token_transfer.amount == amount
    assert decimal_token_transfer.expected_decimals == expected_decimals
    assert decimal_token_transfer.is_approved == False
    
    # Test with explicit is_approved=True
    approved_token_transfer = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=amount,
        is_approved=True
    )
    assert approved_token_transfer.token_id == token_id
    assert approved_token_transfer.account_id == account_id
    assert approved_token_transfer.amount == amount
    assert approved_token_transfer.expected_decimals == None
    assert approved_token_transfer.is_approved == True

def test_to_proto(mock_account_ids):
    """Test converting TokenTransfer to protobuf object"""
    account_id, _, _, token_id, _ = mock_account_ids
    amount = 10
    expected_decimals = 1
    is_approved = True
    
    token_transfer = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=amount,
        expected_decimals=expected_decimals,
        is_approved=is_approved
    )

    assert token_transfer.token_id == token_id

    # Convert to protobuf 
    proto = token_transfer._to_proto()

    assert proto.accountID.shardNum == account_id.shard
    assert proto.accountID.realmNum == account_id.realm
    assert proto.accountID.accountNum == account_id.num 
    assert proto.amount == amount
    assert proto.is_approval is is_approved

    # Check for debiting amount
    debiting_token_transfer = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=-amount,
        expected_decimals=expected_decimals,
        is_approved=is_approved
    )

    assert debiting_token_transfer.token_id == token_id

    # Convert to protobuf 
    proto = debiting_token_transfer._to_proto()

    assert proto.accountID.shardNum == account_id.shard
    assert proto.accountID.realmNum == account_id.realm
    assert proto.accountID.accountNum == account_id.num 
    assert proto.amount == -amount
    assert proto.is_approval is is_approved

def test_from_proto(mock_account_ids):
    """Test converting proto to List[TokenTransfer]"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids

    proto = basic_types_pb2.TokenTransferList(
        token=token_id._to_proto(),
        expected_decimals={'value': 1},
        transfers=[
            basic_types_pb2.AccountAmount(accountID=sender_id._to_proto(), amount=-1, is_approval=True),
            basic_types_pb2.AccountAmount(accountID=receiver_id._to_proto(), amount=1, is_approval=True)
        ]
    )

    token_transfer = TokenTransfer._from_proto(proto)

    assert token_transfer[0].token_id == token_id
    assert token_transfer[0].expected_decimals == 1
    assert token_transfer[0].amount == -1
    assert token_transfer[0].account_id == sender_id
    assert token_transfer[0].is_approved == True

    assert token_transfer[1].token_id == token_id
    assert token_transfer[1].expected_decimals == 1
    assert token_transfer[1].amount == 1
    assert token_transfer[1].account_id == receiver_id
    assert token_transfer[1].is_approved == True

def test_from_proto_with_no_token_transfer(mock_account_ids):
    """Test converting proto return empty array if token_transfer not present in proto"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids

    # If only Nft_transfer present
    proto1 = basic_types_pb2.TokenTransferList(
        token=token_id._to_proto(),
        nftTransfers=[
            basic_types_pb2.NftTransfer(
                senderAccountID=sender_id._to_proto(),
                receiverAccountID=receiver_id._to_proto(),
                serialNumber=1,
                is_approval=True
            )
        ]
    )

    token_transfer1 = TokenTransfer._from_proto(proto1)

    assert len(token_transfer1) == 0

    # TokenTransferList is empty
    proto2 = basic_types_pb2.TokenTransferList()
    token_transfer2 = TokenTransfer._from_proto(proto2)

    assert len(token_transfer2) == 0

def test_from_proto_round_trip(mock_account_ids):
    """Test round trip converting proto to List[TokenTransfer]"""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids

    token_transfer_list = TokenTransferList(token=token_id, expected_decimals=1)
    token_transfer_list.add_token_transfer(
        TokenTransfer(token_id=token_id, account_id=sender_id, amount=-1, expected_decimals=1, is_approved=True)
    )
    token_transfer_list.add_token_transfer(
        TokenTransfer(token_id=token_id, account_id=receiver_id, amount=1, expected_decimals=1, is_approved=True)
    )
    token_transfer_proto = token_transfer_list._to_proto()

    token_transfer = TokenTransfer._from_proto(token_transfer_proto)

    assert token_transfer[0].token_id == token_id
    assert token_transfer[0].expected_decimals == 1
    assert token_transfer[0].amount == -1
    assert token_transfer[0].account_id == sender_id
    assert token_transfer[0].is_approved == True

    assert token_transfer[1].token_id == token_id
    assert token_transfer[1].expected_decimals == 1
    assert token_transfer[1].amount == 1
    assert token_transfer[1].account_id == receiver_id
    assert token_transfer[1].is_approved == True
