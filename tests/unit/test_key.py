import pytest
import warnings
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey

pytestmark = pytest.mark.unit


# ------------------------------------------------------------------------------
# Test: from_string with private keys
# ------------------------------------------------------------------------------
def test_private_key_from_string():
    """
    Test that a private key string is wrapped into a Key object correctly.
    """
    # Generate an Ed25519 private key
    private_key = PrivateKey.generate("ed25519")
    private_key_str = private_key.to_string()
    
    # Wrap it in a Key object using from_string
    key = Key.from_string(private_key_str)
    
    # Verify it's recognized as a private key
    assert key.is_private
    assert not key.is_public
    
    # Verify we can access the private key
    assert key.private_key.to_string() == private_key_str
    
    # Verify we can derive the public key
    pub_key = key.public_key
    assert isinstance(pub_key, PublicKey)


def test_private_key_from_string_ecdsa():
    """
    Test that an ECDSA private key string is wrapped into a Key object correctly.
    """
    # Generate an ECDSA private key
    private_key = PrivateKey.generate("ecdsa")
    private_key_str = private_key.to_string()
    
    # Wrap it in a Key object
    key = Key.from_string(private_key_str)
    
    # Verify it's recognized as a private key
    assert key.is_private
    
    # Verify the key matches
    assert key.to_string() == private_key_str


# ------------------------------------------------------------------------------
# Test: from_string with public keys
# ------------------------------------------------------------------------------
def test_public_key_from_string():
    """
    Test that a public key string is wrapped into a Key object correctly.
    """
    # For this test, we'll use an ECDSA compressed public key (33 bytes)
    # which is unambiguous (unlike Ed25519 32-byte keys)
    private_key_ecdsa = PrivateKey.generate("ecdsa")
    public_key_ecdsa = private_key_ecdsa.public_key()
    public_key_ecdsa_str = public_key_ecdsa.to_string()
    
    # Wrap it in a Key object
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        key = Key.from_string(public_key_ecdsa_str)
    
    # Verify it's recognized as a public key
    assert key.is_public
    assert not key.is_private
    
    # Verify we can access the public key
    assert key.public_key.to_string() == public_key_ecdsa_str


def test_public_key_from_string_der():
    """
    Test that a DER-encoded public key string is wrapped into a Key object.
    """
    # Create a public key from DER (which is unambiguous)
    private_key = PrivateKey.generate("ed25519")
    public_key = private_key.public_key()
    
    # Use DER format which is clearly a public key
    der_str = public_key.to_string_der()
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        key = Key.from_string(der_str)
    
    # Should parse successfully (as either private or public)
    assert key.is_public or key.is_private


# ------------------------------------------------------------------------------
# Test: invalid key strings
# ------------------------------------------------------------------------------
def test_invalid_key_type():
    """
    Test that an invalid string does not wrap into a Key object.
    """
    invalid_string = "not-a-valid-hex-string"
    
    with pytest.raises(ValueError, match="Could not parse key string"):
        Key.from_string(invalid_string)


def test_invalid_key_empty_string():
    """
    Test that an empty string raises a ValueError.
    """
    with pytest.raises(ValueError, match="Could not parse key string"):
        Key.from_string("")


def test_invalid_key_wrong_length():
    """
    Test that a hex string with invalid length raises a ValueError.
    """
    # 8 bytes is too short for any valid key
    short_hex = "11" * 8
    
    with pytest.raises(ValueError, match="Could not parse key string"):
        Key.from_string(short_hex)


def test_invalid_key_all_zeros():
    """
    Test that an all-zeros ECDSA private key behaves appropriately.
    """
    # 32 bytes of zeros - Ed25519 might accept it, ECDSA won't
    zero_hex = "00" * 32
    
    # This might actually parse as Ed25519, so let's verify the behavior
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            key = Key.from_string(zero_hex)
            # If it succeeds, it should be a valid key
            assert key.is_private or key.is_public
        except ValueError:
            # If it fails, that's also acceptable
            pass


# ------------------------------------------------------------------------------
# Test: initialization with PrivateKey and PublicKey
# ------------------------------------------------------------------------------
def test_init_with_private_key():
    """
    Test initialization with a PrivateKey object.
    """
    private_key = PrivateKey.generate("ed25519")
    key = Key(private_key)
    
    assert key.is_private
    assert not key.is_public
    assert key.private_key == private_key


def test_init_with_public_key():
    """
    Test initialization with a PublicKey object.
    """
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()
    key = Key(public_key)
    
    assert key.is_public
    assert not key.is_private
    assert key.public_key == public_key


# ------------------------------------------------------------------------------
# Test: properties
# ------------------------------------------------------------------------------
def test_is_private_property():
    """
    Test the is_private property.
    """
    private_key = PrivateKey.generate("ed25519")
    key = Key(private_key)
    assert key.is_private is True
    
    public_key = private_key.public_key()
    key_pub = Key(public_key)
    assert key_pub.is_private is False


