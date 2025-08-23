import pytest

from hiero_sdk_python import Duration
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token

@pytest.mark.integration
def test_integration_account_info_query_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()
        account_memo = "Test account memo"
        
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .set_account_memo(account_memo)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        new_account_id = receipt.account_id
        
        info = AccountInfoQuery(new_account_id).execute(env.client)
        
        assert str(info.account_id) == str(new_account_id), f"Expected account ID {new_account_id}, but got {info.account_id}"
        assert info.balance.to_tinybars() == Hbar(1).to_tinybars(), f"Expected balance of 1 Hbar, but got {info.balance}"
        assert info.key.to_bytes_raw() == new_account_public_key.to_bytes_raw(), f"Expected public key {new_account_public_key}, but got {info.key}"
        assert info.receiver_signature_required == False, "Expected receiver signature to not be required, but it was"
        assert info.auto_renew_period == Duration(7890000), f"Expected auto renew period of 7890000 seconds, but got {info.auto_renew_period}"
        assert info.expiration_time is not None, "Expected expiration time to be set, but it was None"
        assert info.account_memo == account_memo, f"Expected account memo '{account_memo}', but got '{info.account_memo}'"
        assert info.owned_nfts == 0, f"Expected 0 owned NFTs, but got {info.owned_nfts}"
        assert info.is_deleted == False, "Expected account to not be deleted, but it was"
        assert info.proxy_received.to_tinybars() == 0, f"Expected 0 proxy received tinybars, but got {info.proxy_received.to_tinybars()}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_account_info_query_fails_with_invalid_account_id():
    env = IntegrationTestEnv()
    
    try:
        # Use a non-existent account ID
        account_id = AccountId(0, 0, 123456789)
        
        with pytest.raises(PrecheckError, match="failed precheck with status: INVALID_ACCOUNT_ID"):
            AccountInfoQuery(account_id).execute(env.client)
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_account_info_query_token_relationship_info():
    env = IntegrationTestEnv()
    
    try:
        new_account = env.create_account()
        
        # Create token with kyc key and freeze default and associate it with the new account
        token_id = create_fungible_token(env, 
                                         [lambda tx: tx.set_kyc_key(env.operator_key), 
                                          lambda tx: tx.set_freeze_default(False)]) #Must not be frozen for token operations
        
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token associate failed with status: {ResponseCode(receipt.status).name}"
        
        # Get account info and verify token relationship
        info = AccountInfoQuery(new_account.id).execute(env.client)
        
        assert len(info.token_relationships) == 1, f"Expected 1 token relationship, but got {len(info.token_relationships)}"
        relationship = info.token_relationships[0]
        assert relationship.token_id == token_id, f"Expected token ID {token_id}, but got {relationship.token_id}"
        assert relationship.freeze_status == TokenFreezeStatus.UNFROZEN, f"Expected freeze status to be UNFROZEN, but got {relationship.freeze_status}"
        assert relationship.kyc_status == TokenKycStatus.REVOKED, f"Expected KYC status to be REVOKED, but got {relationship.kyc_status}"
        assert relationship.balance == 0, f"Expected balance to be 0, but got {relationship.balance}"
        assert relationship.symbol == "PTT34", f"Expected symbol 'PTT34', but got {relationship.symbol}"
        assert relationship.decimals == 2, f"Expected decimals to be 2, but got {relationship.decimals}"
        assert relationship.automatic_association == False, f"Expected automatic association to be False, but got {relationship.automatic_association}"
        
        # Unfreeze account for token
        receipt = (
            TokenUnfreezeTransaction()
            .set_account_id(new_account.id)
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token freeze failed with status: {ResponseCode(receipt.status).name}"
        
        # Grant KYC to account
        receipt = (
            TokenGrantKycTransaction()
            .set_account_id(new_account.id)
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"KYC grant failed with status: {ResponseCode(receipt.status).name}"
        
        # Get updated account info and verify changes
        info = AccountInfoQuery(new_account.id).execute(env.client)
        
        assert len(info.token_relationships) == 1, f"Expected 1 token relationship, but got {len(info.token_relationships)}"
        relationship = info.token_relationships[0]
        assert relationship.token_id == token_id, f"Expected token ID {token_id}, but got {relationship.token_id}"
        assert relationship.freeze_status == TokenFreezeStatus.UNFROZEN, f"Expected freeze status to be UNFROZEN, but got {relationship.freeze_status}"
        assert relationship.kyc_status == TokenKycStatus.GRANTED, f"Expected KYC status to be GRANTED, but got {relationship.kyc_status}"
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_account_info_query_token_relationships_length():
    env = IntegrationTestEnv()
    
    try:
        new_account = env.create_account()
        
        # Create first token with decimals set to 8 and associate it with the new account
        decimals_token_id = create_fungible_token(env, [lambda tx: tx.set_decimals(8), lambda tx: tx.set_kyc_key(env.operator_key)])
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(decimals_token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token associate failed with status: {ResponseCode(receipt.status).name}"
        
        info = AccountInfoQuery(new_account.id).execute(env.client)
        
        assert len(info.token_relationships) == 1, f"Expected 1 token relationship, but got {len(info.token_relationships)}"
        assert info.token_relationships[0].decimals == 8, f"Expected decimals to be 8, but got {info.token_relationships[0].decimals}"
        
        # Create second token with default decimals and associate it with the new account
        default_decimals_token_id = create_fungible_token(env)
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(default_decimals_token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token associate failed with status: {ResponseCode(receipt.status).name}"
        
        # Check account info has two token relationships and the first relationship is the second token
        info = AccountInfoQuery(new_account.id).execute(env.client)
        
        assert len(info.token_relationships) == 2, f"Expected 2 token relationships, but got {len(info.token_relationships)}"
        assert info.token_relationships[0].decimals == 2, f"Expected decimals to be 2, but got {info.token_relationships[0].decimals}"
        assert info.token_relationships[1].decimals == 8, f"Expected decimals to be 8, but got {info.token_relationships[1].decimals}"
        
        # Dissociate both tokens
        receipt = (
            TokenDissociateTransaction()
            .set_account_id(new_account.id)
            .add_token_id(default_decimals_token_id)
            .add_token_id(decimals_token_id)
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token dissociate failed with status: {ResponseCode(receipt.status).name}"
        
        # Check account info has no token relationships
        info = AccountInfoQuery(new_account.id).execute(env.client)
        assert str(info.account_id) == str(new_account.id), f"Expected account ID {new_account.id}, but got {info.account_id}"
        assert len(info.token_relationships) == 0, f"Expected 0 token relationships, but got {len(info.token_relationships)}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_account_info_query_nft_owned():
    env = IntegrationTestEnv()
    
    try:
        new_account = env.create_account()
        
        # Create NFT token for the new account
        token_id = create_nft_token(env, [
            lambda tx: tx.set_treasury_account_id(new_account.id),
            lambda tx: tx.freeze_with(env.client).sign(new_account.key)
        ])
        
        # Check initial NFT count is 0
        info = AccountInfoQuery(new_account.id).execute(env.client)
        assert info.owned_nfts == 0, f"Expected 0 owned NFTs, but got {info.owned_nfts}"

        # Mint and transfer NFTs to account
        receipt = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_metadata([b"nft1", b"nft2"])
            .freeze_with(env.client)
            .sign(new_account.key)
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token mint failed with status: {ResponseCode(receipt.status).name}"
        serial_numbers = receipt.serial_numbers
        assert len(serial_numbers) == 2, f"Expected 2 serial numbers, but got {len(serial_numbers)}"

        # Check NFT count is now 2
        info = AccountInfoQuery(new_account.id).execute(env.client)
        assert info.owned_nfts == 2, f"Expected 2 owned NFTs, but got {info.owned_nfts}"
    finally:
        env.close()