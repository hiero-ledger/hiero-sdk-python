import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery


@pytest.mark.integration
def test_integration_token_reject_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create the new account
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Recipient Account"
        )
        
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        token1 = create_fungible_token(env)
        token2 = create_fungible_token(env)
        
        # Associate the tokens to the new account
        token_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token1, token2]
        )
        
        token_associate_transaction.freeze_with(env.client)
        token_associate_transaction.sign(new_account_private_key)
        receipt = token_associate_transaction.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer the tokens to the new account
        token_transfer_transaction = TransferTransaction()
        token_transfer_transaction.add_token_transfer(token1, account_id, 10)
        token_transfer_transaction.add_token_transfer(token1, env.client.operator_account_id, -10)
        token_transfer_transaction.add_token_transfer(token2, account_id, 10)
        token_transfer_transaction.add_token_transfer(token2, env.client.operator_account_id, -10)
        
        receipt = token_transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the tokens
        token_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            token_ids=[token1, token2]
        )
        
        token_reject_transaction.freeze_with(env.client)
        token_reject_transaction.sign(new_account_private_key)
        receipt = token_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token rejection failed with status: {ResponseCode(receipt.status).name}"
        
        # Verify the balance of the new account is 0
        balance = CryptoGetAccountBalanceQuery(account_id).execute(env.client)
        assert balance.token_balances is not None and balance.token_balances.get(token1) == 0 and balance.token_balances.get(token2) == 0
        
        # Verify the balance of the operator account is the same as the initial balance
        balance = CryptoGetAccountBalanceQuery(env.client.operator_account_id).execute(env.client)
        assert balance.token_balances is not None and balance.token_balances.get(token1) == 1000 and balance.token_balances.get(token2) == 1000
    finally:
        env.close()
        

