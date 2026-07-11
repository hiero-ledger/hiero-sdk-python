from __future__ import annotations

import inspect
import logging
from unittest.mock import patch

import pytest
import requests

from hiero_sdk_python.account.account_records_query import AccountRecordsQuery
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.contract.contract_bytecode_query import ContractBytecodeQuery
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.file.file_contents_query import FileContentsQuery
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery


pytestmark = pytest.mark.unit

QUERY_CLASSES = [
    AccountInfoQuery,
    FileContentsQuery,
    TokenInfoQuery,
    AccountRecordsQuery,
    ContractBytecodeQuery,
    ContractCallQuery,
    ContractInfoQuery,
    FileInfoQuery,
    CryptoGetAccountBalanceQuery,
    TokenNftInfoQuery,
    TopicInfoQuery,
    TransactionGetReceiptQuery,
    ScheduleInfoQuery,
]


@pytest.mark.parametrize("query_cls", QUERY_CLASSES, ids=[c.__name__ for c in QUERY_CLASSES])
def test_make_request_source_has_no_print_or_traceback_dump(query_cls):
    """
    Static regression check preventing accidental reintroduction of
    print() or traceback.print_exc() in _make_request().
    """
    source = inspect.getsource(query_cls._make_request)
    assert "print(" not in source, f"{query_cls.__name__}._make_request still calls print()"
    assert "traceback.print_exc()" not in source, (
        f"{query_cls.__name__}._make_request still calls traceback.print_exc()"
    )


@pytest.mark.parametrize("query_cls", QUERY_CLASSES, ids=[c.__name__ for c in QUERY_CLASSES])
def test_make_request_logs_exception_via_logging_module(query_cls, caplog):
    """
    Verify that _make_request routes exceptions through the logging module
    instead of printing directly to stdout or stderr.

    The request header is mocked to raise an exception so the error logging
    path can be exercised consistently across query implementations.
    """
    query = query_cls()

    # Some tests disable the SDK's root logger via the shared client fixture.
    # Override the logger level here so caplog can capture ERROR records.
    with (
        patch.object(query_cls, "_make_request_header", side_effect=ValueError("boom")),
        caplog.at_level(logging.ERROR, logger="hiero_sdk_python"),
        caplog.at_level(logging.ERROR),
        pytest.raises(ValueError),
    ):
        query._make_request()

    assert any(
        record.levelno == logging.ERROR and "Exception in _make_request" in record.message for record in caplog.records
    ), f"No ERROR-level 'Exception in _make_request' log record captured for {query_cls.__name__}"


def test_fetch_nodes_from_mirror_node_source_has_no_print(caplog):
    """
    Static + dynamic check for the missing-mirror-URL fallback path:
    no print(), and the warning is captured by the logging module.
    """
    source = inspect.getsource(Network._fetch_nodes_from_mirror_node)
    assert "print(" not in source

    # Bypass __init__ (which would itself raise ValueError for an unknown
    # network with no mirror URL and no default nodes) -- we only need
    # `self.network` set to exercise this specific private method.
    network = Network.__new__(Network)
    network.network = "not-a-known-network"

    with (
        caplog.at_level(logging.WARNING, logger="hiero_sdk_python"),
        caplog.at_level(logging.WARNING, logger="hiero_sdk_python.client.network"),
    ):
        result = network._fetch_nodes_from_mirror_node()

    assert result == []
    assert any(
        record.levelno == logging.WARNING and "No known mirror node URL" in record.message for record in caplog.records
    )


def test_fetch_nodes_from_mirror_node_logs_request_exception(caplog, monkeypatch):
    """
    Static + dynamic check for the mirror-node-fetch-failure fallback path:
    no print(), and the error is captured by the logging module, with the
    method still falling back to an empty list rather than raising.
    """
    source = inspect.getsource(Network._fetch_nodes_from_mirror_node)
    assert "print(" not in source

    network = Network.__new__(Network)
    network.network = "testnet"

    def raise_request_exception(*args, **kwargs):
        raise requests.RequestException("timeout")

    monkeypatch.setattr("hiero_sdk_python.client.network.requests.get", raise_request_exception)

    with (
        caplog.at_level(logging.ERROR, logger="hiero_sdk_python"),
        caplog.at_level(logging.ERROR, logger="hiero_sdk_python.client.network"),
    ):
        result = network._fetch_nodes_from_mirror_node()

    assert result == []
    assert any(
        record.levelno == logging.ERROR and "Error fetching nodes from mirror node API" in record.message
        for record in caplog.records
    )
