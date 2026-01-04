"""
Example file: Demonstrating how to serialize a PrivateKey to DER (hex)
and then load it back.
*WARNING* DER‐encoded private keys should not be printed or exposed in a real-world scenario.

uv run examples/crypto/private_key_der.py
python examples/crypto/private_key_der.py

"""

from cryptography.exceptions import InvalidSignature
from hiero_sdk_python.crypto.private_key import PrivateKey


def example_serialize_ed25519_der() -> None:
    print("=== Ed25519: Serialize to DER ===")

    privkey = PrivateKey.generate("ed25519")
    print("Generated Ed25519 key:", privkey)

    # This emits Traditional Open SSL DER by default
    der_bytes = privkey.to_bytes_der()
    print("DER bytes length =", len(der_bytes))

    der_hex = der_bytes.hex()
    print("DER hex =", der_hex)

    # Load it back from hex
    privkey2 = PrivateKey.from_string_der(der_hex)
    print("Loaded back from DER:", privkey2)

    # Sign & verify
    signature = privkey2.sign(b"test")
    privkey2.public_key().verify(signature, b"test")
    print("Ed25519 DER reload: Verified signature OK.\n")


def example_serialize_ecdsa_der() -> None:
    print("=== ECDSA: Serialize to DER ===")

    # use generate("ecdsa")
    privkey = PrivateKey.generate("ecdsa")
    print("Generated ECDSA key:", privkey)

    der_bytes = privkey.to_bytes_der()
    print("DER bytes length =", len(der_bytes))

    der_hex = der_bytes.hex()
    print("DER hex =", der_hex)

    privkey2 = PrivateKey.from_string_der(der_hex)
    print("Loaded back from DER:", privkey2)

    signature = privkey2.sign(b"hello ECDSA serialization")
    privkey2.public_key().verify(signature, b"hello ECDSA serialization")
    print("ECDSA DER reload: Verified signature OK.\n")


def main():
    example_serialize_ed25519_der()
    example_serialize_ecdsa_der()


if __name__ == "__main__":
    main()
