import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.integration.utils import env

@pytest.mark.integration
def test_transaction_executes_successfully(env):
    """Test transaction can be executed successfully."""
    executor_client = env.client
    executor_key = env.operator_key

    tx = TopicCreateTransaction().set_memo("Test Topic Creation")
    tx.freeze_with(executor_client) 
    tx.sign(executor_key)
    receipt = tx.execute(executor_client)

    # Verify that the transaction_bodys are generated for all nodes present in client network
    assert len(tx._transaction_body_bytes) == len(env.client.network.nodes)
    assert set(tx._transaction_body_bytes.keys()) == {node._account_id for node in env.client.network.nodes}

    assert receipt.status == ResponseCode.SUCCESS, "Transaction must execute successfully"

@pytest.mark.integration
def test_transaction_executes_successfully_with_node_account_ids(env):
    """Test transaction can be executed successfully when node_account_ids are provided."""
    node_account_ids = [AccountId(0,0,3), AccountId(0,0,4)]
    executor_client = env.client
    executor_key = env.operator_key

    tx = TopicCreateTransaction().set_memo("Test Topic Creation")
    tx.set_node_account_ids(node_account_ids)
    tx.freeze_with(executor_client) 
    tx.sign(executor_key)

    # Verify that the transaction_bodys are generated for the provided node_account_ids only
    assert len(tx._transaction_body_bytes) == 2
    assert set(tx._transaction_body_bytes.keys()) == set(node_account_ids)

    receipt = tx.execute(executor_client)
    assert receipt.status == ResponseCode.SUCCESS, "Transaction must execute successfully"

@pytest.mark.integration
def test_transaction_executes_successfully_with_single_node_account_id(env):
    """Test transaction can be executed successfully when single node_account_id are provided."""
    node_account_id = AccountId(0,0,3)
    executor_client = env.client
    executor_key = env.operator_key

    tx = TopicCreateTransaction().set_memo("Test Topic Creation")
    tx.set_node_account_id(node_account_id)
    tx.freeze_with(executor_client) 
    tx.sign(executor_key)

    # Verify that the transaction_bodys are generated for the provided node_account_id only
    assert len(tx._transaction_body_bytes) == 1
    assert set(tx._transaction_body_bytes.keys()) == {node_account_id}

    receipt = tx.execute(executor_client)
    assert receipt.status == ResponseCode.SUCCESS, "Transaction must execute successfully"

@pytest.mark.integration
def test_transaction_executes_successfully_after_manual_freeze(env):
    """Test transaction can be manually frozen and then executed successfully."""
    executor_client = env.client
    executor_key = env.operator_key

    tx = TopicCreateTransaction().set_memo("Test Topic Creation")
    tx_id = TransactionId.generate(executor_client.operator_account_id)
    
    # Manually set Node and ID
    tx.set_transaction_id(tx_id)
    tx.node_account_id = AccountId.from_string("0.0.3") # Explicitly set to 0.0.3
    
    # Manual Freeze (Generates body ONLY for 0.0.3)
    tx.freeze() 
    unsigned_bytes = tx.to_bytes()
    
    assert unsigned_bytes is not None

    tx2 = Transaction.from_bytes(unsigned_bytes)    
    assert tx2 is not None

    tx2.sign(executor_key)
    receipt = tx2.execute(executor_client)

    assert receipt.status == ResponseCode.SUCCESS, "Transaction must execute successfully"

@pytest.mark.integration
def test_transaction_with_secondary_client_can_execute_successfully(env):
    """Test transaction created by the secondary client and then executed successfully."""
    executor_client = env.client
    executor_key = env.operator_key

    tx_freezer_account = env.create_account(1)
    
    # Secondary Client
    tx_freezer_client = Client(network=env.client.network)
    tx_freezer_client.set_operator(tx_freezer_account.id, tx_freezer_account.key)

    tx = TopicCreateTransaction().set_memo("Test Topic Creation")
    tx_id = TransactionId.generate(executor_client.operator_account_id)
    
    tx.set_transaction_id(tx_id)
    tx.freeze_with(tx_freezer_client)
    
    unsigned_bytes = tx.to_bytes()
    assert unsigned_bytes is not None
    
    tx2 = Transaction.from_bytes(unsigned_bytes)
    assert tx2 is not None
    
    tx2.sign(executor_key)
    receipt = tx2.execute(executor_client)

    assert receipt.status == ResponseCode.SUCCESS, "Transaction must execute successfully"

@pytest.mark.integration
def test_transaction_with_secondary_client_without_operator_can_execute_successfully(env):
    """Test transaction created by the secondary client without operator and then executed successfully."""
    executor_client = env.client
    executor_key = env.operator_key
    
    # Secondary Client with no operator account set
    tx_freezer_client = Client(network=env.client.network)

    tx = TopicCreateTransaction().set_memo("Test Topic Creation")
    tx_id = TransactionId.generate(executor_client.operator_account_id)
    
    tx.set_transaction_id(tx_id)
    tx.freeze_with(tx_freezer_client)
    
    unsigned_bytes = tx.to_bytes()
    assert unsigned_bytes is not None
    
    tx2 = Transaction.from_bytes(unsigned_bytes)
    assert tx2 is not None
    
    tx2.sign(executor_key)
    receipt = tx2.execute(executor_client)

    assert receipt.status == ResponseCode.SUCCESS, "Transaction must execute successfully"

