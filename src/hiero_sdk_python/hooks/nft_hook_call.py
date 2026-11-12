"""NftHookCall class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hooks.hook_call import HookCall
from hiero_sdk_python.hooks.nft_hook_type import NftHookType


@dataclass
class NftHookCall(HookCall):
    """
    A hook call attached to the sender or receiver side of an NFT transfer.

    Attributes:
        hook_id (int, optional): The owner-scoped number of the hook to call.
        evm_hook_call (EvmHookCall, optional): The call data and gas limit.
        hook_type (NftHookType): Whose hook is called (sender or receiver), and
            whether it is called before the transfer only, or before and after it.
    """

    hook_type: NftHookType = NftHookType.PRE_HOOK_SENDER

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
        """
        super().__post_init__()
        if not isinstance(self.hook_type, NftHookType):
            raise TypeError("hook_type must be an NftHookType.")

    def _apply_to(self, nft_transfer: basic_types_pb2.NftTransfer) -> None:
        """Sets this hook call on the matching oneof field of an NftTransfer."""
        getattr(nft_transfer, self.hook_type.value).CopyFrom(self._to_proto())

    @classmethod
    def _from_nft_transfer(
        cls, nft_transfer: basic_types_pb2.NftTransfer
    ) -> tuple[NftHookCall | None, NftHookCall | None]:
        """
        Reads the sender and receiver hook calls, if any, from an NftTransfer protobuf.

        Returns:
            tuple[NftHookCall | None, NftHookCall | None]: The sender and receiver hook calls.
        """
        return (
            cls._from_oneof(nft_transfer, "sender_allowance_hook_call"),
            cls._from_oneof(nft_transfer, "receiver_allowance_hook_call"),
        )

    @classmethod
    def _from_oneof(cls, nft_transfer: basic_types_pb2.NftTransfer, oneof: str) -> NftHookCall | None:
        """Reads one hook call oneof from an NftTransfer protobuf."""
        field = nft_transfer.WhichOneof(oneof)
        if field is None:
            return None
        base = HookCall._from_proto(getattr(nft_transfer, field))
        return cls(hook_id=base.hook_id, evm_hook_call=base.evm_hook_call, hook_type=NftHookType(field))
