import pytest

from unittest.mock import MagicMock
from hiero_sdk_python.hapi.services.basic_types_pb2 import AccountAmount, NftTransfer, TokenTransferList
from hiero_sdk_python.hapi.services.token_airdrop_pb2 import TokenAirdropTransactionBody
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

pytestmark = pytest.mark.unit

def test_build_transaction_body(mock_account_ids):
    """Test building the token airdrop transaction body"""
    sender, receiver, node_account_id, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_nft_transfer(nft_id=nft_id, sender_id=sender, receiver_id=receiver)
    airdrop_tx.operator_account_id = sender
    airdrop_tx.node_account_id = node_account_id
    transaction_body = airdrop_tx.build_transaction_body()

    assert len(transaction_body.tokenAirdrop.token_transfers) == 2
    
    token_transfer_1 = transaction_body.tokenAirdrop.token_transfers[0]
    assert token_transfer_1.token.tokenNum == token_id_1.num
    assert token_transfer_1.expected_decimals.value == 0
    assert len(token_transfer_1.transfers) == 2
    assert token_transfer_1.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_1.transfers[0].amount == -amount
    assert token_transfer_1.transfers[0].is_approval == False
    assert token_transfer_1.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_1.transfers[1].amount == amount
    assert token_transfer_1.transfers[1].is_approval == False
    
    token_transfer_2 = transaction_body.tokenAirdrop.token_transfers[1]
    assert token_transfer_2.token.tokenNum == token_id_2.num
    assert len(token_transfer_2.transfers) == 0
    assert len(token_transfer_2.nftTransfers) == 1
    assert token_transfer_2.nftTransfers[0].serialNumber == serial_number
    assert token_transfer_2.nftTransfers[0].senderAccountID.accountNum == sender.num
    assert token_transfer_2.nftTransfers[0].receiverAccountID.accountNum == receiver.num
    assert token_transfer_2.nftTransfers[0].is_approval == False

def test_build_transaction_body_with_approved_transfer(mock_account_ids):
    """Test building the token airdrop transaction body with approved transfers"""
    sender, receiver, node_account_id, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_approved_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_approved_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_approved_nft_transfer(nft_id=nft_id, sender_id=sender, receiver_id=receiver)
    airdrop_tx.operator_account_id = sender
    airdrop_tx.node_account_id = node_account_id
    transaction_body = airdrop_tx.build_transaction_body()

    assert len(transaction_body.tokenAirdrop.token_transfers) == 2
    
    token_transfer_1 = transaction_body.tokenAirdrop.token_transfers[0]
    assert token_transfer_1.token.tokenNum == token_id_1.num
    assert token_transfer_1.expected_decimals.value == 0
    assert len(token_transfer_1.transfers) == 2
    assert token_transfer_1.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_1.transfers[0].amount == -amount
    assert token_transfer_1.transfers[0].is_approval == True
    assert token_transfer_1.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_1.transfers[1].amount == amount
    assert token_transfer_1.transfers[1].is_approval == True
    
    token_transfer_2 = transaction_body.tokenAirdrop.token_transfers[1]
    assert token_transfer_2.token.tokenNum == token_id_2.num
    assert len(token_transfer_2.transfers) == 0
    assert len(token_transfer_2.nftTransfers) == 1
    assert token_transfer_2.nftTransfers[0].serialNumber == serial_number
    assert token_transfer_2.nftTransfers[0].senderAccountID.accountNum == sender.num
    assert token_transfer_2.nftTransfers[0].receiverAccountID.accountNum == receiver.num
    assert token_transfer_2.nftTransfers[0].is_approval == True

