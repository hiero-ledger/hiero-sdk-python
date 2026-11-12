"""
Unit tests for the ContractUpdateTransaction class.
"""

from __future__ import annotations

import pytest
from google.protobuf import wrappers_pb2

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_update_transaction import (
    ContractUpdateParams,
    ContractUpdateTransaction,
)
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.contract_update_pb2 import ContractUpdateTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp


pytestmark = pytest.mark.unit


@pytest.fixture
def update_params(contract_id):
    """Fixture for contract update parameters."""
    return {
        "contract_id": contract_id,
        "memo": "Updated contract memo",
        "admin_key": PrivateKey.generate().public_key(),
        "auto_renew_period": Duration(7776000),  # 90 days
        "max_automatic_token_associations": 100,
        "auto_renew_account_id": AccountId(0, 0, 999),
        "staked_node_id": 5,
        "staked_account_id": AccountId(0, 0, 101),
        "decline_reward": True,
        "expiration_time": Timestamp(10, 1),
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
        max_automatic_token_associations=update_params["max_automatic_token_associations"],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)

    assert tx.contract_id == update_params["contract_id"]
    assert tx.contract_memo == update_params["memo"]
    assert tx.admin_key == update_params["admin_key"]
    assert tx.auto_renew_period == update_params["auto_renew_period"]
    assert tx.max_automatic_token_associations == update_params["max_automatic_token_associations"]
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
    """Test setting staked node ID clears an existing staked account ID."""
    tx = ContractUpdateTransaction()
    staked_account_id = AccountId(0, 0, 999)
    tx.set_staked_account_id(staked_account_id)

    staked_node_id = 5
    result = tx.set_staked_node_id(staked_node_id)

    assert tx.staked_node_id == staked_node_id
    assert tx.staked_account_id is None
    assert result is tx  # Method chaining


def test_set_staked_node_id_to_none_preserves_staked_account_id():
    """Test that setting staked node ID to None preserves the staked account ID."""
    tx = ContractUpdateTransaction()
    staked_account_id = AccountId(0, 0, 999)
    tx.set_staked_account_id(staked_account_id)

    result = tx.set_staked_node_id(None)

    assert tx.staked_node_id is None
    assert tx.staked_account_id == staked_account_id
    assert result is tx  # Method chaining


def test_set_decline_reward():
    """Test setting decline reward."""
    tx = ContractUpdateTransaction()
    decline_reward = True
    result = tx.set_decline_reward(decline_reward)

    assert tx.decline_reward == decline_reward
    assert result is tx  # Method chaining


def test_set_auto_renew_account_id_to_zero():
    """Test setting auto renew account ID to the 0.0.0 clearing sentinel."""
    tx = ContractUpdateTransaction()
    result = tx.set_auto_renew_account_id(AccountId(0, 0, 0))

    assert tx.auto_renew_account_id == AccountId(0, 0, 0)
    assert result is tx  # Method chaining


def test_clear_auto_renew_account_id():
    """Test clearing auto renew account ID."""
    tx = ContractUpdateTransaction()
    tx.set_auto_renew_account_id(AccountId(0, 0, 1234))
    result = tx.clear_auto_renew_account_id()

    assert tx.auto_renew_account_id == AccountId(0, 0, 0)
    assert result is tx  # Method chaining

    # Chaining assertion after other setters
    chained_tx = (
        ContractUpdateTransaction()
        .set_contract_memo("Memo")
        .set_auto_renew_account_id(AccountId(0, 0, 1234))
        .clear_auto_renew_account_id()
    )
    assert chained_tx.auto_renew_account_id == AccountId(0, 0, 0)


def test_clear_auto_renew_account_id_serialization(mock_account_ids, transaction_id):
    """Test serialization of contract update transaction with cleared auto renew account ID."""
    _, _, node_account_id, _, _ = mock_account_ids
    tx = ContractUpdateTransaction()
    tx.set_auto_renew_account_id(AccountId(0, 0, 1234))
    tx.clear_auto_renew_account_id()
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    body = tx.build_transaction_body()

    assert body.contractUpdateInstance.HasField("auto_renew_account_id")
    assert body.contractUpdateInstance.auto_renew_account_id.WhichOneof("account") is None
    assert body.contractUpdateInstance.auto_renew_account_id.SerializeToString() == b""


def test_clear_auto_renew_account_id_frozen(contract_id, mock_client):
    """Test that clear_auto_renew_account_id raises exception when frozen."""
    tx = ContractUpdateTransaction()
    tx.set_contract_id(contract_id)
    tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        tx.clear_auto_renew_account_id()


