import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_update_nfts_transaction import TokenUpdateNftsTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_nft_token
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery

@pytest.mark.integration
def test_token_update_nfts_updates_metadata():
    env = IntegrationTestEnv()
    
    try:
        # Create supply key
        supply_private_key = PrivateKey.generate_ed25519()

        # Create metadata key
        metadata_private_key = PrivateKey.generate_ed25519() 
        
        nft_count = 4
        # Create initial metadata for NFTs
        mint_metadata = [b"1 2 3"] * nft_count  # Creates a list containing mint_metadata repeated nft_count (4) times, so [b"1 2 3", b"1 2 3", b"1 2 3", b"1 2 3"]
        updated_metadata = b"8 9"

        # Create NFT token with metadata key
        nft_id = create_nft_token(env, [
            lambda tx: tx.set_supply_key(supply_private_key),
            lambda tx: tx.set_metadata_key(metadata_private_key)
        ])

        # Mint NFTs with initial metadata
        mint_transaction = TokenMintTransaction(
            token_id=nft_id,
            metadata=mint_metadata
        )
        
        receipt = mint_transaction.freeze_with(env.client).sign(supply_private_key).execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode.get_name(receipt.status)}"
        serials = receipt.serial_numbers

        # Verify initial metadata
        for i, serial in enumerate(serials):
            nft_info = TokenNftInfoQuery(NftId(nft_id, serial)).execute(env.client)
            assert nft_info.metadata == mint_metadata[i], f"Initial metadata mismatch for serial {serial}"
        
        # Update metadata for first half of NFTs
        update_transaction = TokenUpdateNftsTransaction(
            token_id=nft_id,
            serial_numbers=serials[:nft_count//2],
            metadata=updated_metadata
        )
        
        receipt = update_transaction.freeze_with(env.client).sign(metadata_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"NFT update failed with status: {ResponseCode.get_name(receipt.status)}"

        # Verify updated metadata for first half
        for i, serial in enumerate(serials[:nft_count//2]):
            nft_info = TokenNftInfoQuery(NftId(nft_id, serial)).execute(env.client)
            assert nft_info.metadata == updated_metadata, f"Updated metadata mismatch for serial {serial}"

        # Verify unchanged metadata for second half
        for i, serial in enumerate(serials[nft_count//2:]):
            nft_info = TokenNftInfoQuery(NftId(nft_id, serial)).execute(env.client)
            assert nft_info.metadata == mint_metadata[i], f"Original metadata should be unchanged for serial {serial}"
    finally:
        env.close()

@pytest.mark.integration
def test_can_update_empty_nft_metadata():
    env = IntegrationTestEnv()
    
    try:
        supply_private_key = PrivateKey.generate_ed25519()
        metadata_private_key = PrivateKey.generate_ed25519()

        # Create initial metadata for NFTs - replicate the same metadata for each NFT
        nft_count = 4
        mint_metadata = [b"1 2 3"] * nft_count  # Creates a list containing mint_metadata repeated nft_count (4) times, so [b"1 2 3", b"1 2 3", b"1 2 3", b"1 2 3"]
        
        # Create empty metadata for update
        updated_metadata = b""
        
        # Create NFT token with metadata key
        nft_id = create_nft_token(env, [
            lambda tx: tx.set_supply_key(supply_private_key),
            lambda tx: tx.set_metadata_key(metadata_private_key)
        ])

        # Mint NFTs with initial metadata
        mint_transaction = TokenMintTransaction(
            token_id=nft_id,
            metadata=mint_metadata
        )
        
        receipt = mint_transaction.freeze_with(env.client).sign(supply_private_key).execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode.get_name(receipt.status)}"
        serials = receipt.serial_numbers

        # Get and verify initial metadata list
        for i, serial in enumerate(serials):
            nft_info = TokenNftInfoQuery(NftId(nft_id, serial)).execute(env.client)
            assert nft_info.metadata == mint_metadata[i], f"Initial metadata mismatch for serial {serial}"
        
        # Update metadata for all NFTs to empty
        update_transaction = TokenUpdateNftsTransaction(
            token_id=nft_id,
            serial_numbers=serials,
            metadata=updated_metadata
        )
        update_transaction.transaction_fee = Hbar(3).to_tinybars() # Set transaction fee to be higher than 2 Hbars
        
        receipt = update_transaction.freeze_with(env.client).sign(metadata_private_key).execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT update failed with status: {ResponseCode.get_name(receipt.status)}"
        
        # Get and verify updated metadata list
        for i, serial in enumerate(serials):
            nft_info = TokenNftInfoQuery(NftId(nft_id, serial)).execute(env.client)
            assert nft_info.metadata == updated_metadata, f"Updated metadata mismatch for serial {serial}"
    finally:
        env.close()

@pytest.mark.integration
def test_cannot_update_nft_metadata_when_key_is_not_set():
    env = IntegrationTestEnv()

    try:
        # Create supply key
        supply_private_key = PrivateKey.generate_ed25519()

        # Create metadata key (not used in token creation)
        metadata_private_key = PrivateKey.generate_ed25519()

        # Create NFT metadata
        nft_count = 4
        mint_metadata = [b"1 2 3"] * nft_count  # Creates a list containing mint_metadata repeated nft_count (4) times, so [b"1 2 3", b"1 2 3", b"1 2 3", b"1 2 3"]
        updated_metadata = b"8 9"

        # Create NFT token without metadata key
        nft_id = create_nft_token(env, [
            lambda x: x.set_supply_key(supply_private_key)
        ])

        # Mint NFTs with initial metadata
        mint_transaction = TokenMintTransaction(
            token_id=nft_id,
            metadata=mint_metadata
        )
        
        receipt = mint_transaction.freeze_with(env.client).sign(supply_private_key).execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode.get_name(receipt.status)}"
        serials = receipt.serial_numbers

        # Get and verify initial metadata list
        for i, serial in enumerate(serials):
            nft_info = TokenNftInfoQuery(NftId(nft_id, serial)).execute(env.client)
            assert nft_info.metadata == mint_metadata[i], f"Initial metadata mismatch for serial {serial}"
        
        # Try to update metadata for NFTs - should fail since no metadata key is set
        update_transaction = TokenUpdateNftsTransaction(
            token_id=nft_id,
            serial_numbers=serials,
            metadata=updated_metadata
        )
        update_transaction.transaction_fee = Hbar(3).to_tinybars() # Set transaction fee to be higher than 2 Hbars
        
        receipt = update_transaction.freeze_with(env.client).sign(metadata_private_key).execute(env.client)
        
        assert receipt.status == ResponseCode.INVALID_SIGNATURE, f"NFT update should fail with INVALID_SIGNATURE, got status: {ResponseCode.get_name(receipt.status)}"
    finally:
        env.close()

@pytest.mark.integration
def test_cannot_update_nft_metadata_when_transaction_not_signed_with_metadata_key():
    env = IntegrationTestEnv()
    
    try:
        # Create supply key
        supply_private_key = PrivateKey.generate_ed25519()

        # Create metadata key
        metadata_private_key = PrivateKey.generate_ed25519() 
        
        # Create initial metadata for NFTs
        nft_count = 4
        mint_metadata = [b"1 2 3"] * nft_count  # Creates a list containing mint_metadata repeated nft_count (4) times, so [b"1 2 3", b"1 2 3", b"1 2 3", b"1 2 3"]
        updated_metadata = b"8 9"

        # Create a new NFT token with supply and metadata keys
        # Pass lambda functions to create_nft_token to configure the token with the generated keys
        nft_id = create_nft_token(env, [
            lambda tx: tx.set_supply_key(supply_private_key),
            lambda tx: tx.set_metadata_key(metadata_private_key)
        ])

        # Mint NFTs with initial metadata
        mint_transaction = TokenMintTransaction(
            token_id=nft_id,
            metadata=mint_metadata
        )
        
        receipt = mint_transaction.freeze_with(env.client).sign(supply_private_key).execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode.get_name(receipt.status)}"
        serials = receipt.serial_numbers

        # Verify initial metadata
        for i, serial in enumerate(serials):
            nft_info = TokenNftInfoQuery(NftId(nft_id, serial)).execute(env.client)
            assert nft_info.metadata == mint_metadata[i], f"Initial metadata mismatch for serial {serial}"
        
        # Try to update metadata without signing it with metadata key
        tx = TokenUpdateNftsTransaction(
            token_id=nft_id,
            serial_numbers=serials,
            metadata=updated_metadata
        )
        tx.transaction_fee = Hbar(3).to_tinybars()  # Set transaction fee to be higher than 2 Hbars
        
        receipt = tx.execute(env.client)
        
        assert receipt.status == ResponseCode.INVALID_SIGNATURE, f"NFT update should fail with INVALID_SIGNATURE, got status: {ResponseCode.get_name(receipt.status)}"
        
        # Try to update metadata by signing the transaction with some key
        tx = TokenUpdateNftsTransaction(
            token_id=nft_id,
            serial_numbers=serials,
            metadata=updated_metadata
        )
        tx.transaction_fee = Hbar(3).to_tinybars()  # Set transaction fee to be higher than 2 Hbars
        
        receipt = tx.freeze_with(env.client).sign(env.operator_key).execute(env.client)
        
        assert receipt.status == ResponseCode.INVALID_SIGNATURE, f"NFT update should fail with INVALID_SIGNATURE, got status: {ResponseCode.get_name(receipt.status)}"
    finally:
        env.close()