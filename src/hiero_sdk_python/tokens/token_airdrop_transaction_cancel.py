from __future__ import annotations

from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import basic_types_pb2, token_cancel_airdrop_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.transaction.transaction import Transaction


class TokenCancelAirdropTransaction(Transaction):
    """
    Represents a transaction to cancel token airdrops on the Hedera network.

    This transaction allows users to cancel one or more airdrops for both fungible tokens and NFTs.
    """

    def __init__(self, pending_airdrops: list[PendingAirdropId] | None = None) -> None:
        """
        Initializes a new TokenCancelAirdropTransaction instance.

        Args:
            pending_airdrops (list[PendingAirdropId], optional): An optional list of pending airdrop IDs.
        """
        super().__init__()
        self.pending_airdrops: list[PendingAirdropId] = pending_airdrops or []

    def set_pending_airdrops(self, pending_airdrops: list[PendingAirdropId]) -> TokenCancelAirdropTransaction:
        """
        Sets the list of pending airdrops IDs.

        Args:
            pending_airdrops (list[PendingAirdropId]): The list of pending airdrop IDs to cancel.

        Returns:
            TokenCancelAirdropTransaction: The current instance of the transaction for chaining.
        """
        self.pending_airdrops = pending_airdrops
        return self

    def add_pending_airdrop(self, pending_airdrop: PendingAirdropId) -> TokenCancelAirdropTransaction:
        """
        Adds a single pending airdrop ID to the pending_airdrops list.

        Args:
            pending_airdrop (PendingAirdropId): The pending airdrop ID to add.

        Returns:
            TokenCancelAirdropTransaction: The current instance of the transaction for chaining.
        """
        self.pending_airdrops.append(pending_airdrop)
        return self

    def clear_pending_airdrops(self) -> TokenCancelAirdropTransaction:
        """
        Clears all pending airdrop IDs from the list.

        Returns:
            TokenCancelAirdropTransaction: The current instance of the transaction for chaining.
        """
        self.pending_airdrops.clear()
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the token cancel airdrop transaction.

        Returns:
            TokenCancelAirdropTransactionBody: The protobuf body for this transaction.
        """
        pending_airdrops_proto: list[basic_types_pb2.PendingAirdropId] = [
            pending_airdrop._to_proto() for pending_airdrop in self.pending_airdrops
        ]

        return token_cancel_airdrop_pb2.TokenCancelAirdropTransactionBody(pending_airdrops=pending_airdrops_proto)

    @classmethod
    def _from_proto(
        cls, proto: token_cancel_airdrop_pb2.TokenCancelAirdropTransactionBody
    ) -> TokenCancelAirdropTransaction:
        """
        Construct a TokenCancelAirdropTransaction from a TokenCancelAirdropTransactionBody.

        Args:
            proto: The protobuf message to read from.

        Returns:
            TokenCancelAirdropTransaction: A new transaction instance loaded from the protobuf.
        """
        pending_airdrops = [PendingAirdropId._from_proto(pending_airdrop) for pending_airdrop in proto.pending_airdrops]
        return cls(pending_airdrops=pending_airdrops)

    @classmethod
    def _from_protobuf(
        cls,
        transaction_body: transaction_pb2.TransactionBody,
        body_bytes: bytes | None = None,
        sig_map=None,
    ) -> TokenCancelAirdropTransaction:
        """
        Creates a TokenCancelAirdropTransaction instance from protobuf components.

        Args:
            transaction_body (TransactionBody): The parsed TransactionBody protobuf.
            body_bytes (bytes, optional): The raw bytes of the transaction body.
            sig_map (SignatureMap, optional): The SignatureMap protobuf containing signatures.

        Returns:
            TokenCancelAirdropTransaction: A new transaction instance with all fields restored.
        """
        try:
            transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)
        except TypeError:
            transaction = super()._from_protobuf(transaction_body)

        if transaction_body.HasField("tokenCancelAirdrop"):
            token_cancel_airdrop_body = transaction_body.tokenCancelAirdrop
            proto_tx = cls._from_proto(token_cancel_airdrop_body)
            transaction.pending_airdrops = proto_tx.pending_airdrops

        return transaction

    def build_transaction_body(self):
        """Builds and returns the protobuf transaction body for canceling a token airdrop."""
        token_airdrop_cancel_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenCancelAirdrop.CopyFrom(token_airdrop_cancel_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token cancel airdrop transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_airdrop_cancel_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenCancelAirdrop.CopyFrom(token_airdrop_cancel_body)
        return schedulable_body

    def _get_method(self, channel):
        return _Method(transaction_func=channel.token.cancelAirdrop, query_func=None)