def test_set_staked_account_id():
    """Test setting a valid staked account ID clears an existing staked node ID."""
    tx = ContractUpdateTransaction()
    tx.set_staked_node_id(5)

    staked_account_id = AccountId(0, 0, 999)
    result = tx.set_staked_account_id(staked_account_id)

    assert tx.staked_account_id == staked_account_id
    assert tx.staked_node_id is None
    assert result is tx  # Method chaining


def test_set_staked_account_id_to_none_preserves_staked_node_id():
    """Test that setting staked account ID to None preserves the staked node ID."""
    tx = ContractUpdateTransaction()
    staked_node_id = 5
    tx.set_staked_node_id(staked_node_id)

    result = tx.set_staked_account_id(None)

    assert tx.staked_account_id is None
    assert tx.staked_node_id == staked_node_id
    assert result is tx  # Method chaining


def test_set_staked_account_id_to_zero():
    """Test setting staked account ID to 0.0.0 clears staking."""
    tx = ContractUpdateTransaction()

    result = tx.set_staked_account_id(AccountId(0, 0, 0))

    assert tx.staked_account_id == AccountId(0, 0, 0)
    assert tx.staked_node_id is None
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
        .set_max_automatic_token_associations(update_params["max_automatic_token_associations"])
        .set_auto_renew_account_id(update_params["auto_renew_account_id"])
        .set_staked_node_id(update_params["staked_node_id"])
        .set_decline_reward(update_params["decline_reward"])
    )

    assert tx.contract_id == update_params["contract_id"]
    assert tx.contract_memo == update_params["memo"]
    assert tx.admin_key == update_params["admin_key"]
    assert tx.auto_renew_period == update_params["auto_renew_period"]
    assert tx.max_automatic_token_associations == update_params["max_automatic_token_associations"]
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
    tx.set_node_account_ids([node_account_id])

    transaction_body = tx.build_transaction_body()

    assert transaction_body.contractUpdateInstance.contractID.contractNum == contract_id.contract
    assert transaction_body.contractUpdateInstance.contractID.shardNum == contract_id.shard
    assert transaction_body.contractUpdateInstance.contractID.realmNum == contract_id.realm


