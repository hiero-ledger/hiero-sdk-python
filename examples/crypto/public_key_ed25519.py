"""
Example file: Working with an Ed25519 PublicKey using the PublicKey class
uv run examples/crypto/public_key_ed25519.py
python examples/crypto/public_key_ed25519.py
"""

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
from hiero_sdk_python.crypto.public_key import PublicKey


def example_load_ed25519_from_raw() -> None:
    """
    Demonstrate creating a PublicKey object from a 32-byte Ed25519 public key.
    Please ensure to pass a public key not a private key.
    """
    # Ed25519 public key bytes are always 32 bytes.
    # Most random 32 bytes will be a valid key, so here is a random example:
    raw_pub = bytes.fromhex(
        "8baa5f735dbf40f275283bed504cb752b1ce58a7118476d28f528ecd265c5f58"
    )

    # 1) Construct via from_bytes_ed25519
    pubk_obj = PublicKey.from_bytes_ed25519(raw_pub)  # or from_bytes
    print("Loaded Ed25519 PublicKey from raw bytes =", pubk_obj)

    # 2) Convert back to raw hex
    back_to_hex = pubk_obj.to_string_ed25519()  # or to_string
    print("Back to Ed25519 hex:", back_to_hex)


def example_load_ed25519_from_hex() -> None:
    """
    Demonstrate creating a PublicKey object from a 32-byte hex string
    representing an Ed25519 public key.
    """
    # Must be 64 hex characters e.g.
    hex_str = "09fe6e485c1fb4e24c80b591fc79103c28006d549428a0d3ccb2a88412f2bda8"

    # Construct using from_string_ed25519
    pubk_obj = PublicKey.from_string_ed25519(hex_str)  # or from_string
    print("Loaded Ed25519 PublicKey from hex:", pubk_obj)


def example_verify_ed25519_signature() -> None:
    """
    Demonstrate verifying an Ed25519 signature.
    """
    # Ed25519 is "EdDSA over Curve25519".
    # Key pair:
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Wrap in the PublicKey class
    pubk_obj = PublicKey(public_key)

    # Sign data
    data = b"Hello Ed25519"
    signature = private_key.sign(data)

    # Verify
    try:
        pubk_obj.verify(signature, data)
        print("Ed25519 signature is valid!")
    except InvalidSignature:
        print("Ed25519 signature is INVALID!")


def main():
    example_load_ed25519_from_raw()
    print("-----")
    example_load_ed25519_from_hex()
    print("-----")
    example_verify_ed25519_signature()


if __name__ == "__main__":
    main()
