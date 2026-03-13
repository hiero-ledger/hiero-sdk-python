from typing import List

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.hapi.services import basic_types_pb2


class KeyList(Key):
  def __init__(self, keys: List[Key] = None, threshold: int | None = None) -> None:
    self.keys: List[Key] = keys or []
    self.threshold: int | None = threshold

  def set_keys(self, keys: List[Key]) -> "KeyList":
    self.keys = keys
    return self
  
  def add_key(self, key: Key) -> "KeyList":
    self.keys.append(key)
    return self

  def set_threshold(self, threshold: int | None) -> "KeyList":
    self.threshold = threshold
    return self
  
  @classmethod
  def from_proto(cls, proto: basic_types_pb2.KeyList, threshold: int = None) -> "KeyList":
    keys = []
    for key in proto.keys:
      keys.append(Key.from_proto_key(key))
    
    return cls(
      keys=keys,
      threshold=threshold
    )

  def to_proto(self) -> basic_types_pb2.KeyList:
    proto_keys = []
    for key in self.keys:
      proto_keys.append(key.to_proto_key())
    
    return basic_types_pb2.KeyList(keys=proto_keys)
  
  def to_proto_key(self) -> basic_types_pb2.Key:
    proto_key_list = []

    for key in self.keys:
        proto_key_list.append(key.to_proto_key())

    if self.threshold is not None:
        threshold_key = basic_types_pb2.ThresholdKey(
            threshold=self.threshold,
            keys=basic_types_pb2.KeyList(keys=proto_key_list)
        )
        return basic_types_pb2.Key(thresholdKey=threshold_key)

    key_list = basic_types_pb2.KeyList(keys=proto_key_list)
    return basic_types_pb2.Key(keyList=key_list)