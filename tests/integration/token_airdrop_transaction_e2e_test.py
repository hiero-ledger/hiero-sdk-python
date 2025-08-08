import pytest

from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token

def _mint_nft(env: IntegrationTestEnv, nft_id):
    token_mint_tx = TokenMintTransaction(
        token_id=nft_id,
        metadata=[b"NFT Token A"]
    )
    token_mint_tx.freeze_with(env.client)
    token_mint_receipt = token_mint_tx.execute(env.client)
    return token_mint_receipt.serial_numbers[0]

def _associate_token_to_account(env: IntegrationTestEnv, account_id, private_key, token_ids):
    token_associate_tx = TokenAssociateTransaction(
        account_id=account_id,
        token_ids=token_ids
    )
    token_associate_tx.freeze_with(env.client)
    token_associate_tx.sign(private_key)
    token_associate_tx.execute(env.client)

@pytest.mark.integration
def test_integration_token_airdrop_transaction_can_execute():
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

        balance_before_tx = CryptoGetAccountBalanceQuery(account_id=new_account_id).execute(env.client)

        token_id = create_fungible_token(env)
        assert token_id is not None

        nft_id = create_nft_token(env)
        assert nft_id is not None

        serial_number =_mint_nft(env, nft_id)

        _associate_token_to_account(env, new_account_id, new_account_private_key, [token_id, nft_id])
        
        airdrop_tx = TokenAirdropTransaction(
            token_transfers=[
                TokenTransfer(token_id, env.client.operator_account_id, -1),
                TokenTransfer(token_id, new_account_id, 1)
            ],
            nft_transfers=[
                TokenNftTransfer(nft_id, env.client.operator_account_id, new_account_id, serial_number)
            ]
        )
        airdrop_tx.freeze_with(env.client)
        airdrop_tx.sign(env.client.operator_private_key)
        airdrop_receipt = airdrop_tx.execute(env.client)

        balance_after_tx = CryptoGetAccountBalanceQuery(account_id=new_account_id).execute(env.client)

        assert airdrop_receipt.status == ResponseCode.SUCCESS, f"Token airdrop failed with status: {ResponseCode(airdrop_receipt.status).name}"
        
        assert balance_before_tx.token_balances == {}
        assert len(balance_after_tx.token_balances) == 2
        
        assert token_id in balance_after_tx.token_balances
        assert balance_after_tx.token_balances[token_id] == 1

        assert nft_id in balance_after_tx.token_balances
        assert balance_after_tx.token_balances[nft_id] == 1
    finally:
        env.close() 
