"""
Defines AirdropPendingTransaction for claiming 1–10 unique pending airdrops
using Hedera's TokenClaimAirdropTransactionBody.
"""
from typing import Optional, List, Any

from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.hapi.services.token_claim_airdrop_pb2 import TokenClaimAirdropTransactionBody
from hiero_sdk_python.hapi.services import transaction_body_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TokenClaimAirdropTransaction(Transaction):
   """
   Represents a PendingAirdropId transaction.
   """
   MAX_IDS: int = 10
   MIN_IDS: int = 1

   def __init__(
       self,
       pending_airdrop_ids: Optional[List[PendingAirdropId]] = None,
   ) -> None:
       """
       Initialize the AirdropPendingTransaction.

       Args:
           pending_airdrop_ids (Optional[List[PendingAirdropId]]):
           Optional list of pending airdrop IDs.
       """
       super().__init__()
       self._pending_airdrop_ids: List[PendingAirdropId] = list(pending_airdrop_ids or [])

   def _validate_all(self, ids: List[PendingAirdropId]) -> None:
       """
       Validates that pending_airdrop_ids:
       - No more than 10
       - No duplicates
       """
       n = len(ids)
       if n > self.MAX_IDS:
           raise ValueError(f"Up to {self.MAX_IDS} airdrops can be claimed at once (got {n}).")
       # Don't enforce MIN here—only enforce at build/serialize time
       if len(set(ids)) != n:
           raise ValueError("Duplicate airdrop IDs are not allowed.")

   def _validate_final(self) -> None:
       """
       Validates that pending_airdrop_ids:
       - No fewer than 1
       """
       # Called right before build/serialize
       n = len(self._pending_airdrop_ids)
       if n < self.MIN_IDS:
           raise ValueError(f"You must claim at least {self.MIN_IDS} airdrop (got {n}).")
       self._validate_all(self._pending_airdrop_ids)

   def add_pending_airdrop_ids(
           self,
           pending_airdrop_ids: List[PendingAirdropId]
   ) -> "TokenClaimAirdropTransaction":
       """
       Add to the list of pending airdrop IDs.

       Args:
           pending_airdrop_ids (List[PendingAirdropId]):
           The additional list of pending airdrop IDs.

       Returns:
           AirdropPendingTransaction: self (for chaining)
       """
       self._require_not_frozen()
       candidate = self._pending_airdrop_ids + list(pending_airdrop_ids) #Extend list
       self._validate_all(candidate)  # enforce MAX and no dups
       self._pending_airdrop_ids = candidate
       return self

   @property
   def pending_airdrop_ids(self) -> List[PendingAirdropId]:
       """
       Get the list of pending airdrop IDs.

       Returns:
           List[PendingAirdropId]: The list of pending airdrop IDs.
       """
       return list(self._pending_airdrop_ids)

   def _pending_airdrop_ids_to_proto(self) -> List[Any]:
       """
       Convert the current list of pending airdrop ids to its protobuf representation.

       Returns:
           Protobuf list of pending airdrop ids
       """
       return [
           airdrop._to_proto()  # type: ignore[reportPrivateUsage]
           for airdrop in self._pending_airdrop_ids
       ]

   def _from_proto(
           self,
           proto: TokenClaimAirdropTransactionBody
   ) -> "TokenClaimAirdropTransaction":
       """
       Populate a TokenClaimAirdropTransaction from a protobuf message.

       Args:
           proto (TokenClaimAirdropTransactionBody): The protobuf message to read from.

       Returns:
           TokenClaimAirdropTransaction:
           This transaction instance with data loaded from the protobuf.
       """
       pending_airdrops = [
           PendingAirdropId._from_proto(airdrop) # type: ignore[reportPrivateUsage]
           for airdrop in proto.pending_airdrops
       ]
       self._pending_airdrop_ids = pending_airdrops
       self._validate_all(self._pending_airdrop_ids)
       return self

   def build_transaction_body(self) -> transaction_body_pb2.TransactionBody :
       self._validate_final()

       pending_airdrop_claim_body = TokenClaimAirdropTransactionBody(
           pending_airdrops=self._pending_airdrop_ids_to_proto()
       )
       transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
       transaction_body.tokenClaimAirdrop.CopyFrom(pending_airdrop_claim_body)
       return transaction_body

   def _get_method(self, channel: _Channel) -> _Method:
       """
       Returns the gRPC method used to claim pending token airdrops.

       Args:
           channel (_Channel): The channel with service stubs.

       Returns:
           _Method: Wraps the gRPC method for TokenClaimAirdrop.
       """
       return _Method(
           transaction_func=channel.token.claimAirdrop,
           query_func=None
       )

   def __repr__(self) -> str:
       """Developer-friendly representation with class name and pending IDs."""
       return (
           f"{self.__class__.__name__}("
           f"pending_airdrop_ids={self._pending_airdrop_ids!r})"
       )

   def __str__(self) -> str:
       """Human-readable summary with count and list of pending IDs."""
       ids = ", ".join(str(aid) for aid in self._pending_airdrop_ids)
       return f"TokenClaimAirdropTransaction with {len(self._pending_airdrop_ids)} ID(s): {ids}"
