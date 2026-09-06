"""Test cases for the TCK param_utils helpers."""

from __future__ import annotations

import pytest

from tck.util.param_utils import decode_hex, parse_session_id


pytestmark = pytest.mark.unit


class TestDecodeHex:
    def test_decodes_plain_hex(self):
        assert decode_hex("60006000") == b"\x60\x00\x60\x00"

    def test_decodes_0x_prefixed_hex(self):
        assert decode_hex("0x60006000") == b"\x60\x00\x60\x00"

    def test_rejects_non_hex_characters(self):
        with pytest.raises(ValueError):
            decode_hex("0xZZ")

    def test_rejects_odd_length(self):
        with pytest.raises(ValueError):
            decode_hex("0x123")

    def test_rejects_embedded_whitespace(self):
        """bytes.fromhex alone would accept "60 00"."""
        with pytest.raises(ValueError):
            decode_hex("60 00")

    def test_rejects_surrounding_whitespace(self):
        with pytest.raises(ValueError):
            decode_hex(" 6000\n")


class TestParseSessionId:
    def test_returns_session_id(self):
        assert parse_session_id({"sessionId": "session-1"}) == "session-1"

    @pytest.mark.parametrize("params", [{}, {"sessionId": ""}, {"sessionId": 123}])
    def test_rejects_missing_or_invalid_session_id(self, params):
        with pytest.raises(ValueError):
            parse_session_id(params)
