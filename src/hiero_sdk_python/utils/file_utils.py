"""
hiero_sdk_python.utils.file_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility functions shared by the file service transactions.
"""

from __future__ import annotations


def encode_file_contents(contents: str | bytes | bytearray | None) -> bytes | None:
    """
    Validate file contents and encode them to bytes.

    Strings are encoded as UTF-8; bytes and bytearray are returned as bytes.

    Args:
        contents (str | bytes | bytearray | None): The contents to encode.

    Returns:
        Optional[bytes]: The encoded contents, or None if input is None.

    Raises:
        TypeError: If contents is not str, bytes, bytearray, or None.
    """
    if contents is None:
        return None
    if isinstance(contents, str):
        return contents.encode("utf-8")
    if isinstance(contents, (bytes, bytearray)):
        return bytes(contents)
    raise TypeError("contents must be of type bytes or str")
