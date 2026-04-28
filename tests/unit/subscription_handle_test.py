from __future__ import annotations

from unittest.mock import Mock

from hiero_sdk_python.utils.subscription_handle import SubscriptionHandle


def test_not_cancelled_by_default():
    """Test a new handle starts in a non-cancelled state."""
    handle = SubscriptionHandle()
    assert not handle.is_cancelled()


def test_cancel_marks_as_cancelled():
    """Test calling cancel updates the is_cancelled status."""
    handle = SubscriptionHandle()
    handle.cancel()
    assert handle.is_cancelled()


def test_set_thread_and_join_calls_thread_join_with_timeout():
    """Test that join correctly forwards the timeout to the underlying thread."""
    handle = SubscriptionHandle()
    mock_thread = Mock()
    handle.set_thread(mock_thread)
    handle.join(timeout=0.25)
    mock_thread.join.assert_called_once_with(0.25)


def test_join_without_thread_raises_nothing():
    """Test join is a no-op if no thread has been associated."""
    handle = SubscriptionHandle()
    # should not raise
    handle.join()


def test_cancel_triggers_grpc_termination():
    """Test that cancelling the handle terminates the active gRPC call."""
    handle = SubscriptionHandle()
    mock_call = Mock()
    handle._set_call(mock_call)
    handle.cancel()
    mock_call.cancel.assert_called_once()


def test_immediate_cancellation_of_late_call():
    """Test a gRPC call is cancelled immediately if set after the handle was cancelled."""
    handle = SubscriptionHandle()
    mock_call = Mock()
    handle.cancel()
    handle._set_call(mock_call)
    mock_call.cancel.assert_called_once()
