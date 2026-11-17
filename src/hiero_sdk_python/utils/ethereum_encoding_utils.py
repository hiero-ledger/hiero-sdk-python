from __future__ import annotations


_UINT64_MAX = (1 << 64) - 1


def _int_to_minimal_bytes(v: int) -> bytes:
    """Minimal big-endian encoding of a non-negative int (0 -> b"")."""
    return v.to_bytes((v.bit_length() + 7) // 8, "big")


def _uint64_to_eth_bytes(v: int) -> bytes:
    """
    Encode an unsigned 64-bit value as canonical minimal big-endian bytes.

    Raises:
      TypeError: If v is not of type int.
      ValueError: if v is outside the range of an unsigned 64-bit integer.
    """
    if isinstance(v, bool) or not isinstance(v, int):
        raise TypeError("value must be of type int")
    if not 0 <= v <= _UINT64_MAX:
        raise ValueError("value is out of range for uint64")

    return _int_to_minimal_bytes(v)


def _eth_bytes_to_uint64(b: bytes | None) -> int:
    """
    Decode canonical big-endian bytes to an unsigned 64-bit int.

    Raises:
        TypeError: If b is not of type bytes.
    """
    if b is None:
        return 0

    if not isinstance(b, bytes):
        raise TypeError("parameter must be of type bytes")
    return int.from_bytes(b[-8:], "big")


def _big_int_to_eth_bytes(v: int | None) -> bytes:
    """
    Encode big int value as canonical minimal big-endian bytes.

    Raises:
        TypeError: If v is not of int type.
    """
    if v is None:
        return b""

    if isinstance(v, bool) or not isinstance(v, int):
        raise TypeError("value must be of type int")
    return _int_to_minimal_bytes(abs(v))


def _eth_bytes_to_big_int(b: bytes | None) -> int:
    """
    Decode canonical big-endian bytes to an int.

    Raises:
        TypeError: If b is not of type bytes.
    """
    if b is None:
        return 0

    if not isinstance(b, bytes):
        raise TypeError("parameter must be of type bytes")
    return int.from_bytes(b, "big")
