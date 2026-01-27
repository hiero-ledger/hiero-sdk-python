import pytest
import warnings
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import utils as asym_utils
from cryptography.exceptions import InvalidSignature
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.hapi.services.basic_types_pb2 import Key
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.utils.crypto_utils import keccak256

pytestmark = pytest.mark.unit


@pytest.fixture
def ed25519_keypair():
    """Returns (private_key, public_key) for Ed25519."""
    private = ed25519.Ed25519PrivateKey.generate()
    public = private.public_key()
    return private, public


@pytest.fixture
def ecdsa_keypair():
    """Returns (private_key, public_key) for ECDSA with secp256k1."""
    private = ec.generate_private_key(ec.SECP256K1())
    public = private.public_key()
    return private, public


# ------------------------------------------------------------------------------
# Test: from_bytes_ed25519
# ------------------------------------------------------------------------------
def test_from_bytes_ed25519_valid(ed25519_keypair):
    # ed25519_keypair fixture returns (private_key, public_key) but only use public
    _, public = ed25519_keypair

    # Serialize the public key into its “raw” 32-byte form
    raw_bytes = public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    # Ed25519 public keys are always exactly 32 bytes
    assert len(raw_bytes) == 32

    # The loader emits a warning because a 32-byte blob could also be
    # an Ed25519 *private* seed
    with pytest.warns(UserWarning, match="cannot distinguish Ed25519 private seeds"):
        # Attempt to construct a PublicKey wrapper from the raw bytes
        pubk = PublicKey.from_bytes_ed25519(raw_bytes)

    # Confirm that the wrapper recognized it as an Ed25519 key
    assert pubk.is_ed25519()

    # Confirm that converting it back to raw bytes also yields 32 bytes
    assert len(pubk.to_bytes_ed25519()) == 32


def test_from_bytes_ed25519_wrong_length():
    # 31 bytes is incorrect
    data = b"\x01" * 31
    with pytest.raises(ValueError, match="must be 32 bytes"):
        PublicKey.from_bytes_ed25519(data)


def test_from_bytes_ed25519_private_seed(ed25519_keypair):
    """
    Demonstrate that from_bytes_ed25519 cannot tell a private seed apart
    from a public key: it will emit the same warning and return a PublicKey
    whose raw bytes round-trip to exactly the seed.
    """
    priv, _ = ed25519_keypair

    seed = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    assert len(seed) == 32

    with pytest.warns(UserWarning, match="cannot distinguish Ed25519 private seeds"):
        pk = PublicKey.from_bytes_ed25519(seed)

    # …and still treat it as “Ed25519 public” under the hood
    assert pk.is_ed25519()

    # Round-tripping back to raw bytes returns the same 32 bytes (the seed)
    assert pk.to_bytes_ed25519() == seed


# ------------------------------------------------------------------------------
# Test: from_bytes_ecdsa
# ------------------------------------------------------------------------------
def test_from_bytes_ecdsa_compressed_valid(ecdsa_keypair):
    _, pub = ecdsa_keypair

    # Serialize the public key into its SEC1 compressed form (33 bytes):
    compressed = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,  # Compressed
    )
    assert len(compressed) == 33

    # Load the wrapper from the raw compressed point
    pubk = PublicKey.from_bytes_ecdsa(compressed)

    # It should detect and wrap an ECDSA (secp256k1) key
    assert pubk.is_ecdsa()

    # Round-trip: exporting back to compressed bytes should exactly match input
    assert pubk.to_bytes_ecdsa() == compressed


def test_from_bytes_ecdsa_uncompressed_valid(ecdsa_keypair):
    _, pub = ecdsa_keypair

    # Serialize the public key into its SEC1 uncompressed form (65 bytes):
    uncompressed = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,  # Uncompressed
    )
    assert len(uncompressed) == 65

    pubk = PublicKey.from_bytes_ecdsa(uncompressed)

    # It should detect and wrap an ECDSA (secp256k1) key
    assert pubk.is_ecdsa()

    # When exporting, PublicKey always emits the compressed form:
    compressed = pubk.to_bytes_ecdsa()

    # The first byte should be 0x02 or 0x03, indicating the parity of Y
    assert compressed[0] in (2, 3)

    # And the total length of the compressed point must be 33 bytes
    assert len(compressed) == 33


