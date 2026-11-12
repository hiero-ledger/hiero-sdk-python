"""HookCall class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hooks.evm_hook_call import EvmHookCall


@dataclass
class HookCall:
    """
    A call to a hook from within a transaction.

    The hook's owner is implied by the call site. For example, an account
    allowance hook called from a transfer belongs to the account whose
    authorization is required, so only the owner-scoped hook number is given.

    Attributes:
        hook_id (int, optional): The owner-scoped number of the hook to call.
        evm_hook_call (EvmHookCall, optional): The call data and gas limit.
    """

    hook_id: int | None = None
    evm_hook_call: EvmHookCall | None = None

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
        """
        if self.hook_id is not None and (isinstance(self.hook_id, bool) or not isinstance(self.hook_id, int)):
            raise TypeError("hook_id must be an integer.")
        if self.evm_hook_call is not None and not isinstance(self.evm_hook_call, EvmHookCall):
            raise TypeError("evm_hook_call must be an EvmHookCall instance.")

    def _to_proto(self) -> basic_types_pb2.HookCall:
        """
        Converts this HookCall to its protobuf representation.

        Raises:
            ValueError: If hook_id or evm_hook_call is not set.
        """
        if self.hook_id is None:
            raise ValueError("HookCall requires a hook_id.")
        if self.evm_hook_call is None:
            raise ValueError("HookCall requires an evm_hook_call.")
        return basic_types_pb2.HookCall(hook_id=self.hook_id, evm_hook_call=self.evm_hook_call._to_proto())

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.HookCall) -> HookCall:
        """Creates a HookCall from its protobuf representation."""
        return cls(
            hook_id=proto.hook_id if proto.HasField("hook_id") else None,
            evm_hook_call=EvmHookCall._from_proto(proto.evm_hook_call) if proto.HasField("evm_hook_call") else None,
        )
