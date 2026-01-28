import pytest
import warnings
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives import serialization
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.crypto.private_key import PrivateKey

pytestmark = pytest.mark.unit


def test_generate_ed25519():
    """
    Test generating an Ed25519 key, then:
      1) Confirm it's detected as Ed25519 (not ECDSA).
      2) Sign/verify some sample data.
      3) Check raw/hex/DER serialization.
      4) Confirm the __repr__ includes "Ed25519".
    """
    priv = PrivateKey.generate("ed25519")
    assert priv.is_ed25519()
    assert not priv.is_ecdsa()

    data = b"hello ed25519"
    sig = priv.sign(data)

    # Verify the signature with the derived public key
    pub = priv.public_key()
    pub.verify(sig, data)  # should succeed if signature is valid

    # Check round-trip raw bytes
    raw_bytes = priv.to_bytes_ed25519_raw()
    assert len(raw_bytes) == 32

    # Check hex string conversion
    raw_hex = priv.to_string_ed25519_raw()
    assert len(raw_hex) == 64
    assert raw_hex == raw_bytes.hex()

    # Check DER
    der_bytes = priv.to_bytes_der()
    assert len(der_bytes) > 0
    der_hex = priv.to_string_der()
    assert der_hex == der_bytes.hex()

    # Check __repr__ includes Ed25519
    rep = repr(priv)
    assert "Ed25519" in rep


def test_generate_ecdsa():
    """
    Test generating an ECDSA (secp256k1) key, then:
      1) Confirm it's detected as ECDSA (not Ed25519).
      2) Sign/verify sample data.
      3) Check raw/hex/DER serialization.
      4) Confirm the __repr__ includes "ECDSA".
    """
    priv = PrivateKey.generate("ecdsa")
    assert priv.is_ecdsa()
    assert not priv.is_ed25519()

    data = b"hello ecdsa"
    sig = priv.sign(data)

    # Verify the signature with the derived public key
    pub = priv.public_key()
    pub.verify(sig, data)  # should succeed

    # Check raw bytes
    raw_bytes = priv.to_bytes_ecdsa_raw()
    assert len(raw_bytes) == 32

    # Check hex string
    raw_hex = priv.to_string_ecdsa_raw()
    assert len(raw_hex) == 64
    assert raw_hex == raw_bytes.hex()

    # Check DER
    der_bytes = priv.to_bytes_der()
    assert len(der_bytes) > 0

    # Check __repr__ includes ECDSA
    rep = repr(priv)
    assert "ECDSA" in rep


def test_from_string_ed25519():
    """
    Test from_string_ed25519 by providing a valid 32-byte seed (in hex),
    ensuring it loads as an Ed25519 key and can sign/verify data.
    """
    seed_hex = "01" * 32
    priv = PrivateKey.from_string_ed25519(seed_hex)
    assert priv.is_ed25519()

    # Verify sign/verify flow
    sig = priv.sign(b"data")
    priv.public_key().verify(sig, b"data")


def test_from_string_ed25519_invalid_length():
    """
    Test from_string_ed25519 with an invalid hex length (< 32 bytes),
    expecting a ValueError due to insufficient seed length.
    """
    short_hex = "12" * 16  # Only 16 bytes
    with pytest.raises(ValueError, match="Ed25519 private key seed must be 32 bytes"):
        PrivateKey.from_string_ed25519(short_hex)


def test_from_string_ecdsa():
    """
    Test from_string_ecdsa with a valid 32-byte scalar in hex.
    Then sign/verify data to ensure it's functional.
    """
    scalar_hex = "abcdef0000000000000000000000000000000000000000000000000000000001"
    priv = PrivateKey.from_string_ecdsa(scalar_hex)
    assert priv.is_ecdsa()

    sig = priv.sign(b"test-ecdsa")
    priv.public_key().verify(sig, b"test-ecdsa")