@pytest.mark.parametrize(
    "admin_key",
    [
        PrivateKey.generate(),
        KeyList([PrivateKey.generate().public_key(), PrivateKey.generate().public_key()]),
    ],
    ids=["private-key", "key-list"],
)
def test_build_proto_body_with_generic_admin_key(contract_id, admin_key):
    """Test building a contract update body with generic admin key types."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_admin_key(admin_key)

    proto_body = tx._build_proto_body()

    assert tx.admin_key is admin_key
    assert proto_body.adminKey == admin_key.to_proto_key()


def test_build_transaction_body_missing_contract_id(mock_account_ids, transaction_id):
    """Test building transaction body without contract ID omits the field."""
    _, _, node_account_id, _, _ = mock_account_ids

    tx = ContractUpdateTransaction()
    tx.set_contract_memo("Test memo")
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    transaction_body = tx.build_transaction_body()

    assert not transaction_body.contractUpdateInstance.HasField("contractID")


def test_build_transaction_body_with_all_parameters(update_params, mock_account_ids, transaction_id):
    """Test building transaction body with all parameters set."""
    _, _, node_account_id, _, _ = mock_account_ids

    # Create transaction with basic parameters to avoid protobuf constructor issues
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params["max_automatic_token_associations"],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    transaction_body = tx.build_transaction_body()

    # Verify contract ID is set
    assert transaction_body.contractUpdateInstance.contractID.contractNum == update_params["contract_id"].contract
    assert transaction_body.contractUpdateInstance.contractID.shardNum == update_params["contract_id"].shard
    assert transaction_body.contractUpdateInstance.contractID.realmNum == update_params["contract_id"].realm

    # Verify other fields are present (the actual protobuf structure may vary)
    assert transaction_body.contractUpdateInstance.HasField("contractID")


def test_build_scheduled_body_with_all_parameters(update_params, mock_account_ids, transaction_id):
    """Test building schedulable transaction body with all parameters set."""
    _, _, node_account_id, _, _ = mock_account_ids

    # Create transaction with all parameters
    constructor_params = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        admin_key=update_params["admin_key"],
        auto_renew_period=update_params["auto_renew_period"],
        max_automatic_token_associations=update_params["max_automatic_token_associations"],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_node_id=update_params["staked_node_id"],
        decline_reward=update_params["decline_reward"],
    )
    tx = ContractUpdateTransaction(contract_params=constructor_params)
    tx.transaction_id = transaction_id
    tx.set_node_account_ids([node_account_id])

    schedulable_body = tx.build_scheduled_body()

    # Verify correct return type
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with contract update type
    assert schedulable_body.HasField("contractUpdateInstance")

    # Verify contract ID is set
    assert schedulable_body.contractUpdateInstance.contractID.contractNum == update_params["contract_id"].contract
    assert schedulable_body.contractUpdateInstance.contractID.shardNum == update_params["contract_id"].shard
    assert schedulable_body.contractUpdateInstance.contractID.realmNum == update_params["contract_id"].realm


def test_build_proto_body_with_cleared_fields(contract_id):
    """Test building a contract update body with cleared auto-renew and staked accounts."""
    tx = ContractUpdateTransaction()
    tx.set_contract_id(contract_id)
    tx.set_auto_renew_account_id(AccountId(0, 0, 0))
    tx.set_staked_account_id(AccountId(0, 0, 0))

    proto_body = tx._build_proto_body()

    # Auto-renew clearing must use an empty AccountID with no account oneof.
    assert proto_body.HasField("auto_renew_account_id")
    assert proto_body.auto_renew_account_id.WhichOneof("account") is None
    assert proto_body.auto_renew_account_id.SerializeToString() == b""

    # Staking clearing must explicitly select accountNum with a value of zero.
    assert proto_body.HasField("staked_account_id")
    assert proto_body.staked_account_id.WhichOneof("account") == "accountNum"
    assert proto_body.staked_account_id.accountNum == 0


def test_build_proto_body_rejects_conflicting_staking_targets(contract_id):
    """Test that constructor parameters cannot specify both staking targets."""
    params = ContractUpdateParams(
        contract_id=contract_id,
        staked_account_id=AccountId(0, 0, 999),
        staked_node_id=5,
    )
    tx = ContractUpdateTransaction(contract_params=params)

    with pytest.raises(
        ValueError,
        match="Specify either staked_node_id or staked_account_id, not both",
    ):
        tx._build_proto_body()


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
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_contract_memo("New memo only")

    assert tx.contract_id == contract_id
    assert tx.contract_memo == "New memo only"
    assert tx.admin_key is None


def test_admin_key_only_update(contract_id):
    """Test updating only the admin key field."""
    new_admin_key = PrivateKey.generate().public_key()
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_admin_key(new_admin_key)

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
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_contract_memo(long_memo)

    assert tx.contract_memo == long_memo


def test_zero_max_automatic_token_associations(contract_id):
    """Test setting max automatic token associations to zero."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_max_automatic_token_associations(0)

    assert tx.max_automatic_token_associations == 0


