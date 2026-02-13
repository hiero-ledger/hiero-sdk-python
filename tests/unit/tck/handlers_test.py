"""Test cases for the Hiero SDK TCK handlers registry and dispatch functionality."""
import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.exceptions import (PrecheckError, ReceiptStatusError, MaxAttemptsError)
from tck.handlers.registry import (
    register_handler, get_handler, get_all_handlers, dispatch, safe_dispatch,
    validate_request_params
)
from tck.errors import (
    JsonRpcError,
    METHOD_NOT_FOUND,
    INTERNAL_ERROR,
    HIERO_ERROR,
    INVALID_PARAMS)
from tck.handlers import registry

pytestmark = pytest.mark.unit

@pytest.fixture(autouse=True)
def clear_handlers():
    """Clear the handlers registry before each test."""
    registry._HANDLERS.clear()
    yield
    registry._HANDLERS.clear()


class TestHandlerRegistration:
    """Test handler registration via decorator."""

    def test_handler_registration_via_decorator(self):
        """Test that @register_handler decorator adds handler to registry."""
        @register_handler("test_method")
        def test_handler(_params):
            return {"status": "ok"}

        handler = get_handler("test_method")
        if handler is None:
            raise AssertionError("Expected handler to be registered")
        if handler({"test": "param"}) != {"status": "ok"}:
            raise AssertionError("Expected handler to return ok status")

    def test_get_all_handlers(self):
        """Test that get_all_handlers returns copy of all registered handlers."""
        @register_handler("method1")
        def handler1(_params):
            return "result1"
    
        @register_handler("method2")
        def handler2(_params):
            return "result2"

        all_handlers = get_all_handlers()
        if len(all_handlers) != 2:
            raise AssertionError("Expected two handlers to be registered")
        if "method1" not in all_handlers:
            raise AssertionError("Expected method1 to be registered")
        if "method2" not in all_handlers:
            raise AssertionError("Expected method2 to be registered")

    def test_get_nonexistent_handler_returns_none(self):
        """Test that getting a non-existent handler returns None."""
        handler = get_handler("nonexistent")
        if handler is not None:
            raise AssertionError("Expected None for nonexistent handler")

    def test_handler_override_behavior(self):
        """Test that registering the same method twice overwrites the first handler."""
        @register_handler("override_method")
        def first_handler(_params):
            return "first"

        @register_handler("override_method")
        def second_handler(_params):
            return "second"

        handler = get_handler("override_method")
        if handler({}) != "second":
            raise AssertionError("Second handler should overwrite first")

    def test_get_all_handlers_returns_copy(self):
        """Test that get_all_handlers returns a copy that doesn't affect the registry."""
        @register_handler("protected_method")
        def protected_handler(_params):
            return "protected"
        
        all_handlers = get_all_handlers()
        all_handlers["protected_method"] = lambda: "modified"
        all_handlers["injected_method"] = lambda: "injected"
        
        # Original registry should be unchanged
        if get_handler("protected_method")({}) != "protected":
            raise AssertionError("Expected protected_method to be unchanged")
        if get_handler("injected_method") is not None:
            raise AssertionError("Expected injected_method to be absent")


