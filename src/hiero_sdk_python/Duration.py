from dataclasses import dataclass
from hiero_sdk_python.hapi.services.duration_pb2 import Duration as proto_Duration

@dataclass(frozen=True, init=True)
class Duration:
    """A frozen dataclass representing a duration in seconds."""
    seconds: int

    def __post_init__(self) -> None:
        """Validate types after initialization."""
        if not isinstance(self.seconds, int):
            raise TypeError(f"seconds must be an integer, got {type(self.seconds).__name__}")

    def _to_proto(self) -> proto_Duration:
        return proto_Duration(seconds=self.seconds)

    @classmethod
    def _from_proto(cls, proto: proto_Duration) -> 'Duration':
        if isinstance(proto, Duration):
            raise ValueError("Invalid duration proto")
        return cls(seconds=proto.seconds)

    def __str__(self) -> str:
        return f"Duration of {self.seconds} seconds."

    def __repr__(self) -> str:
        return f"Duration(seconds={self.seconds})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return False
        return self.seconds == other.seconds