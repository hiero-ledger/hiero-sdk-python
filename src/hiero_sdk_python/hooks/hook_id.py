"""HookId class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hooks.hook_entity_id import HookEntityId


@dataclass(frozen=True)
class HookId:
    """
    The fully qualified ID of a hook: the owning entity plus a 64-bit hook number.

    Attributes:
        entity_id (HookEntityId): The account or contract that owns the hook.
        hook_id (int): The owner-scoped hook number.
    """

    entity_id: HookEntityId
    hook_id: int

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
        """
        if not isinstance(self.entity_id, HookEntityId):
            raise TypeError("entity_id must be a HookEntityId instance.")
        if isinstance(self.hook_id, bool) or not isinstance(self.hook_id, int):
            raise TypeError("hook_id must be an integer.")

    def _to_proto(self) -> basic_types_pb2.HookId:
        """Converts this HookId to its protobuf representation."""
        return basic_types_pb2.HookId(entity_id=self.entity_id._to_proto(), hook_id=self.hook_id)

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.HookId) -> HookId:
        """Creates a HookId from its protobuf representation."""
        return cls(entity_id=HookEntityId._from_proto(proto.entity_id), hook_id=proto.hook_id)