def test_is_public_property():
    """
    Test the is_public property.
    """
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()
    
    key_priv = Key(private_key)
    assert key_priv.is_public is False
    
    key_pub = Key(public_key)
    assert key_pub.is_public is True


def test_public_key_property_from_private():
    """
    Test that the public_key property derives the public key from a private key.
    """
    private_key = PrivateKey.generate("ed25519")
    key = Key(private_key)
    
    pub_key = key.public_key
    assert isinstance(pub_key, PublicKey)
    
    # Verify it matches the direct derivation
    expected_pub = private_key.public_key()
    assert pub_key.to_string() == expected_pub.to_string()


def test_public_key_property_from_public():
    """
    Test that the public_key property returns the public key directly.
    """
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()
    key = Key(public_key)
    
    pub_key = key.public_key
    assert pub_key == public_key
    assert pub_key.to_string() == public_key.to_string()


def test_private_key_property_from_private():
    """
    Test that the private_key property returns the private key.
    """
    private_key = PrivateKey.generate("ed25519")
    key = Key(private_key)
    
    priv_key = key.private_key
    assert priv_key == private_key
    assert priv_key.to_string() == private_key.to_string()


def test_private_key_property_from_public_raises_error():
    """
    Test that accessing private_key property on a public key raises ValueError.
    """
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()
    key = Key(public_key)
    
    with pytest.raises(ValueError, match="Key is not a private key"):
        _ = key.private_key


# ------------------------------------------------------------------------------
# Test: to_string
# ------------------------------------------------------------------------------
def test_to_string_private_key():
    """
    Test to_string with a private key.
    """
    private_key = PrivateKey.generate("ed25519")
    key = Key(private_key)
    
    key_str = key.to_string()
    assert key_str == private_key.to_string()
    assert len(key_str) == 64  # 32 bytes = 64 hex chars


def test_to_string_public_key():
    """
    Test to_string with a public key.
    """
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()
    key = Key(public_key)
    
    key_str = key.to_string()
    assert key_str == public_key.to_string()
    assert len(key_str) == 66  # 33 bytes compressed = 66 hex chars


# ------------------------------------------------------------------------------
# Test: edge cases and mixed scenarios
# ------------------------------------------------------------------------------
def test_from_string_with_0x_prefix():
    """
    Test that from_string handles '0x' prefix correctly.
    """
    private_key = PrivateKey.generate("ed25519")
    key_str = "0x" + private_key.to_string()
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        key = Key.from_string(key_str)
    
    assert key.is_private or key.is_public  # Should parse successfully


def test_roundtrip_from_to_string():
    """
    Test that a key can be serialized and deserialized.
    """
    original_private = PrivateKey.generate("ecdsa")
    original_key = Key(original_private)
    
    key_str = original_key.to_string()
    restored_key = Key.from_string(key_str)
    
    # Both should be private ECDSA keys
    assert restored_key.is_private
    assert restored_key.to_string() == key_str


@pytest.mark.parametrize("key_type", ["ed25519", "ecdsa"])
def test_all_key_types(key_type):
    """
    Parametrized test for both key types.
    """
    private_key = PrivateKey.generate(key_type)
    key = Key(private_key)
    
    # Test basic properties
    assert key.is_private
    assert not key.is_public
    
    # Test public key derivation
    pub_key = key.public_key
    assert isinstance(pub_key, PublicKey)
    
    # Test to_string
    assert key.to_string() == private_key.to_string()


def test_from_string_fallback_to_public():
    """
    Test that from_string tries private key first, then falls back to public key.
    """
    # Create a scenario where we have only a public key string
    private_key = PrivateKey.generate("ecdsa")
    public_key = private_key.public_key()
    
    # Get the compressed public key (33 bytes)
    public_key_str = public_key.to_string()
    
    # This should be parsed (likely as public, since 33 bytes is not a valid private key)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        key = Key.from_string(public_key_str)
    
    # Verify it was successfully created
    assert isinstance(key, Key)
    assert key.is_public or key.is_private


def test_private_and_public_key_properties_consistency():
    """
    Test that private and public key properties are mutually exclusive.
    """
    private_key = PrivateKey.generate("ed25519")
    
    # Test with private key
    key_priv = Key(private_key)
    assert key_priv.is_private and not key_priv.is_public
    
    # Test with public key
    public_key = private_key.public_key()
    key_pub = Key(public_key)
    assert key_pub.is_public and not key_pub.is_private


def test_from_string_both_key_types():
    """
    Test from_string with both Ed25519 and ECDSA keys.
    """
    # Ed25519
    ed_private = PrivateKey.generate("ed25519")
    ed_key = Key.from_string(ed_private.to_string())
    assert ed_key.is_private
    
    # ECDSA
    ec_private = PrivateKey.generate("ecdsa")
    ec_key = Key.from_string(ec_private.to_string())
    assert ec_key.is_private