def test_from_bytes_ecdsa_wrong_length():
    # 32 bytes is not a valid ECDSA public point
    data = b"\x02" + b"\x00" * 31
    with pytest.raises(ValueError, match="must be 33 or 65 bytes"):
        PublicKey.from_bytes_ecdsa(data)


def test_from_bytes_ecdsa_invalid():
    # 33 bytes but invalid prefix or data
    # 0x05 is not a valid secp256k1 prefix (should be 0x02 or 0x03 if compressed)
    data = b"\x05" + b"\x00" * 32
    with pytest.raises(ValueError, match="Invalid ECDSA public key bytes"):
        PublicKey.from_bytes_ecdsa(data)


# ------------------------------------------------------------------------------
# Test: from_der
# ------------------------------------------------------------------------------
def test_from_der_ed25519(ed25519_keypair):
    """
    Generate an Ed25519 public key in DER‐encoded SPKI form and load it
    via the wrapper, then verify round-trip DER output.
    """
    _, pub = ed25519_keypair

    # Serialize to DER-encoded SubjectPublicKeyInfo
    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pubk = PublicKey.from_der(der)

    # It should detect it is Ed25519
    assert pubk.is_ed25519()

    # Converting back to DER should match the original bytes exactly
    assert pubk.to_bytes_der() == der


def test_from_der_ecdsa(ecdsa_keypair):
    """
    Generate an ECDSA (secp256k1) public key in DER-encoded SPKI form and load it,
    then verify round-trip DER output.
    """
    _, pub = ecdsa_keypair

    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pk = PublicKey.from_der(der)

    # It should detect it is ECDSA on curve secp256k1
    assert pk.is_ecdsa()

    # Converting back to DER should match the original exactly
    assert pk.to_bytes_der() == der


def test_from_der_unsupported_curve():
    """
    Ensure that DER-encoded keys on curves other than secp256k1
    (e.g. secp384r1) are rejected with an appropriate error.
    """
    # Generate a keypair on an unsupported curve (secp384r1)
    private_key = ec.generate_private_key(ec.SECP384R1())
    public_key = private_key.public_key()

    # Serialize to DER SPKI
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # from_der should raise ValueError about unsupported curve
    with pytest.raises(ValueError, match="Unsupported ECDSA curve"):
        PublicKey.from_der(der)


def test_from_der_invalid():
    """
    Passing corrupted or non-DER bytes should trigger a parse error
    in from_der().
    """
    # Create a bogus DER-like blob
    der = b"\x30\x82" + b"\xff" * 50

    # Expect a ValueError indicating failure to parse DER public key
    with pytest.raises(ValueError, match="Could not parse DER public key"):
        PublicKey.from_der(der)


# ------------------------------------------------------------------------------
# Test: from_bytes (the catch-all)
# ------------------------------------------------------------------------------
def test_from_bytes_ed25519_catch_all(ed25519_keypair):
    """
    Ensure that the catch-all loader treats 32 raw bytes as Ed25519.
    """
    _, pub = ed25519_keypair

    # Serialize the public key into its “raw” 32-byte form
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    # from_bytes() always warns about ambiguous 32-byte inputs
    with pytest.warns(UserWarning, match="cannot distinguish Ed25519 private seeds"):
        pubk = PublicKey.from_bytes(raw)

    # Confirm it recognized Ed25519
    assert pubk.is_ed25519()


def test_from_bytes_ecdsa_catch_all_compressed(ecdsa_keypair):
    """
    Ensure that the catch-all loader treats 33 compressed bytes as secp256k1 ECDSA.
    """
    _, pub = ecdsa_keypair

    # Serialize the public key into SEC1 compressed form (33 bytes)
    compressed = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )

    # from_bytes() still issues the Ed25519-seed ambiguity warning
    with pytest.warns(UserWarning, match="cannot distinguish Ed25519 private seeds"):
        pubk = PublicKey.from_bytes(compressed)

    # Confirm it recognized ECDSA
    assert pubk.is_ecdsa()