@pytest.mark.integration
def test_integration_token_reject_transaction_can_execute_for_nft():
    env = IntegrationTestEnv()
    
    try:
        nft_id_1 = create_nft_token(env)
        nft_id_2 = create_nft_token(env)
        
        receipt = (TokenMintTransaction()
            .set_token_id(nft_id_1)
            .set_metadata([b"metadata1", b"metadata2"])
            .execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        serials_1 = receipt.serial_numbers
        
        receipt = (TokenMintTransaction()
            .set_token_id(nft_id_2)
            .set_metadata([b"metadata1", b"metadata2"])
            .execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        serials_2 = receipt.serial_numbers
        
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        receipt = (AccountCreateTransaction()
            .set_key(new_account_public_key).set_initial_balance(Hbar(1))
            .set_account_memo("Receiver Account").execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        account_id = receipt.account_id
        assert account_id is not None
        
        # Associate the tokens to the new account
        receipt = (TokenAssociateTransaction().set_account_id(account_id)
            .add_token_id(nft_id_1).add_token_id(nft_id_2)
            .freeze_with(env.client).sign(new_account_private_key).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        receipt = (TransferTransaction()
            .add_nft_transfer(NftId(nft_id_1, serials_1[0]), env.client.operator_account_id, account_id).add_nft_transfer(NftId(nft_id_1, serials_1[1]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id_2, serials_2[0]), env.client.operator_account_id, account_id).add_nft_transfer(NftId(nft_id_2, serials_2[1]), env.client.operator_account_id, account_id)
            .execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the tokens
        receipt = (TokenRejectTransaction()
            .set_owner_id(account_id)
            .set_nft_ids([NftId(nft_id_1, serials_1[1]), NftId(nft_id_2, serials_2[1])])
            .freeze_with(env.client).sign(new_account_private_key).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Token rejection failed with status: {ResponseCode(receipt.status).name}"
        
        # Verify the balance is decremented by 1 for each token
        balance = CryptoGetAccountBalanceQuery(account_id).execute(env.client)
        assert balance.token_balances and balance.token_balances.get(nft_id_1) == 1, f"Expected 1 NFT for token {nft_id_1}, got {balance.token_balances.get(nft_id_1)}"
        assert balance.token_balances and balance.token_balances.get(nft_id_2) == 1, f"Expected 1 NFT for token {nft_id_2}, got {balance.token_balances.get(nft_id_2)}"
        
        # Verify the NFTs are transferred back to the treasury
        nft_info_1 = TokenNftInfoQuery(NftId(nft_id_1, serials_1[1])).execute(env.client)
        assert nft_info_1.account_id == env.operator_id, f"Expected NFT owner to be {env.operator_id}, got {nft_info_1.account_id}"
        
        nft_info_2 = TokenNftInfoQuery(NftId(nft_id_2, serials_2[1])).execute(env.client)
        assert nft_info_2.account_id == env.operator_id, f"Expected NFT owner to be {env.operator_id}, got {nft_info_2.account_id}"
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_reject_transaction_can_execute_for_ft_and_nft_parallel():
    env = IntegrationTestEnv()
    
    try:
        nft_id_1 = create_nft_token(env)
        nft_id_2 = create_nft_token(env)
        
        token_id_1 = create_fungible_token(env)
        token_id_2 = create_fungible_token(env)
        
        receipt = TokenMintTransaction().set_token_id(nft_id_1).set_metadata([b"metadata1", b"metadata2"]).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Token minting failed with status: {ResponseCode(receipt.status).name}"
        serials_1 = receipt.serial_numbers
        
        receipt = TokenMintTransaction().set_token_id(nft_id_2).set_metadata([b"metadata1", b"metadata2"]).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Token minting failed with status: {ResponseCode(receipt.status).name}"
        serials_2 = receipt.serial_numbers
        
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        receipt = AccountCreateTransaction().set_key(new_account_public_key).set_initial_balance(Hbar(1)).set_account_memo("Receiver Account").execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        account_id = receipt.account_id
        assert account_id is not None
        
        receipt = (TokenAssociateTransaction().set_account_id(account_id).add_token_id(token_id_1).add_token_id(token_id_2).add_token_id(nft_id_1).add_token_id(nft_id_2)
            .freeze_with(env.client).sign(new_account_private_key).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"

        receipt = (TransferTransaction()
            .add_token_transfer(token_id_1, account_id, 10).add_token_transfer(token_id_1, env.client.operator_account_id, -10)
            .add_token_transfer(token_id_2, account_id, 10).add_token_transfer(token_id_2, env.client.operator_account_id, -10)
            .add_nft_transfer(NftId(nft_id_1, serials_1[0]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id_1, serials_1[1]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id_2, serials_2[0]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id_2, serials_2[1]), env.client.operator_account_id, account_id)
            .execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        reject_transaction = (TokenRejectTransaction().set_owner_id(account_id)
            .set_token_ids([token_id_1, token_id_2])
            .set_nft_ids([NftId(nft_id_1, serials_1[1]), NftId(nft_id_2, serials_2[1])]))
        reject_transaction.transaction_fee = Hbar(3).to_tinybars()  # Set transaction fee to be higher than 2 Hbars
        receipt = reject_transaction.freeze_with(env.client).sign(new_account_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Token rejection failed with status: {ResponseCode(receipt.status).name}"
        
        balance = CryptoGetAccountBalanceQuery(account_id).execute(env.client)
        assert balance.token_balances and balance.token_balances.get(token_id_1) == 0, f"Expected token balance to be 0 for token {token_id_1}, got {balance.token_balances.get(token_id_1)}"
        assert balance.token_balances and balance.token_balances.get(token_id_2) == 0, f"Expected token balance to be 0 for token {token_id_2}, got {balance.token_balances.get(token_id_2)}"
        
        balance = CryptoGetAccountBalanceQuery(env.operator_id).execute(env.client)
        assert balance.token_balances and balance.token_balances.get(token_id_1) == 1000, f"Expected token balance to be 1000 for token {token_id_1}, got {balance.token_balances.get(token_id_1)}"
        assert balance.token_balances and balance.token_balances.get(token_id_2) == 1000, f"Expected token balance to be 1000 for token {token_id_2}, got {balance.token_balances.get(token_id_2)}"
        
        nft_info_1 = TokenNftInfoQuery(NftId(nft_id_1, serials_1[1])).execute(env.client)
        assert nft_info_1.account_id == env.operator_id, f"Expected NFT owner to be {env.operator_id}, got {nft_info_1.account_id}"
        
        nft_info_2 = TokenNftInfoQuery(NftId(nft_id_2, serials_2[1])).execute(env.client)
        assert nft_info_2.account_id == env.operator_id, f"Expected NFT owner to be {env.operator_id}, got {nft_info_2.account_id}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_reject_transaction_fails_with_invalid_signature():
    env = IntegrationTestEnv()
    
    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create the new account
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Recipient Account"
        )
        
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        token1 = create_fungible_token(env)
        
        # Associate the tokens to the new account
        token_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token1]  
        )
        
        token_associate_transaction.freeze_with(env.client)
        token_associate_transaction.sign(new_account_private_key)
        receipt = token_associate_transaction.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer the tokens to the new account
        token_transfer_transaction = TransferTransaction()
        token_transfer_transaction.add_token_transfer(token1, account_id, 10)
        token_transfer_transaction.add_token_transfer(token1, env.client.operator_account_id, -10)
        
        receipt = token_transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        wrong_key = PrivateKey.generate()
        
        # Reject the tokens
        token_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            token_ids=[token1]
        )
        
        token_reject_transaction.freeze_with(env.client)
        # Sign with wrong key
        token_reject_transaction.sign(wrong_key)
        receipt = token_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.INVALID_SIGNATURE, f"Token rejection should have failed with INVALID_SIGNATURE status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_reject_transaction_fails_with_reference_size_exceeded():
    env = IntegrationTestEnv()
    
    try:
        nft_id = create_nft_token(env)
        
        token_id = create_fungible_token(env)
        
        # Mint 10 NFTs
        receipt = (TokenMintTransaction().set_token_id(nft_id)
            .set_metadata([b"1", b"2", b"3", b"4", b"5", b"6", b"7", b"8", b"9", b"10"]).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        serials = receipt.serial_numbers
        
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Receiver Account"
        )
        receipt = account_transaction.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        account_id = receipt.account_id
        assert account_id is not None
        
        # Associate the tokens to the new account
        token_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[nft_id, token_id]
        )
        receipt = token_associate_transaction.freeze_with(env.client).sign(new_account_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer the tokens to the new account
        receipt = (TransferTransaction().add_token_transfer(token_id, env.client.operator_account_id, -10).add_token_transfer(token_id, account_id, 10)
            .add_nft_transfer(NftId(nft_id, serials[0]), env.client.operator_account_id, account_id).add_nft_transfer(NftId(nft_id, serials[1]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id, serials[2]), env.client.operator_account_id, account_id).add_nft_transfer(NftId(nft_id, serials[3]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id, serials[4]), env.client.operator_account_id, account_id).add_nft_transfer(NftId(nft_id, serials[5]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id, serials[6]), env.client.operator_account_id, account_id).add_nft_transfer(NftId(nft_id, serials[7]), env.client.operator_account_id, account_id)
            .add_nft_transfer(NftId(nft_id, serials[8]), env.client.operator_account_id, account_id).add_nft_transfer(NftId(nft_id, serials[9]), env.client.operator_account_id, account_id)
            .execute(env.client))
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the tokens with 11 token references - should fail with TOKEN_REFERENCE_LIST_SIZE_LIMIT_EXCEEDED
        token_reject_transaction = (TokenRejectTransaction().set_owner_id(account_id).set_token_ids([token_id])
            .set_nft_ids([NftId(nft_id, serials[0]), NftId(nft_id, serials[1]), NftId(nft_id, serials[2]), NftId(nft_id, serials[3]), NftId(nft_id, serials[4]), 
                     NftId(nft_id, serials[5]), NftId(nft_id, serials[6]), NftId(nft_id, serials[7]), NftId(nft_id, serials[8]), NftId(nft_id, serials[9])]))
        
        token_reject_transaction.transaction_fee = Hbar(3).to_tinybars()    # Set transaction fee to be higher than 2 Hbars
        receipt = token_reject_transaction.freeze_with(env.client).sign(new_account_private_key).execute(env.client)
        assert receipt.status == ResponseCode.TOKEN_REFERENCE_LIST_SIZE_LIMIT_EXCEEDED, f"Token rejection should have failed with TOKEN_REFERENCE_LIST_SIZE_LIMIT_EXCEEDED status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_reject_transaction_fails_with_invalid_token_id():
    env = IntegrationTestEnv()
    
    try:
        # Leave the token_ids/nft_ids empty
        token_reject_transaction = TokenRejectTransaction(
            owner_id=env.operator_id,
        )
        
        with pytest.raises(PrecheckError, match="failed precheck with status: EMPTY_TOKEN_REFERENCE_LIST"):
            token_reject_transaction.execute(env.client)
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_reject_transaction_fails_treasury_rejects():
    env = IntegrationTestEnv()
    
    try:
        # Create fungible token with treasury
        token_id = create_fungible_token(env)
        
        # Skip the transfer 
        
        # Reject the token with the treasury
        token_reject_transaction = TokenRejectTransaction(
            owner_id=env.operator_id,
            token_ids=[token_id]
        )
        
        receipt = token_reject_transaction.execute(env.client)

        assert receipt.status == ResponseCode.ACCOUNT_IS_TREASURY, f"Token rejection should have failed with ACCOUNT_IS_TREASURY status but got: {ResponseCode(receipt.status).name}"
        
        # Create NFT with treasury
        nft_token_id = create_nft_token(env)
        
        # Mint NFT
        mint = TokenMintTransaction(
            token_id=nft_token_id,
            metadata=[b"test metadata"]
        )
        
        receipt = mint.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        
        # Attempt to reject the NFT token with the treasury
        token_reject_transaction = TokenRejectTransaction(
            owner_id=env.operator_id,
            token_ids=[nft_token_id]
        )
        
        receipt = token_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.ACCOUNT_IS_TREASURY, f"Token rejection should have failed with ACCOUNT_IS_TREASURY status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_reject_transaction_fails_when_fungible_token_owner_has_no_balance():
    env = IntegrationTestEnv()
    
    try:
        # Create fungible token with treasury
        token_id = create_fungible_token(env)
        
        # Create receiver account
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Receiver Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        # Associate the token to the receiver account
        token_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        token_associate_transaction.freeze_with(env.client)
        token_associate_transaction.sign(new_account_private_key)
        receipt = token_associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Skip the transfer
        
        # Reject the token - should fail with INSUFFICIENT_TOKEN_BALANCE
        token_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            token_ids=[token_id]
        )
        
        token_reject_transaction.freeze_with(env.client)
        token_reject_transaction.sign(new_account_private_key)
        receipt = token_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.INSUFFICIENT_TOKEN_BALANCE, f"Token rejection should have failed with INSUFFICIENT_TOKEN_BALANCE status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_reject_transaction_fails_when_nft_owner_has_no_balance():
    env = IntegrationTestEnv()
    
    try:
        # Create receiver account
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Receiver Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        # Create NFT with treasury
        nft_token_id = create_nft_token(env)
        
        # Mint NFTs
        mint_transaction = TokenMintTransaction(
            token_id=nft_token_id,
            metadata=[b"test metadata"]
        )
        
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        
        serials = receipt.serial_numbers
        
        # Associate the NFT to the receiver account
        nft_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[nft_token_id]
        )
        
        nft_associate_transaction.freeze_with(env.client)
        nft_associate_transaction.sign(new_account_private_key)
        receipt = nft_associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT association failed with status: {ResponseCode(receipt.status).name}"
        
        # Skip the transfer
        
        # Reject the NFT - should fail with INVALID_OWNER_ID
        nft_id = NftId(nft_token_id, serials[0])
        nft_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            nft_ids=[nft_id]
        )
        
        nft_reject_transaction.freeze_with(env.client)
        nft_reject_transaction.sign(new_account_private_key)
        receipt = nft_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.INVALID_OWNER_ID, f"Token rejection should have failed with INVALID_OWNER_ID status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_reject_transaction_fails_with_token_reference_repeated_fungible():
    env = IntegrationTestEnv()
    
    try:
        # Create a new account with private key
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create the new account
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Recipient Account"
        )
        
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        # Create fungible token with treasury
        token_id = create_fungible_token(env)
        
        # Associate the token to the new account
        token_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        token_associate_transaction.freeze_with(env.client)
        token_associate_transaction.sign(new_account_private_key)
        receipt = token_associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer tokens to the new account
        token_transfer_transaction = TransferTransaction()
        token_transfer_transaction.add_token_transfer(token_id, account_id, 10)
        token_transfer_transaction.add_token_transfer(token_id, env.client.operator_account_id, -10)
        
        receipt = token_transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the token with duplicate token id - should fail with TOKEN_REFERENCE_REPEATED
        token_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            token_ids=[token_id, token_id]  # Duplicate token ID
        )
        
        token_reject_transaction.freeze_with(env.client)
        token_reject_transaction.sign(new_account_private_key)
        
        with pytest.raises(PrecheckError, match="failed precheck with status: TOKEN_REFERENCE_REPEATED"):
            token_reject_transaction.execute(env.client)
    finally:
        env.close()

