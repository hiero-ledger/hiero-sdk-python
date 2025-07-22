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
        return self


# Transaction: allows intended airdrop recipient to manually claim a pending token transfer by triggering:
# TokenAssociate
# CryptoTransfer

# Airdrop → Claim → token transfers recorded in token_transfer_list in the transaction record → Removed from network state and cannot be claimed again

# Requirements:
# Once claimed: transfer is irreversible and removed from network state
# All pending airdrops must succeed for the transaction to complete


# Fees charged:
# Receiver = transaction fee
# Sender = association + custom fees

# User Receives PendingAirdropId.

# User Builds TokenClaimAirdropTransaction with the list.

# Transaction Body is serialized and signed.

# Send via channel.token.claimAirdrop() method.

# Check response for success.

# from proto_module import TokenClaimAirdropTransactionBody, TransactionBody

# class TokenClaimAirdropTransaction:
#     def __init__(self, pending_airdrop_ids: list[PendingAirdropId]):
#         if not 1 <= len(pending_airdrop_ids) <= 10:
#             raise ValueError("Must include 1 to 10 pending airdrop IDs")
#         self.pending_airdrop_ids = pending_airdrop_ids

#     def to_protobuf(self):
#         return TokenClaimAirdropTransactionBody(
#             pending_airdrops=[aid.to_bytes() for aid in self.pending_airdrop_ids]
#         )

#     def build_transaction_body(self) -> TransactionBody:
#         return TransactionBody(
#             tokenClaimAirdrop=self.to_protobuf()
#         )

#     async def execute(self, channel):  # Channel = gRPC stub
#         tx_body = self.build_transaction_body()
#  ...
