"""Tests for the TCK Node handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tck.errors import INVALID_PARAMS, JsonRpcError
from tck.handlers import node as node_handlers
from tck.param.node import DeleteNodeParams


pytestmark = pytest.mark.unit


class TestBuildDeleteNodeTransaction:
    def test_node_id_is_set(self):
        params = DeleteNodeParams(
            sessionId="session-1",
            nodeId="5",
        )

        transaction = node_handlers._build_delete_node_transaction(params)

        assert transaction.node_id == 5

    def test_missing_node_id_is_allowed_during_build(self):
        params = DeleteNodeParams(
            sessionId="session-1",
        )

        transaction = node_handlers._build_delete_node_transaction(params)

        assert transaction.node_id is None

    def test_negative_node_id_is_preserved(self):
        params = DeleteNodeParams(
            sessionId="session-1",
            nodeId="-1",
        )

        transaction = node_handlers._build_delete_node_transaction(params)

        assert transaction.node_id == -1

    def test_invalid_node_id_raises_invalid_params(self):
        params = DeleteNodeParams(
            sessionId="session-1",
            nodeId="not-a-number",
        )

        with pytest.raises(ValueError):
            node_handlers._build_delete_node_transaction(params)


class TestDeleteNodeHandler:
    def test_delete_node_handler_is_registered(self):
        from tck.handlers.registry import get_handler, rpc_method

        rpc_method("deleteNode")(node_handlers.delete_node)

        assert get_handler("deleteNode") is not None

    @patch("tck.handlers.node.execute_validated")
    @patch("tck.handlers.node.get_client")
    def test_delete_node_returns_success_status(
        self,
        mock_get_client,
        mock_execute_validated,
    ):
        client = MagicMock()
        receipt = MagicMock()
        receipt.status = 22

        mock_get_client.return_value = client
        mock_execute_validated.return_value = receipt

        params = DeleteNodeParams(
            sessionId="session-1",
            nodeId="5",
        )

        response = node_handlers.delete_node(params)

        assert response.status == "SUCCESS"
        mock_get_client.assert_called_once_with("session-1")
        mock_execute_validated.assert_called_once()

    @patch("tck.handlers.node.execute_validated")
    @patch("tck.handlers.node.get_client")
    def test_delete_node_applies_common_transaction_params(
        self,
        mock_get_client,
        mock_execute_validated,
    ):
        client = MagicMock()
        receipt = MagicMock()
        receipt.status = 22

        mock_get_client.return_value = client
        mock_execute_validated.return_value = receipt

        common_params = MagicMock()

        params = DeleteNodeParams(
            sessionId="session-1",
            nodeId="5",
            commonTransactionParams=common_params,
        )

        node_handlers.delete_node(params)

        common_params.apply_common_params.assert_called_once()

    def test_delete_node_transaction_missing_node_id_fails_at_proto_build(self):
        params = DeleteNodeParams(
            sessionId="session-1",
        )

        transaction = node_handlers._build_delete_node_transaction(params)

        with pytest.raises(ValueError, match="Missing required NodeID"):
            transaction._build_proto_body()