def test_build_transaction_body_with_expected_decimal(mock_account_ids):
    """Test building the token airdrop transaction body with expected decimals"""
    sender, receiver, node_account_id, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    decimal = 1
    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer_with_decimals(token_id=token_id_1, account_id=sender, amount=-amount, decimals=decimal)
    airdrop_tx.add_token_transfer_with_decimals(token_id=token_id_1, account_id=receiver, amount=amount, decimals=decimal)
    airdrop_tx.add_approved_token_transfer_with_decimals(token_id=token_id_2, account_id=sender, amount=-amount, decimals=decimal)
    airdrop_tx.add_approved_token_transfer_with_decimals(token_id=token_id_2, account_id=receiver, amount=amount, decimals=decimal)
    airdrop_tx.operator_account_id = sender
    airdrop_tx.node_account_id = node_account_id
    transaction_body = airdrop_tx.build_transaction_body()

    assert len(transaction_body.tokenAirdrop.token_transfers) == 2
    
    token_transfer_1 = transaction_body.tokenAirdrop.token_transfers[0]
    assert token_transfer_1.token.tokenNum == token_id_1.num
    assert token_transfer_1.expected_decimals.value == decimal
    assert len(token_transfer_1.transfers) == 2
    assert token_transfer_1.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_1.transfers[0].amount == -amount
    assert token_transfer_1.transfers[0].is_approval == False
    assert token_transfer_1.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_1.transfers[1].amount == amount
    assert token_transfer_1.transfers[1].is_approval == False

    token_transfer_2 = transaction_body.tokenAirdrop.token_transfers[1]
    assert token_transfer_2.token.tokenNum == token_id_2.num
    assert len(token_transfer_2.transfers) == 2
    assert token_transfer_2.expected_decimals.value == decimal
    assert token_transfer_2.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_2.transfers[0].amount == -amount
    assert token_transfer_2.transfers[0].is_approval == True
    assert token_transfer_2.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_2.transfers[1].amount == amount
    assert token_transfer_2.transfers[1].is_approval == True