class TestDispatch:
    """Test method dispatch functionality."""

    def test_dispatch_registered_method(self):
        """Test that dispatch invokes registered handler correctly."""
        @register_handler("setup")
        def setup_handler(_params):
            return {"ready": True}

        result = dispatch("setup", {"key": "value"}, None)
        if result != {"ready": True}:
            raise AssertionError("Expected handler result to match")

    def test_dispatch_with_session_id(self):
        """Test that dispatch passes session_id to handler when provided."""
        @register_handler("session_method")
        def session_handler(params, session_id):
            return {"session": session_id, "params": params}

        result = dispatch("session_method", {"data": "test"}, "session123")
        if result != {"session": "session123", "params": {"data": "test"}}:
            raise AssertionError("Expected session id and params to be passed through")

    def test_dispatch_unknown_method_raises_method_not_found(self):
        """Test that dispatching unknown method raises METHOD_NOT_FOUND error."""
        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("unknown_method", {}, None)

        if excinfo.value.code != METHOD_NOT_FOUND:
            raise AssertionError("Expected METHOD_NOT_FOUND error")
        if "Method not found" not in excinfo.value.message:
            raise AssertionError("Expected Method not found message")

    def test_dispatch_reraises_json_rpc_error(self):
        """Test that dispatch re-raises JsonRpcError exceptions."""
        @register_handler("error_method")
        def error_handler(params):
            raise JsonRpcError.invalid_params_error()

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("error_method", {}, None)

        if excinfo.value.code != INVALID_PARAMS:
            raise AssertionError("Expected INVALID_PARAMS error")

    def test_dispatch_converts_generic_exception_to_internal_error(self):
        """Test that dispatch converts generic exceptions to INTERNAL_ERROR."""
        @register_handler("crash_method")
        def crash_handler(params):
            raise ValueError("Something went wrong")

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("crash_method", {}, None)
        
        if excinfo.value.code != INTERNAL_ERROR:
            raise AssertionError("Expected INTERNAL_ERROR error")
        if "Something went wrong" not in excinfo.value.data:
            raise AssertionError("Expected error details to include message")

    def test_dispatch_converts_precheck_error_to_hiero_error(self):
        """Test that dispatch converts PrecheckError to HIERO_ERROR."""
        @register_handler("precheck_method")
        def precheck_handler(_params):
            raise PrecheckError(status=123, transaction_id="0.0.456", message="Account does not exist")

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("precheck_method", {}, None)
        
        if excinfo.value.code != HIERO_ERROR:
            raise AssertionError("Expected HIERO_ERROR error")
        if "Hiero error" not in excinfo.value.message:
            raise AssertionError("Expected Hiero error message")

    def test_dispatch_converts_receipt_status_error_to_hiero_error(self):
        """Test that dispatch converts ReceiptStatusError to HIERO_ERROR."""
        @register_handler("receipt_method")
        def receipt_handler(_params):
            mock_receipt = MagicMock()
            raise ReceiptStatusError(status=21, transaction_id=None, transaction_receipt=mock_receipt, message="Transaction failed")

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("receipt_method", {}, None)
        
        if excinfo.value.code != HIERO_ERROR:
            raise AssertionError("Expected HIERO_ERROR error")
        if "Hiero error" not in excinfo.value.message:
            raise AssertionError("Expected Hiero error message")

    def test_dispatch_converts_max_attempts_error_to_hiero_error(self):
        """Test that dispatch converts MaxAttemptsError to HIERO_ERROR."""
        @register_handler("max_attempts_method")
        def max_attempts_handler(_params):
            raise MaxAttemptsError("Max retries exceeded", node_id="0.0.1")

        with pytest.raises(JsonRpcError) as excinfo:
            dispatch("max_attempts_method", {}, None)
        
        if excinfo.value.code != HIERO_ERROR:
            raise AssertionError("Expected HIERO_ERROR error")
        if "Hiero error" not in excinfo.value.message:
            raise AssertionError("Expected Hiero error message")


