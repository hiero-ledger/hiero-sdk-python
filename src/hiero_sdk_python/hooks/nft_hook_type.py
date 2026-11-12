"""NftHookType enum for HIP-1195 hooks."""

from __future__ import annotations

from enum import Enum


class NftHookType(Enum):
    """
    Which party's account allowance hook is called for an NFT transfer, and how.

    The `PRE_*` types make one call before the transfer, to
    `allow(HookContext, ProposedTransfers)`. The `PRE_POST_*` types make two calls,
    to `allowPre(...)` before the transfer and `allowPost(...)` after it.

    Attributes:
        PRE_HOOK_SENDER: One call to the sender's hook.
        PRE_POST_HOOK_SENDER: Two calls to the sender's hook.
        PRE_HOOK_RECEIVER: One call to the receiver's hook.
        PRE_POST_HOOK_RECEIVER: Two calls to the receiver's hook.
    """

    PRE_HOOK_SENDER = "pre_tx_sender_allowance_hook"
    PRE_POST_HOOK_SENDER = "pre_post_tx_sender_allowance_hook"
    PRE_HOOK_RECEIVER = "pre_tx_receiver_allowance_hook"
    PRE_POST_HOOK_RECEIVER = "pre_post_tx_receiver_allowance_hook"

    @property
    def is_sender(self) -> bool:
        """Returns True if this type calls the sender's hook."""
        return self in (NftHookType.PRE_HOOK_SENDER, NftHookType.PRE_POST_HOOK_SENDER)

    @property
    def is_receiver(self) -> bool:
        """Returns True if this type calls the receiver's hook."""
        return not self.is_sender
