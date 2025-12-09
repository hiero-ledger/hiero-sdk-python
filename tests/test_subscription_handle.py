from unittest.mock import Mock
import importlib.util
from pathlib import Path

# Load the module directly from the source file to avoid importing the
# package `hiero_sdk_python` (its top-level __init__ triggers imports of
# many modules that require generated protobufs during test collection).
repo_root = Path(__file__).resolve().parent.parent
module_path = repo_root / "src" / "hiero_sdk_python" / "utils" / "subscription_handle.py"
spec = importlib.util.spec_from_file_location("subscription_handle", str(module_path))
subscription_handle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subscription_handle)
SubscriptionHandle = subscription_handle.SubscriptionHandle


def test_not_cancelled_by_default():
    handle = SubscriptionHandle()
    assert not handle.is_cancelled()


def test_cancel_marks_as_cancelled():
    handle = SubscriptionHandle()
    handle.cancel()
    assert handle.is_cancelled()


def test_set_thread_and_join_calls_thread_join_with_timeout():
    handle = SubscriptionHandle()
    mock_thread = Mock()
    handle.set_thread(mock_thread)
    handle.join(timeout=0.25)
    mock_thread.join.assert_called_once_with(0.25)


def test_join_without_thread_raises_nothing():
    handle = SubscriptionHandle()
    # should not raise
    handle.join()
