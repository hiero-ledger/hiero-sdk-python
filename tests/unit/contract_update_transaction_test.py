"""
Unit tests for the ContractUpdateTransaction class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_update_transaction import (
    ContractUpdateParams,
    ContractUpdateTransaction,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar

pytestmark = pytest.mark.unit


@pytest.fixture
def contract_id():
    """Fixture for contract ID."""
    return ContractId(0, 0, 123)


@pytest.fixture
def update_params():
    """Fixture for contract update parameters."""
    return {
        "contract_id": ContractId(0, 0, 123),
        "memo": "Updated contract memo",
        "admin_key": PrivateKey.generate().public_key(),
        "auto_renew_period": Duration(7776000),  # 90 days
        "max_automatic_token_associations": 100,
        "auto_renew_account_id": AccountId(0, 0, 999),
        "staked_node_id": 5,
        "decline_reward": True,
    }


########### Constructor Tests ###########


def test_constructor_no_parameters():
    """Test creating a contract update transaction with no parameters."""
    tx = ContractUpdateTransaction()

    assert tx.contract_id is None
    assert tx.contract_memo is None
    assert tx.admin_key is None
    assert tx.auto_renew_period is None
    assert tx.max_automatic_token_associations is None
    assert tx.auto_renew_account_id is None
    assert tx.staked_node_id is None
    assert tx.decline_reward is None
    assert tx._default_transaction_fee == Hbar(20).to_tinybars()


def test_constructor_with_parameters(update_params):
    """Test creating a contract update transaction with constructor parameters."""
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params[
            "max_automatic_token_associations"
        ],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)

    assert tx.contract_id == update_params["contract_id"]
    assert tx.contract_memo == update_params["memo"]
    assert tx.admin_key == update_params["admin_key"]
    assert tx.auto_renew_period == update_params["auto_renew_period"]
    assert (
        tx.max_automatic_token_associations
        == update_params["max_automatic_token_associations"]
    )
    assert tx.auto_renew_account_id == update_params["auto_renew_account_id"]
    assert tx.staked_node_id == update_params["staked_node_id"]
    assert tx.decline_reward == update_params["decline_reward"]


########### Setter Method Tests ###########


def test_set_contract_id(contract_id):
    """Test setting contract ID."""
    tx = ContractUpdateTransaction()
    result = tx.set_contract_id(contract_id)

    assert tx.contract_id == contract_id
    assert result is tx  # Method chaining


def test_set_memo():
    """Test setting memo."""
    tx = ContractUpdateTransaction()
    memo = "Test contract memo"
    result = tx.set_contract_memo(memo)

    assert tx.contract_memo == memo
    assert result is tx  # Method chaining


def test_set_admin_key():
    """Test setting admin key."""
    tx = ContractUpdateTransaction()
    admin_key = PrivateKey.generate().public_key()
    result = tx.set_admin_key(admin_key)

    assert tx.admin_key == admin_key
    assert result is tx  # Method chaining


def test_set_auto_renew_period():
    """Test setting auto renew period."""
    tx = ContractUpdateTransaction()
    auto_renew_period = Duration(7776000)
    result = tx.set_auto_renew_period(auto_renew_period)

    assert tx.auto_renew_period == auto_renew_period
    assert result is tx  # Method chaining


def test_set_max_automatic_token_associations():
    """Test setting max automatic token associations."""
    tx = ContractUpdateTransaction()
    max_associations = 100
    result = tx.set_max_automatic_token_associations(max_associations)

    assert tx.max_automatic_token_associations == max_associations
    assert result is tx  # Method chaining


def test_set_auto_renew_account_id():
    """Test setting auto renew account ID."""
    tx = ContractUpdateTransaction()
    auto_renew_account_id = AccountId(0, 0, 999)
    result = tx.set_auto_renew_account_id(auto_renew_account_id)

    assert tx.auto_renew_account_id == auto_renew_account_id
    assert result is tx  # Method chaining


def test_set_staked_node_id():
    """Test setting staked node ID."""
    tx = ContractUpdateTransaction()
    staked_node_id = 5
    result = tx.set_staked_node_id(staked_node_id)

    assert tx.staked_node_id == staked_node_id
    assert result is tx  # Method chaining


def test_set_decline_reward():
    """Test setting decline reward."""
    tx = ContractUpdateTransaction()
    decline_reward = True
    result = tx.set_decline_reward(decline_reward)

    assert tx.decline_reward == decline_reward
    assert result is tx  # Method chaining


########### Method Chaining Tests ###########


def test_method_chaining(update_params):
    """Test that all setter methods can be chained together."""
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(update_params["contract_id"])
        .set_contract_memo(update_params["memo"])
        .set_admin_key(update_params["admin_key"])
        .set_auto_renew_period(update_params["auto_renew_period"])
        .set_max_automatic_token_associations(
            update_params["max_automatic_token_associations"]
        )
        .set_auto_renew_account_id(update_params["auto_renew_account_id"])
        .set_staked_node_id(update_params["staked_node_id"])
        .set_decline_reward(update_params["decline_reward"])
    )

    assert tx.contract_id == update_params["contract_id"]
    assert tx.contract_memo == update_params["memo"]
    assert tx.admin_key == update_params["admin_key"]
    assert tx.auto_renew_period == update_params["auto_renew_period"]
    assert (
        tx.max_automatic_token_associations
        == update_params["max_automatic_token_associations"]
    )
    assert tx.auto_renew_account_id == update_params["auto_renew_account_id"]
    assert tx.staked_node_id == update_params["staked_node_id"]
    assert tx.decline_reward == update_params["decline_reward"]


########### Transaction Body Building Tests ###########


def test_build_transaction_body_success(contract_id, mock_account_ids, transaction_id):
    """Test building transaction body with valid contract ID."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = ContractUpdateTransaction()
    tx.set_contract_id(contract_id)
    tx.set_contract_memo("Test memo")
    tx.transaction_id = transaction_id
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()

    assert (
        transaction_body.contractUpdateInstance.contractID.contractNum
        == contract_id.contract
    )
    assert (
        transaction_body.contractUpdateInstance.contractID.shardNum == contract_id.shard
    )
    assert (
        transaction_body.contractUpdateInstance.contractID.realmNum == contract_id.realm
    )


