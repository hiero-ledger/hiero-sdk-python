import pytest

from hiero_sdk_python.tokens.token_transfer import TokenTransfer

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
