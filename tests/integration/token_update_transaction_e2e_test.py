import datetime
import pytest

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from tests.integration.utils import IntegrationTestEnv, create_fungible_token, create_nft_token

private_key = PrivateKey.generate()

@pytest.mark.integration
def test_integration_token_update_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        auto_renew_period = Duration(2592000)
        
        receipt = (
           TokenUpdateTransaction()
           .set_token_id(token_id)
           .set_token_name("UpdatedName")
           .set_token_symbol("UPD")
           .set_auto_renew_period(auto_renew_period)
           .set_freeze_key(private_key)
           .freeze_with(env.client)
           .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        
        assert info.name == "UpdatedName", "Token failed to update"
        assert info.symbol == "UPD", "Token symbol failed to update"
        assert info.auto_renew_period == auto_renew_period, "Token auto_renew_period failed to update"
        assert info.freeze_key.to_bytes_raw() == private_key.public_key().to_bytes_raw(), "Freeze key did not update correctly"
        assert info.admin_key.to_bytes_raw() == env.public_operator_key.to_bytes_raw(), "Admin key mismatch after update"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_preserves_fields_without_updating_parameters():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        original_info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        
        assert info.name == original_info.name, "Token name should not have changed"
        assert info.symbol == original_info.symbol, "Token symbol should not have changed"
        assert info.memo == original_info.memo, "Token memo should not have changed"
        assert info.metadata == original_info.metadata, "Token metadata should not have changed"
        assert info.treasury == original_info.treasury, "Token treasury should not have changed"
        assert info.auto_renew_period == original_info.auto_renew_period, "Token auto renew period should not have been changed"
        assert info.auto_renew_account == original_info.auto_renew_account, "Token auto renew account should not have been changed"
        assert info.expiry == original_info.expiry, "Token expiry should not have been changed"
        assert info.admin_key.to_bytes_raw() == original_info.admin_key.to_bytes_raw(), "Admin key should not have changed"
        assert info.freeze_key.to_bytes_raw() == original_info.freeze_key.to_bytes_raw(), "Freeze key should not have changed"
        assert info.wipe_key.to_bytes_raw() == original_info.wipe_key.to_bytes_raw(), "Wipe key should not have changed"
        assert info.supply_key.to_bytes_raw() == original_info.supply_key.to_bytes_raw(), "Supply key should not have changed"
        assert info.kyc_key is None, "Kyc key should not have changed"
        assert info.fee_schedule_key is None, "Fee Schedule key should not have changed"
        assert info.pause_key is None, "Pause key should not have changed"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_different_keys():
    env = IntegrationTestEnv()
    
    try:
        # Generate 8 key pairs
        keys = [PrivateKey.generate() for _ in range(8)]
        
        # Create new account with first key
        tx = (
            AccountCreateTransaction()
            .set_key(keys[0].public_key())
            .set_initial_balance(Hbar(2))
        )
        receipt = tx.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Create fungible token with initial metadata and pause keys both set to the first key
        token_id = create_fungible_token(env, opts=[
            lambda tx: tx.set_metadata_key(keys[0]),
            lambda tx: tx.set_pause_key(keys[0]),
            lambda tx: tx.set_kyc_key(keys[0]),
            lambda tx: tx.set_fee_schedule_key(keys[0])
        ])
        
        # Update token with different keys
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_name("UpdatedName")
            .set_token_symbol("UPD")
            .set_treasury_account_id(env.operator_id)
            .set_admin_key(env.operator_key)
            .set_freeze_key(keys[1])
            .set_wipe_key(keys[2])
            .set_supply_key(keys[3])
            .set_metadata_key(keys[4])
            .set_pause_key(keys[5])
            .set_kyc_key(keys[6])
            .set_fee_schedule_key(keys[7])
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify updates
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        
        assert info.name == "UpdatedName", "Token name mismatch"
        assert info.symbol == "UPD", "Token symbol mismatch"
        assert info.freeze_key.to_bytes_raw() == keys[1].public_key().to_bytes_raw(), "Freeze key mismatch"
        assert info.wipe_key.to_bytes_raw() == keys[2].public_key().to_bytes_raw(), "Wipe key mismatch"
        assert info.supply_key.to_bytes_raw() == keys[3].public_key().to_bytes_raw(), "Supply key mismatch"
        assert info.metadata_key.to_bytes_raw() == keys[4].public_key().to_bytes_raw(), "Metadata key mismatch"
        assert info.pause_key.to_bytes_raw() == keys[5].public_key().to_bytes_raw(), "Pause key mismatch"
        assert info.kyc_key.to_bytes_raw() == keys[6].public_key().to_bytes_raw(), "Kyc key mismatch"
        assert info.fee_schedule_key.to_bytes_raw() == keys[7].public_key().to_bytes_raw(), "Fee Schedule key mismatch"
        assert info.admin_key.to_bytes_raw() == env.public_operator_key.to_bytes_raw(), "Admin key mismatch"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_treasury():
    env = IntegrationTestEnv()
    
    try:
        # Generate new key and create new account
        new_private_key = PrivateKey.generate()
        new_public_key = new_private_key.public_key()
        
        receipt = (
            AccountCreateTransaction()
            .set_key(new_public_key)
            .set_initial_balance(Hbar(2))
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode.get_name(receipt.status)}"
        account_id = receipt.account_id
        
        # Create fungible token
        token_id = create_fungible_token(env)
        
        tx = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .add_token_id(token_id)
            .freeze_with(env.client)
        )
        receipt = tx.sign(new_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Update token with new treasury account
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_symbol("UPD")
            .set_treasury_account_id(account_id)
            .freeze_with(env.client)
            .sign(new_private_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify updates
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        
        assert info.symbol == "UPD", "Token symbol mismatch"
        assert info.treasury == account_id, "Treasury account mismatch"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_fail_invalid_token_id():
    env = IntegrationTestEnv()
        
    try:
        token_id = TokenId(1, 1, 999999999)
        tx = TokenUpdateTransaction(token_id=token_id)

        receipt = tx.execute(env.client)
        
        assert receipt.status == ResponseCode.INVALID_TOKEN_ID, f"Token update should have failed with INVALID_TOKEN_ID status but got: {ResponseCode.get_name(receipt.status)}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_fungible_metadata():
    env = IntegrationTestEnv()
    
    try:
        new_metadata = b"Updated metadata"
        
        # Create token with initial metadata (empty)
        token_id = create_fungible_token(env)
        
        # Query initial token info and verify metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"
        
        # Update token with new metadata
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(new_metadata)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify updated metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == new_metadata, "Updated metadata mismatch"
        
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_nft_metadata():
    env = IntegrationTestEnv()
    
    try:
        new_metadata = b"Updated metadata"
        
        # Create NFT with initial metadata
        token_id = create_nft_token(env)
        
        # Query initial token info and verify metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"
        
        # Update token with new metadata
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(new_metadata)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify updated metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == new_metadata, "Updated metadata mismatch"
        
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_metadata_immutable_fungible_token():
    env = IntegrationTestEnv()
    
    try:
        new_metadata = b"Updated metadata"
        
        # Generate metadata key
        metadata_key = PrivateKey.generate()
        
        # Create fungible token with metadata key but no admin key
        token_id = create_fungible_token(env, opts=[
            lambda tx: tx.set_metadata_key(metadata_key),
            lambda tx: tx.set_admin_key(None)
        ])
        
        # Query initial token info and verify metadata and keys
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"
        assert info.metadata_key.to_bytes_raw() == metadata_key.public_key().to_bytes_raw(), "Metadata key mismatch"
        assert info.admin_key is None, "Admin key should be None"
        
        # Update token with new metadata, signed by metadata key
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(new_metadata)
            .freeze_with(env.client)
            .sign(metadata_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify updated metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == new_metadata, "Updated metadata mismatch"
        
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_metadata_immutable_nft():
    env = IntegrationTestEnv()
    
    try:
        new_metadata = b"Updated metadata"
        
        # Generate metadata key
        metadata_key = PrivateKey.generate()
        
        # Create NFT token with metadata key but no admin key
        token_id = create_nft_token(env, [
            lambda tx: tx.set_metadata_key(metadata_key),
            lambda tx: tx.set_admin_key(None)
        ])
        
        # Query initial token info and verify metadata and keys
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"
        assert info.metadata_key.to_bytes_raw() == metadata_key.public_key().to_bytes_raw(), "Metadata key mismatch"
        assert info.admin_key is None, "Admin key should be None"
        
        # Update token with new metadata, signed by metadata key
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(new_metadata)
            .freeze_with(env.client)
            .sign(metadata_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify updated metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == new_metadata, "Updated metadata mismatch"
        
    finally:
        env.close()

@pytest.mark.integration
def test_token_update_transaction_cannot_update_metadata_fungible():
    env = IntegrationTestEnv()
    
    try:
        # Create fungible token with initial metadata
        token_id = create_fungible_token(env)
        
        # Query initial token info and verify metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"
        
        # Try to update token with new memo, metadata should remain unchanged
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_memo("updated memo")
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify metadata remains unchanged
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Metadata should not have changed"
        
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_cannot_update_metadata_nft():
    env = IntegrationTestEnv()
    
    try:
        # Create NFT token with initial metadata
        token_id = create_nft_token(env)
        
        # Query initial token info and verify metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"
        
        # Try to update token with new memo, metadata should remain unchanged
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_memo("asdf")
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query token info and verify metadata remains unchanged
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Metadata should not have changed"
        
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_erase_metadata_fungible_token():
    env = IntegrationTestEnv()

    try:
        # Create fungible token with initial metadata
        token_id = create_fungible_token(env)

        # Query initial token info and verify metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"

        # Update token with empty metadata
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(b"")
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"

        # Query token info and verify metadata was erased
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Metadata should have been erased"

    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_erase_metadata_nft():
    env = IntegrationTestEnv()

    try:
        # Create NFT token with initial metadata
        token_id = create_nft_token(env)

        # Query initial token info and verify metadata
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Initial metadata mismatch"

        # Update token with empty metadata
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(b"")
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"

        # Query token info and verify metadata was erased
        info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        assert info.metadata == b"", "Metadata should have been erased"

    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_cannot_update_metadata_without_key_fungible():
    env = IntegrationTestEnv()
    
    try:
        # Generate metadata and admin keys
        metadata_key = PrivateKey.generate()
        admin_key = PrivateKey.generate()
        
        # Create fungible token with metadata key
        token_id = create_fungible_token(env, [
            lambda tx: tx.set_admin_key(admin_key),
            lambda tx: tx.set_metadata_key(metadata_key),
            lambda tx: tx.freeze_with(env.client).sign(admin_key)
        ])
        
        # Try to update metadata without signing with metadata key
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(b"New metadata")
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.INVALID_SIGNATURE, f"Token update should have failed with INVALID_SIGNATURE status but got: {ResponseCode.get_name(receipt.status)}"
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_update_transaction_cannot_update_metadata_without_key_nft():
    env = IntegrationTestEnv()

    try:
        # Generate metadata and admin keys
        metadata_key = PrivateKey.generate()
        admin_key = PrivateKey.generate()

        # Create NFT token with metadata key
        token_id = create_nft_token(env, [
            lambda tx: tx.set_admin_key(admin_key),
            lambda tx: tx.set_supply_key(admin_key), 
            lambda tx: tx.set_metadata_key(metadata_key),
            lambda tx: tx.freeze_with(env.client).sign(admin_key)
        ])

        # Try to update metadata without signing with metadata key
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(b"New metadata")
            .execute(env.client)
        )

        assert receipt.status == ResponseCode.INVALID_SIGNATURE, f"Token update should have failed with INVALID_SIGNATURE status but got: {ResponseCode.get_name(receipt.status)}"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_update_transaction_cannot_update_immutable_fungible_token():
    env = IntegrationTestEnv()
    
    try:
        # Create fungible token with no admin or metadata keys (immutable)
        token_id = create_fungible_token(env, [
            lambda tx: tx.set_admin_key(None),
            lambda tx: tx.set_metadata_key(None)
        ])
        
        # Try to update metadata on immutable token
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_metadata(b"New metadata")
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.TOKEN_IS_IMMUTABLE, f"Token update should have failed with TOKEN_IS_IMMUTABLE status but got: {ResponseCode.get_name(receipt.status)}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_transaction_cannot_update_immutable_nft():
    env = IntegrationTestEnv()
    
    try:
        # Create NFT token with no admin or metadata keys (immutable)
        nft_token_id = create_nft_token(env, [
            lambda tx: tx.set_admin_key(None),
            lambda tx: tx.set_metadata_key(None)
        ])
        
        # Try to update metadata on immutable token
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(nft_token_id)
            .set_metadata(b"New metadata")
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.TOKEN_IS_IMMUTABLE, f"Token update should have failed with TOKEN_IS_IMMUTABLE status but got: {ResponseCode.get_name(receipt.status)}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_auto_renew_account():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)

        old_info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )

        # Update auto renew account
        recipient = env.create_account(1)

        receipt = (
           TokenUpdateTransaction()
           .set_token_id(token_id)
           .set_auto_renew_account_id(recipient.id)
           .freeze_with(env.client)
           .sign(recipient.key)
           .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        new_info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )
        
        assert new_info.auto_renew_account == recipient.id, "Updated auto_renew_account mismatch"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_update_expiration_time():
    env = IntegrationTestEnv()
    auto_renew_period = Duration(2592000) # 30 days
    try:
        token_id = create_fungible_token(env, [lambda tx: tx.set_auto_renew_period(auto_renew_period)])

        old_info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )

        # Update expiration time, makesure new expiration time must be greater than old one
        # Old expiration will be around ~30 days based on autoRenewPeriod
        expiration_time = Timestamp.from_date(datetime.datetime.now() + datetime.timedelta(days=50))
        receipt = (
           TokenUpdateTransaction()
           .set_token_id(token_id)
           .set_expiration_time(expiration_time)
           .freeze_with(env.client)
           .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        new_info = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .execute(env.client)
        )

        assert new_info.expiry.seconds > old_info.expiry.seconds, "Updated expiry must be greater"
        assert new_info.expiry.seconds == expiration_time.seconds, "Updated expiry mismatch"
    finally:
        env.close()

def test_integration_token_update_kyc_key_fungible_token():
    env = IntegrationTestEnv()
    admin_key = PrivateKey.generate()
    kyc_key = PrivateKey.generate()

    try:
        token_id = create_fungible_token(env, [
            lambda tx: tx.set_admin_key(admin_key),
            lambda tx: tx.set_kyc_key(kyc_key),
            lambda tx: tx.freeze_with(env.client).sign(admin_key).sign(kyc_key)
        ])
        
        recipient = env.create_account(1);
        association_receipt = (
            TokenAssociateTransaction(account_id=recipient.id, token_ids=[token_id])
            .freeze_with(env.client)
            .sign(env.client.operator_private_key)
            .sign(recipient.key)
            .execute(env.client)
        )
        assert association_receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode.get_name(association_receipt.status)}"
        # Update Kyc Key
        new_kyc_key = PrivateKey.generate()
        
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_kyc_key(new_kyc_key)
            .freeze_with(env.client)
            .sign(admin_key)
            .sign(new_kyc_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"

        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
        assert token_info.kyc_key.to_string() == new_kyc_key.public_key().to_string(), "Updated kyc_key mismatch"

        # Verify that kyc key work
        kyc_receipt = (
            TokenGrantKycTransaction(token_id=token_id)
            .set_account_id(recipient.id)
            .freeze_with(env.client)
            .sign(new_kyc_key)
            .sign(env.client.operator_private_key)
            .execute(env.client)
        )
        assert kyc_receipt.status == ResponseCode.SUCCESS, f"Token grant kyc failed with status: {ResponseCode.get_name(kyc_receipt.status)}"
        
    finally:
        env.close()

def test_integration_token_update_kyc_key_nft():
    env = IntegrationTestEnv()
    admin_key = PrivateKey.generate()
    kyc_key = PrivateKey.generate()

    try:
        token_id = create_nft_token(env, [
            lambda tx: tx.set_admin_key(admin_key),
            lambda tx: tx.set_kyc_key(kyc_key),
            lambda tx: tx.freeze_with(env.client).sign(admin_key).sign(kyc_key)
        ])
        
        recipient = env.create_account(1);
        association_receipt = (
            TokenAssociateTransaction(account_id=recipient.id, token_ids=[token_id])
            .freeze_with(env.client)
            .sign(env.client.operator_private_key)
            .sign(recipient.key)
            .execute(env.client)
        )
        assert association_receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode.get_name(association_receipt.status)}"
        
        # Update Kyc Key
        new_kyc_key = PrivateKey.generate()
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_kyc_key(new_kyc_key)
            .freeze_with(env.client)
            .sign(admin_key)
            .sign(new_kyc_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"

        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
        assert token_info.kyc_key.to_string() == new_kyc_key.public_key().to_string(), "Updated kyc_key mismatch"

        # Verify that kyc key work
        kyc_receipt = (
            TokenGrantKycTransaction(token_id=token_id)
            .set_account_id(recipient.id)
            .freeze_with(env.client)
            .sign(new_kyc_key)
            .sign(env.client.operator_private_key)
            .execute(env.client)
        )
        assert kyc_receipt.status == ResponseCode.SUCCESS, f"Token grant kyc failed with status: {ResponseCode.get_name(kyc_receipt.status)}"
        
    finally:
        env.close()

def test_integation_token_update_fee_schedule_key_fungible_token():
    env = IntegrationTestEnv()
    admin_key = PrivateKey.generate()
    fee_schedule_key = PrivateKey.generate()

    try:
        token_id = create_fungible_token(env, [
            lambda tx: tx.set_admin_key(admin_key),
            lambda tx: tx.set_fee_schedule_key(fee_schedule_key),
            lambda tx: tx.freeze_with(env.client).sign(admin_key)
        ])
        
        # Update Fee Schedule Key
        new_fee_schedule_key = PrivateKey.generate()
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_fee_schedule_key(new_fee_schedule_key)
            .freeze_with(env.client)
            .sign(admin_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"

        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
        assert token_info.fee_schedule_key.to_string() == new_fee_schedule_key.public_key().to_string(), "Updated fee_schedule_key mismatch"
        
        # Verify fee_schedule_key
        update_receipt = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([CustomFixedFee(amount=1, fee_collector_account_id=env.client.operator_account_id)])
            .freeze_with(env.client)
            .sign(new_fee_schedule_key)
            .execute(env.client)
        )

        assert update_receipt.status == ResponseCode.SUCCESS
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert len(token_info.custom_fees) == 1
        assert token_info.custom_fees[0].amount == 1
        assert token_info.custom_fees[0].fee_collector_account_id == env.client.operator_account_id
    finally:
        env.close()

def test_integation_token_update_fee_schedule_key_nft():
    env = IntegrationTestEnv()
    admin_key = PrivateKey.generate()
    fee_schedule_key = PrivateKey.generate()

    try:
        token_id = create_nft_token(env, [
            lambda tx: tx.set_admin_key(admin_key),
            lambda tx: tx.set_fee_schedule_key(fee_schedule_key),
            lambda tx: tx.freeze_with(env.client).sign(admin_key)
        ])
        
        # Update Fee Schedule Key
        new_fee_schedule_key = PrivateKey.generate()
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_fee_schedule_key(new_fee_schedule_key)
            .freeze_with(env.client)
            .sign(admin_key)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"

        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
        assert token_info.fee_schedule_key.to_string() == new_fee_schedule_key.public_key().to_string(), "Updated fee_schedule_key mismatch"
        
        # Verify fee_schedule_key
        update_receipt = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([CustomFixedFee(amount=1, fee_collector_account_id=env.client.operator_account_id)])
            .freeze_with(env.client)
            .sign(new_fee_schedule_key)
            .execute(env.client)
        )

        assert update_receipt.status == ResponseCode.SUCCESS
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert len(token_info.custom_fees) == 1
        assert token_info.custom_fees[0].amount == 1
        assert token_info.custom_fees[0].fee_collector_account_id == env.client.operator_account_id
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_update_with_public_key():
    """Test updating token keys with PublicKey directly (not PrivateKey)."""
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        # Generate a new key pair for the freeze key
        freeze_private_key = PrivateKey.generate_ed25519()
        freeze_public_key = freeze_private_key.public_key()
        
        # Update token with PublicKey
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_name("UpdatedWithPublicKey")
            .set_freeze_key(freeze_public_key)  # Using PublicKey directly
            .freeze_with(env.client)
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query the token and verify the freeze key matches the public key
        info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
        
        assert info.name == "UpdatedWithPublicKey", "Token name failed to update"
        assert info.freeze_key is not None
        
        # info.freeze_key is already a PublicKey object, so we can compare directly
        assert info.freeze_key.to_bytes_raw() == freeze_public_key.to_bytes_raw(), "Freeze key on network should match the PublicKey used in transaction"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_update_non_custodial_workflow():
    """
    Test the non-custodial workflow where:
    1. Operator builds a TokenUpdateTransaction using only a PublicKey
    2. Operator gets the transaction bytes
    3. User (with the PrivateKey) signs the bytes
    4. Operator executes the signed transaction
    """
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        # 1. SETUP: Create a new key pair for the "user"
        user_private_key = PrivateKey.generate_ed25519()
        user_public_key = user_private_key.public_key()
        
        # =================================================================
        # STEP 1 & 2: OPERATOR (CLIENT) BUILDS THE TRANSACTION
        # =================================================================
        
        tx = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_name("NonCustodialToken")
            .set_freeze_key(user_public_key)  # <-- Using PublicKey!
            .freeze_with(env.client)
        )
        
        tx_bytes = tx.to_bytes()
        
        # =================================================================
        # STEP 3: USER (SIGNER) SIGNS THE TRANSACTION
        # =================================================================
        
        tx_from_bytes = Transaction.from_bytes(tx_bytes)
        tx_from_bytes.sign(user_private_key)
        
        # =================================================================
        # STEP 4: OPERATOR (CLIENT) EXECUTES THE SIGNED TX
        # =================================================================
        
        receipt = tx_from_bytes.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # PROOF: Query the token and check if the freeze key matches
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
        
        assert token_info.freeze_key is not None
        
        # This is the STRONG assertion:
        # Compare the bytes of the key from the network
        # with the bytes of the key we originally used.
        # token_info.freeze_key is already a PublicKey object, so we can compare directly
        assert token_info.freeze_key.to_bytes_raw() == user_public_key.to_bytes_raw(), "Freeze key on network should match the PublicKey used in transaction"
        assert token_info.name == "NonCustodialToken", "Token name should be updated"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_update_with_ecdsa_public_key():
    """Test updating token keys with ECDSA PublicKey."""
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        # Generate a new ECDSA key pair for the admin key
        admin_private_key = PrivateKey.generate_ecdsa()
        admin_public_key = admin_private_key.public_key()
        
        # Update token with ECDSA PublicKey
        # Note: When updating admin_key, we need to sign with the new admin key
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_name("UpdatedWithECDSA")
            .set_admin_key(admin_public_key)  # Using ECDSA PublicKey
            .freeze_with(env.client)
            .sign(admin_private_key)  # Sign with the new admin key
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query the token and verify the admin key matches the public key
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
        assert token_info is not None
        assert token_info.admin_key is not None
        
        # token_info.admin_key is already a PublicKey object, so we can compare directly
        assert token_info.admin_key.to_bytes_raw() == admin_public_key.to_bytes_raw(), "Admin key on network should match the ECDSA PublicKey used in transaction"
        assert token_info.name == "UpdatedWithECDSA", "Token name should be updated"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_update_with_mixed_key_types():
    """Test updating token with mixed PrivateKey and PublicKey types."""
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        # Generate keys - mix of PrivateKey and PublicKey
        admin_private_key = PrivateKey.generate_ed25519()
        freeze_public_key = PrivateKey.generate_ed25519().public_key()
        wipe_private_key = PrivateKey.generate_ecdsa()
        supply_public_key = PrivateKey.generate_ecdsa().public_key()
        
        # Update token with mixed key types
        # Note: When updating admin_key, we need to sign with the new admin key
        receipt = (
            TokenUpdateTransaction()
            .set_token_id(token_id)
            .set_token_name("MixedKeysToken")
            .set_admin_key(admin_private_key)      # PrivateKey
            .set_freeze_key(freeze_public_key)      # PublicKey
            .set_wipe_key(wipe_private_key)        # PrivateKey
            .set_supply_key(supply_public_key)     # PublicKey
            .freeze_with(env.client)
            .sign(admin_private_key)  # Sign with the new admin key
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token update transaction failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Query the token and verify all keys are correctly set
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
        
        assert token_info.name == "MixedKeysToken", "Token name should be updated"
        assert token_info.admin_key is not None
        assert token_info.freeze_key is not None
        assert token_info.wipe_key is not None
        assert token_info.supply_key is not None
        
        # token_info keys are already PublicKey objects, so we can compare directly
        # Verify admin key (from PrivateKey)
        assert token_info.admin_key.to_bytes_raw() == admin_private_key.public_key().to_bytes_raw()
        
        # Verify freeze key (from PublicKey)
        assert token_info.freeze_key.to_bytes_raw() == freeze_public_key.to_bytes_raw()
        
        # Verify wipe key (from PrivateKey)
        assert token_info.wipe_key.to_bytes_raw() == wipe_private_key.public_key().to_bytes_raw()
        
        # Verify supply key (from PublicKey)
        assert token_info.supply_key.to_bytes_raw() == supply_public_key.to_bytes_raw()
    finally:
        env.close()