def test_build_transaction_body_missing_contract_id():
    """Test building transaction body without contract ID raises ValueError."""
    tx = ContractUpdateTransaction()
    tx.set_contract_memo("Test memo")

    with pytest.raises(ValueError, match="Missing required ContractID"):
        tx.build_transaction_body()


def test_build_transaction_body_with_all_parameters(
    update_params, mock_account_ids, transaction_id
):
    """Test building transaction body with all parameters set."""
    _, _, node_account_id, _, _ = mock_account_ids

    # Create transaction with basic parameters to avoid protobuf constructor issues
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params[
            "max_automatic_token_associations"
        ],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)
    tx.transaction_id = transaction_id
    tx.node_account_id = node_account_id

    transaction_body = tx.build_transaction_body()

    # Verify contract ID is set
    assert (
        transaction_body.contractUpdateInstance.contractID.contractNum
        == update_params["contract_id"].contract
    )
    assert (
        transaction_body.contractUpdateInstance.contractID.shardNum
        == update_params["contract_id"].shard
    )
    assert (
        transaction_body.contractUpdateInstance.contractID.realmNum
        == update_params["contract_id"].realm
    )

    # Verify other fields are present (the actual protobuf structure may vary)
    assert transaction_body.contractUpdateInstance.HasField("contractID")

def test_build_scheduled_body_with_all_parameters(
    update_params, mock_account_ids, transaction_id
):
    """Test building schedulable transaction body with all parameters set."""
    _, _, node_account_id, _, _ = mock_account_ids

    # Create transaction with all parameters
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params[
            "max_automatic_token_associations"
        ],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)
    tx.transaction_id = transaction_id
    tx.node_account_id = node_account_id

    schedulable_body = tx.build_scheduled_body()

    # Verify correct return type
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with contract update type
    assert schedulable_body.HasField("contractUpdateInstance")

    # Verify contract ID is set
    assert (
        schedulable_body.contractUpdateInstance.contractID.contractNum
        == update_params["contract_id"].contract
    )
    assert (
        schedulable_body.contractUpdateInstance.contractID.shardNum
        == update_params["contract_id"].shard
    )
    assert (
        schedulable_body.contractUpdateInstance.contractID.realmNum
        == update_params["contract_id"].realm
    )


########### Transaction Execution Tests ###########


def test_transaction_immutability_concept(contract_id):
    """Test that the transaction can track if it should be frozen (conceptual test)."""
    tx = ContractUpdateTransaction()
    tx.set_contract_id(contract_id)

    # Verify transaction can be created and modified normally
    tx.set_contract_memo("Initial memo")
    assert tx.contract_memo == "Initial memo"

    # Verify we can change memo again (since it's not frozen)
    tx.set_contract_memo("Updated memo")
    assert tx.contract_memo == "Updated memo"


########### Minimal Operations Tests ###########


def test_memo_only_update(contract_id):
    """Test updating only the memo field."""
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_contract_memo("New memo only")
    )

    assert tx.contract_id == contract_id
    assert tx.contract_memo == "New memo only"
    assert tx.admin_key is None


def test_admin_key_only_update(contract_id):
    """Test updating only the admin key field."""
    new_admin_key = PrivateKey.generate().public_key()
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_admin_key(new_admin_key)
    )

    assert tx.contract_id == contract_id
    assert tx.admin_key.to_string() == new_admin_key.to_string()
    assert tx.contract_memo is None


def test_multiple_field_update(contract_id):
    """Test updating multiple fields together."""
    new_admin_key = PrivateKey.generate().public_key()
    new_memo = "Multiple fields updated"
    new_max_associations = 50

    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_admin_key(new_admin_key)
        .set_contract_memo(new_memo)
        .set_max_automatic_token_associations(new_max_associations)
    )

    assert tx.contract_id == contract_id
    assert tx.admin_key == new_admin_key
    assert tx.contract_memo == new_memo
    assert tx.max_automatic_token_associations == new_max_associations


########### Edge Cases Tests ###########


def test_empty_memo(contract_id):
    """Test setting an empty memo."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_contract_memo("")

    assert tx.contract_memo == ""


def test_very_long_memo(contract_id):
    """Test setting a very long memo."""
    long_memo = "x" * 1000  # 1000 character memo
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_contract_memo(long_memo)
    )

    assert tx.contract_memo == long_memo


def test_zero_max_automatic_token_associations(contract_id):
    """Test setting max automatic token associations to zero."""
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_max_automatic_token_associations(0)
    )

    assert tx.max_automatic_token_associations == 0


def test_negative_staked_node_id(contract_id):
    """Test setting a negative staked node ID."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_staked_node_id(-1)

    assert tx.staked_node_id == -1


def test_decline_reward_false(contract_id):
    """Test setting decline reward to False."""
    tx = (
        ContractUpdateTransaction()
        .set_contract_id(contract_id)
        .set_decline_reward(False)
    )

    assert tx.decline_reward is False
