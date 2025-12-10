"""Minimal shim for basic_types_pb2 used in tests."""

class _ProtoMessage:
    def CopyFrom(self, other):
        for k, v in getattr(other, "__dict__", {}).items():
            setattr(self, k, v)


class TransactionID(_ProtoMessage):
    def __init__(self):
        self.accountID = _ProtoMessage()
        self.transactionValidStart = _ProtoMessage()
        self.scheduled = False
