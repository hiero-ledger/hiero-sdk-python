import threading

class SubscriptionHandle:
    """
    Represents a handle to an ongoing subscription.
    Calling .cancel() will signal the subscription thread to stop.
    """
    def __init__(self):
        self._cancelled = threading.Event()
        self._thread = None 

    def cancel(self):
        """
        Signals to cancel the subscription.
        """
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        """
        Returns True if this subscription is already cancelled.
        """
        return self._cancelled.is_set()

    def set_thread(self, thread: threading.Thread):
        """
        (Optional) Store the thread object for reference.
        """
        self._thread = thread

    def join(self, timeout=None):
        """
        (Optional) Wait for the subscription thread to end.
        """
        if self._thread:
            self._thread.join(timeout)
