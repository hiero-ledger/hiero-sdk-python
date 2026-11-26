"""
Ethereum integer encoding helpers.

Ethereum transaction fields that hold integers (nonce, gas limit, gas price,
value, chain id, signature r/s, ...) are serialized in RLP as *unsigned*,
big-endian byte strings in their canonical (minimal) form:

* No leading zero bytes are allowed.
* The integer ``0`` is encoded as the empty byte string ``b""``.
* Negative values cannot be represented and are rejected, never wrapped
  or converted with ``abs()``. A wrapped or sign-flipped amount would still
  produce a transaction that the network accepts and executes.
* Each field has a fixed maximum width: 64 bits (uint64) or 256 bits (uint256). Values that do not fit are rejected.

Decoding applies the same rules in reverse. Input that is not canonical
(it has a leading zero byte) or is wider than the target type raises an
error instead of being truncated, so malformed data is never silently
misreported.
"""

from __future__ import annotations


_UINT64_BITS = 64
_UINT256_BITS = 256


def _uint_to_eth_bytes(v: int, bits: int) -> bytes:
    """
    Encode an unsigned int of the given bit width as canonical bytes.

    Raises:
        TypeError: If v or bits is not an int.
        ValueError: If bits is invalid, or v is outside 0..2**bits - 1.
    """
    if isinstance(v, bool) or not isinstance(v, int):
        raise TypeError("value must be of type int")
    if bits == _UINT256_BITS:
        v = abs(v)
    if not 0 <= v <= ((1 << bits) - 1):
        raise ValueError(f"value is out of range for uint{bits}")

    return v.to_bytes((v.bit_length() + 7) // 8, "big")


def _eth_bytes_to_uint(b: bytes | None, bits: int) -> int:
    """
    Decode canonical bytes to an unsigned int. None and b"" decode to 0.

    Raises:
        TypeError: If b is not bytes or None, or bits is not an int.
    """
    if b is None:
        return 0
    if not isinstance(b, bytes):
        raise TypeError("parameter must be of type bytes")
    if b[:1] == b"\x00":
        raise ValueError("encoded value must not have leading zero bytes")

    if bits == _UINT64_BITS:
        b = b[-8:]

    return int.from_bytes(b, "big")


def _uint64_to_eth_bytes(v: int) -> bytes:
    """
    Encode a uint64 as canonical bytes.

    Raises:
        TypeError: If v is not an int.
        ValueError: If v is outside 0..2**64 - 1.
    """
    return _uint_to_eth_bytes(v, _UINT64_BITS)


def _eth_bytes_to_uint64(b: bytes | None) -> int:
    """
    Decode canonical bytes to a uint64. None and b"" decode to 0.
    Input longer than 8 bytes is truncated to the low 8.

    Raises:
        TypeError: If b is not bytes or None.
        ValueError: If b has a leading zero byte.
    """
    return _eth_bytes_to_uint(b, _UINT64_BITS)


def _big_int_to_eth_bytes(v: int | None) -> bytes:
    """
    Encode an int of up to 256 bits as canonical bytes. None and 0 encode to b"".
    Negative values encode their absolute value.

    Raises:
        TypeError: If v is not an int or None.
        ValueError: If abs(v) is larger than 2**256 - 1.
    """
    if v is None:
        return b""
    return _uint_to_eth_bytes(v, _UINT256_BITS)


def _eth_bytes_to_big_int(b: bytes | None) -> int:
    """
    Decode canonical bytes to an unsigned int. None and b"" decode to 0.

    Raises:
        TypeError: If b is not bytes or None.
        ValueError: If b has a leading zero byte.
    """
    return _eth_bytes_to_uint(b, _UINT256_BITS)
