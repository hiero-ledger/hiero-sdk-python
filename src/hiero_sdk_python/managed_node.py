import time
from hiero_sdk_python.managed_node_address import _ManagedNodeAddress


class _ManagedNode:
    
    def __init__(self, address: str, min_backoff: int):
        """
        Initialize a new ManagedNode instance.
        
        Args:
            address (str): The address of the node.
            min_backoff (int): The minimum backoff time in seconds.
        """
        self._address = _ManagedNodeAddress._from_string(address)
        self._current_backoff = min_backoff
        self._last_used = time.time()
        self._use_count = 0
        self._min_backoff = min_backoff
        self._max_backoff = 3600 # 1 Hour
        self._bad_grpc_status_count = 0
        self._readmit_time = None
        
    def _get_attempts(self):
        return self._bad_grpc_status_count
    
    def _get_address(self):
        if self._address:
            return str(self._address)
        return None
    
    def _get_readmit_time(self):
        return self._readmit_time
    
    def _set_min_backoff(self, min_backoff):
        if self._current_backoff == self._min_backoff:
            self._current_backoff = min_backoff
        self._min_backoff = min_backoff
    
    def _get_min_backoff(self):
        return self._min_backoff
    
    def _set_max_backoff(self, max_backoff):
        self._max_backoff = max_backoff
    
    def _get_max_backoff(self):
        return self._max_backoff
    
    def _in_use(self):
        self._use_count += 1
        self._last_used = time.time()
    
    def _is_healthy(self):
        if self._readmit_time is None:
            return True
        return self._readmit_time < time.time()
    
    def _increase_backoff(self):
        self._bad_grpc_status_count += 1
        self._current_backoff *= 2
        if self._current_backoff > self._max_backoff:
            self._current_backoff = self._max_backoff
        self._readmit_time = time.time() + self._current_backoff
    
    def _decrease_backoff(self):
        self._current_backoff //= 2
        if self._current_backoff < self._min_backoff:
            self._current_backoff = self._min_backoff
    
    def _wait(self):
        return self._readmit_time - self._last_used if self._readmit_time else 0
    
    def _get_use_count(self):
        return self._use_count
    
    def _get_last_used(self):
        return self._last_used