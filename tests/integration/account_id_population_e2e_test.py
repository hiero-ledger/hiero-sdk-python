"""
Integration tests for AccountId.
"""

import time
import pytest
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from tests.integration.utils_for_test import env

@pytest.mark.integration
def test_populate_account_id_num(env):
    """Test populate AccountId num from mirror node."""
    private_key = PrivateKey.generate_ecdsa()
    public_key = private_key.public_key()

    evm_address = public_key.to_evm_address()

    tx_receipt = (
        AccountCreateTransaction()
        .set_initial_balance(1)
        .set_key_with_alias(private_key)
        .freeze_with(env.client)
        .execute(env.client)
    )

    account_id = tx_receipt.account_id
    assert account_id is not None

    # Wait for mirrornode to update
    time.sleep(5)

    mirro_acc_id = AccountId.from_evm_address(evm_address, 0, 0)
    assert mirro_acc_id.num == 0

    mirro_acc_id.populate_account_num(env.client)
    
    assert mirro_acc_id.shard == account_id.shard
    assert mirro_acc_id.realm == account_id.realm
    assert mirro_acc_id.num != 0
    assert mirro_acc_id.num == account_id.num


@pytest.mark.integration
def test_populate_account_id_evm_address(env):
    """Test populate AccountId evm address from mirror node."""
    private_key = PrivateKey.generate_ecdsa()
    public_key = private_key.public_key()

    evm_address = public_key.to_evm_address()

    tx_receipt = (
        AccountCreateTransaction()
        .set_initial_balance(1)
        .set_key_with_alias(private_key)
        .freeze_with(env.client)
        .execute(env.client)
    )

    account_id = tx_receipt.account_id
    assert account_id is not None

    # Wait for mirrornode to update
    time.sleep(5)

    mirro_acc_id = AccountId.from_string(f"{account_id.shard}.{account_id.realm}.{account_id.num}")
    assert mirro_acc_id.evm_address is None
    
    mirro_acc_id.populate_evm_address(env.client)

    assert mirro_acc_id.evm_address is not None
    assert mirro_acc_id.evm_address == evm_address
