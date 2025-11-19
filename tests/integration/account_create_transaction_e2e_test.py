import pytest
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_account_create_transaction_can_execute(env):
    """Test account_create_transaction can be executed."""
    new_account_private_key = PrivateKey.generate()
    new_account_public_key = new_account_private_key.public_key()
    initial_balance = Hbar(2)
        
    assert initial_balance.to_tinybars() == 200000000
        
    transaction = AccountCreateTransaction(
        key=new_account_public_key,
        initial_balance=initial_balance,
        memo="Recipient Account"
    )
        
    transaction.freeze_with(env.client)
    receipt = transaction.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.account_id is not None, "AccountID not found in receipt. Account may not have been created."
    
    
def test_create_account_without_alias(env):
    """Test account_create_transaction without alias."""
    public_key = PrivateKey.generate().public_key()
    initial_balance = Hbar(2)

    tx = (
        AccountCreateTransaction(
            initial_balance=initial_balance,
            memo="Recipient Account Without alias"
        )
        .set_key_without_alias(public_key)
        .freeze_with(env.client)
    )

    receipt = tx.execute(env.client)
    account_id = receipt.account_id
    
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.account_id is not None, "AccountID not found in receipt. Account may not have been created."

    info = AccountInfoQuery(account_id=account_id).execute(env.client)

    assert info.account_id == account_id
    assert info.contract_account_id.startswith('00000000000000000000')


def test_create_account_with_alias_derived_from_ecdsa_key(env):
    """Test account_create_transaction with alias derived form key."""
    public_key = PrivateKey.generate_ecdsa().public_key()
    initial_balance = Hbar(2)

    tx = (
        AccountCreateTransaction(
            initial_balance=initial_balance,
            memo="Recipient Account With alias"
        )
        .set_key_with_alias(public_key)
        .freeze_with(env.client)
    )
    
    receipt = tx.execute(env.client)
    account_id = receipt.account_id
    
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.account_id is not None, "AccountID not found in receipt. Account may not have been created."

    info = AccountInfoQuery(account_id=account_id).execute(env.client)

    assert info.account_id == account_id
    assert info.contract_account_id == public_key.to_evm_address().__str__()


def test_create_account_with_alias_derived_from_non_ecdsa_key():
    """Test create_account_transaction raise error for non_ecdsa key when deriving alias from key"""
    public_key = PrivateKey.generate_ed25519().public_key()
    tx = AccountCreateTransaction()

    with pytest.raises(ValueError):
        tx.set_key_with_alias(public_key)


def test_create_account_with_alias_from_seperate_ecdsa_key(env):
    """Test create_account_transaction from seperate ecdsa key."""
    public_key = PrivateKey.generate().public_key()
    alias_key = PrivateKey.generate_ecdsa()
    initial_balance = Hbar(2)

    tx = (
        AccountCreateTransaction(
            initial_balance=initial_balance,
            memo="Recipient Account With alias"
        )
        .set_key_with_alias(public_key, alias_key.public_key())
        .freeze_with(env.client)
    ).sign(alias_key) # Need to sign the tx with alias_key
    
    receipt = tx.execute(env.client)
    account_id = receipt.account_id
    
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.account_id is not None, "AccountID not found in receipt. Account may not have been created."

    info = AccountInfoQuery(account_id=account_id).execute(env.client)

    assert info.account_id == account_id
    assert info.contract_account_id == alias_key.public_key().to_evm_address().to_string()


def test_create_account_with_alias_from_seperate_non_ecdsa_key():
    """Test create_account_transaction raise error when seperate non_ecdsa key is used for alias."""
    public_key = PrivateKey.generate()
    alias_key = PrivateKey.generate_ed25519().public_key()

    tx = AccountCreateTransaction()
    with pytest.raises(ValueError):
        tx.set_key_with_alias(public_key,alias_key)