def test_from_string_ecdsa_zero_scalar():
    """
    Ensure that ECDSA scalar = 0 raises ValueError.
    """
    zero_scalar_hex = "00" * 32
    with pytest.raises(ValueError, match="ECDSA private key scalar cannot be zero"):
        PrivateKey.from_string_ecdsa(zero_scalar_hex)


def test_from_string_der_ed25519():
    """
    Test from_string_der with a known valid DER encoding for Ed25519.
    Then confirm sign/verify works.

    This example DER was built using a known Ed25519 seed (all '01').
    """
    der_hex = (
        "302e020100300506032b657004220420"
        "0101010101010101010101010101010101010101010101010101010101010101"
    )
    priv = PrivateKey.from_string_der(der_hex)
    assert priv.is_ed25519()

    sig = priv.sign(b"der-ed25519")
    priv.public_key().verify(sig, b"der-ed25519")


def test_from_string_der_ecdsa_round_trip():
    """
    Generate a secp256k1 private key with scalar = 1, serialize to DER hex,
    then load it back via from_string_der() and confirm it's ECDSA.
    """
    # 1) Construct a PrivateKey from the scalar = 1
    scalar_one = (1).to_bytes(32, "big")
    original = PrivateKey.from_bytes_ecdsa(scalar_one)

    # 2) Serialize to DER hex
    der_hex = original.to_string_der()
    assert len(der_hex) % 2 == 0  # must be even

    # 3) Load it back
    loaded = PrivateKey.from_string_der(der_hex)
    assert loaded.is_ecdsa()

    # 4) Confirm the raw scalar round-trips perfectly
    assert loaded.to_bytes_ecdsa_raw() == scalar_one


def test_from_string_der_invalid_hex():
    """
    Attempt to load DER from a string that is not valid hex,
    expecting a ValueError from the hex parsing step.
    """
    with pytest.raises(ValueError, match="Invalid hex string for DER private key"):
        PrivateKey.from_string_der("not-hex-data-zzzz")


def test_from_string_der_parse_failure():
    """
    Provide valid hex but not valid DER-encoded data,
    expecting a parse failure ValueError.
    """
    # Just random small hex that won't parse as DER
    random_hex = "112233445566"
    with pytest.raises(ValueError, match="Could not parse DER private key"):
        PrivateKey.from_string_der(random_hex)


def test_from_string_invalid_hex():
    """
    Provide a string that is not valid hex to from_string (the catch-all),
    expecting a ValueError in hex decode.
    """
    with pytest.raises(ValueError, match="Invalid hex string for private key"):
        PrivateKey.from_string("not-a-hex-string")


def test_from_string_unrecognized():
    """
    Provide a valid hex string but only 8 bytes => fails both 32-byte raw
    and DER parse => expect ValueError from from_bytes.
    """
    short_hex = "11" * 8
    with pytest.raises(ValueError, match="Failed to load private key from bytes"):
        PrivateKey.from_string(short_hex)


def test_from_bytes_ed25519():
    """
    Test from_bytes_ed25519 with direct 32-byte seed => should load as Ed25519.
    """
    seed = bytes.fromhex("02" * 32)
    priv = PrivateKey.from_bytes_ed25519(seed)
    assert priv.is_ed25519()


def test_from_bytes_ecdsa():
    """
    Test from_bytes_ecdsa with direct 32-byte scalar => should load as ECDSA.
    """
    # Example random scalar
    scalar = bytes.fromhex("abcdef" + "00" * 29 + "01")[:32]
    priv = PrivateKey.from_bytes_ecdsa(scalar)
    assert priv.is_ecdsa()


def test_from_bytes():
    """
    Test the catch-all from_bytes(32 bytes):
      - If Ed25519 load succeeds, we get Ed25519.
      - If Ed25519 fails, tries ECDSA.
      - If both fail, tries DER.
    Check the warning is triggered for 32-byte data.
    """
    # 32 bytes that definitely pass as Ed25519.
    seed = bytes.fromhex("11" * 32)
    with warnings.catch_warnings(record=True) as w:
        priv = PrivateKey.from_bytes(seed)
        assert len(w) == 1  # confirm we got the "ambiguity" warning
    assert priv.is_ed25519()


