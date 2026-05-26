from __future__ import annotations

import pytest

from hiero_sdk_python.crypto.mnemonic import MnemonicPhrase


def test_generate_is_valid_default_24_words():
    """Generated default mnemonic should be valid and contain 24 words."""
    phrase = MnemonicPhrase.generate()
    assert phrase.is_valid()
    assert len(phrase.phrase.split()) == 24


def test_from_phrase_normalizes_and_validates():
    """Input phrase should be whitespace-normalized and pass checksum validation."""
    phrase = MnemonicPhrase.from_phrase(
        "  abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about  "
    )
    assert (
        phrase.phrase == "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    )


def test_invalid_phrase_raises_value_error():
    """Invalid checksum mnemonic should raise ValueError during construction."""
    invalid = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"

    with pytest.raises(ValueError, match="Invalid BIP-39 mnemonic phrase."):
        MnemonicPhrase.from_phrase(invalid)


def test_seed_and_ed25519_key_derivation_is_deterministic():
    """Known mnemonic+passphrase should produce deterministic seed and Ed25519 key bytes."""
    phrase = MnemonicPhrase.from_phrase(
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    )
    seed = phrase.to_seed(passphrase="TREZOR")
    assert seed.hex().startswith("c55257c360c07c72029aebc1b53c05ed")

    private_key = phrase.to_private_key_ed25519(passphrase="TREZOR")
    assert private_key.to_string_ed25519_raw() == seed[:32].hex()
