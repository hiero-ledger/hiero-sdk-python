from __future__ import annotations

import threading
from typing import Any


class SubscriptionHandle:
    """
    Represents a handle to an ongoing subscription.

    Calling .cancel() will signal the subscription thread to stop.
    """

    def __init__(self):
        self._cancelled = threading.Event()
        self._thread: threading.Thread | None = None
        self._call: Any | None = None
        self._lock = threading.Lock()

    def _set_call(self, call: Any):
        """Sets the active gRPC call so it can be cancelled."""
        with self._lock:
            self._call = call

            if self._cancelled.is_set():
                self._call.cancel()

    def cancel(self):
        """Signals to cancel the subscription."""
        with self._lock:
            self._cancelled.set()

            if self._call:
                self._call.cancel()

    def is_cancelled(self) -> bool:
        """Returns True if this subscription is already cancelled."""
        return self._cancelled.is_set()

    def set_thread(self, thread: threading.Thread):
        """(Optional) Store the thread object for reference."""
        self._thread = thread

    def join(self, timeout=None):
        """(Optional) Wait for the subscription thread to end."""
        if self._thread:
            self._thread.join(timeout)
