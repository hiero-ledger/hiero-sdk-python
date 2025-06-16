from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token


@pytest.mark.integration
def test_integration_token_airdrop_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        initial_balance = Hbar(2)
        
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=initial_balance,
            memo="Recipient Account"
        )
        
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.accountId
        assert account_id is not None
        
        token_id = create_fungible_token(env)
        assert token_id is not None

        nft_id = create_nft_token(env)
        assert nft_id is not None
        
        metadata = [b"NFT Token A"]
        mint_tx = TokenMintTransaction(
            token_id=nft_id,
            metadata=metadata
        )
        
        mint_tx.freeze_with(env.client)
        mint_receipt = mint_tx.execute(env.client)
        serial_number = mint_receipt.serial_numbers[0]

        token_associate_tx = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id, nft_id]
        )
        token_associate_tx.freeze_with(env.client)
        token_associate_tx.sign(new_account_private_key)
        token_associate_tx.execute(env.client)

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

        assert airdrop_receipt.status == ResponseCode.SUCCESS, f"Token airdrop failed with status: {ResponseCode(airdrop_receipt.status).name}"
    finally:
        env.close() 
