import pytest
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2

def test_to_proto_key_with_ed25519_public_key():
    """Tests _to_proto_key with an Ed25519 PublicKey """
    tx = TokenCreateTransaction()
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()
    
    expected_proto = public_key._to_proto()
    result_proto = tx._to_proto_key(public_key)
    
    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)

def test_to_proto_key_with_ecdsa_public_key():
    """Tests _to_proto_key with an ECDSA PublicKey """
    tx = TokenCreateTransaction()
    private_key = PrivateKey.generate_ecdsa()
    public_key = private_key.public_key()
    
    expected_proto = public_key._to_proto()
    result_proto = tx._to_proto_key(public_key)
    
    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)

def test_to_proto_key_with_ed25519_private_key():
    """Tests _to_proto_key with an Ed25519 PrivateKey (Backward-Compatibility)."""
    tx = TokenCreateTransaction()
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()
    
    expected_proto = public_key._to_proto()
    result_proto = tx._to_proto_key(private_key)
    
    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)

def test_to_proto_key_with_ecdsa_private_key():
    """Tests _to_proto_key with an ECDSA PrivateKey (Backward-Compatibility)."""
    tx = TokenCreateTransaction()
    private_key = PrivateKey.generate_ecdsa()
    public_key = private_key.public_key()
    
    expected_proto = public_key._to_proto()
    result_proto = tx._to_proto_key(private_key)
    
    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)

def test_to_proto_key_with_none():
    """Tests the _to_proto_key function with None."""
    tx = TokenCreateTransaction()
    result = tx._to_proto_key(None)
    assert result is None

def test_to_proto_key_with_invalid_string_raises_error():
    """Tests the _to_proto_key safety net with a string."""
    tx = TokenCreateTransaction()
    
    with pytest.raises(TypeError) as e:
        tx._to_proto_key("this is not a key")
        
    assert "Key must be of type PrivateKey or PublicKey" in str(e.value)

# =================================================================
# Tests for _build_proto_body (The Refactored Tests)
# =================================================================

def test_set_keys_with_private_key_generates_public_in_proto(mock_account_ids):
    """Verify PrivateKey in setter results in PublicKey in proto body."""
    priv = PrivateKey.generate()
    tx = TokenCreateTransaction()
    
    # Using the PrivateKey
    tx.set_supply_key(priv)

    # Using the fixture correctly
    acct = mock_account_ids[0]
    tx.set_treasury_account_id(acct)
    tx.set_initial_supply(1)
    tx.set_token_name("T")
    tx.set_token_symbol("TKN")

    body = tx._build_proto_body()
    
    assert body.supplyKey == priv.public_key()._to_proto()

def test_set_keys_with_public_key(mock_account_ids):
    """Verify PublicKey in setter results in PublicKey in proto body."""
    priv = PrivateKey.generate()
    pub = priv.public_key()
    tx = TokenCreateTransaction()
    
    # Using the PublicKey
    tx.set_supply_key(pub)

    acct = mock_account_ids[0]
    tx.set_treasury_account_id(acct)
    tx.set_initial_supply(1)
    tx.set_token_name("T2")
    tx.set_token_symbol("TKN2")

    body = tx._build_proto_body()
    
    assert body.supplyKey == pub._to_proto()

@pytest.mark.parametrize("algo", ["ed25519", "ecdsa"])
def test_both_key_algorithms_work(algo, mock_account_ids):
    """Verify both key types work in setters (Private and Public)."""
    if algo == "ed25519":
        priv = PrivateKey.generate_ed25519()
    else:
        priv = PrivateKey.generate_ecdsa()

    pub = priv.public_key()
    tx = TokenCreateTransaction()
    
    # Setting one key with Private, one with Public
    tx.set_admin_key(priv)
    tx.set_supply_key(pub)

    acct = mock_account_ids[0]
    tx.set_treasury_account_id(acct)
    tx.set_initial_supply(1)
    tx.set_token_name("T3")
    tx.set_token_symbol("T3")

    body = tx._build_proto_body()
    
    # Using the STRONG asserts for both
    assert body.adminKey == priv.public_key()._to_proto()
    assert body.supplyKey == pub._to_proto()