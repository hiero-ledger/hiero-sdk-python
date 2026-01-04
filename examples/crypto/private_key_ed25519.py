"""
Example file: Working with Ed25519 PrivateKey using the PrivateKey class
*WARNING* Ed25519 seeds should not be printed or exposed in a real‑world scenario

uv run examples/crypto/private_key_ed25519.py
python examples/crypto/private_key_ed25519.py

"""

from cryptography.exceptions import InvalidSignature
from hiero_sdk_python.crypto.private_key import PrivateKey


def example_generate_ed25519() -> None:
    """
    Demonstrates generating a brand new Ed25519 PrivateKey, signing data,
    and verifying the signature with its corresponding PublicKey.
    """
    print("=== Ed25519: Generate & Sign ===")
    # 1) Generate Ed25519 by specifying in "'"
    privkey = PrivateKey.generate("ed25519")
    print("Generated Ed25519 PrivateKey (hex) =", privkey)

    # 2) Get the public key for this ed25519 private key
    pubkey = privkey.public_key()
    print("Derived public key =", pubkey)

    # 3) Sign data
    data = b"hello ed25519!"
    signature = privkey.sign(data)
    print("Signature (hex) =", signature.hex())
    # 4) Verify signature using the public key
    try:
        pubkey.verify(signature, data)
        print("Signature is VALID (Ed25519)!")
    except InvalidSignature:
        print("Signature is INVALID (Ed25519)!")
    print()


def example_load_ed25519_raw() -> None:
    """
    Demonstrates creating a PrivateKey from a 32-byte raw Ed25519 seed.
    Then uses it for signing and verifying.
    """
    print("=== Ed25519: Load from Raw ===")
    raw_seed_hex = "01" * 32  # Example 32 bytes

    # Now this becomes a raw seed
    raw_seed = bytes.fromhex(raw_seed_hex)

    # Create private ed25519 key from ed25519 seed.
    privkey = PrivateKey.from_bytes_ed25519(raw_seed)
    print("Loaded Ed25519 PrivateKey from raw seed =", privkey)

    # Derive the public key
    pubkey = privkey.public_key()

    # Sign & verify
    data = b"Ed25519 from raw"
    signature = privkey.sign(data)
    try:
        pubkey.verify(signature, data)
        print("Signature valid with Ed25519 from raw seed!")
    except InvalidSignature:
        print("Signature invalid?!")
    print()


def example_load_ed25519_from_hex() -> None:
    """
    Demonstrates creating a PrivateKey from a hex-encoded string for Ed25519.
    Must be 32 bytes in total, i.e. 64 hex characters.
    """
    print("=== Ed25519: Load from Hex ===")
    # A random 32-byte example:
    ed_hex = "a1" * 16 + "b2" * 16  # => 64 hex characters => 32 bytes

    # Create private ed25519 key from hex.
    privkey = PrivateKey.from_string_ed25519(ed_hex)
    print("Loaded Ed25519 PrivateKey from hex =", privkey)

    # Derive the public key
    pubkey = privkey.public_key()

    # Sign & verify
    data = b"Test data"
    signature = privkey.sign(data)
    try:
        pubkey.verify(signature, data)
        print("Ed25519 signature valid with hex-loaded key!")
    except InvalidSignature:
        print("Signature invalid?!")
    print()


def example_load_ed25519_der() -> None:
    """
    Demonstrates loading an Ed25519 private key from DER bytes (hex form).
    In actual usage, you might read the raw DER bytes from a file (binary),
    then call from_der(...) or from_string_der(...).
    """
    print("=== Ed25519: Load from DER ===")
    # This DER encodes a small example Ed25519 key whose raw seed might be all 0x01.
    # 46 bytes in total; for demonstration only.
    der_hex = (
        "302e020100300506032b657004220420"
        "0101010101010101010101010101010101010101010101010101010101010101"
    )

    # Create private and public key
    privkey = PrivateKey.from_string_der(der_hex)
    print("Loaded Ed25519 PrivateKey from DER =", privkey)
    pubkey = privkey.public_key()

    # Sign/Verify
    data = b"DER-based Ed25519"
    signature = privkey.sign(data)
    try:
        pubkey.verify(signature, data)
        print("Ed25519 signature valid using DER-loaded key!")
    except InvalidSignature:
        print("Signature invalid?!")
    print()


def main_ed25519():
    example_generate_ed25519()
    example_load_ed25519_raw()
    example_load_ed25519_from_hex()
    example_load_ed25519_der()


if __name__ == "__main__":
    main_ed25519()