def test_from_bytes_not_32_der():
    """
    Provide something that's not 32 bytes => it tries DER => expect failure
    if it's not valid DER.
    """
    random_33 = b"\x01" * 33
    with pytest.raises(ValueError, match="Failed to load private key from bytes"):
        PrivateKey.from_bytes(random_33)


def test_sign_verify_ed25519():
    """
    Generate Ed25519 => sign => verify => then tamper with the signature
    to confirm we get an InvalidSignature exception.
    """
    priv = PrivateKey.generate("ed25519")
    data = b"test sign"
    sig = priv.sign(data)
    pub = priv.public_key()

    # Valid signature
    pub.verify(sig, data)

    # Tamper with the signature (flip last byte)
    tampered_sig = bytearray(sig)
    tampered_sig[-1] ^= 0xFF
    with pytest.raises(InvalidSignature):
        pub.verify(tampered_sig, data)


def test_sign_verify_ecdsa():
    """
    Generate ECDSA => sign => verify => then tamper with the signature
    to confirm we get an InvalidSignature exception.
    """
    priv = PrivateKey.generate("ecdsa")
    data = b"test ecdsa"
    sig = priv.sign(data)
    pub = priv.public_key()

    # Valid signature
    pub.verify(sig, data)

    # Tamper with the signature (flip some byte in the middle)
    tampered_sig = bytearray(sig)
    tampered_sig[5] ^= 0xFF
    with pytest.raises(InvalidSignature):
        pub.verify(tampered_sig, data)


def test_from_string_strips_0x_prefix():
    """Make sure from_string()/from_string_ed25519()/from_string_ecdsa() drop a leading 0x."""
    hex_seed = "0x" + "ab" * 32
    # Should load as Ed25519
    priv = PrivateKey.from_string_ed25519(hex_seed)
    assert priv.is_ed25519()

    # Similarly for the general catch-all
    priv2 = PrivateKey.from_string(hex_seed)
    # Depending on the bytes, it might parse as Ed25519 or ECDSA
    # If 0xab… is valid as an Ed25519 seed, it’ll be Ed25519:
    assert priv2.is_ed25519()


def test_from_bytes_ambiguity_prefers_ecdsa_when_ed25519_fails(monkeypatch):
    """
    Ensure from_bytes tries Ed25519 first, then ECDSA.
    We monkey-patch Ed25519 to always fail, then give it a scalar of 1
    (which ECDSA will accept), and confirm the result is ECDSA.
    """
    # 1) Prepare a 32-byte big-endian scalar = 1
    ecdsa_scalar_one = (1).to_bytes(32, "big")

    # 2) Force the Ed25519 loader to always return None
    monkeypatch.setattr(PrivateKey, "_try_load_ed25519", staticmethod(lambda b: None))

    # 3) Now from_bytes should skip Ed25519 and succeed with ECDSA
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        priv = PrivateKey.from_bytes(ecdsa_scalar_one)
        # We should still get the ambiguity warning
        assert any("try Ed25519" in str(wi.message) for wi in w)

    assert priv.is_ecdsa(), "from_bytes should have returned an ECDSA key"
    # And round-trip raw scalar
    assert priv.to_bytes_ecdsa_raw() == ecdsa_scalar_one


def test_type_checks_are_mutually_exclusive():
    ed = PrivateKey.generate("ed25519")
    ec_key = PrivateKey.generate("ecdsa")
    assert ed.is_ed25519() and not ed.is_ecdsa()
    assert ec_key.is_ecdsa() and not ec_key.is_ed25519()


@pytest.mark.parametrize("length", [0, 1, 31, 33])
def test_from_bytes_invalid_lengths(length):
    bad = b"\x00" * length
    with pytest.raises(ValueError, match="Failed to load private key from bytes"):
        PrivateKey.from_bytes(bad)


