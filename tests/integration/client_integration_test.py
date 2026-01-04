import pytest
from hiero_sdk_python import Client, PrivateKey, AccountId

"""Integration tests for factory methods with operator setup."""
def test_for_testnet_then_set_operator():
    """Test for_testnet factory followed by set_operator."""
    client = Client.for_testnet()
    
    # Generate valid credentials
    # Assuming AccountId constructor takes (shard, realm, num)
    operator_id = AccountId(0, 0, 12345)
    operator_key = PrivateKey.generate_ed25519()
    
    client.set_operator(operator_id, operator_key)
    
    # Verify operator was set correctly
    assert client.operator_account_id == operator_id
    assert client.operator_private_key.to_string() == operator_key.to_string()
    assert client.operator is not None
    assert client.network.network == "testnet"
    
    client.close()
    
def test_for_mainnet_then_set_operator():
    """Test for_mainnet factory followed by set_operator."""
    client = Client.for_mainnet()
    
    operator_id = AccountId(0, 0, 67890)
    operator_key = PrivateKey.generate_ecdsa()
    client.set_operator(operator_id, operator_key)
    
    assert client.operator_account_id == operator_id
    assert client.operator_private_key.to_string() == operator_key.to_string()
    assert client.network.network == "mainnet"
    
    client.close()
    
def test_factory_methods_return_different_instances():
    """Test that factory methods return new instances."""
    client1 = Client.for_testnet()
    client2 = Client.for_testnet()
    
    assert client1 is not client2
    
    client1.close()
    client2.close()