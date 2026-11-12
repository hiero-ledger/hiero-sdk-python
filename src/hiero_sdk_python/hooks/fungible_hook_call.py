"""FungibleHookCall class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hooks.fungible_hook_type import FungibleHookType
from hiero_sdk_python.hooks.hook_call import HookCall


@dataclass
class FungibleHookCall(HookCall):
    """
    A hook call attached to an HBAR or fungible token transfer.

    Attributes:
        hook_id (int, optional): The owner-scoped number of the hook to call.
        evm_hook_call (EvmHookCall, optional): The call data and gas limit.
        hook_type (FungibleHookType): Whether the hook is called before the
            transfer only, or before and after it.
    """

    hook_type: FungibleHookType = FungibleHookType.PRE_TX_ALLOWANCE_HOOK

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
        """
        super().__post_init__()
        if not isinstance(self.hook_type, FungibleHookType):
            raise TypeError("hook_type must be a FungibleHookType.")

    def _apply_to(self, account_amount: basic_types_pb2.AccountAmount) -> None:
        """Sets this hook call on the matching oneof field of an AccountAmount."""
        getattr(account_amount, self.hook_type.value).CopyFrom(self._to_proto())

    @classmethod
    def _from_account_amount(cls, account_amount: basic_types_pb2.AccountAmount) -> FungibleHookCall | None:
        """
        Reads the hook call, if any, from an AccountAmount protobuf.

        Returns:
            FungibleHookCall | None: The hook call, or None if no hook is set.
        """
        field = account_amount.WhichOneof("hook_call")
        if field is None:
            return None
        base = HookCall._from_proto(getattr(account_amount, field))
        return cls(hook_id=base.hook_id, evm_hook_call=base.evm_hook_call, hook_type=FungibleHookType(field))
