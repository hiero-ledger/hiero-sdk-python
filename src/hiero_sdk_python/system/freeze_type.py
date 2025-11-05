"""
Defines FreezeType enum for representing freeze types
"""
from enum import Enum

from hiero_sdk_python.hapi.services.freeze_type_pb2 import (
    FreezeType as proto_FreezeType,
)


class FreezeType(Enum):
    """
    Freeze type:

    • UNKNOWN_FREEZE_TYPE - not applicable
    • FREEZE_ONLY       - Freeze only
    • PREPARE_UPGRADE   - Prepare upgrade
    • FREEZE_UPGRADE    - Freeze upgrade
    • FREEZE_ABORT      - Freeze abort
    • TELEMETRY_UPGRADE - Telemetry upgrade
    """

    UNKNOWN_FREEZE_TYPE = 0
    FREEZE_ONLY = 1
    PREPARE_UPGRADE = 2
    FREEZE_UPGRADE = 3
    FREEZE_ABORT = 4
    TELEMETRY_UPGRADE = 5

    @staticmethod
    def _from_proto(proto_obj: proto_FreezeType) -> "FreezeType":
        """
        Converts a protobuf FreezeType to a FreezeType enum.
        
        Args:
            proto_obj (proto_FreezeType): The protobuf FreezeType object.
        
        Returns:
            FreezeType: The corresponding FreezeType enum value.
        """
        if proto_obj == proto_FreezeType.FREEZE_ONLY:
            return FreezeType.FREEZE_ONLY
        elif proto_obj == proto_FreezeType.PREPARE_UPGRADE:
            return FreezeType.PREPARE_UPGRADE
        elif proto_obj == proto_FreezeType.FREEZE_UPGRADE:
            return FreezeType.FREEZE_UPGRADE
        elif proto_obj == proto_FreezeType.FREEZE_ABORT:
            return FreezeType.FREEZE_ABORT
        elif proto_obj == proto_FreezeType.TELEMETRY_UPGRADE:
            return FreezeType.TELEMETRY_UPGRADE
        return FreezeType.UNKNOWN_FREEZE_TYPE

    def _to_proto(self) -> proto_FreezeType:
        """
        Converts a FreezeType enum to a protobuf FreezeType object.
        
        Args:
            self (FreezeType): The FreezeType enum value.
        
        Returns:
            proto_FreezeType: The corresponding protobuf FreezeType object.
        """
        if self == FreezeType.FREEZE_ONLY:
            return proto_FreezeType.FREEZE_ONLY
        elif self == FreezeType.PREPARE_UPGRADE:
            return proto_FreezeType.PREPARE_UPGRADE
        elif self == FreezeType.FREEZE_UPGRADE:
            return proto_FreezeType.FREEZE_UPGRADE
        elif self == FreezeType.FREEZE_ABORT:
            return proto_FreezeType.FREEZE_ABORT
        elif self == FreezeType.TELEMETRY_UPGRADE:
            return proto_FreezeType.TELEMETRY_UPGRADE
        return proto_FreezeType.UNKNOWN_FREEZE_TYPE

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FreezeType):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return False
