from unittest.mock import Mock

from hiero_sdk_python.utils.subscription_handle import SubscriptionHandle


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
