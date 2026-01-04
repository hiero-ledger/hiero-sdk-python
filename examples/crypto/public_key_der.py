"""
Example file: Working with DER-encoded SubjectPublicKeyInfo (SPKI) public keys.

uv run examples/crypto/public_key_der.py
python examples/crypto/public_key_der.py

"""

from cryptography.hazmat.primitives.asymmetric import ec, ed25519, utils
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature
from hiero_sdk_python.crypto.public_key import PublicKey, keccak256


def example_load_ecdsa_der() -> None:
    """
    Demonstrate creating a secp256k1 ECDSA PublicKey from DER-encoded bytes.
    """
    # Generate a ECDSA key pair.
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    # Export public key to DER format (SubjectPublicKeyInfo)
    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # 1) Create via from_der()
    pubk_obj = PublicKey.from_der(der_bytes)
    print("Loaded ECDSA secp256k1 from DER:", pubk_obj)

    # 2) Convert back to DER hex:
    der_hex = pubk_obj.to_string_der()
    print("DER-encoded hex:", der_hex)


def example_load_ed25519_der() -> None:
    """
    Demonstrate creating an Ed25519 PublicKey from DER-encoded bytes.
    """
    # Generate a Ed25519 key pair.
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Export public key to DER format (SubjectPublicKeyInfo)
    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # 1) Create via from_der
    pubk_obj = PublicKey.from_der(der_bytes)
    print("Loaded Ed25519 from DER:", pubk_obj)

    # 2) Convert back to hex
    der_hex = pubk_obj.to_string_der()
    print("Ed25519 DER hex:", der_hex)


def example_verify_der_signature() -> None:
    """
    Demonstrate verifying an ECDSA signature using a DER-encoded public key.
    """
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Wrap into public key object from DER
    pubk_obj = PublicKey.from_der(der_bytes)

    # Sign and verify, specifying hash algorithm for ECDSA
    data = b"Hello DER"
    signature = private_key.sign(
        keccak256(data), ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )
    try:
        pubk_obj.verify(signature, data)
        print("DER: ECDSA signature verified!")
    except InvalidSignature:
        print("DER: ECDSA signature invalid.")


def main():
    example_load_ecdsa_der()
    print("-----")
    example_load_ed25519_der()
    print("-----")
    example_verify_der_signature()


if __name__ == "__main__":
    main()
