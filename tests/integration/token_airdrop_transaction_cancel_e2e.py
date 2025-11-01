from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.tokens.token_airdrop_transaction_cancel import TokenCancelAirdropTransaction
import pytest

from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token

#Mint NFT and return serial_number
def mint_nft(env: IntegrationTestEnv, nft_id):
    token_mint_tx = TokenMintTransaction(
        token_id=nft_id,
        metadata=[b"NFT Token"]
    )
    token_mint_tx.freeze_with(env.client)
    token_mint_receipt = token_mint_tx.execute(env.client)
    return token_mint_receipt.serial_numbers[0]

# Perform token airdrop_tx and return list of pending_airdop_records
def airdrop_tokens(env: IntegrationTestEnv, account_id, token_id, nft_id, serial_number):
    airdrop_tx = TokenAirdropTransaction(
        token_transfers=[
            TokenTransfer(token_id, env.client.operator_account_id, -1),
            TokenTransfer(token_id, account_id, 1)
        ],
        nft_transfers=[
            TokenNftTransfer(nft_id, env.client.operator_account_id, account_id, serial_number)
        ]
    )
    airdrop_tx.freeze_with(env.client)
    airdrop_tx.sign(env.client.operator_private_key)
    airdrop_receipt = airdrop_tx.execute(env.client)
    airdrop_record = TransactionRecordQuery(airdrop_receipt.transaction_id).execute(env.client)
    return airdrop_record.new_pending_airdrops

@pytest.mark.integration
def test_integration_token_cancel_airdrop_transaction_can_execute():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        initial_balance = Hbar(2)
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        account_transaction.freeze_with(env.client)
        account_receipt = account_transaction.execute(env.client)
        new_account_id = account_receipt.account_id
        assert new_account_id is not None

        token_id = create_fungible_token(env)
        assert token_id is not None

        nft_id = create_nft_token(env)
        assert nft_id is not None

        # Mint nft and get serial_number
        serial_number = mint_nft(env, nft_id)

        # Perform token airdrop_tx
        pending_airdrop_records = airdrop_tokens(env, new_account_id, token_id, nft_id, serial_number)

        pending_airdrops = []
        for record in pending_airdrop_records:
            pending_airdrops.append(record.pending_airdrop_id)

        cancel_airdrop_tx = TokenCancelAirdropTransaction(pending_airdrops=pending_airdrops)
        cancel_airdrop_tx.freeze_with(env.client)
        cancel_airdrop_tx.sign(env.client.operator_private_key)
        cancel_airdrop_receipt = cancel_airdrop_tx.execute(env.client)

        assert cancel_airdrop_receipt.status == ResponseCode.SUCCESS, f"Token airdrop failed with status: {ResponseCode(cancel_airdrop_receipt.status).name}"
    finally:
        env.close()