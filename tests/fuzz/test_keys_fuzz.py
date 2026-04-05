import warnings

import pytest
from hypothesis import given

from hiero_sdk_python import PrivateKey, PublicKey
from tests.fuzz.conftest import get_strategy

pytestmark = pytest.mark.fuzz


def _load_private_key_from_string(text: str) -> PrivateKey:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return PrivateKey.from_string(text)


def _load_private_key_from_bytes(data: bytes) -> PrivateKey:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return PrivateKey.from_bytes(data)


def _load_public_key_from_string(text: str) -> PublicKey:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return PublicKey.from_string(text)


def _load_public_key_from_bytes(data: bytes) -> PublicKey:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return PublicKey.from_bytes(data)


@given(text=get_strategy("private_key_valid_string"))
def test_private_key_from_string_roundtrips_valid_inputs(text: str) -> None:
    """Valid private-key strings must produce a stable key object and raw bytes."""
    parsed = _load_private_key_from_string(text)
    reparsed = _load_private_key_from_string(parsed.to_string_raw())

    assert parsed.to_bytes_raw() == reparsed.to_bytes_raw()
    assert parsed.is_ed25519() == reparsed.is_ed25519()
    assert parsed.to_string_raw() == parsed.to_bytes_raw().hex()


@given(data=get_strategy("private_key_valid_bytes"))
def test_private_key_from_bytes_roundtrips_valid_inputs(data: bytes) -> None:
    """Valid private-key byte encodings must round-trip through raw or DER serialization."""
    parsed = _load_private_key_from_bytes(data)
    reparsed = _load_private_key_from_bytes(parsed.to_bytes_der())

    assert parsed.to_bytes_raw() == reparsed.to_bytes_raw()
    assert parsed.is_ed25519() == reparsed.is_ed25519()


@given(text=get_strategy("private_key_invalid_string"))
def test_private_key_from_string_rejects_invalid_inputs(text: str) -> None:
    """Malformed private-key strings must raise ValueError."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError):
            PrivateKey.from_string(text)


@given(data=get_strategy("private_key_invalid_bytes"))
def test_private_key_from_bytes_rejects_invalid_inputs(data: bytes) -> None:
    """Malformed private-key bytes must raise ValueError."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError):
            PrivateKey.from_bytes(data)


@given(text=get_strategy("public_key_valid_string"))
def test_public_key_from_string_roundtrips_valid_inputs(text: str) -> None:
    """Valid public-key strings must preserve canonical raw bytes."""
    parsed = _load_public_key_from_string(text)
    reparsed = _load_public_key_from_string(parsed.to_string_raw())

    assert parsed.to_bytes_raw() == reparsed.to_bytes_raw()
    assert parsed.is_ed25519() == reparsed.is_ed25519()
    assert parsed.to_string_raw() == parsed.to_bytes_raw().hex()


@given(data=get_strategy("public_key_valid_bytes"))
def test_public_key_from_bytes_roundtrips_valid_inputs(data: bytes) -> None:
    """Valid public-key byte encodings must round-trip through DER serialization."""
    parsed = _load_public_key_from_bytes(data)
    reparsed = _load_public_key_from_bytes(parsed.to_bytes_der())

    assert parsed.to_bytes_raw() == reparsed.to_bytes_raw()
    assert parsed.is_ed25519() == reparsed.is_ed25519()


@given(text=get_strategy("public_key_invalid_string"))
def test_public_key_from_string_rejects_invalid_inputs(text: str) -> None:
    """Malformed public-key strings must raise ValueError."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError):
            PublicKey.from_string(text)


@given(data=get_strategy("public_key_invalid_bytes"))
def test_public_key_from_bytes_rejects_invalid_inputs(data: bytes) -> None:
    """Malformed public-key bytes must raise ValueError."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError):
            PublicKey.from_bytes(data)
