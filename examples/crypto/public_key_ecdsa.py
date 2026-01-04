"""
Example file: Working with an ECDSA (secp256k1) PublicKey using the PublicKey class.
uv run examples/crypto/public_key_ecdsa.py
python examples/crypto/public_key_ecdsa.py

"""

from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from hiero_sdk_python.crypto.public_key import PublicKey, keccak256


def example_load_compressed_ecdsa() -> None:
    """
    Demonstrate creating a PublicKey object from a compressed 33-byte ECDSA hex.
    """
    # A mock 33-byte compressed hex:
    compressed_pubkey = bytes.fromhex(
        "0281c2e57fecef82ff4f546dece3684acb6e2fe12a97af066348de81ccaf05d0a4"
    )

    # 1) Construct via the specialized from_bytes_ecdsa()
    pubk_obj = PublicKey.from_bytes_ecdsa(compressed_pubkey)  # or from_bytes
    print("Loaded ECDSA PublicKey (compressed) =", pubk_obj)

    # 2) Convert it back to compressed hex
    compressed_hex = pubk_obj.to_string_ecdsa()
    print("Back to compressed hex:", compressed_hex)


def example_load_uncompressed_ecdsa_from_hex() -> None:
    """
    Demonstrate creating an ECDSA (secp256k1) public key from an uncompressed 65-byte hex string.
    """
    # Uncompressed secp256k1 public keys start with 0x04 and are 65 bytes total.
    uncompressed_hex = (
        "04"
        "0abe0517fcf06e0c160ca821aa2909945752e08169f46c984cb6b02076a3b"
        "29513f047e5c13770101c321f332157377d2862b7c7ed14eedca3978b3b9d007659"
    )

    # 1) Load directly from a hex string using the specialized from_string_ecdsa().
    pubk_obj = PublicKey.from_string_ecdsa(uncompressed_hex)  # or from_string
    print("Loaded uncompressed ECDSA PublicKey from hex:", pubk_obj)

    # 2) Convert to compressed raw bytes or hex:
    compressed_bytes = pubk_obj.to_bytes_ecdsa()  # or to_bytes_raw
    print(
        f"Compressed ECDSA bytes (len={len(compressed_bytes)}): {compressed_bytes.hex()}"
    )


def example_verify_ecdsa_signature() -> None:
    """
    Demonstrate verifying a signature with an ECDSA secp256k1 public key.
    """
    # Generate a key pair to be able to sign
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    # 1) Wrap in the PublicKey class
    pubk_obj = PublicKey(public_key)

    # 2) Sign some data
    data = b"Hello ECDSA"
    signature = private_key.sign(
        keccak256(data), ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )

    # 3) Verify with pubk_obj
    try:
        pubk_obj.verify(signature, data)
        print("ECDSA signature is valid!")
    except InvalidSignature:
        print("ECDSA signature is INVALID!")


def main():
    example_load_compressed_ecdsa()
    print("-----")
    example_load_uncompressed_ecdsa_from_hex()
    print("-----")
    example_verify_ecdsa_signature()


if __name__ == "__main__":
    main()
