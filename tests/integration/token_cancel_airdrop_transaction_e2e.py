from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.tokens.token_cancel_airdrop_transaction import TokenCancelAirdropTransaction
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

# ===== 1. Create Dummy Fungible Token =====
fungible_create = (
    TokenCreateTransaction()
    .set_token_name("Test Fungible")
    .set_token_symbol("TFUNG")
    .set_token_type(TokenType.FUNGIBLE_COMMON)
    .set_initial_supply(1000000)
    .set_treasury_account_id(env.client.operator_account_id)
)
fungible_receipt = (
    fungible_create
    .freeze_with(env.client)
    .sign(env.client.operator_key)
    .execute(env.client)
    .get_receipt(env.client)
)
fungible_token_id = fungible_receipt.token_id

# ===== 2. Create Dummy NFT Collection =====
# Generate a supply key (for minting NFTs)
nft_supply_key = PrivateKey.generate("ed25519")

nft_create = (
    TokenCreateTransaction()
    .set_token_name("Test NFT")
    .set_token_symbol("TNFT")
    .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
    .set_initial_supply(0)  # NFT must be 0
    .set_supply_key(nft_supply_key)
    .set_treasury_account_id(env.client.operator_account_id)
)
nft_receipt = (
    nft_create
    .freeze_with(env.client)
    .sign(env.client.operator_key)
    .sign(nft_supply_key)
    .execute(env.client)
    .get_receipt(env.client)
)
nft_token_id = nft_receipt.token_id

# ===== 3. Mint One NFT in the Collection =====
metadata = [b"TEST_NFT_METADATA"]
nft_mint_receipt = (
    TokenMintTransaction()
    .set_token_id(nft_token_id)
    .set_metadata(metadata)
    .freeze_with(env.client)
    .sign(nft_supply_key)
    .execute(env.client)
    .get_receipt(env.client)
)

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

@pytest.mark.integration
def test_get_airdrop_contents_returns_correct_transfers():
    env = IntegrationTestEnv()

    try:
        
        token_id = create_fungible_token(env)  
        nft_token_id = create_nft_token(env) 
        account_sender = env.client.operator_account_id
        account_receiver = AccountId.from_string("0.0.1001")
        # Mint an NFT for this token
        serial_number = mint_nft(env, nft_token_id)
        nft_id = NftId(token_id=nft_token_id, serial_number=serial_number)


        # Create TokenAirdropTransaction and add transfers
        tx = TokenAirdropTransaction()
        tx.add_token_transfer(token_id=token_id, account_id=account_sender, amount=-10)
        tx.add_token_transfer(token_id=token_id, account_id=account_receiver, amount=10)
        tx.add_nft_transfer(nft_id=nft_id, sender=account_sender, receiver=account_receiver)

        # Get planned transfers
        contents = tx.get_airdrop_contents()

        fungible = [c for c in contents if c["type"] == "fungible"]
        nft = [c for c in contents if c["type"] == "nft"]

        # Assertions
        assert len(fungible) == 2
        assert len(nft) == 1

        assert fungible[0]["token_id"] == str(token_id)
        assert fungible[1]["account_id"] == str(account_receiver)
        assert fungible[0]["amount"] == -10

        assert nft[0]["token_id"] == str(nft_token_id)
        assert nft[0]["serial_number"] == 1
        assert nft[0]["sender"] == str(account_sender)
        assert nft[0]["receiver"] == str(account_receiver)

    finally:
        env.close()
