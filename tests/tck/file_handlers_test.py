"""Test cases for the Hiero SDK TCK file-service handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.response_code import ResponseCode
from tck.handlers.file import delete_file
from tck.param.file import DeleteFileParams


pytestmark = pytest.mark.unit

SESSION_ID = "test-session"


@pytest.fixture(autouse=True)
def mock_client():
    """Patch get_client for every test in this module."""
    with patch("tck.handlers.file.get_client") as get_client:
        get_client.return_value = MagicMock()
        yield


def _success_receipt(transaction_cls):
    """Wire the mocked transaction chain to return a SUCCESS receipt."""
    receipt = MagicMock()
    receipt.status = ResponseCode.SUCCESS
    transaction = transaction_cls.return_value.set_grpc_deadline.return_value
    transaction.execute.return_value.get_receipt.return_value = receipt
    return transaction


class TestDeleteFileParams:
    def test_binds_camel_case_file_id(self):
        """fileId should bind from the camelCase JSON key."""
        params = DeleteFileParams.parse_json_params({"sessionId": SESSION_ID, "fileId": "0.0.15432"})

        assert params.fileId == "0.0.15432", "Expected fileId to bind"

    def test_empty_string_is_preserved(self):
        """An empty fileId must stay distinct from an omitted one."""
        params = DeleteFileParams.parse_json_params({"sessionId": SESSION_ID, "fileId": ""})

        assert params.fileId == "", "Empty string collapsed to None"

    def test_omitted_file_id_is_none(self):
        """An omitted fileId should parse as None."""
        params = DeleteFileParams.parse_json_params({"sessionId": SESSION_ID})

        assert params.fileId is None, "Expected None for omitted fileId"


class TestDeleteFile:
    @patch("tck.handlers.file.FileDeleteTransaction")
    def test_deletes_valid_file(self, transaction_cls):
        """Spec test 1: a valid fileId is set on the transaction."""
        transaction = _success_receipt(transaction_cls)

        result = delete_file(DeleteFileParams.parse_json_params({"sessionId": SESSION_ID, "fileId": "0.0.15432"}))

        assert result.status == "SUCCESS", "Expected SUCCESS status"
        assert transaction.set_file_id.called, "Expected set_file_id to be called"

    @patch("tck.handlers.file.FileDeleteTransaction")
    def test_empty_file_id_raises(self, transaction_cls):
        """Spec test 3: fileId="" raises, surfacing as an SDK internal error."""
        _success_receipt(transaction_cls)
        params = DeleteFileParams.parse_json_params({"sessionId": SESSION_ID, "fileId": ""})

        with pytest.raises(ValueError, match="[Ff]ile"):
            delete_file(params)

    @patch("tck.handlers.file.FileDeleteTransaction")
    def test_omitted_file_id_submits_zero_id(self, transaction_cls):
        """Spec test 4: an omitted fileId still reaches the network as 0.0.0."""
        transaction = _success_receipt(transaction_cls)

        delete_file(DeleteFileParams.parse_json_params({"sessionId": SESSION_ID}))

        set_id = transaction.set_file_id.call_args[0][0]
        assert str(set_id) == "0.0.0", "Expected 0.0.0"

    @patch("tck.handlers.file.FileDeleteTransaction")
    def test_invalid_file_id_format_raises(self, transaction_cls):
        """Spec test 9: a malformed fileId raises before the network call."""
        _success_receipt(transaction_cls)
        params = DeleteFileParams.parse_json_params({"sessionId": SESSION_ID, "fileId": "invalid.file.id"})

        with pytest.raises(ValueError, match="[Ff]ile"):
            delete_file(params)

