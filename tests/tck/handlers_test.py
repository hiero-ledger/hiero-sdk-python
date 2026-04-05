"""Test cases for the Hiero SDK TCK handlers registry and dispatch functionality."""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.exceptions import (
    MaxAttemptsError,
    PrecheckError,
    ReceiptStatusError,
)
from tck.errors import (
    HIERO_ERROR,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JsonRpcError,
)
from tck.handlers import registry
from tck.handlers.registry import (
    dispatch,
    get_all_handlers,
    get_handler,
    parse_result,
    rpc_method,
    safe_dispatch,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clear_handlers():
    """Clear the handlers registry before each test."""
    registry._HANDLERS.clear()
    yield
    registry._HANDLERS.clear()


class DummyParams:
    """Mock params class used for dispatch tests."""

    @classmethod
    def parse_json_params(cls, params):
        return params


@dataclass
class DummyResult:
    """Dataclass used to test parse_result."""
    value: int | None = None
    other: str | None = None


class TestHandlerRegistration:

    def test_handler_registration_via_decorator(self):
        """Test that @rpc_method decorator registers handler."""

        @rpc_method("test_method")
        def handler(params: DummyParams):
            return {"status": "ok"}

        handler_fn = get_handler("test_method")

        assert handler_fn is not None, "Expected handler to be registered"

        result = handler_fn({})
        assert result == {"status": "ok"}, "Expected handler result"


    def test_get_all_handlers(self):
        """Test retrieving all handlers."""

        @rpc_method("method1")
        def handler1(params: DummyParams):
            return "result1"

        @rpc_method("method2")
        def handler2(params: DummyParams):
            return "result2"

        handlers = get_all_handlers()

        assert len(handlers) == 2, "Expected two handlers"
        assert "method1" in handlers, "method1 missing"
        assert "method2" in handlers, "method2 missing"


    def test_get_nonexistent_handler_returns_none(self):
        """Nonexistent handler should return None."""
        assert get_handler("missing") is None, "Expected None"


    def test_handler_override(self):
        """Second registration should overwrite first."""

        @rpc_method("override")
        def first(params: DummyParams):
            return "first"

        @rpc_method("override")
        def second(params: DummyParams):
            return "second"

        handler = get_handler("override")

        assert handler({}) == "second", "Override failed"


    def test_get_all_handlers_returns_copy(self):
        """Returned dict should not modify registry."""

        @rpc_method("protected")
        def handler(params: DummyParams):
            return "ok"

        handlers = get_all_handlers()

        handlers["protected"] = lambda: "bad"
        handlers["injected"] = lambda: "bad"

        assert get_handler("protected")({}) == "ok", "Registry mutated"
        assert get_handler("injected") is None, "Unexpected handler injected"


class TestDispatch:

    def test_dispatch_success(self):
        """Dispatch should call registered handler."""

        @rpc_method("setup")
        def handler(params: DummyParams):
            return DummyResult(value=1, other="value")
        
        params = DummyParams()
        result = dispatch("setup", params)

        
        assert result == {"value": 1, "other": "value"}, "Dispatch failed"


    def test_dispatch_unknown_method(self):
        """Unknown method should raise METHOD_NOT_FOUND."""
        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("missing", DummyParams())

        assert excinfo.value.code == METHOD_NOT_FOUND, "Expected METHOD_NOT_FOUND"


    def test_dispatch_reraises_json_rpc_error(self):
        """JsonRpcError should pass through."""

        @rpc_method("error")
        def handler(params: DummyParams):
            raise JsonRpcError.invalid_params_error()

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("error", DummyParams())

        assert excinfo.value.code == INVALID_PARAMS, "Expected INVALID_PARAMS"


    def test_dispatch_converts_generic_exception(self):
        """Generic exception → INTERNAL_ERROR."""

        @rpc_method("crash")
        def handler(params: DummyParams):
            raise ValueError("Boom")

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("crash", DummyParams())

        assert excinfo.value.code == INTERNAL_ERROR, "Expected INTERNAL_ERROR"


    def test_dispatch_converts_precheck_error(self):
        """PrecheckError → HIERO_ERROR."""

        @rpc_method("precheck")
        def handler(params: DummyParams):
            raise PrecheckError(
                status=1,
                transaction_id="0.0.1",
                message="failure",
            )

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("precheck", DummyParams())

        assert excinfo.value.code == HIERO_ERROR, "Expected HIERO_ERROR"


    def test_dispatch_converts_receipt_status_error(self):
        """ReceiptStatusError → HIERO_ERROR."""

        @rpc_method("receipt")
        def handler(params: DummyParams):
            raise ReceiptStatusError(
                status=1,
                transaction_id=None,
                transaction_receipt=MagicMock(),
                message="fail",
            )

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("receipt", DummyParams())

        assert excinfo.value.code == HIERO_ERROR, "Expected HIERO_ERROR"


    def test_dispatch_converts_max_attempts_error(self):
        """MaxAttemptsError → HIERO_ERROR."""

        @rpc_method("max_attempts")
        def handler(params: DummyParams):
            raise MaxAttemptsError("fail", node_id="0.0.1")

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("max_attempts", DummyParams())

        assert excinfo.value.code == HIERO_ERROR, "Expected HIERO_ERROR"


class TestSafeDispatch:

    def test_safe_dispatch_success(self):
        """safe_dispatch should return raw result."""

        @rpc_method("success")
        def handler(params: DummyParams):
            return DummyResult(value=1, other="value")

        result = safe_dispatch("success", {}, 1)

        assert result == {"value":1, "other":"value"}, "Unexpected result"


    def test_safe_dispatch_json_error(self):
        """JsonRpcError should produce JSON-RPC error response."""

        @rpc_method("json_error")
        def handler(params: DummyParams):
            raise JsonRpcError.invalid_params_error(data="field")

        response = safe_dispatch("json_error", {}, 10)

        assert response["error"]["code"] == INVALID_PARAMS, "Expected INVALID_PARAMS"


    def test_safe_dispatch_generic_exception(self):
        """Generic exception → INTERNAL_ERROR."""

        @rpc_method("generic_error")
        def handler(params: DummyParams):
            raise RuntimeError("unexpected")

        response = safe_dispatch("generic_error", {}, 2)

        assert response["error"]["code"] == INTERNAL_ERROR, "Expected INTERNAL_ERROR"



class TestParseResult:

    def test_parse_result_dataclass(self):
        """Dataclass should convert to dict."""
        result = DummyResult(value=10, other="other")

        parsed = parse_result(result)

        assert parsed == {"value": 10, "other": "other"}, "Expected filtered dataclass result"

    def test_parse_result_dataclass_ignore_none(self):
        """Dataclass should convert to dict without None values."""
        result = DummyResult(value=10, other=None)

        parsed = parse_result(result)

        assert parsed == {"value": 10}, "Expected filtered dataclass result"