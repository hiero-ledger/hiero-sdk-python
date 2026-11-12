"""FungibleHookType enum for HIP-1195 hooks."""

from __future__ import annotations

from enum import Enum


class FungibleHookType(Enum):
    """
    How an account allowance hook is called for an HBAR or fungible token transfer.

    Attributes:
        PRE_TX_ALLOWANCE_HOOK: One call before the transfer, to
            `allow(HookContext, ProposedTransfers)`.
        PRE_POST_TX_ALLOWANCE_HOOK: Two calls, to `allowPre(...)` before the
            transfer and `allowPost(...)` after it.
    """

    PRE_TX_ALLOWANCE_HOOK = "pre_tx_allowance_hook"
    PRE_POST_TX_ALLOWANCE_HOOK = "pre_post_tx_allowance_hook"