def test_create_account_with_alias_from_seperate_ecdsa_key_when_not_sign(env):
    """Test create_account_transaction from seperate ecdsa key fails if not sign by alias key."""
    public_key = PrivateKey.generate().public_key()
    alias_key = PrivateKey.generate_ecdsa()
    initial_balance = Hbar(2)

    tx = (
        AccountCreateTransaction(
            initial_balance=initial_balance,
            memo="Recipient Account With alias"
        )
        .set_key_with_alias(public_key, alias_key.public_key())
        .freeze_with(env.client)
    )
    
    receipt = tx.execute(env.client)
    assert receipt.status == ResponseCode.INVALID_SIGNATURE


def test_create_account_with_same_alias(env):
    """Test create_account_transaction fails when creating an account with same alias."""
    private_key = PrivateKey.generate_ecdsa()
    alias_evm_address = private_key.public_key().to_evm_address()
    initial_balance = Hbar(2)

    # Create an account with the alisa_evm_address
    tx1 = (
        AccountCreateTransaction(
            key=private_key.public_key(),
            initial_balance=initial_balance,
            memo="Recipient Account With alias"
        )
        .set_alias(alias_evm_address)
        .freeze_with(env.client)
    )
    
    receipt1 = tx1.execute(env.client)
    account_id = receipt1.account_id
    
    assert receipt1.status == ResponseCode.SUCCESS
    assert receipt1.account_id is not None, "AccountID not found in receipt. Account may not have been created."

    info = AccountInfoQuery(account_id=account_id).execute(env.client)

    assert info.account_id == account_id
    assert info.contract_account_id == alias_evm_address.__str__()

    # Verify that no account with same alias can be created again
    tx2 = (
        AccountCreateTransaction(
            initial_balance=initial_balance,
            memo="Recipient Account With alias",
            key=PrivateKey.generate().public_key()
        )
        .set_alias(alias_evm_address)
        .freeze_with(env.client)
    ).sign(private_key)

    receipt2 = tx2.execute(env.client)
    assert receipt2.status == ResponseCode.ALIAS_ALREADY_ASSIGNED


def test_create_account_with_staked_account_id(env):
    """Test create_account_transaction with staked_account_id set."""
    public_key = PrivateKey.generate().public_key()
    initial_balance = Hbar(2)

    tx = (
        AccountCreateTransaction(
            key=public_key,
            initial_balance=initial_balance,
            memo="Recipient Account With staked_account_id"
        )
        .set_staked_account_id(env.operator_id)
        .freeze_with(env.client)
    )
    
    receipt = tx.execute(env.client)
    account_id = receipt.account_id
    
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.account_id is not None, "AccountID not found in receipt. Account may not have been created."

    info = AccountInfoQuery(account_id=account_id).execute(env.client)

    assert info.account_id == account_id
    assert info.staked_account_id == env.operator_id


def test_create_account_with_staked_node_id(env):
    """Test create_account_transaction with staked_node_id set."""
    public_key = PrivateKey.generate().public_key()
    initial_balance = Hbar(2)

    tx = (
        AccountCreateTransaction(
            key=public_key,
            initial_balance=initial_balance,
            memo="Recipient Account With Staked node_id"
        )
        .set_staked_node_id(1)
        .freeze_with(env.client)
    )
    
    receipt = tx.execute(env.client)
     # This might succeed or fail depending on network state, but should not crash
    assert receipt.status in [
        ResponseCode.SUCCESS,
        ResponseCode.INVALID_STAKING_ID,
    ], f"Unexpected status: {ResponseCode(receipt.status).name}"


def test_create_account_with_decline_reward(env):
    """Test create_account_transaction with staked_account_id set."""
    public_key = PrivateKey.generate().public_key()
    initial_balance = Hbar(2)

    tx = (
        AccountCreateTransaction(
            key=public_key,
            initial_balance=initial_balance,
            memo="Recipient Account decline_reward"
        )
        .set_staked_account_id(env.operator_id)
        .set_decline_staking_reward(True)
        .freeze_with(env.client)
    )
    
    receipt = tx.execute(env.client)
    account_id = receipt.account_id
    
    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.account_id is not None, "AccountID not found in receipt. Account may not have been created."

    info = AccountInfoQuery(account_id=account_id).execute(env.client)

    assert info.account_id == account_id
    assert info.staked_account_id == env.operator_id
    assert info.decline_staking_reward is True
