"""HookExtensionPoint enum for HIP-1195 hooks."""

from __future__ import annotations

from enum import IntEnum
from typing import cast

from hiero_sdk_python.hapi.services import hook_types_pb2


class HookExtensionPoint(IntEnum):
    """
    The Hiero extension points that accept a hook.

    Attributes:
        ACCOUNT_ALLOWANCE_HOOK: Customizes an account's allowances during a
            CryptoTransfer transaction.
    """

    ACCOUNT_ALLOWANCE_HOOK = hook_types_pb2.HookExtensionPoint.ACCOUNT_ALLOWANCE_HOOK

    def _to_proto(self) -> hook_types_pb2.HookExtensionPoint:
        """Returns the protobuf enum value."""
        return cast(hook_types_pb2.HookExtensionPoint, int(self))

    @classmethod
    def _from_proto(cls, proto: int) -> HookExtensionPoint:
        """
        Creates a HookExtensionPoint from its protobuf enum value.

        Raises:
            ValueError: If the value is not a known extension point.
        """
        return cls(proto)
