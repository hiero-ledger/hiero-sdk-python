import pytest
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token

@pytest.mark.integration
def test_transaction_record_query_can_execute():
    env = IntegrationTestEnv()
    
    try:
        # Generate new key
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create new account
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .execute(env.client)
            )
        assert receipt.status == ResponseCode.SUCCESS, "Account creation failed"
        
        record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)
        
        # Verify transaction details
        assert record.transaction_id == receipt.transaction_id, "Transaction ID should match the queried record"
        assert record.transaction_fee > 0, "Transaction fee should be greater than zero"
        assert record.transaction_memo == "", "Transaction memo should be empty by default"
        assert record.transaction_hash is not None, "Transaction hash should not be None"
    finally:
        env.close()

@pytest.mark.integration
def test_transaction_record_query_can_execute_nft_transfer():
    env = IntegrationTestEnv()
    
    try:
        new_account = env.create_account()
        
        token_id = create_nft_token(env)
        
        # Mint NFTs
        receipt = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_metadata([b"NFT 1", b"NFT 2"])
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"NFT mint failed with status: {ResponseCode(receipt.status).name}"
        serial_numbers = receipt.serial_numbers
        
        assert len(serial_numbers) == 2, "Expected two NFTs to be minted"
        
        # Associate token with new account
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer NFTs
        receipt = (
            TransferTransaction()
            .add_nft_transfer(NftId(token_id, serial_numbers[0]), env.operator_id, new_account.id)
            .add_nft_transfer(NftId(token_id, serial_numbers[1]), env.operator_id, new_account.id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Query the record
        record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)
        
        # Verify NFT transfers
        assert len(record.nft_transfers) == 1
        assert len(record.nft_transfers[token_id]) == 2, "Expected two NFT transfers in the record"
        for i, transfer in enumerate(record.nft_transfers[token_id]):
            assert transfer.sender_id == env.operator_id, "Sender should be the operator account"
            assert transfer.receiver_id == new_account.id, "Receiver should be the new account"
            assert transfer.serial_number == serial_numbers[i], "Serial number should match the minted NFT"
        
        # Verify transaction details
        assert record.transaction_id == receipt.transaction_id, "Transaction ID should match the queried record"
        assert record.transaction_fee > 0, "Transaction fee should be greater than zero"
        assert record.transaction_memo == "", "Transaction memo should be empty by default"
        assert record.transaction_hash is not None, "Transaction hash should not be None"
    finally:
        env.close()

def test_transaction_record_query_can_execute_fungible_transfer():
    env = IntegrationTestEnv()
    
    try:
        new_account = env.create_account()
        
        token_id = create_fungible_token(env)
        
        # Associate token with new account
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer tokens
        transfer_amount = 1000
        receipt = (
            TransferTransaction()
            .add_token_transfer(token_id, env.operator_id, -transfer_amount)
            .add_token_transfer(token_id, new_account.id, transfer_amount)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Query the record
        record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)
        
        # Verify token transfers
        assert len(record.token_transfers) == 1
        assert record.token_transfers[token_id][env.operator_id] == -transfer_amount, "Operator should have sent tokens"
        assert record.token_transfers[token_id][new_account.id] == transfer_amount, "New account should have received tokens"
        
        # Verify transaction details
        assert record.transaction_id == receipt.transaction_id, "Transaction ID should match the queried record"
        assert record.transaction_fee > 0, "Transaction fee should be greater than zero"
        assert record.transaction_memo == "", "Transaction memo should be empty by default"
        assert record.transaction_hash is not None, "Transaction hash should not be None"
    finally:
        env.close()