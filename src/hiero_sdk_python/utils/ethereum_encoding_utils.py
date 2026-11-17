from __future__ import annotations


_UINT64_MAX = (1 << 64) - 1


def _int_to_minimal_bytes(v: int) -> bytes:
    """Minimal big-endian encoding of a non-negative int (0 -> b"")."""
    return v.to_bytes((v.bit_length() + 7) // 8, "big")


def _uint64_to_eth_bytes(v: int) -> bytes:
    """
    Encode an unsigned 64-bit value as canonical minimal big-endian bytes.

    Raises:
      ValueError: if v is outside the range of an unsigned 64-bit integer.
    """
    if isinstance(v, bool) or not isinstance(v, int):
        raise TypeError("value must be of type int")
    if not 0 <= v <= _UINT64_MAX:
        raise ValueError(f"value {v} is out of range for uint64")

    return _int_to_minimal_bytes(v)


def _eth_bytes_to_uint64(b: bytes | None) -> int:
    """
    Decode canonical big-endian bytes to an unsigned 64-bit int.
    """
    if b is None:
        return 0

    if not isinstance(b, bytes):
        raise TypeError("parameter must be of type bytes")
    return int.from_bytes(b[-8:], "big")


def _big_int_to_eth_bytes(v: int) -> bytes: ...


def _eth_bytes_to_big_int(b: bytes) -> int: ...
