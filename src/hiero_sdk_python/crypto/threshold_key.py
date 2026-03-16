"""Composite threshold-key support."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.hapi.services import basic_types_pb2

if TYPE_CHECKING:
    from hiero_sdk_python.utils.key_utils import Key


@dataclass(frozen=True)
class ThresholdKey:
    """A protobuf-compatible threshold key."""

    threshold: int
    keys: KeyList = field(default_factory=KeyList)

    def __init__(self, threshold: int, keys: Iterable[Key] | KeyList | None = None) -> None:
        """Initialize a threshold key from a threshold value and child keys."""
        if not isinstance(threshold, int):
            raise TypeError("Threshold must be an integer.")
        if threshold < 0:
            raise ValueError("Threshold must be non-negative.")

        key_list = keys if isinstance(keys, KeyList) else KeyList(keys)

        object.__setattr__(self, "threshold", threshold)
        object.__setattr__(self, "keys", key_list)

    def _to_proto_threshold_key(self) -> basic_types_pb2.ThresholdKey:
        """Convert this threshold key to its nested protobuf form."""
        return basic_types_pb2.ThresholdKey(
            threshold=self.threshold,
            keys=self.keys._to_proto_key_list(),
        )

    def _to_proto(self) -> basic_types_pb2.Key:
        """Convert this threshold key to a protobuf Key."""
        return basic_types_pb2.Key(thresholdKey=self._to_proto_threshold_key())

    @classmethod
    def _from_proto_threshold_key(cls, proto: basic_types_pb2.ThresholdKey) -> ThresholdKey:
        """Build a threshold key from its nested protobuf form."""
        return cls(
            threshold=proto.threshold,
            keys=KeyList._from_proto_key_list(proto.keys),
        )