def test_add_zero_transfer_amount(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids
    airdrop_tx = TokenAirdropTransaction()

    with pytest.raises(ValueError):
        airdrop_tx.add_token_transfer(token_id, account_id, 0)

    with pytest.raises(ValueError):
        airdrop_tx.add_token_transfer_with_decimals(token_id, account_id, 0, 1)

    with pytest.raises(ValueError):
        airdrop_tx.add_approved_token_transfer(token_id, account_id, 0)
        
    with pytest.raises(ValueError):
        airdrop_tx.add_approved_token_transfer_with_decimals(token_id, account_id, 0, 1)

def test_add_unbalanced_transfer_amount(mock_account_ids):
    sender, receiver, _, token_id, _ = mock_account_ids
    airdrop_tx = TokenAirdropTransaction()
    airdrop_tx.add_token_transfer(token_id, sender, -1)
    airdrop_tx.add_token_transfer(token_id, receiver, -2)

    with pytest.raises(ValueError):
        airdrop_tx.build_transaction_body()

def test_add_invalid_transfer(mock_account_ids):
    _, _, _, _, _ = mock_account_ids
    airdrop_tx = TokenAirdropTransaction()

    with pytest.raises(ValueError):
        airdrop_tx.build_transaction_body()

def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token airdrop transaction with a private key."""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_nft_transfer(nft_id=nft_id, sender_id=sender, receiver_id=receiver)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    # Freeze the transaction
    airdrop_tx.freeze_with(mock_client)
    
    # Sign the transaction
    airdrop_tx.sign(private_key)
    
    node_id = mock_client.network.current_node._account_id
    body_bytes = airdrop_tx._transaction_body_bytes[node_id]

    assert body_bytes in airdrop_tx._signature_map, "Body bytes should be a key in the signature map dictionary"
    assert len(airdrop_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = airdrop_tx._signature_map[body_bytes].sigPair[0]

    assert sig_pair.pubKeyPrefix == b'public_key'  
    assert sig_pair.ed25519 == b'signature'

def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token airdrop transaction to protobuf format after signing."""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_nft_transfer(nft_id=nft_id, sender_id=sender, receiver_id=receiver)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    airdrop_tx.freeze_with(mock_client)

    airdrop_tx.sign(private_key)
    proto = airdrop_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
    
def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token airdrop transaction."""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1
    
    nft_id = NftId(token_id_2, serial_number)
    
    airdrop_tx = TokenAirdropTransaction()
    
    # Add token and NFT transfers
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_nft_transfer(nft_id=nft_id, sender_id=sender, receiver_id=receiver)
    
    schedulable_body = airdrop_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenAirdrop")
    assert len(schedulable_body.tokenAirdrop.token_transfers) == 2
    
    token_transfer_1 = schedulable_body.tokenAirdrop.token_transfers[0]
    assert token_transfer_1.token.tokenNum == token_id_1.num
    assert token_transfer_1.expected_decimals.value == 0
    assert len(token_transfer_1.transfers) == 2
    assert token_transfer_1.transfers[0].accountID == sender._to_proto()
    assert token_transfer_1.transfers[0].amount == -amount
    assert token_transfer_1.transfers[0].is_approval == False
    assert token_transfer_1.transfers[1].accountID == receiver._to_proto()
    assert token_transfer_1.transfers[1].amount == amount
    assert token_transfer_1.transfers[1].is_approval == False
    
    token_transfer_2 = schedulable_body.tokenAirdrop.token_transfers[1]
    assert token_transfer_2.token.tokenNum == token_id_2.num
    assert len(token_transfer_2.transfers) == 0
    assert len(token_transfer_2.nftTransfers) == 1
    assert token_transfer_2.nftTransfers[0].serialNumber == serial_number
    assert token_transfer_2.nftTransfers[0].senderAccountID == sender._to_proto()
    assert token_transfer_2.nftTransfers[0].receiverAccountID == receiver._to_proto()
    assert token_transfer_2.nftTransfers[0].is_approval == False

def test_from_proto(mock_account_ids):
    """Test _from_proto() correctly reconstructs a TokenAirdropTransaction."""
    sender_id, receiver_id, _, token_id1, token_id2 = mock_account_ids

    proto = TokenAirdropTransactionBody()

    proto.token_transfers.append(
        TokenTransferList(
            token=token_id1._to_proto(),
            expected_decimals={'value': 1},
            transfers=[
                AccountAmount(accountID=sender_id._to_proto(), amount=-1, is_approval=True),
                AccountAmount(accountID=receiver_id._to_proto(), amount=1, is_approval=True)
            ]
        )
    )
    proto.token_transfers.append(
        TokenTransferList(
            token=token_id2._to_proto(),
            nftTransfers=[
                NftTransfer(
                    senderAccountID=sender_id._to_proto(),
                    receiverAccountID=receiver_id._to_proto(),
                    serialNumber=1,
                    is_approval=True
                )
            ]
        )
    )

    airdrop_tx = TokenAirdropTransaction._from_proto(proto)

    token_transfer = airdrop_tx.token_transfers[token_id1]
    assert token_transfer[0].token_id == token_id1
    assert token_transfer[0].account_id == sender_id
    assert token_transfer[0].amount == -1
    assert token_transfer[0].expected_decimals == 1
    assert token_transfer[0].is_approved == True

    assert token_transfer[1].token_id == token_id1
    assert token_transfer[1].account_id == receiver_id
    assert token_transfer[1].amount == 1
    assert token_transfer[1].expected_decimals == 1
    assert token_transfer[1].is_approved == True

    nft_transfer = airdrop_tx.nft_transfers[token_id2]
    assert nft_transfer[0].token_id == token_id2
    assert nft_transfer[0].sender_id == sender_id
    assert nft_transfer[0].receiver_id == receiver_id
    assert nft_transfer[0].serial_number == 1
    assert nft_transfer[0].is_approved == True

def test_from_proto_without_nft_transfers(mock_account_ids):
    """Test _from_proto should handle absence of NFT transfers."""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids

    proto = TokenAirdropTransactionBody()

    proto.token_transfers.append(
        TokenTransferList(
            token=token_id._to_proto(),
            expected_decimals={'value': 1},
            transfers=[
                AccountAmount(accountID=sender_id._to_proto(), amount=-1, is_approval=True),
                AccountAmount(accountID=receiver_id._to_proto(), amount=1, is_approval=True)
            ]
        )
    )

    airdrop_tx = TokenAirdropTransaction._from_proto(proto)

    token_transfer = airdrop_tx.token_transfers[token_id];
    assert token_transfer[0].token_id == token_id
    assert token_transfer[0].account_id == sender_id
    assert token_transfer[0].amount == -1
    assert token_transfer[0].expected_decimals == 1
    assert token_transfer[0].is_approved == True

    assert token_transfer[1].token_id == token_id
    assert token_transfer[1].account_id == receiver_id
    assert token_transfer[1].amount == 1
    assert token_transfer[1].expected_decimals == 1
    assert token_transfer[1].is_approved == True

    assert not airdrop_tx.nft_transfers

def test_from_proto_without_token_transfer(mock_account_ids):
    """_from_proto should handle absence of token transfers."""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids

    proto = TokenAirdropTransactionBody()

    proto.token_transfers.append(
        TokenTransferList(
            token=token_id._to_proto(),
            nftTransfers=[
                NftTransfer(
                    senderAccountID=sender_id._to_proto(),
                    receiverAccountID=receiver_id._to_proto(),
                    serialNumber=1,
                    is_approval=True
                )
            ]
        )
    )

    airdrop_tx = TokenAirdropTransaction._from_proto(proto)

    nft_transfer = airdrop_tx.nft_transfers[token_id]
    assert nft_transfer[0].token_id == token_id
    assert nft_transfer[0].sender_id == sender_id
    assert nft_transfer[0].receiver_id == receiver_id
    assert nft_transfer[0].serial_number == 1
    assert nft_transfer[0].is_approved == True

    assert not airdrop_tx.token_transfers