def test_from_bytes_der_catch_all_ed25519(ed25519_keypair):
    """
    Ensure that the catch-all loader falls back to DER decoding.
    """
    _, pub = ed25519_keypair

    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with pytest.warns(UserWarning, match="cannot distinguish Ed25519 private seeds"):
        pubk = PublicKey.from_bytes(der)

    # Confirm it recognized Ed25519
    assert pubk.is_ed25519()


def test_from_bytes_der_catch_all_ecdsa(ecdsa_keypair):
    """
    Ensure that the catch-all loader falls back to DER decoding for ECDSA DER SPKI.
    """
    _, pub = ecdsa_keypair

    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with pytest.warns(UserWarning, match="cannot distinguish Ed25519 private seeds"):
        pubk = PublicKey.from_bytes(der)

    # Confirm it recognized ECDSA
    assert pubk.is_ecdsa()


def test_from_bytes_invalid():
    """
    Passing a blob that matches none of the 32/33/65 length cases
    should fall through to DER, then raise ValueError.
    """
    # 1 byte of data: too small for Ed25519 (32), ECDSA (33/65), not valid DER
    data = b"\x00"

    # Always warns about Ed25519 ambiguity, then fails in DER loader
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError, match="Failed to load public key"):
            PublicKey.from_bytes(data)


# ------------------------------------------------------------------------------
# Test: from_string_xxx
# ------------------------------------------------------------------------------
def test_from_string_ed25519(ed25519_keypair):
    """
    Test loading an Ed25519 public key from a valid hex string.
    Ensures the warning about seed vs. public key ambiguity is emitted
    and that round-trip hex output matches the input.
    """
    _, pub = ed25519_keypair
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    hex_str = raw.hex()

    with pytest.warns(
        UserWarning, match="cannot distinguish Ed25519 private seeds from public keys"
    ):
        pubk = PublicKey.from_string_ed25519(hex_str)
    assert pubk.is_ed25519()
    assert pubk.to_string_ed25519() == hex_str


def test_from_string_ed25519_invalid_hex():
    """
    Test that passing a malformed hex string to from_string_ed25519
    raises a ValueError.
    """
    with pytest.raises(ValueError, match="Invalid hex string for Ed25519 public key"):
        PublicKey.from_string_ed25519("zzzzzz")


def test_from_string_ecdsa_compressed(ecdsa_keypair):
    """
    Test loading a compressed ECDSA secp256k1 public key from a valid hex string.
    Ensures correct detection and round-trip hex output.
    """
    _, pub = ecdsa_keypair
    compressed = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )
    hex_str = compressed.hex()
    pubk = PublicKey.from_string_ecdsa(hex_str)
    assert pubk.is_ecdsa()
    assert pubk.to_string_ecdsa() == hex_str


def test_from_string_ecdsa_uncompressed(ecdsa_keypair):
    """
    Test loading an uncompressed ECDSA secp256k1 public key from hex.
    Verifies detection and compression on output.
    """
    _, pub = ecdsa_keypair
    uncompressed = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    hex_str = uncompressed.hex()
    pubk = PublicKey.from_string_ecdsa(hex_str)
    assert pubk.is_ecdsa()
    # Round trip to compressed form
    assert len(pubk.to_bytes_ecdsa()) == 33


def test_from_string_ecdsa_invalid_hex():
    """
    Test that passing a malformed hex string to from_string_ecdsa
    raises a ValueError.
    """
    with pytest.raises(ValueError, match="Invalid hex string for ECDSA public key"):
        PublicKey.from_string_ecdsa("not-a-hex")