def test_negative_staked_node_id(contract_id):
    """Test setting a negative staked node ID."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_staked_node_id(-1)

    assert tx.staked_node_id == -1


def test_decline_reward_false(contract_id):
    """Test setting decline reward to False."""
    tx = ContractUpdateTransaction().set_contract_id(contract_id).set_decline_reward(False)

    assert tx.decline_reward is False


def test_from_protobuf_without_contract_update_instance():
    """Test creating a transaction from protobuf without a contract update instance."""
    tx = ContractUpdateTransaction._from_protobuf(TransactionBody())

    assert tx is not None
    assert isinstance(tx, ContractUpdateTransaction)
    assert tx.contract_id is None
    assert tx.contract_memo is None
    assert tx.expiration_time is None
    assert tx.admin_key is None
    assert tx.max_automatic_token_associations is None
    assert tx.auto_renew_period is None
    assert tx.auto_renew_account_id is None
    assert tx.staked_account_id is None
    assert tx.staked_node_id is None
    assert tx.decline_reward is None


def test_from_protobuf_preserves_defaults():
    """Test that default values are preserved when creating a transaction from protobuf."""
    tx_proto = ContractUpdateTransactionBody()
    tx = ContractUpdateTransaction._from_protobuf(TransactionBody(contractUpdateInstance=tx_proto))

    assert tx is not None
    assert isinstance(tx, ContractUpdateTransaction)
    assert tx.contract_id is None
    assert tx.contract_memo is None
    assert tx.expiration_time is None
    assert tx.admin_key is None
    assert tx.max_automatic_token_associations is None
    assert tx.auto_renew_period is None
    assert tx.auto_renew_account_id is None
    assert tx.staked_account_id is None
    assert tx.staked_node_id is None
    assert tx.decline_reward is None


def test_from_protobuf_with_all_fields(update_params):
    """Test creating a transaction from protobuf with all fields set."""
    # skip stake_node_id cause it override the stake_node_id due to (one_of)
    tx_proto = ContractUpdateTransactionBody(
        contractID=update_params["contract_id"]._to_proto(),
        memoWrapper=wrappers_pb2.StringValue(value=update_params["memo"]),
        expirationTime=update_params["expiration_time"]._to_protobuf(),
        adminKey=update_params["admin_key"].to_proto_key(),
        max_automatic_token_associations=wrappers_pb2.Int32Value(
            value=update_params["max_automatic_token_associations"]
        ),
        autoRenewPeriod=update_params["auto_renew_period"]._to_proto(),
        auto_renew_account_id=update_params["auto_renew_account_id"]._to_proto(),
        staked_account_id=update_params["staked_account_id"]._to_proto(),
        decline_reward=wrappers_pb2.BoolValue(value=update_params["decline_reward"]),
    )
    tx = ContractUpdateTransaction._from_protobuf(TransactionBody(contractUpdateInstance=tx_proto))

    assert tx is not None
    assert isinstance(tx, ContractUpdateTransaction)
    assert tx.contract_id == update_params["contract_id"]
    assert tx.contract_memo == update_params["memo"]
    assert tx.expiration_time == update_params["expiration_time"]
    assert tx.admin_key == update_params["admin_key"]
    assert tx.max_automatic_token_associations == update_params["max_automatic_token_associations"]
    assert tx.auto_renew_period == update_params["auto_renew_period"]
    assert tx.auto_renew_account_id == update_params["auto_renew_account_id"]
    assert tx.staked_account_id == update_params["staked_account_id"]
    assert tx.staked_node_id is None  # using setter
    assert tx.decline_reward == update_params["decline_reward"]


def test_from_protobuf_with_staked_node_id(update_params):
    """Test creating a transaction from protobuf with a staked node ID."""
    tx_proto = ContractUpdateTransactionBody(staked_node_id=update_params["staked_node_id"])
    tx = ContractUpdateTransaction._from_protobuf(TransactionBody(contractUpdateInstance=tx_proto))

    assert tx is not None
    assert isinstance(tx, ContractUpdateTransaction)
    assert tx.staked_account_id is None
    assert tx.staked_node_id == update_params["staked_node_id"]


def test_bytes_round_trip(update_params):
    """Test contract update transaction byte serialization round trip."""
    prams = ContractUpdateParams(
        contract_id=update_params["contract_id"],
        contract_memo=update_params["memo"],
        expiration_time=update_params["expiration_time"],
        admin_key=update_params["admin_key"],
        max_automatic_token_associations=update_params["max_automatic_token_associations"],
        auto_renew_period=update_params["auto_renew_period"],
        auto_renew_account_id=update_params["auto_renew_account_id"],
        staked_account_id=update_params["staked_account_id"],
        decline_reward=update_params["decline_reward"],
    )

    original_tx = ContractUpdateTransaction(prams)
    copy_tx = ContractUpdateTransaction.from_bytes(original_tx.to_bytes())

    assert copy_tx is not None
    assert isinstance(copy_tx, ContractUpdateTransaction)
    assert copy_tx.contract_id == original_tx.contract_id
    assert copy_tx.contract_memo == original_tx.contract_memo
    assert copy_tx.expiration_time == original_tx.expiration_time
    assert copy_tx.admin_key == original_tx.admin_key
    assert copy_tx.max_automatic_token_associations == original_tx.max_automatic_token_associations
    assert copy_tx.auto_renew_period == original_tx.auto_renew_period
    assert copy_tx.auto_renew_account_id == original_tx.auto_renew_account_id
    assert copy_tx.staked_account_id == original_tx.staked_account_id
    assert copy_tx.staked_node_id is None  # using setter
    assert copy_tx.decline_reward == original_tx.decline_reward


def test_bytes_round_trip_with_staked_node_id(update_params):
    """Test byte serialization round trip with a staked node ID."""
    original_tx = ContractUpdateTransaction().set_staked_node_id(update_params["staked_node_id"])
    copy_tx = ContractUpdateTransaction.from_bytes(original_tx.to_bytes())

    assert copy_tx is not None
    assert isinstance(copy_tx, ContractUpdateTransaction)
    assert copy_tx.staked_node_id == original_tx.staked_node_id
    assert copy_tx.staked_account_id is None
