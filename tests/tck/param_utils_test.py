from __future__ import annotations

import pytest

from tck.util.param_utils import decode_hex


pytestmark = pytest.mark.unit


class TestDecodeHex:
    def test_decodes_plain_hex(self):
        assert decode_hex("1234abcd") == b"\x12\x34\xab\xcd"

    def test_decodes_0x_prefixed_hex(self):
        assert decode_hex("0x1234abcd") == b"\x12\x34\xab\xcd"

    def test_decodes_uppercase_hex(self):
        assert decode_hex("1234ABCD") == b"\x12\x34\xab\xcd"

    def test_decodes_empty_string(self):
        assert decode_hex("") == b""

    def test_decodes_bare_0x_prefix(self):
        assert decode_hex("0x") == b""

    def test_rejects_odd_length(self):
        with pytest.raises(ValueError):
            decode_hex("0x123")

    def test_rejects_non_hex_characters(self):
        with pytest.raises(ValueError):
            decode_hex("0xZZ")

    def test_rejects_embedded_whitespace(self):
        with pytest.raises(ValueError):
            decode_hex("12 34")
