import pytest

from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.token_transfer_list import TokenTransferList

pytestmark = pytest.mark.unit

def test_token_transfer_list_constructor(mock_account_ids):
    """Test TokenTransferList constructor with various parameters"""
    account_id1, account_id2, _, token_id, _ = mock_account_ids
    expected_decimals = 1
    transfers = [TokenTransfer(token_id, account_id1, 10)]
    nft_transfers = [TokenNftTransfer(token_id, account_id1, account_id2, 10)]
    
    token_transfer_list = TokenTransferList(
        token=token_id,
    )
    assert token_transfer_list.token == token_id
    assert token_transfer_list.expected_decimals == None
    assert token_transfer_list.transfers == []
    assert token_transfer_list.nft_transfers == []

    #Test with explicit expected_decimals
    decimal_token_transfer_list = TokenTransferList(
        token=token_id,
        expected_decimals=expected_decimals
    )
    assert decimal_token_transfer_list.token == token_id
    assert decimal_token_transfer_list.expected_decimals == expected_decimals
    assert decimal_token_transfer_list.transfers == []
    assert decimal_token_transfer_list.nft_transfers == []

    #Test with explicit transfers
    transfers_token_transfer_list = TokenTransferList(
        token=token_id,
        transfers=transfers
    )
    assert transfers_token_transfer_list.token == token_id
    assert transfers_token_transfer_list.expected_decimals == None
    assert transfers_token_transfer_list.transfers == transfers
    assert transfers_token_transfer_list.nft_transfers == []

    #Test with explicit nft_transfers
    nft_transfers_token_transfer_list = TokenTransferList(
        token=token_id,
        nft_transfers=nft_transfers
    )
    assert nft_transfers_token_transfer_list.token == token_id
    assert nft_transfers_token_transfer_list.expected_decimals == None
    assert nft_transfers_token_transfer_list.transfers == []
    assert nft_transfers_token_transfer_list.nft_transfers == nft_transfers

def test_token_transfer_list_add_token_transfer(mock_account_ids):
    """Test TokenTransferList add_token_transfer function"""
    account_id, _, _, token_id, _ = mock_account_ids
    transfer = TokenTransfer(token_id, account_id, 10)

    token_transfer_list = TokenTransferList(
        token=token_id,
    )

    token_transfer_list.add_token_transfer(transfer)

    assert token_transfer_list.transfers is not None
    assert token_transfer_list.transfers == [transfer]

def test_token_transfer_list_add_nft_transfer(mock_account_ids):
    """Test TokenTransferList add_nft_transfer function"""
    account_id1, account_id2, _, token_id, _ = mock_account_ids
    transfer = TokenNftTransfer(token_id, account_id1, account_id2, 10)

    token_transfer_list = TokenTransferList(
        token=token_id,
    )

    token_transfer_list.add_nft_transfer(transfer)

    assert token_transfer_list.nft_transfers is not None
    assert token_transfer_list.nft_transfers == [transfer]

def test_to_proto(mock_account_ids):
    """Test converting TokenTransferList to protobuf object"""
    sender_id, receiver_id, _, token_id_1, token_id_2 = mock_account_ids
    expected_decimals = 1
    transfers = [TokenTransfer(token_id_1, sender_id, -10), TokenTransfer(token_id_1, receiver_id, 10)]
    nft_transfers = [TokenNftTransfer(token_id_2, sender_id, receiver_id, 1)]
    
    
    token_transfer_list = TokenTransferList(
        token=token_id_1,
        transfers=transfers,
        expected_decimals=expected_decimals
    )

    # Convert to protobuf 
    proto = token_transfer_list._to_proto()

    assert proto.token.shardNum == token_id_1.shard
    assert proto.token.realmNum == token_id_1.realm
    assert proto.token.tokenNum == token_id_1.num 
    assert proto.expected_decimals.value == expected_decimals
    assert len(proto.transfers) == 2
    assert len(proto.nftTransfers) == 0
    assert proto.transfers[0].accountID.accountNum == sender_id.num
    assert proto.transfers[0].amount == -10
    assert proto.transfers[1].accountID.accountNum == receiver_id.num
    assert proto.transfers[1].amount == 10

    # Check for NFT Transfer
    nft_transfer_list = TokenTransferList(
        token=token_id_2,
        nft_transfers=nft_transfers,
    )

    # Convert to protobuf 
    proto = nft_transfer_list._to_proto()

    assert proto.token.shardNum == token_id_2.shard
    assert proto.token.realmNum == token_id_2.realm
    assert proto.token.tokenNum == token_id_2.num 
    assert proto.expected_decimals.value == 0
    assert len(proto.transfers) == 0
    assert len(proto.nftTransfers) == 1
    assert proto.nftTransfers[0].senderAccountID.accountNum == sender_id.num
    assert proto.nftTransfers[0].receiverAccountID.accountNum == receiver_id.num
    assert proto.nftTransfers[0].serialNumber == 1