class TestSafeDispatch:
    """Test safe dispatch with error handling."""

    def test_safe_dispatch_returns_success_response(self):
        """Test that safe_dispatch returns result for successful dispatch."""
        @register_handler("success_method")
        def success_handler(_params):
            return {"success": True}

        # safe_dispatch should return raw result without wrapping
        result = safe_dispatch("success_method", {}, None, 1)
        if result != {"success": True}:
            raise AssertionError("Expected raw handler result from safe_dispatch")

    def test_safe_dispatch_returns_error_response_for_json_rpc_error(self):
        """Test that safe_dispatch returns error response for JsonRpcError."""
        @register_handler("json_error_method")
        def error_handler(_params):
            raise JsonRpcError.invalid_params_error(data="field_name")

        response = safe_dispatch("json_error_method", {}, None, 42)

        if "error" not in response:
            raise AssertionError("Expected error in response")
        if response["error"]["code"] != INVALID_PARAMS:
            raise AssertionError("Expected INVALID_PARAMS error code")
        if response["error"]["message"] != "Invalid params":
            raise AssertionError("Expected Bad params message")
        if response["error"]["data"] != "field_name":
            raise AssertionError("Expected error data to match")
        if response["id"] != 42:
            raise AssertionError("Expected response id to match request id")

    def test_safe_dispatch_transforms_precheck_error(self):
        """Test that safe_dispatch transforms PrecheckError to HIERO_ERROR."""
        @register_handler("precheck_method")
        def precheck_handler(_params):
            raise PrecheckError(status=123, transaction_id="0.0.456", message="Account does not exist")

        response = safe_dispatch("precheck_method", {}, None, 1)

        if "error" not in response:
            raise AssertionError("Expected error in response")
        if response["error"]["code"] != HIERO_ERROR:
            raise AssertionError("Expected HIERO_ERROR error code")
        if "Hiero error" not in response["error"]["message"]:
            raise AssertionError("Expected Hiero error message")

    def test_safe_dispatch_transforms_receipt_status_error(self):
        """Test that safe_dispatch transforms ReceiptStatusError to HIERO_ERROR."""
        @register_handler("receipt_method")
        def receipt_handler(params):
            mock_receipt = MagicMock()
            raise ReceiptStatusError(status=21, transaction_id=None, transaction_receipt=mock_receipt, message="Transaction failed")
        response = safe_dispatch("receipt_method", {}, None, 2)

        if "error" not in response:
            raise AssertionError("Expected error in response")
        if response["error"]["code"] != HIERO_ERROR:
            raise AssertionError("Expected HIERO_ERROR error code")

    def test_safe_dispatch_transforms_max_attempts_error(self):
        """Test that safe_dispatch transforms MaxAttemptsError to HIERO_ERROR."""
        @register_handler("max_attempts_method")
        def max_attempts_handler(params):
            raise MaxAttemptsError("Max retries exceeded", node_id="0.0.1")
        response = safe_dispatch("max_attempts_method", {}, None, 3)

        if "error" not in response:
            raise AssertionError("Expected error in response")
        if response["error"]["code"] != HIERO_ERROR:
            raise AssertionError("Expected HIERO_ERROR error code")

    def test_safe_dispatch_transforms_generic_exception(self):
        """Test that safe_dispatch transforms generic Exception to INTERNAL_ERROR."""
        @register_handler("generic_error_method")
        def generic_error_handler(params):
            raise RuntimeError("Unexpected error")

        response = safe_dispatch("generic_error_method", {}, None, 4)

        if "error" not in response:
            raise AssertionError("Expected error in response")
        if response["error"]["code"] != INTERNAL_ERROR:
            raise AssertionError("Expected INTERNAL_ERROR error code")
        if response["id"] != 4:
            raise AssertionError("Expected response id to match request id")
    
    def test_safe_dispatch_includes_request_id_in_response(self):
        """Test that safe_dispatch returns raw result without id field (id is added at server level)."""
        @register_handler("test_id_method")
        def test_id_handler(_params):
            return {"data": "test"}
        
        # safe_dispatch returns raw result; request_id is added by server layer
        response = safe_dispatch("test_id_method", {}, None, "request_id_123")
        if response != {"data": "test"}:
            raise AssertionError("Expected raw response to be returned")


class TestValidateRequestParams:
    """Test request parameter validation."""
    
    def test_validate_valid_params(self):
        """Test that validate_request_params accepts valid params."""
        params = {"memo": "Test topic", "sequence_number": 42}
        required = {"memo": str, "sequence_number": int}

        # Should not raise- explicitly verify by calling and asserting no exception
        try:
            validate_request_params(params, required)
        except JsonRpcError:
            pytest.fail("validate_request_params raised JsonRpcError unexpectedly")

    def test_validate_missing_required_field(self):
        """Test that missing required field raises INVALID_PARAMS."""
        params = {"memo": "Test topic"}
        required = {"memo": str, "sequence_number": int}

        with pytest.raises(JsonRpcError) as excinfo:
            validate_request_params(params, required)

        if excinfo.value.code != INVALID_PARAMS:
            raise AssertionError("Expected INVALID_PARAMS error")
        if "sequence_number" not in excinfo.value.message:
            raise AssertionError("Expected missing field name in message")

    def test_validate_incorrect_field_type(self):
        """Test that incorrect field type raises INVALID_PARAMS."""
        params = {"memo": "Test topic", "sequence_number": "not_a_number"}
        required = {"memo": str, "sequence_number": int}

        with pytest.raises(JsonRpcError) as excinfo:
            validate_request_params(params, required)

        if excinfo.value.code != INVALID_PARAMS:
            raise AssertionError("Expected INVALID_PARAMS error")
        if "sequence_number" not in excinfo.value.message:
            raise AssertionError("Expected field name in message")

    def test_validate_non_dict_params_raises_invalid_params(self):
        """Test that non-dict params raises INVALID_PARAMS."""
        with pytest.raises(JsonRpcError) as excinfo:
            validate_request_params(["not", "a", "dict"], {"memo": str})

        if excinfo.value.code != INVALID_PARAMS:
            raise AssertionError("Expected INVALID_PARAMS error")

    def test_validate_none_value_for_required_field(self):
        """Test that None value for required field raises INVALID_PARAMS."""
        params = {"memo": None, "sequence_number": 42}
        required = {"memo": str, "sequence_number": int}

        with pytest.raises(JsonRpcError) as excinfo:
            validate_request_params(params, required)

        if excinfo.value.code != INVALID_PARAMS:
            raise AssertionError("Expected INVALID_PARAMS error")
        if "memo" not in excinfo.value.message:
            raise AssertionError("Expected field name in message")