def test_from_bytes_warning_message():
    seed = b"\x11" * 32
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = PrivateKey.from_bytes(seed)
        assert any("try Ed25519" in str(wi.message) for wi in w)


@pytest.mark.parametrize("key_type", ["ed25519", "ecdsa"])
def test_raw_roundtrip_idempotent(key_type):
    priv1 = PrivateKey.generate(key_type)
    raw = priv1.to_bytes_raw()
    if key_type == "ed25519":
        priv2 = PrivateKey.from_bytes_ed25519(raw)
    else:
        priv2 = PrivateKey.from_bytes_ecdsa(raw)
    assert priv2.to_bytes_raw() == raw


def test_generate_invalid_key_type():
    with pytest.raises(ValueError, match="Invalid key_type"):
        PrivateKey.generate("rsa")


@pytest.mark.parametrize("key_type", ["ed25519", "ecdsa"])
def test_to_string_alias(key_type):
    priv = PrivateKey.generate(key_type)
    assert priv.to_string() == priv.to_string_raw()


def test_from_string_ecdsa_strips_0x():
    hex_scalar = "0x" + "ab" * 32
    priv = PrivateKey.from_string_ecdsa(hex_scalar)
    assert priv.is_ecdsa()


@pytest.mark.parametrize(
    "fn, length",
    [
        (PrivateKey.from_bytes_ed25519, 31),
        (PrivateKey.from_bytes_ed25519, 33),
        (PrivateKey.from_bytes_ecdsa, 31),
        (PrivateKey.from_bytes_ecdsa, 33),
    ],
)
def test_from_bytes_wrong_length(fn, length):
    bad = b"\x00" * length
    with pytest.raises(ValueError):
        fn(bad)


def test_public_key_roundtrip_der_and_raw():
    """
    Test that private -> public -> raw DER -> PublicKey.from_der works
    for an ECDSA key (though it also works for Ed25519).
    """
    priv = PrivateKey.generate("ecdsa")
    pub = priv.public_key()
    der = pub.to_string_der()
    pub2 = PublicKey.from_string_der(der)
    assert pub2.to_string_ecdsa() == pub.to_string_ecdsa()


@pytest.mark.parametrize("key_type", ["ed25519", "ecdsa"])
def test_repr_contains_full_hex(key_type):
    """
    Test that repr includes the full 64-character hex seed for both key types.
    """
    priv = PrivateKey.generate(key_type)
    rep = repr(priv)

    # Must contain 'hex='
    assert "hex=" in rep

    # Extract the hex part after 'hex=' up to the closing '>'
    hex_part = rep.split("hex=")[1].rstrip(">")
    # Should be exactly 64 hex characters
    assert len(hex_part) == 64
    # All characters should be valid lowercase hex digits
    assert re.fullmatch(r"[0-9a-f]{64}", hex_part)


@pytest.mark.parametrize("key_type", ["ed25519", "ecdsa"])
def test_der_roundtrip(key_type):
    """
    Make sure that if we serialize a key to DER and then load it back,
    we get the same raw seed/scalar.
    """
    priv1 = PrivateKey.generate(key_type)
    der_hex = priv1.to_string_der()
    priv2 = PrivateKey.from_string_der(der_hex)
    assert priv2.to_bytes_raw() == priv1.to_bytes_raw()
    assert priv2.is_ed25519() == (key_type == "ed25519")


@pytest.fixture(params=["ed25519", "ecdsa"])
def raw_seed(request):
    """
    A fixture that yields the raw seed/scalar for each key type.
    """
    return PrivateKey.generate(request.param).to_bytes_raw()


def test_from_bytes_fixture(raw_seed):
    """
    Demonstrate using the raw_seed fixture. from_bytes picks Ed25519 or ECDSA
    based on the content. If it’s a valid Ed25519 seed, it becomes Ed25519;
    otherwise if that fails, it tries ECDSA next.
    """
    priv = PrivateKey.from_bytes(raw_seed)
    assert priv.to_bytes_raw() == raw_seed
