from __future__ import annotations

from dataclasses import dataclass

from mnemonic import Mnemonic

from hiero_sdk_python.crypto.private_key import PrivateKey


@dataclass(frozen=True)
class MnemonicPhrase:
    """BIP-39 mnemonic utilities for deterministic wallet workflows."""

    phrase: str

    @classmethod
    def generate(cls, strength: int = 256) -> MnemonicPhrase:
        """Generate a valid English BIP-39 mnemonic phrase."""
        return cls(Mnemonic("english").generate(strength=strength))

    @classmethod
    def from_phrase(cls, phrase: str) -> MnemonicPhrase:
        """Construct and validate a BIP-39 mnemonic phrase."""
        mnemonic = Mnemonic("english")
        normalized = " ".join(phrase.strip().split())
        if not mnemonic.check(normalized):
            raise ValueError("Invalid BIP-39 mnemonic phrase.")
        return cls(normalized)

    def is_valid(self) -> bool:
        """Check whether the phrase has valid BIP-39 checksum and words."""
        return Mnemonic("english").check(self.phrase)

    def to_seed(self, passphrase: str = "") -> bytes:
        """Convert mnemonic phrase to BIP-39 seed bytes."""
        return Mnemonic.to_seed(self.phrase, passphrase=passphrase)

    def to_private_key_ed25519(self, passphrase: str = "") -> PrivateKey:
        """Derive an Ed25519 private key from the first 32 bytes of BIP-39 seed.

        This provides deterministic key material suitable for local development
        and reproducible testing workflows.
        """
        seed = self.to_seed(passphrase=passphrase)
        return PrivateKey.from_bytes_ed25519(seed[:32])