def test_from_string_catch_all_ecdsa(ecdsa_keypair):
    _, pub = ecdsa_keypair
    compressed = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    ).hex()

    # Should still warn about the 32-byte ambiguity, then detect ECDSA
    with pytest.warns(UserWarning, match="cannot distinguish"):
        pubk = PublicKey.from_string(compressed)
    assert pubk.is_ecdsa()
    assert pubk.to_string_ecdsa() == compressed


def test_from_string_der(ecdsa_keypair):
    """
    Test loading an ECDSA secp256k1 public key from a DER hex string.
    Ensures correct detection and round-trip DER output.
    """
    _, pub = ecdsa_keypair
    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    hex_str = der.hex()
    pubk = PublicKey.from_string_der(hex_str)
    assert pubk.is_ecdsa()
    assert pubk.to_string_der() == hex_str


def test_from_string_der_invalid():
    """
    Test that passing a non-hex string to from_string_der raises a ValueError.
    """
    with pytest.raises(ValueError, match="Invalid hex string for DER public key"):
        PublicKey.from_string_der("gghh")


def test_from_string_catch_all_ed25519(ed25519_keypair):
    """
    Test the catch-all from_string method with an Ed25519 public key hex.
    Ensures warning and correct detection.
    """
    _, pub = ed25519_keypair
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    hex_str = raw.hex()

    with pytest.warns(UserWarning, match="from_string.*cannot distinguish"):
        pubk = PublicKey.from_string(hex_str)
    assert pubk.is_ed25519()


# ------------------------------------------------------------------------------
# Test: _from_proto
# ------------------------------------------------------------------------------
def test_from_proto_ed25519(ed25519_keypair):
    _, pub = ed25519_keypair
    pubk = PublicKey(pub)
    proto = pubk._to_proto()
    assert pubk._from_proto(proto).to_bytes_raw() == pubk.to_bytes_raw()


def test_from_proto_ecdsa(ecdsa_keypair):
    _, pub = ecdsa_keypair
    pubk = PublicKey(pub)
    proto = pubk._to_proto()
    assert pubk._from_proto(proto).to_bytes_raw() == pubk.to_bytes_raw()


def test_from_proto_unsupported_type():
    # Create a Key proto with an unsupported type
    proto = Key()
    # Set some arbitrary bytes to a RSA_3072 as currently we do not support it
    proto.RSA_3072 = b"currently unsupported"

    # Verify that attempting to parse an unsupported key type raises ValueError
    with pytest.raises(ValueError, match="Unsupported public key type in protobuf"):
        PublicKey._from_proto(proto)


# ------------------------------------------------------------------------------
# Test: _to_proto
# ------------------------------------------------------------------------------
def test_to_proto_ed25519(ed25519_keypair):
    _, pub = ed25519_keypair
    pubk = PublicKey(pub)

    # Convert to the protobuf Key message
    proto = pubk._to_proto()
    # Ensure the oneof field named “key” is set to the ed25519 variant
    assert proto.WhichOneof("key") == "ed25519"
    # The bytes in the proto should exactly match the raw Ed25519 bytes
    assert proto.ed25519 == pubk.to_bytes_ed25519()


def test_to_proto_ecdsa(ecdsa_keypair):
    _, pub = ecdsa_keypair
    pubk = PublicKey(pub)

    # Convert to the protobuf Key message
    proto = pubk._to_proto()
    # Ensure the oneof field named “key” is set to the ECDSA_secp256k1 variant
    assert proto.WhichOneof("key") == "ECDSA_secp256k1"
    # The bytes in the proto should exactly match the compressed secp256k1 bytes
    assert proto.ECDSA_secp256k1 == pubk.to_bytes_ecdsa()


# ------------------------------------------------------------------------------
# Test: verify signatures
# ------------------------------------------------------------------------------
def test_verify_ed25519_success(ed25519_keypair):
    """
    Verify that an Ed25519 signature created by the private key can be
    successfully validated by the PublicKey wrapper’s verify() method.
    """
    priv, pub = ed25519_keypair
    pubk = PublicKey(pub)

    # The message to be signed
    msg = b"hello world"

    # Use the Ed25519 private key to sign the message.
    sig = priv.sign(msg)

    # Verify the signature against the original message.
    # If the signature is correct, verify() returns None and raises no error.
    pubk.verify(sig, msg)


