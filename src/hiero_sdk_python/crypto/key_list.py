from typing import List

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.hapi.services import basic_types_pb2


class KeyList(Key):
    """
    Represents a list of cryptographic keys that can sign a transaction.

    The list may optionally define a threshold, specifying how many
    keys must sign for the transaction to be valid.
    """

    def __init__(self, keys: List[Key] = None, threshold: int | None = None) -> None:
        """
        Initialize a KeyList.

        Args:
          keys (List[Key], optional): A list of keys that belong to this KeyList.
          threshold (int, optional): The minimum number of keys required to sign.

        Raises:
          TypeError: If keys are not a list of Key objects or threshold not an int.
        """
        if keys is not None:
            if not isinstance(keys, list):
                raise TypeError("keys must be a list of Key objects")

            for key in keys:
                if not isinstance(key, Key):
                    raise TypeError("All elements in keys must be instances of Key")

        if threshold is not None and not isinstance(threshold, int):
            raise TypeError("threshold must be an integer")

        self.keys: List[Key] = keys or []
        self.threshold: int | None = threshold

    def set_keys(self, keys: List[Key]) -> "KeyList":
        """
        Set the keys contained in this KeyList.

        Args:
          keys (List[Key]): The new list of keys.

        Returns:
          KeyList: The current instance for method chaining.

        Raises:
          TypeError: If keys is not a list of Key objects.
        """
        if not isinstance(keys, list):
            raise TypeError("keys must be a list of Key objects")

        for key in keys:
            if not isinstance(key, Key):
                raise TypeError("All elements in keys must be instances of Key")

        self.keys = keys
        return self

    def add_key(self, key: Key) -> "KeyList":
        """
        Add a key to the KeyList.

        Args:
          key (Key): The key to add.

        Returns:
          KeyList: The current instance for method chaining.

        Raises:
          TypeError: If key is not an instance of Key.
        """
        if not isinstance(key, Key):
            raise TypeError("All elements in keys must be instances of Key")

        self.keys.append(key)
        return self

    def set_threshold(self, threshold: int | None) -> "KeyList":
        """
        Set the threshold for this KeyList.

        Args:
          threshold (int | None): The minimum number of keys required to sign.

        Returns:
          KeyList: The current instance for method chaining.

        Raises:
          TypeError: If threshold is not an integer.
        """
        if threshold is not None and not isinstance(threshold, int):
            raise TypeError("threshold must be an integer")

        self.threshold = threshold
        return self

    @classmethod
    def from_proto(
        cls, proto: basic_types_pb2.KeyList, threshold: int = None
    ) -> "KeyList":
        """
        Create a KeyList from a protobuf representation.

        Args:
          proto (basic_types_pb2.KeyList): The protobuf KeyList.
          threshold (int, optional): Optional threshold value for the KeyList.

        Returns:
          KeyList: The constructed KeyList instance.
        """
        keys = []
        for key in proto.keys:
            keys.append(Key.from_proto_key(key))

        return cls(keys=keys, threshold=threshold)

    def to_proto(self) -> basic_types_pb2.KeyList:
        """
        Convert this KeyList to its protobuf representation.

        Returns:
          basic_types_pb2.KeyList: The protobuf KeyList object.
        """
        proto_keys = []
        for key in self.keys:
            proto_keys.append(key.to_proto_key())

        return basic_types_pb2.KeyList(keys=proto_keys)

    def to_proto_key(self) -> basic_types_pb2.Key:
        """
        Convert this KeyList to a protobuf Key object.

        If a threshold is defined, the result will be a ThresholdKey.
        Otherwise, it will be a standard KeyList.

        Returns:
          basic_types_pb2.Key: The protobuf Key representation.
        """
        proto_key_list = []

        for key in self.keys:
            proto_key_list.append(key.to_proto_key())

        if self.threshold is not None:
            threshold_key = basic_types_pb2.ThresholdKey(
                threshold=self.threshold,
                keys=basic_types_pb2.KeyList(keys=proto_key_list),
            )
            return basic_types_pb2.Key(thresholdKey=threshold_key)

        key_list = basic_types_pb2.KeyList(keys=proto_key_list)
        return basic_types_pb2.Key(keyList=key_list)
