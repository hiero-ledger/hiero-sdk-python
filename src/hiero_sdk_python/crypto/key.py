from abc import ABC, abstractmethod

from hiero_sdk_python.hapi.services import basic_types_pb2


class Key(ABC):
  @classmethod
  def from_proto_key(cls, proto: basic_types_pb2.Key) -> "Key":
    from hiero_sdk_python.crypto.public_key import PublicKey
    from hiero_sdk_python.crypto.evm_address import EvmAddress
    from hiero_sdk_python.contract.contract_id import ContractId
    from hiero_sdk_python.crypto.key_list import KeyList

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
        return ContractId._from_proto(proto.delegatable_contract_id)
      
      case "keyList":
        return KeyList.from_proto(proto=proto.keyList)

      case "thresholdKey":
        return KeyList.from_proto(proto=proto.thresholdKey.keyList, threshold=proto.thresholdKey.threshold)
        
      case _:
        raise ValueError(f"Unknown key type: {key_type}")
      
  
  @classmethod
  def from_bytes(cls, data: bytes) -> "Key":
    key = basic_types_pb2.Key()
    key.ParseFromString(data)
    return cls.from_proto_key(key)

  
  @abstractmethod
  def to_proto_key(self) -> basic_types_pb2.Key:
    pass

  def to_bytes(self) -> bytes:
    return self.to_proto_key().SerializeToString()

