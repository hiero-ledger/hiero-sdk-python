"""
Example file: Working with ECDSA (secp256k1) PrivateKey using the PrivateKey class
*WARNING* ECDSA seeds should not be printed or exposed in a real‑world scenario

uv run examples/crypto/private_key_ecdsa.py
python examples/crypto/private_key_ecdsa.py

"""

from cryptography.exceptions import InvalidSignature
from hiero_sdk_python.crypto.private_key import PrivateKey


def example_generate_ecdsa() -> None:
    """
    Demonstrates generating a new ECDSA (secp256k1) PrivateKey,
    signing data, and verifying with the associated PublicKey.
    """
    print("=== ECDSA: Generate & Sign ===")
    # 1) Generate ECDSA
    privkey = PrivateKey.generate("ecdsa")
    print("Generated ECDSA PrivateKey (hex) =", privkey)

    # 2) Get the public key
    pubkey = privkey.public_key()
    print("Derived public key =", pubkey)

    # 3) Sign data
    data = b"hello ECDSA!"
    signature = privkey.sign(data)
    print("Signature (hex) =", signature.hex())

    # 4) Verify signature using the public key
    try:
        pubkey.verify(signature, data)
        print("Signature is VALID (ECDSA)!")
    except InvalidSignature:
        print("Signature is INVALID (ECDSA)!")
    print()


def example_load_ecdsa_raw() -> None:
    """
    Demonstrates creating an ECDSA (secp256k1) PrivateKey from raw 32 bytes (a scalar).
    Then signs and verifies.
    """
    print("=== ECDSA: Load from Raw ===")
    # 32 bytes. Example: 0xAB repeated.
    raw_scalar_hex = "ab" * 32
    raw_scalar = bytes.fromhex(raw_scalar_hex)

    # 1) Generate ECDSA
    privkey = PrivateKey.from_bytes_ecdsa(raw_scalar)
    print("Loaded ECDSA PrivateKey from raw scalar =", privkey)

    # 2) Get the public key
    pubkey = privkey.public_key()

    # 3) Sign/Verify
    data = b"ECDSA from raw scalar"
    signature = privkey.sign(data)
    try:
        pubkey.verify(signature, data)
        print("ECDSA signature valid with raw scalar!")
    except InvalidSignature:
        print("Signature invalid?!")
    print()


def example_load_ecdsa_from_hex() -> None:
    """
    Demonstrates creating an ECDSA (secp256k1) PrivateKey from a hex-encoded 32-byte scalar.
    """
    print("=== ECDSA: Load from Hex ===")
    # 32-byte scalar in hex. Must not be zero; example:
    ecdsa_hex = "abcdef0000000000000000000000000000000000000000000000000000000001"

    # 1) Generate ECDSA
    privkey = PrivateKey.from_string_ecdsa(ecdsa_hex)
    print("Loaded ECDSA PrivateKey from hex =", privkey)

    # 2) Get the public key
    pubkey = privkey.public_key()

    # 3) Quick sign/verify
    data = b"Testing ECDSA hex load"
    signature = privkey.sign(data)
    try:
        pubkey.verify(signature, data)
        print("ECDSA signature valid with hex-loaded key!")
    except InvalidSignature:
        print("Signature invalid?!")
    print()


def example_load_ecdsa_der() -> None:
    """
    Demonstrates loading an ECDSA (secp256k1) private key from DER bytes.
    TraditionalOpenSSL in hex form for demonstration.
    """
    print("=== ECDSA: Load from DER ===")
    # Example TraditionalOpenSSL DER-encoded key (for scalar=1).
    # (Truncated for demonstration)
    der_hex = (
        "30740201010"
        "4200000000000000000000000000000000000000000000000000000000000000001"
        "a00706052b8104000aa1440342000479be667ef9dcbbac55a06295ce870b07029bfc"
        "db2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8"
    )

    # 1) Generate DER
    privkey = PrivateKey.from_string_der(der_hex)
    print("Loaded ECDSA PrivateKey from DER =", privkey)

    # 2) Get the public key
    pubkey = privkey.public_key()

    # 3) Sign/Verify
    data = b"DER-based ECDSA"
    signature = privkey.sign(data)
    try:
        pubkey.verify(signature, data)
        print("ECDSA signature valid using DER-loaded key!")
    except InvalidSignature:
        print("Signature invalid?!")
    print()


def main_ecdsa():
    example_generate_ecdsa()
    example_load_ecdsa_raw()
    example_load_ecdsa_from_hex()
    example_load_ecdsa_der()


if __name__ == "__main__":
    main_ecdsa()
