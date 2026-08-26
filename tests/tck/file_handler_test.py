"""Unit tests for the updateFile parameter model and handler.

Covers:
- UpdateFileParams.parse_json_params field mapping and validation
- _build_update_file_transaction setter application
- Empty-contents "leave unchanged" rule (contents="" → None → set_contents not called)
- Omitted fields leave transaction attributes at their default None values
- update_file handler happy path returning StatusOnlyResponse("SUCCESS")
- Invalid fileId propagates as ValueError
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from tck.errors import INVALID_PARAMS, JsonRpcError
from tck.handlers.file import _build_update_file_transaction, update_file
from tck.param.file import UpdateFileParams
from tck.response.file import UpdateFileResponse


pytestmark = pytest.mark.unit

# A valid secp256k1 DER-encoded private key hex (reused from common_params_test).
_VALID_KEY_HEX = (
    "30540201010420d0b3d3c266ad9aa414f41e3050d64f4012765abc94a745cbd0607"
    "bf41da51a96a00706052b8104000aa124032200037aa11171d538daf5c624f313bc"
    "106fff289e4a24768880d0fa71dd302a1fa9e7"
)

_SESSION_ID = "test-session-1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_params(**overrides) -> UpdateFileParams:
    """Return an UpdateFileParams with sensible defaults and optional overrides."""
    defaults = dict(
        fileId=None,
        keys=None,
        contents=None,
        expirationTime=None,
        memo=None,
        sessionId=_SESSION_ID,
        commonTransactionParams=None,
    )
    defaults.update(overrides)
    return UpdateFileParams(**defaults)


# ---------------------------------------------------------------------------
# UpdateFileParams.parse_json_params
# ---------------------------------------------------------------------------


class TestUpdateFileParamsParsing:
    def test_parse_all_fields(self):
        """All provided fields are mapped to the correct attributes."""
        raw = {
            "sessionId": _SESSION_ID,
            "fileId": "0.0.1234",
            "keys": [_VALID_KEY_HEX],
            "contents": "hello",
            "expirationTime": "9999999999",
            "memo": "my memo",
        }

        params = UpdateFileParams.parse_json_params(raw)

        assert params.sessionId == _SESSION_ID
        assert params.fileId == "0.0.1234"
        assert params.keys == [_VALID_KEY_HEX]
        assert params.contents == "hello"
        assert params.expirationTime == "9999999999"
        assert params.memo == "my memo"

    def test_empty_contents_collapses_to_none(self):
        """Per spec, contents="" means 'leave unchanged'; parse_json_params maps it to None."""
        raw = {"sessionId": _SESSION_ID, "contents": ""}

        params = UpdateFileParams.parse_json_params(raw)

        assert params.contents is None

    def test_whitespace_contents_preserved_verbatim(self):
        """Whitespace in contents (e.g. leading/trailing spaces or whitespace-only) is preserved."""
        raw = {"sessionId": _SESSION_ID, "contents": "  hello  "}

        params = UpdateFileParams.parse_json_params(raw)

        assert params.contents == "  hello  "

    def test_omitted_optional_fields_are_none(self):
        """Fields absent from the raw dict default to None."""
        raw = {"sessionId": _SESSION_ID}

        params = UpdateFileParams.parse_json_params(raw)

        assert params.fileId is None
        assert params.keys is None
        assert params.contents is None
        assert params.expirationTime is None
        assert params.memo is None
        assert params.commonTransactionParams is None

    def test_invalid_keys_type_raises_value_error(self):
        """keys must be a list; a non-list value raises ValueError."""
        raw = {"sessionId": _SESSION_ID, "keys": "not-a-list"}

        with pytest.raises(ValueError, match="keys must be a list"):
            UpdateFileParams.parse_json_params(raw)

    def test_invalid_keys_element_raises_value_error(self):
        """keys items must be non-empty strings."""
        raw = {"sessionId": _SESSION_ID, "keys": [""]}

        with pytest.raises(ValueError, match="keys must be a list of non-empty strings"):
            UpdateFileParams.parse_json_params(raw)

    def test_missing_session_id_raises(self):
        """sessionId is required; omitting it raises ValueError."""
        with pytest.raises(ValueError, match="sessionId"):
            UpdateFileParams.parse_json_params({})


# ---------------------------------------------------------------------------
# _build_update_file_transaction — setter application
# ---------------------------------------------------------------------------


class TestBuildUpdateFileTransaction:
    def test_file_id_setter_applied(self):
        """fileId is parsed and set on the transaction."""
        params = _make_params(fileId="0.0.5678")

        tx = _build_update_file_transaction(params)

        assert tx.file_id == FileId.from_string("0.0.5678")

    def test_keys_setter_applied(self):
        """keys list is decoded and set on the transaction."""
        params = _make_params(keys=[_VALID_KEY_HEX])

        tx = _build_update_file_transaction(params)

        assert tx.keys is not None
        assert len(tx.keys) == 1

    def test_contents_setter_applied(self):
        """Non-empty contents are encoded to bytes and stored."""
        params = _make_params(contents="file body")

        tx = _build_update_file_transaction(params)

        # FileUpdateTransaction._encode_contents converts str → bytes.
        assert tx.contents == b"file body"

    def test_empty_contents_does_not_call_set_contents(self):
        """contents='' collapses to None in parse_json_params, so set_contents
        is never invoked and the transaction contents attribute stays None."""
        # Simulate what parse_json_params does for contents="":
        params = _make_params(contents=None)  # already collapsed

        tx = _build_update_file_transaction(params)

        assert tx.contents is None

    def test_expiration_time_setter_applied(self):
        """expirationTime epoch-seconds string is converted to a Timestamp."""
        params = _make_params(expirationTime="9999999999")

        tx = _build_update_file_transaction(params)

        assert isinstance(tx.expiration_time, Timestamp)
        assert tx.expiration_time.seconds == 9999999999
        assert tx.expiration_time.nanos == 0

    def test_memo_setter_applied(self):
        """memo string is set on file_memo."""
        params = _make_params(memo="update memo")

        tx = _build_update_file_transaction(params)

        assert tx.file_memo == "update memo"

    def test_omitted_fields_leave_transaction_attributes_none(self):
        """When no optional fields are provided, all transaction attributes remain None."""
        params = _make_params()

        tx = _build_update_file_transaction(params)

        assert tx.file_id is None
        assert tx.keys is None
        assert tx.contents is None
        assert tx.expiration_time is None
        assert tx.file_memo is None

    def test_invalid_file_id_raises_value_error(self):
        """An unparseable fileId string propagates as ValueError."""
        params = _make_params(fileId="not-a-valid-file-id")

        with pytest.raises(ValueError):
            _build_update_file_transaction(params)

    def test_invalid_expiration_time_raises_json_rpc_error(self):
        """An unparseable expirationTime string raises JsonRpcError invalid params error."""
        params = _make_params(expirationTime="not-an-int")

        with pytest.raises(JsonRpcError) as exc_info:
            _build_update_file_transaction(params)

        assert exc_info.value.code == INVALID_PARAMS
        assert exc_info.value.data == "expirationTime must be an integer"


# ---------------------------------------------------------------------------
# update_file handler — happy path
# ---------------------------------------------------------------------------


class TestUpdateFileHandler:
    def test_happy_path_returns_success_status(self):
        """update_file returns StatusOnlyResponse('SUCCESS') when the receipt is SUCCESS."""
        mock_client = MagicMock(spec=Client)

        # Build a receipt mock with status = ResponseCode.SUCCESS
        mock_receipt = MagicMock()
        mock_receipt.status = ResponseCode.SUCCESS

        # response.get_receipt(...) returns the mock receipt
        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        params = _make_params(fileId="0.0.999", memo="via handler")

        with (
            patch("tck.handlers.file.get_client", return_value=mock_client),
            patch("tck.handlers.file.FileUpdateTransaction.execute", return_value=mock_response),
        ):
            result = update_file(params)

        assert isinstance(result, UpdateFileResponse)
        assert result.status == "SUCCESS"

    def test_happy_path_applies_common_params_when_present(self):
        """apply_common_params is called when commonTransactionParams is not None."""
        mock_client = MagicMock(spec=Client)
        mock_common = MagicMock()

        mock_receipt = MagicMock()
        mock_receipt.status = ResponseCode.SUCCESS
        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        params = _make_params(fileId="0.0.999", commonTransactionParams=mock_common)

        with (
            patch("tck.handlers.file.get_client", return_value=mock_client),
            patch("tck.handlers.file.FileUpdateTransaction.execute", return_value=mock_response),
        ):
            update_file(params)

        mock_common.apply_common_params.assert_called_once()
