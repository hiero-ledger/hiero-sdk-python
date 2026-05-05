from __future__ import annotations

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.utils.crypto_utils import keccak256


class EvmAddress(Key):
    """
    Represents a 20-byte EVM address derived from the rightmost 20 bytes of
    32 byte Keccak-256 hash of an ECDSA public key.
    """

    def __init__(self, address_bytes: bytes) -> None:
        """
        Initialize an EvmAddress instance from bytes.

        Args:
        address_bytes (bytes): A 20-byte sequence representing the EVM address.
        """
        if len(address_bytes) != 20:
            raise ValueError("EvmAddress must be exactly 20 bytes long.")

        self.address_bytes: bytes = address_bytes

    @classmethod
    def from_string(cls, evm_address: str) -> EvmAddress:
        """Create an EvmAddress from a hex string (with or without '0x' prefix)."""
        if not isinstance(evm_address, str):
            raise TypeError("evm_address must be a of type string.")

        address = evm_address[2:] if evm_address.startswith("0x") else evm_address

        if len(address) == 40:
            return cls(address_bytes=bytes.fromhex(address))

        raise ValueError("Invalid hex string for evm_address.")

    @classmethod
    def from_bytes(cls, address_bytes: bytes) -> EvmAddress:
        """Create an EvmAddress from raw bytes."""
        return cls(address_bytes)

    def to_proto_key(self):
        raise RuntimeError("to_proto_key() not implemented for EvmAddress")

    def to_string(self) -> str:
        """Return the EVM address as a hex string."""
        return bytes.hex(self.address_bytes)

    def __str__(self) -> str:
        return self.to_string()

    def to_checksum_address(self) -> str:
        """Return the EIP-55 checksum address.
        Reference: https://eips.ethereum.org/EIPS/eip-55
        """
        lower_address = self.to_string().lower()

        address_hash = keccak256(lower_address.encode("ascii")).hex()

        checksummed = "".join(
            char.upper() if char.isalpha() and int(address_hash[index], 16) >= 8 else char
            for index, char in enumerate(lower_address)
        )

        return f"0x{checksummed}"

    @staticmethod
    def normalize(address: str) -> str:
        """Normalize an EVM address to 40 lowercase hex characters without ``0x``."""
        if not isinstance(address, str):
            raise TypeError("address must be a string")
        addr = address.lower()
        if addr.startswith("0x"):
            addr = addr[2:]

        if len(addr) != 40 or not all(c in "0123456789abcdef" for c in addr):
            raise ValueError("Invalid address")

        return addr

    @staticmethod
    def is_valid(address: str) -> bool:
        """Return ``True`` when ``address`` is valid lowercase/uppercase hex EVM address."""
        if not isinstance(address, str):
            return False

        addr = address.lower()
        if addr.startswith("0x"):
            addr = addr[2:]
        return len(addr) == 40 and all(c in "0123456789abcdef" for c in addr)

    @staticmethod
    def is_checksum_valid(address: str) -> bool:
        """Return ``True`` only if ``address`` is ``0x``-prefixed and EIP-55 checksummed."""
        if not isinstance(address, str) or not address.startswith("0x"):
            return False

        raw = address[2:]

        if not EvmAddress.is_valid(raw):
            return False

        checksummed = EvmAddress.from_string(raw).to_checksum_address()
        return checksummed == address

    def __repr__(self) -> str:
        return f"<EvmAddress hex={self.to_string()}>"

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, EvmAddress):
            return False

        return self.address_bytes == obj.address_bytes

    def __hash__(self) -> int:
        return hash(self.address_bytes)
