"""Unit tests for the createFile TCK method (params, transaction builder, handler)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.response_code import ResponseCode
from tck.handlers.file import _build_create_file_transaction, create_file
from tck.param.file import CreateFileParams
from tck.response.file import CreateFileResponse
from tck.util.client_utils import _CLIENTS, store_client


pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clear_clients():
    """Clear the client registry before and after each test."""
    _CLIENTS.clear()
    yield
    _CLIENTS.clear()


@pytest.fixture
def der_key() -> str:
    """A real DER-encoded ed25519 private key string, matching the TCK spec's key format."""
    return PrivateKey.generate_ed25519().to_string_der()


class TestCreateFileParams:
    """Test CreateFileParams.parse_json_params."""

    def test_parses_all_fields(self, der_key):
        raw_params = {
            "sessionId": "session-1",
            "keys": [der_key],
            "contents": "hello world",
            "expirationTime": "1234567890",
            "memo": "test file",
        }

        params = CreateFileParams.parse_json_params(raw_params)

        assert params.sessionId == "session-1"
        assert params.keys == [der_key]
        assert params.contents == "hello world"
        assert params.expirationTime == 1234567890
        assert params.memo == "test file"
        assert params.commonTransactionParams is None

    def test_all_optional_fields_omitted(self):
        params = CreateFileParams.parse_json_params({"sessionId": "session-1"})

        assert params.keys is None
        assert params.contents is None
        assert params.expirationTime is None
        assert params.memo is None

    def test_keys_not_a_list_raises(self):
        with pytest.raises(ValueError, match="keys must be a list"):
            CreateFileParams.parse_json_params({"sessionId": "session-1", "keys": "not-a-list"})

    def test_missing_session_id_raises(self):
        with pytest.raises(ValueError, match="sessionId"):
            CreateFileParams.parse_json_params({})

    def test_invalid_expiration_time_becomes_none(self):
        params = CreateFileParams.parse_json_params({"sessionId": "session-1", "expirationTime": "not-a-number"})
        assert params.expirationTime is None


class TestBuildCreateFileTransaction:
    """Test _build_create_file_transaction."""

    def test_builds_transaction_with_all_fields(self, der_key):
        params = CreateFileParams.parse_json_params(
            {
                "sessionId": "session-1",
                "keys": [der_key],
                "contents": "hello world",
                "expirationTime": "1234567890",
                "memo": "test file",
            }
        )

        tx = _build_create_file_transaction(params)

        assert isinstance(tx, FileCreateTransaction)
        assert len(tx.keys) == 1
        assert tx.contents == b"hello world"
        assert tx.expiration_time.seconds == 1234567890
        assert tx.file_memo == "test file"

    def test_builds_transaction_with_no_fields(self):
        params = CreateFileParams.parse_json_params({"sessionId": "session-1"})

        tx = _build_create_file_transaction(params)

        assert isinstance(tx, FileCreateTransaction)
        assert tx.keys == []
        assert tx.contents is None
        assert tx.file_memo is None


class TestCreateFileHandler:
    """Test the create_file RPC handler."""

    def _mock_execute_chain(self, status: int, file_id: FileId | None):
        """Build a mocked FileCreateTransaction.execute()->response.get_receipt() chain."""
        mock_receipt = MagicMock()
        mock_receipt.status = status
        mock_receipt.file_id = file_id

        mock_response = MagicMock()
        mock_response.get_receipt.return_value = mock_receipt

        return patch.object(FileCreateTransaction, "execute", return_value=mock_response)

    def test_create_file_success(self, der_key):
        store_client("session-1", MagicMock())
        params = CreateFileParams.parse_json_params({"sessionId": "session-1", "keys": [der_key]})

        with self._mock_execute_chain(ResponseCode.SUCCESS, FileId(0, 0, 100)):
            response = create_file(params)

        assert isinstance(response, CreateFileResponse)
        assert response.fileId == "0.0.100"
        assert response.status == "SUCCESS"

    def test_create_file_success_status_but_no_file_id(self):
        """If the receipt is SUCCESS but somehow has no file_id, fileId should be empty, not raise."""
        store_client("session-1", MagicMock())
        params = CreateFileParams.parse_json_params({"sessionId": "session-1"})

        with self._mock_execute_chain(ResponseCode.SUCCESS, None):
            response = create_file(params)

        assert response.fileId == ""
        assert response.status == "SUCCESS"