def test_verify_ed25519_fail(ed25519_keypair):
    priv, pub = ed25519_keypair
    pubk = PublicKey(pub)

    msg = b"hello world"
    sig = priv.sign(msg)
    wrong_msg = b"hello worlds"

    # If the signature is incorrect, it would raise cryptography.exceptions.InvalidSignature.
    with pytest.raises(InvalidSignature):
        pubk.verify(sig, wrong_msg)


def test_verify_ecdsa_success(ecdsa_keypair):
    priv, pub = ecdsa_keypair
    pk = PublicKey(pub)

    msg = b"some message"
    msg_hash = keccak256(msg)
    signature = priv.sign(msg_hash, ec.ECDSA(asym_utils.Prehashed(hashes.SHA256())))
    # If the signature is correct, verify() returns None and raises no error.
    pk.verify(signature, msg)


def test_verify_ecdsa_fail(ecdsa_keypair):
    priv, pub = ecdsa_keypair
    pk = PublicKey(pub)

    msg = b"some message"
    signature = priv.sign(msg, ec.ECDSA(hashes.SHA256()))
    wrong_msg = b"some message but slightly changed"

    # If the signature is incorrect, it would raise cryptography.exceptions.InvalidSignature.
    with pytest.raises(InvalidSignature):
        pk.verify(signature, wrong_msg)


# ------------------------------------------------------------------------------
# Test: representation (__repr__)
# ------------------------------------------------------------------------------
def test_repr_ed25519(ed25519_keypair):
    _, pub = ed25519_keypair
    pubk = PublicKey(pub)

    # Call repr(), which should include algorithm name and raw-hex
    r = repr(pubk)
    assert "Ed25519" in r
    # It must include the raw public-key hex string
    assert pubk.to_string_raw() in r


def test_repr_ecdsa(ecdsa_keypair):
    _, pub = ecdsa_keypair
    pubk = PublicKey(pub)
    r = repr(pubk)

    assert "ECDSA" in r
    # It must include the raw public-key hex string
    assert pubk.to_string_raw() in r


def test_to_evm_address_ecdsa_key(ecdsa_keypair):
    """Test that the evm_address is created."""
    _, pub = ecdsa_keypair

    public_key = PublicKey(pub)
    evm_address = public_key.to_evm_address()

    assert evm_address is not None
    assert isinstance(evm_address, EvmAddress)
    assert len(evm_address.address_bytes) == 20


def test_to_evm_address_from_ecdsa_key_manual_derivation(ecdsa_keypair):
    """Verify that to_evm_address() matches manual derivation."""
    _, pub = ecdsa_keypair
    public_key = PublicKey(pub)

    # Manual derivation
    uncompressed = public_key.to_bytes_ecdsa(compressed=False)
    evm_bytes = keccak256(uncompressed[1:])[-20:]

    derived_bytes = public_key.to_evm_address().address_bytes

    assert evm_bytes == derived_bytes


def test_to_evm_address_with_same_ecdsa_key(ecdsa_keypair):
    """Test deriving EVM address from a valid same ECDSA public key."""
    _, pub = ecdsa_keypair
    public_key = PublicKey(pub)

    evm_addr1 = public_key.to_evm_address()

    assert isinstance(evm_addr1, EvmAddress)
    assert len(evm_addr1.address_bytes) == 20

    # Derivation should be same for the same key
    evm_addr2 = public_key.to_evm_address()
    assert isinstance(evm_addr1, EvmAddress)
    assert len(evm_addr1.address_bytes) == 20

    assert evm_addr1 == evm_addr2


def test_to_evm_address_raises_for_ed25519(ed25519_keypair):
    """Ensure ValueError is raised when deriving EVM address from Ed25519 key."""
    _, pub = ed25519_keypair
    public_key = PublicKey(pub)

    with pytest.raises(ValueError, match="Cannot derive an EVM address"):
        public_key.to_evm_address()