@pytest.mark.integration
def test_token_reject_transaction_fails_with_token_reference_repeated_nft():
    env = IntegrationTestEnv()
    
    try:
        # Create a new account with private key
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create the new account
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Recipient Account"
        )
        
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        # Create NFT with treasury
        nft_token_id = create_nft_token(env)
        
        # Mint NFTs
        mint_transaction = TokenMintTransaction(
            token_id=nft_token_id,
            metadata=[b"test metadata"]
        )
        
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        
        serials = receipt.serial_numbers
        
        # Associate the NFT to the receiver account
        nft_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[nft_token_id]
        )
        
        nft_associate_transaction.freeze_with(env.client)
        nft_associate_transaction.sign(new_account_private_key)
        receipt = nft_associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer NFT to the receiver
        nft_transfer_transaction = TransferTransaction()
        nft_transfer_transaction.add_nft_transfer(
            NftId(nft_token_id, serials[0]), 
            env.client.operator_account_id, 
            account_id
        )
        
        receipt = nft_transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the NFT with duplicate NFT id - should fail with TOKEN_REFERENCE_REPEATED
        nft_id = NftId(nft_token_id, serials[0])
        nft_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            nft_ids=[nft_id, nft_id]  # Duplicate NFT ID
        )
        
        nft_reject_transaction.freeze_with(env.client)
        nft_reject_transaction.sign(new_account_private_key)
        
        with pytest.raises(PrecheckError, match="failed precheck with status: TOKEN_REFERENCE_REPEATED"):
            nft_reject_transaction.execute(env.client)
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_reject_transaction_fails_when_rejecting_nft_with_token_id():
    env = IntegrationTestEnv()
    
    try:
        # Create NFT with treasury
        nft_token_id = create_nft_token(env)
        
        # Mint NFTs
        mint_transaction = TokenMintTransaction(
            token_id=nft_token_id,
            metadata=[b"metadata1", b"metadata2", b"metadata3"]
        )
        
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        
        serials = receipt.serial_numbers
        
        # Create receiver account with auto associations
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        account_transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Receiver Account"
        )
        
        receipt = account_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        # Associate the NFT to the receiver
        nft_associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[nft_token_id]
        )
        
        nft_associate_transaction.freeze_with(env.client)
        nft_associate_transaction.sign(new_account_private_key)
        receipt = nft_associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer NFTs to the receiver
        nft_transfer_transaction = TransferTransaction()
        nft_transfer_transaction.add_nft_transfer(NftId(nft_token_id, serials[0]), env.client.operator_account_id, account_id)
        nft_transfer_transaction.add_nft_transfer(NftId(nft_token_id, serials[1]), env.client.operator_account_id, account_id)
        nft_transfer_transaction.add_nft_transfer(NftId(nft_token_id, serials[2]), env.client.operator_account_id, account_id)
        
        receipt = nft_transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the whole collection - should fail
        token_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            token_ids=[nft_token_id]
        )
        
        token_reject_transaction.freeze_with(env.client)
        token_reject_transaction.sign(new_account_private_key)
        
        receipt = token_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.ACCOUNT_AMOUNT_TRANSFERS_ONLY_ALLOWED_FOR_FUNGIBLE_COMMON, f"Token rejection should have failed with ACCOUNT_AMOUNT_TRANSFERS_ONLY_ALLOWED_FOR_FUNGIBLE_COMMON status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_reject_transaction_fails_with_nft_token_frozen():
    env = IntegrationTestEnv()
    try:
        # Create NFT with treasury
        nft_token_id = create_nft_token(env)
        
        # Mint NFTs
        mint_transaction = TokenMintTransaction(
            token_id=nft_token_id,
            metadata=[b"test metadata", b"test metadata", b"test metadata"]
        )
        
        receipt = mint_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        
        serials = receipt.serial_numbers
        
        # Create a new account with private key
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create the new account
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Recipient Account"
        )
        
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        # Associate the NFT to the receiver
        associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[nft_token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer NFTs to the receiver
        nft_transfer_transaction = TransferTransaction()
        nft_transfer_transaction.add_nft_transfer(NftId(nft_token_id, serials[0]), env.client.operator_account_id, account_id)
        nft_transfer_transaction.add_nft_transfer(NftId(nft_token_id, serials[1]), env.client.operator_account_id, account_id)
        
        receipt = nft_transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Freeze the token
        token_freeze_transaction = TokenFreezeTransaction(
            token_id=nft_token_id,
            account_id=account_id
        )
        
        receipt = token_freeze_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token freeze failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the NFT - should fail with ACCOUNT_FROZEN_FOR_TOKEN
        nft_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            nft_ids=[NftId(nft_token_id, serials[1])]
        )
        
        nft_reject_transaction.freeze_with(env.client)
        nft_reject_transaction.sign(new_account_private_key)
        receipt = nft_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.ACCOUNT_FROZEN_FOR_TOKEN, f"Token rejection should have failed with ACCOUNT_FROZEN_FOR_TOKEN status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_reject_transaction_fails_with_fungible_token_frozen():
    env = IntegrationTestEnv()
    
    try:
        # Create a new account with private key
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()
        
        # Create the new account
        transaction = AccountCreateTransaction(
            key=new_account_public_key,
            initial_balance=Hbar(1),
            memo="Recipient Account"
        )
        
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        
        account_id = receipt.account_id
        
        # Create fungible token with treasury
        token_id = create_fungible_token(env)
        
        # Associate the token to the receiver
        associate_transaction = TokenAssociateTransaction(
            account_id=account_id,
            token_ids=[token_id]
        )
        
        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer tokens to the receiver
        token_transfer_transaction = TransferTransaction()
        token_transfer_transaction.add_token_transfer(token_id, account_id, 10)
        token_transfer_transaction.add_token_transfer(token_id, env.client.operator_account_id, -10)

        receipt = token_transfer_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Freeze the token
        token_freeze_transaction = TokenFreezeTransaction(
            token_id=token_id,
            account_id=account_id
        )
        
        receipt = token_freeze_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token freeze failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the token - should fail with ACCOUNT_FROZEN_FOR_TOKEN
        token_reject_transaction = TokenRejectTransaction(
            owner_id=account_id,
            token_ids=[token_id]
        )
        
        token_reject_transaction.freeze_with(env.client)
        token_reject_transaction.sign(new_account_private_key)
        receipt = token_reject_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.ACCOUNT_FROZEN_FOR_TOKEN, f"Token rejection should have failed with ACCOUNT_FROZEN_FOR_TOKEN status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_reject_transaction_receiver_sig_required_nft():
    env = IntegrationTestEnv()
    
    try:
        treasury_private_key = PrivateKey.generate()
        treasury_public_key = treasury_private_key.public_key()
        
        receipt = (AccountCreateTransaction().set_key(treasury_public_key).set_initial_balance(Hbar(0))
            .set_receiver_signature_required(True).set_account_memo("Treasury Account")
            .freeze_with(env.client).sign(treasury_private_key).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Treasury account creation failed with status: {ResponseCode(receipt.status).name}"
        treasury_id = receipt.account_id
        
        # Create a new NFT token with a custom treasury account that requires receiver signatures
        # Pass lambda functions to create_nft_token to configure the treasury account and sign with its key
        nft_token_id = create_nft_token(env, [
            lambda tx: tx.set_treasury_account_id(treasury_id).freeze_with(env.client),
            lambda tx: tx.sign(treasury_private_key)
        ])
        
        receipt = (TokenMintTransaction().set_token_id(nft_token_id).set_metadata([b"test metadata 1", b"test metadata 2"]).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"NFT minting failed with status: {ResponseCode(receipt.status).name}"
        serials = receipt.serial_numbers
        
        receiver_private_key = PrivateKey.generate()
        receiver_public_key = receiver_private_key.public_key()
        
        receipt = (AccountCreateTransaction().set_key(receiver_public_key).set_initial_balance(Hbar(1)).set_account_memo("Receiver Account").execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Receiver account creation failed with status: {ResponseCode(receipt.status).name}"
        receiver_id = receipt.account_id
        
        associate_transaction = TokenAssociateTransaction(
            account_id=receiver_id,
            token_ids=[nft_token_id]
        )
        receipt = associate_transaction.freeze_with(env.client).sign(receiver_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"NFT association failed with status: {ResponseCode(receipt.status).name}"
        
        nft_transfer_transaction = TransferTransaction()
        nft_transfer_transaction.add_nft_transfer(NftId(nft_token_id, serials[0]), treasury_id, receiver_id)
        nft_transfer_transaction.add_nft_transfer(NftId(nft_token_id, serials[1]), treasury_id, receiver_id)
        
        receipt = nft_transfer_transaction.freeze_with(env.client).sign(treasury_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject one of the NFTs
        nft_id = NftId(nft_token_id, serials[1])
        receipt = (TokenRejectTransaction().set_owner_id(receiver_id).set_nft_ids([nft_id])
            .freeze_with(env.client).sign(receiver_private_key).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"NFT rejection failed with status: {ResponseCode(receipt.status).name}"
        
        # Verify the balance is decremented by 1
        token_balance = CryptoGetAccountBalanceQuery(account_id=receiver_id).execute(env.client)
        assert token_balance.token_balances.get(nft_token_id) == 1, f"Expected NFT balance to be 1, got {token_balance.token_balances.get(nft_token_id)}"
        
        # Verify the NFT is transferred back to the treasury
        nft_info = TokenNftInfoQuery(nft_id=nft_id).execute(env.client)
        assert nft_info.account_id == treasury_id, f"Expected NFT owner to be {treasury_id}, got {nft_info.account_id}"
    finally:
        env.close()

@pytest.mark.integration
def test_token_reject_transaction_receiver_sig_required_fungible():
    env = IntegrationTestEnv()
    
    try:
        treasury_private_key = PrivateKey.generate()
        treasury_public_key = treasury_private_key.public_key()
        
        transaction = AccountCreateTransaction(
            key=treasury_public_key,
            initial_balance=Hbar(0),
            receiver_signature_required=True,
            memo="Treasury Account"
        )
        receipt = transaction.freeze_with(env.client).sign(treasury_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Treasury account creation failed with status: {ResponseCode(receipt.status).name}"
        treasury_id = receipt.account_id
        
        # Create a fungible token with a custom treasury account that requires receiver signatures
        # Pass lambda functions to create_fungible_token to configure the treasury account and sign with its key
        fungible_token_id = create_fungible_token(env, [
            lambda tx: tx.set_treasury_account_id(treasury_id).freeze_with(env.client),
            lambda tx: tx.sign(treasury_private_key)
        ])
        
        # Create receiver account
        receiver_private_key = PrivateKey.generate()
        receiver_public_key = receiver_private_key.public_key()
        
        receiver_transaction = AccountCreateTransaction(
            key=receiver_public_key,
            initial_balance=Hbar(1),
            memo="Receiver Account"
        )
        receipt = receiver_transaction.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Receiver account creation failed with status: {ResponseCode(receipt.status).name}"
        receiver_id = receipt.account_id
        
        # Associate the token to the receiver
        associate_transaction = TokenAssociateTransaction(
            account_id=receiver_id,
            token_ids=[fungible_token_id]
        )
        receipt = associate_transaction.freeze_with(env.client).sign(receiver_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Token association failed with status: {ResponseCode(receipt.status).name}"
        
        # Transfer tokens to the receiver
        ft_transfer_transaction = TransferTransaction()
        ft_transfer_transaction.add_token_transfer(fungible_token_id, treasury_id, -10)
        ft_transfer_transaction.add_token_transfer(fungible_token_id, receiver_id, 10)
        
        receipt = ft_transfer_transaction.freeze_with(env.client).sign(treasury_private_key).execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Token transfer failed with status: {ResponseCode(receipt.status).name}"
        
        # Reject the token
        receipt = (TokenRejectTransaction().set_owner_id(receiver_id).set_token_ids([fungible_token_id])
            .freeze_with(env.client).sign(receiver_private_key).execute(env.client))
        assert receipt.status == ResponseCode.SUCCESS, f"Token rejection failed with status: {ResponseCode(receipt.status).name}"
        
        # Verify the balance of the receiver is 0
        receiver_balance = CryptoGetAccountBalanceQuery(account_id=receiver_id).execute(env.client)
        assert receiver_balance.token_balances.get(fungible_token_id) == 0, f"Expected token balance to be 0, got {receiver_balance.token_balances.get(fungible_token_id)}"
        
        # Verify the tokens are transferred back to the treasury
        treasury_balance = CryptoGetAccountBalanceQuery(account_id=treasury_id).execute(env.client)
        assert treasury_balance.token_balances.get(fungible_token_id) == 1000, f"Expected treasury token balance to be 1000, got {treasury_balance.token_balances.get(fungible_token_id)}"
    finally:
        env.close()
