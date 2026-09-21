from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from tck.handlers.file import _build_update_file_transaction, update_file
from tck.param.file import UpdateFileParams
from tck.response.base import StatusOnlyResponse


pytestmark = pytest.mark.unit

_SESSION_ID = "session-test-123"
_VALID_KEY_HEX = PrivateKey.generate().to_string_der()


def _make_params(**kwargs) -> UpdateFileParams:
    return UpdateFileParams(sessionId=_SESSION_ID, **kwargs)


class TestUpdateFileParams:
    def test_parse_valid_params(self):
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

    def test_whitespace_contents_collapses_to_none(self):
        """non_empty_string_or_none strips blank strings to None."""
        raw = {"sessionId": _SESSION_ID, "contents": "   "}

        params = UpdateFileParams.parse_json_params(raw)

        assert params.contents is None

    def test_non_empty_contents_preserved(self):
        raw = {"sessionId": _SESSION_ID, "contents": "test content"}

        params = UpdateFileParams.parse_json_params(raw)

        assert params.contents == "test content"

    def test_omitted_optional_fields_are_none(self):
        raw = {"sessionId": _SESSION_ID}

        params = UpdateFileParams.parse_json_params(raw)

        assert params.fileId is None
        assert params.keys is None
        assert params.contents is None
        assert params.expirationTime is None
        assert params.memo is None
        assert params.commonTransactionParams is None

    def test_invalid_keys_type_raises_value_error(self):
        raw = {"sessionId": _SESSION_ID, "keys": "not-a-list"}

        with pytest.raises(ValueError, match="keys must be a list"):
            UpdateFileParams.parse_json_params(raw)

    def test_missing_session_id_raises(self):
        with pytest.raises(ValueError, match="sessionId"):
            UpdateFileParams.parse_json_params({})


class TestBuildUpdateFileTransaction:
    def test_all_setters_applied(self):
        params = _make_params(
            fileId="0.0.5678",
            keys=[_VALID_KEY_HEX],
            contents="file body",
            expirationTime="9999999999",
            memo="update memo",
        )

        tx = _build_update_file_transaction(params)

        assert tx.file_id == FileId.from_string("0.0.5678")
        assert tx.keys is not None
        assert len(tx.keys) == 1
        assert tx.contents == b"file body"
        assert isinstance(tx.expiration_time, Timestamp)
        assert tx.expiration_time.seconds == 9999999999
        assert tx.expiration_time.nanos == 0
        assert tx.file_memo == "update memo"

    def test_empty_contents_does_not_call_set_contents(self):
        params = _make_params(contents=None)

        tx = _build_update_file_transaction(params)

        assert tx.contents is None

    def test_omitted_fields_leave_transaction_attributes_none(self):
        params = _make_params()

        tx = _build_update_file_transaction(params)

        assert tx.file_id is None
        assert tx.keys is None
        assert tx.contents is None
        assert tx.expiration_time is None
        assert tx.file_memo is None

    def test_invalid_file_id_raises_value_error(self):
        params = _make_params(fileId="not-a-valid-file-id")

        with pytest.raises(ValueError):
            _build_update_file_transaction(params)


class TestUpdateFileHandler:
    def test_happy_path_returns_success_status(self):
        mock_client = MagicMock(spec=Client)

        mock_receipt = MagicMock()
        mock_receipt.status = ResponseCode.SUCCESS

        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        params = _make_params(fileId="0.0.999", memo="via handler")

        with (
            patch("tck.handlers.file.get_client", return_value=mock_client),
            patch("tck.handlers.file.FileUpdateTransaction.execute", return_value=mock_response),
        ):
            result = update_file(params)

        assert isinstance(result, StatusOnlyResponse)
        assert result.status == "SUCCESS"

    def test_happy_path_applies_common_params_when_present(self):
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
