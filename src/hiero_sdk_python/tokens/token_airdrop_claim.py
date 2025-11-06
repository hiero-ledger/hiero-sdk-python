"""
Defines TokenClaimAirdropTransaction for claiming 1–10 unique pending airdrops
using Hedera's TokenClaimAirdropTransactionBody.

Validations enforced:
- 1 ≤ pending_airdrop_ids ≤ 10
- No duplicate PendingAirdropId entries
"""

from typing import Optional, List, Any

from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.hapi.services.token_claim_airdrop_pb2 import ( # pylint: disable=no-name-in-module
    TokenClaimAirdropTransactionBody,
)
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method


class TokenClaimAirdropTransaction(Transaction):
    """Claim 1–10 unique pending airdrops via TokenClaimAirdropTransactionBody.
    TokenClaimAirdropTransaction is only required if the receiver account has required signing to claim airdrops.
    This transaction MUST be signed by the receiver for each PendingAirdropId to claim.
    """

    MAX_IDS: int = 10
    MIN_IDS: int = 1

    def __init__(
            self,
            pending_airdrop_ids: Optional[List[PendingAirdropId]] = None
    ) -> None:
        """Initialize the TokenClaimAirdropTransaction.

        Args:
            pending_airdrop_ids: Optional list of pending airdrop IDs.
        """
        super().__init__()
        self._pending_airdrop_ids: List[PendingAirdropId] = list(pending_airdrop_ids or [])

    def _validate_all(self, ids: List[PendingAirdropId]) -> None:
        """Validate a candidate list of pending airdrop IDs.

        Ensures the list contains no more than ``MAX_IDS`` entries and has no
        duplicates.

        Args:
            ids: Pending-airdrop IDs to validate.

        Raises:
            ValueError: If more than ``MAX_IDS`` IDs are provided or duplicates
                are detected.
        """
        n = len(ids)
        if n > self.MAX_IDS:
            raise ValueError(f"Up to {self.MAX_IDS} airdrops can be claimed at once (got {n}).")
        # Don't enforce MIN here—only enforce at build/serialize time
        if len(set(ids)) != n:
            raise ValueError("Duplicate airdrop IDs are not allowed.")

    def _validate_final(self) -> None:
        """Validate the transaction's final pending-airdrop ID list.

        Checks that at least ``MIN_IDS`` IDs are present, and re-runs the global
        validations (max count and no duplicates).

        Raises:
            ValueError: If fewer than ``MIN_IDS`` IDs are present or if the
                subsequent global validations fail.
        """
        # Called right before build/serialize as pending airdrops are currenly optional
        n = len(self._pending_airdrop_ids)
        if n < self.MIN_IDS:
            raise ValueError(f"You must claim at least {self.MIN_IDS} airdrop (got {n}).")
        self._validate_all(self._pending_airdrop_ids)

    def add_pending_airdrop_id(
            self,
            pending_airdrop_id: PendingAirdropId
        ) -> "TokenClaimAirdropTransaction":
        """Append a single PendingAirdropId.

        Args:
            pending_airdrop_id: The pending airdrop ID to add.

        Returns:
            TokenClaimAirdropTransaction: self (for chaining).
        """
        return self.add_pending_airdrop_ids([pending_airdrop_id])

    def add_pending_airdrop_ids(
            self,
            pending_airdrop_ids: List[PendingAirdropId]
        ) -> "TokenClaimAirdropTransaction":
        """Add many pending airdrop IDs.

        Args:
            pending_airdrop_ids: Additional list of pending airdrop IDs.

        Returns:
            TokenClaimAirdropTransaction: self (for chaining).

        Raises:
            ValueError: If the resulting list exceeds ``MAX_IDS`` or contains duplicates.
        """
        self._require_not_frozen()
        candidate = self._pending_airdrop_ids + list(pending_airdrop_ids)  # extend list
        self._validate_all(candidate)  # enforce MAX and no dups
        self._pending_airdrop_ids = candidate
        return self

    def _pending_airdrop_ids_to_proto(self) -> List[Any]:
        """Convert the current list of PendingAirdropId to protobuf messages.

        Returns:
            List[Any]: The protobuf representations of the pending airdrop IDs.
        """
        return [
            airdrop._to_proto()  # type: ignore[reportPrivateUsage]  # pylint: disable=protected-access
            for airdrop in self._pending_airdrop_ids
        ]

    @classmethod
    def _from_proto(
        cls,
        proto: TokenClaimAirdropTransactionBody
    ) -> "TokenClaimAirdropTransaction":
        """Construct a TokenClaimAirdropTransaction from a TokenClaimAirdropTransactionBody.

        Args:
            proto: The protobuf message to read from.

        Returns:
            TokenClaimAirdropTransaction: A new transaction instance loaded from the protobuf.

        Raises:
            ValueError: If the decoded IDs violate validation rules.
        """
        pending_airdrops = [
            PendingAirdropId._from_proto(airdrop)  # type: ignore[reportPrivateUsage]  # pylint: disable=protected-access
            for airdrop in proto.pending_airdrops
        ]
        inst = cls(pending_airdrop_ids=pending_airdrops)
        inst._validate_all(inst._pending_airdrop_ids)  # enforce max and no duplicates immediately

        return inst

    def build_transaction_body(self) -> transaction_pb2.TransactionBody: # pylint: disable=no-member
        """Build the TransactionBody for this claim.

        Returns:
            transaction_body_pb2.TransactionBody: 
                A TransactionBody with TokenClaimAirdrop populated.

        Raises:
            ValueError: If validation fails.
        """
        self._validate_final()

        pending_airdrop_claim_body = TokenClaimAirdropTransactionBody(
            pending_airdrops=self._pending_airdrop_ids_to_proto()
        )
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body() # pylint: disable=no-member
        transaction_body.tokenClaimAirdrop.CopyFrom(pending_airdrop_claim_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the gRPC method used to claim pending token airdrops.

        Args:
            channel: The channel with service stubs.

        Returns:
            _Method: Wraps the gRPC method for TokenClaimAirdrop.
        """
        return _Method(
            transaction_func=channel.token.claimAirdrop,
            query_func=None
        )

    def get_pending_airdrop_ids(self) -> List[PendingAirdropId]:
        """Returns a copy of the list of pending airdrop IDs currently stored inside TokenClaimAirdropTransaction object"""
        return list(self._pending_airdrop_ids)

    def __repr__(self) -> str:
        """Developer-friendly representation with class name and pending IDs."""
        return (
            f"{self.__class__.__name__}("
            f"pending_airdrop_ids={self._pending_airdrop_ids!r})"
        )

    def __str__(self) -> str:
        """Human-readable summary showing each pending airdrop on its own line"""
        if not self._pending_airdrop_ids:
            return "No pending airdrops in this transaction."

        lines = [
            f"   → {aid}"
            for aid in self._pending_airdrop_ids
        ]

        ids_block = "\n".join(lines)
        summary = (
            f"Pending Airdrops to claim:\n"
            f"{ids_block}\n"
        )
        return summary