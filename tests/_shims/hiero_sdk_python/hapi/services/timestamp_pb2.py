"""Minimal shim for timestamp_pb2.Timestamp used in tests."""

class Timestamp:
    def __init__(self, seconds: int = 0, nanos: int = 0):
        self.seconds = int(seconds)
        self.nanos = int(nanos)
