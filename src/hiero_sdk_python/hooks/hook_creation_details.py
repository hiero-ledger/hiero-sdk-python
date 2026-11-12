"""HookCreationDetails class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.hapi.services import hook_types_pb2
from hiero_sdk_python.hooks.evm_hook import EvmHook
from hiero_sdk_python.hooks.hook_extension_point import HookExtensionPoint


@dataclass
class HookCreationDetails:
    """
    Everything needed to create a hook on an account or contract.

    Attributes:
        extension_point (HookExtensionPoint): Where the hook plugs in.
        hook_id (int): The owner-scoped number to create the hook at.
        evm_hook (EvmHook, optional): The hook implementation.
        admin_key (Key, optional): A key that can manage the hook's storage
            without the owner's signature.
    """

    extension_point: HookExtensionPoint = HookExtensionPoint.ACCOUNT_ALLOWANCE_HOOK
    hook_id: int = 0
    evm_hook: EvmHook | None = None
    admin_key: Key | None = None

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
        """
        if not isinstance(self.extension_point, HookExtensionPoint):
            raise TypeError("extension_point must be a HookExtensionPoint.")
        if isinstance(self.hook_id, bool) or not isinstance(self.hook_id, int):
            raise TypeError("hook_id must be an integer.")
        if self.evm_hook is not None and not isinstance(self.evm_hook, EvmHook):
            raise TypeError("evm_hook must be an EvmHook instance.")
        if self.admin_key is not None and not isinstance(self.admin_key, Key):
            raise TypeError("admin_key must be a Key instance.")

    def _to_proto(self) -> hook_types_pb2.HookCreationDetails:
        """
        Converts these details to their protobuf representation.

        Raises:
            ValueError: If evm_hook is not set.
        """
        if self.evm_hook is None:
            raise ValueError("HookCreationDetails requires an evm_hook.")
        proto = hook_types_pb2.HookCreationDetails(
            extension_point=self.extension_point._to_proto(),
            hook_id=self.hook_id,
            evm_hook=self.evm_hook._to_proto(),
        )
        if self.admin_key is not None:
            proto.admin_key.CopyFrom(self.admin_key.to_proto_key())
        return proto

    @classmethod
    def _from_proto(cls, proto: hook_types_pb2.HookCreationDetails) -> HookCreationDetails:
        """Creates HookCreationDetails from its protobuf representation."""
        return cls(
            extension_point=HookExtensionPoint._from_proto(proto.extension_point),
            hook_id=proto.hook_id,
            evm_hook=EvmHook._from_proto(proto.evm_hook) if proto.HasField("evm_hook") else None,
            admin_key=Key.from_proto_key(proto.admin_key) if proto.HasField("admin_key") else None,
        )


def _validate_hook_list(hooks: list[HookCreationDetails]) -> list[HookCreationDetails]:
    """
    Validates a list of hook creation details and returns a copy of it.

    Raises:
        TypeError: If hooks is not a list of HookCreationDetails.
    """
    if not isinstance(hooks, list | tuple):
        raise TypeError("hooks must be a list of HookCreationDetails.")
    for hook in hooks:
        if not isinstance(hook, HookCreationDetails):
            raise TypeError("hooks must be a list of HookCreationDetails.")
    return list(hooks)


def _validate_hook_id(hook_id: int) -> int:
    """
    Validates a hook number.

    Raises:
        TypeError: If hook_id is not an integer.
    """
    if isinstance(hook_id, bool) or not isinstance(hook_id, int):
        raise TypeError("hook_id must be an integer.")
    return hook_id
