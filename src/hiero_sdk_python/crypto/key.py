from __future__ import annotations

from abc import ABC, abstractmethod

from hiero_sdk_python.hapi.services import basic_types_pb2


class Key(ABC):
    """
    Abstract base class representing a Hiero cryptographic key.
    This class defines the common interface for all supported key types.

    Concrete implementations must implement to_proto_key.
    """

    @classmethod
    def from_proto_key(cls, proto: basic_types_pb2.Key) -> Key:
        """
        Convert a protobuf Key message into the appropriate SDK Key object.

        The method inspects the oneof key field in the protobuf message
        and constructs the corresponding SDK key implementation.

        Supported types:
        - ed25519
        - ECDSA_secp256k1
        - contractID
        - delegatable_contract_id
        - keyList
        - thresholdKey

        Args:
          proto (basic_types_pb2.Key): The protobuf Key message.

        Returns:
          Key: The corresponding Key implementation.

        Raises:
          TypeError: If proto is not a Key protobuf message.
          ValueError: If the key type is unknown.
        """
        from hiero_sdk_python.contract.contract_id import ContractId
        from hiero_sdk_python.contract.delegate_contract_id import DelegateContractId
        from hiero_sdk_python.crypto.evm_address import EvmAddress
        from hiero_sdk_python.crypto.key_list import KeyList
        from hiero_sdk_python.crypto.public_key import PublicKey

        if not isinstance(proto, basic_types_pb2.Key):
            raise TypeError("proto must be an instance of basic_types_pb2.Key")

        key_type = proto.WhichOneof("key")

        match key_type:
            case "ed25519":
                return PublicKey._from_bytes_ed25519(proto.ed25519)

            case "ECDSA_secp256k1":
                if len(proto.ECDSA_secp256k1) == 20:
                    return EvmAddress.from_bytes(proto.ECDSA_secp256k1)

                return PublicKey.from_bytes_ecdsa(proto.ECDSA_secp256k1)

            case "contractID":
                return ContractId._from_proto(proto.contractID)

            case "delegatable_contract_id":
                return DelegateContractId._from_proto(proto.delegatable_contract_id)

            case "keyList":
                return KeyList.from_proto(proto=proto.keyList)

            case "thresholdKey":
                return KeyList.from_proto(
                    proto=proto.thresholdKey.keys,
                    threshold=proto.thresholdKey.threshold,
                )

            case _:
                raise ValueError(f"Unknown key type: {key_type}")

    @classmethod
    def from_bytes(cls, data: bytes) -> Key:
        """
        Deserialize a Key object from protobuf-encoded bytes.

        Args:
          data (bytes): Serialized protobuf Key bytes.

        Returns:
          Key: The reconstructed Key instance.

        Raises:
          TypeError: If data is not bytes.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")

        key = basic_types_pb2.Key()
        key.ParseFromString(data)
        return cls.from_proto_key(key)

    @abstractmethod
    def to_proto_key(self) -> basic_types_pb2.Key:
        """
        Convert this key into its protobuf representation.

        Returns:
          basic_types_pb2.Key: The protobuf Key message.
        """
        pass

    def to_bytes(self) -> bytes:
        """
        Serialize this Key into protobuf bytes.

        Returns:
          bytes: The serialized protobuf Key.
        """
        return self.to_proto_key().SerializeToString()
