from __future__ import annotations

import inspect
import logging
from unittest.mock import patch

import pytest
import requests

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_records_query import AccountRecordsQuery
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.contract.contract_bytecode_query import ContractBytecodeQuery
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.file.file_contents_query import FileContentsQuery
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_info_query import ScheduleInfoQuery
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit

_ACCOUNT_ID = AccountId(0, 0, 100)
_TOKEN_ID = TokenId(0, 0, 200)

QUERY_FACTORIES = [
    (AccountInfoQuery, lambda: AccountInfoQuery(_ACCOUNT_ID), "_make_request_header"),
    (FileContentsQuery, lambda: FileContentsQuery(FileId(0, 0, 101)), "_make_request_header"),
    (TokenInfoQuery, lambda: TokenInfoQuery(_TOKEN_ID), "_make_request_header"),
    (AccountRecordsQuery, lambda: AccountRecordsQuery(_ACCOUNT_ID), "_make_request_header"),
    (
        ContractBytecodeQuery,
        lambda: ContractBytecodeQuery(ContractId(0, 0, 102)),
        "_make_request_header",
    ),
    (ContractCallQuery, lambda: ContractCallQuery(ContractId(0, 0, 102)), "_make_request_header"),
    (ContractInfoQuery, lambda: ContractInfoQuery(ContractId(0, 0, 102)), "_make_request_header"),
    (FileInfoQuery, lambda: FileInfoQuery(FileId(0, 0, 101)), "_make_request_header"),
    (
        CryptoGetAccountBalanceQuery,
        lambda: CryptoGetAccountBalanceQuery(_ACCOUNT_ID),
        "_make_request_header",
    ),
    (TokenNftInfoQuery, lambda: TokenNftInfoQuery(NftId(_TOKEN_ID, 1)), "_make_request_header"),
    (TopicInfoQuery, lambda: TopicInfoQuery(TopicId(0, 0, 103)), "_make_request_header"),
    (
        TransactionGetReceiptQuery,
        lambda: TransactionGetReceiptQuery(TransactionId(_ACCOUNT_ID)),
        "transaction_id._to_proto",
    ),
    (ScheduleInfoQuery, lambda: ScheduleInfoQuery(ScheduleId(0, 0, 104)), "_make_request_header"),
]

_IDS = [cls.__name__ for cls, _, _ in QUERY_FACTORIES]


@pytest.mark.parametrize("query_cls,factory,patch_target", QUERY_FACTORIES, ids=_IDS)
def test_make_request_source_has_no_print_or_traceback_dump(query_cls, factory, patch_target):
    """Ensure _make_request does not use print() or traceback.print_exc()."""
    source = inspect.getsource(query_cls._make_request)
    assert "print(" not in source, f"{query_cls.__name__}._make_request still calls print()"
    assert "traceback.print_exc()" not in source, (
        f"{query_cls.__name__}._make_request still calls traceback.print_exc()"
    )


@pytest.mark.parametrize("query_cls,factory,patch_target", QUERY_FACTORIES, ids=_IDS)
def test_make_request_logs_exception_via_module_logger(query_cls, factory, patch_target, caplog):
    """Ensure _make_request logs exceptions with the module logger and exc_info."""
    query = factory()

    # Patch either the query helper or an inline header builder.
    if "." in patch_target:
        attr_name, method_name = patch_target.split(".")
        patch_obj = type(getattr(query, attr_name))
        patch_ctx = patch.object(patch_obj, method_name, side_effect=ValueError("boom"))
    else:
        patch_ctx = patch.object(query_cls, patch_target, side_effect=ValueError("boom"))

    # Override the parent logger level so ERROR logs are captured.
    with (
        patch_ctx,
        caplog.at_level(logging.ERROR, logger="hiero_sdk_python"),
        caplog.at_level(logging.ERROR),
        pytest.raises(ValueError),
    ):
        query._make_request()

    matching = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR and "Exception in _make_request" in record.message
    ]
    assert matching, f"No ERROR-level 'Exception in _make_request' log record captured for {query_cls.__name__}"

    record = matching[0]
    assert record.name == query_cls.__module__, (
        f"Expected log emitted by '{query_cls.__module__}', got '{record.name}' "
        "(likely used logging.error(...) instead of logger.error(...))"
    )
    assert record.exc_info is not None, f"{query_cls.__name__} logged the error without exc_info -- traceback is lost"


def test_fetch_nodes_from_mirror_node_logs_missing_url(caplog):
    """Ensure missing mirror URL is logged and an empty list is returned."""
    source = inspect.getsource(Network._fetch_nodes_from_mirror_node)
    assert "print(" not in source

    # Bypass __init__; only self.network is needed for this private method.
    network = Network.__new__(Network)
    network.network = "not-a-known-network"

    with (
        caplog.at_level(logging.WARNING, logger="hiero_sdk_python"),
        caplog.at_level(logging.WARNING, logger="hiero_sdk_python.client.network"),
    ):
        result = network._fetch_nodes_from_mirror_node()

    assert result == []
    matching = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING and "No known mirror node URL" in record.message
    ]
    assert matching
    assert matching[0].name == Network.__module__


def test_fetch_nodes_from_mirror_node_logs_request_exception(caplog, monkeypatch):
    """Ensure request failures are logged and fall back to an empty list."""
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
    matching = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR and "Error fetching nodes from mirror node API" in record.message
    ]
    assert matching
    assert matching[0].name == Network.__module__


def test_fetch_nodes_from_mirror_node_logs_malformed_response(caplog, monkeypatch):
    """Ensure malformed mirror node responses are logged and fall back to an empty list instead of raising."""
    source = inspect.getsource(Network._fetch_nodes_from_mirror_node)
    assert "print(" not in source

    network = Network.__new__(Network)
    network.network = "testnet"

    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            # Missing required fields -> NodeAddress._from_dict raises.
            return {"nodes": [{"unexpected": "shape"}]}

    monkeypatch.setattr("hiero_sdk_python.client.network.requests.get", lambda *_a, **_k: _FakeResponse())

    with (
        caplog.at_level(logging.ERROR, logger="hiero_sdk_python"),
        caplog.at_level(logging.ERROR, logger="hiero_sdk_python.client.network"),
    ):
        result = network._fetch_nodes_from_mirror_node()

    assert result == []
    matching = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR and "Error parsing mirror node API response" in record.message
    ]
    assert matching
    assert matching[0].name == Network.__module__
