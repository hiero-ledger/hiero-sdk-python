# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId

class AirdropPendingTransaction(Transaction):
    """
    Represents a transaction that includes from 1 to 10 PendingAirdropId instances.
    """

    def __init__(self, pending_airdrop_ids: Optional[List[PendingAirdropId]] = None) -> None:
        """
        Initialize the AirdropPendingTransaction.

        Args:
            pending_airdrop_ids (Optional[List[PendingAirdropId]]): Optional list of pending airdrop IDs.
        """
        super().__init__()
        self._pending_airdrop_ids: List[PendingAirdropId] = pending_airdrop_ids or []
        self._validate_airdrop_ids()

    def _validate_airdrop_ids(self):
        """
        Validates that pending_airdrop_ids follow spec rules:
        - Between 1 and 10
        - No duplicates
        """
        if not (1 <= len(self._pending_airdrop_ids) <= 10):
            raise ValueError("The number of pending airdrops must be between 1 and 10.")
        if len(set(self._pending_airdrop_ids)) != len(self._pending_airdrop_ids):
            raise ValueError("Duplicate PendingAirdropId entries are not allowed.")

    @property
    def pending_airdrop_ids(self) -> List[PendingAirdropId]:
        """
        Get the list of pending airdrop IDs.

        Returns:
            List[PendingAirdropId]: The list of pending airdrop IDs.
        """
        return self._pending_airdrop_ids

    def add_pending_airdrop_id(self, pending_airdrop_id: PendingAirdropId) -> "AirdropPendingTransaction":
        """
        Add a single pending airdrop ID.

        Args:
            pending_airdrop_id (PendingAirdropId): A pending airdrop identifier to add.

        Returns:
            AirdropPendingTransaction: self (for chaining)
        """
        self._require_not_frozen()
        self._pending_airdrop_ids.append(pending_airdrop_id)
        self._validate_airdrop_ids()
        return self

    def set_pending_airdrop_ids(self, pending_airdrop_ids: List[PendingAirdropId]) -> "AirdropPendingTransaction":
        """
        Replace the list of pending airdrop IDs.

        Args:
            pending_airdrop_ids (List[PendingAirdropId]): The new list of pending airdrop IDs.

        Returns:
            AirdropPendingTransaction: self (for chaining)
        """
        self._require_not_frozen()
        self._pending_airdrop_ids = pending_airdrop_ids
        self._validate_airdrop_ids()
        return self