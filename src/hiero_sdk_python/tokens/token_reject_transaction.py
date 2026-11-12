"""
hiero_sdk_python.tokens.token_reject_transaction.py.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenRejectTransaction for rejecting fungible token and NFT transfers on
the Hedera network via the Hedera Token Service (HTS) API.
"""

from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.token_reject_pb2 import (
    TokenReference,
    TokenRejectTransactionBody,
)
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction


class TokenRejectTransaction(Transaction):
    """
    Represents a token reject transaction on the Hedera network.

    This transaction rejects a token transfer.
    Allows users to reject and return unwanted airdrops
    to the treasury account without incurring custom fees.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token reject transaction.
    """

    def __init__(
        self,
        owner_id: AccountId | None = None,
        token_ids: list[TokenId] | None = None,
        nft_ids: list[NftId] | None = None,
    ) -> None:
        """
        TokenRejectTransaction instance with optional owner_id, token_ids, and nft_ids.

        Args:
            owner_id (AccountId, optional): The ID of the account to reject the token transfer.
            token_ids (list[TokenId], optional): The IDs of the fungible tokens to reject.
            nft_ids (list[NftId], optional): The IDs of the non-fungible tokens (NFTs) to reject.
        """
        super().__init__()
        self.owner_id: AccountId | None = owner_id
        self.token_ids: list[TokenId] = list(token_ids) if token_ids else []
        self.nft_ids: list[NftId] = list(nft_ids) if nft_ids else []
        self._rejection_order: list[tuple[str, TokenId | NftId]] = [
            *(("token", token_id) for token_id in self.token_ids),
            *(("nft", nft_id) for nft_id in self.nft_ids),
        ]

    def set_owner_id(self, owner_id: AccountId) -> TokenRejectTransaction:
        """Set the owner account ID for rejected tokens."""
        self._require_not_frozen()
        self.owner_id = owner_id
        return self

    def set_token_ids(self, token_ids: list[TokenId]) -> TokenRejectTransaction:
        """Set the list of fungible token IDs to reject."""
        self._require_not_frozen()
        self.token_ids = list(token_ids)
        self._rejection_order = [
            *(("token", token_id) for token_id in self.token_ids),
            *(entry for entry in self._rejection_order if entry[0] == "nft"),
        ]
        return self

    def add_token_id(self, token_id: TokenId) -> TokenRejectTransaction:
        """
        Appends a fungible token ID to the list of tokens to reject.

        Args:
            token_id (TokenId): The fungible token ID to add.

        Returns:
            TokenRejectTransaction: This transaction instance (for chaining).

        Raises:
            TypeError: If token_id is not a TokenId instance.
        """
        self._require_not_frozen()
        if not isinstance(token_id, TokenId):
            raise TypeError("token_id must be a TokenId instance.")
        self.token_ids.append(token_id)
        self._rejection_order.append(("token", token_id))
        return self

    def set_nft_ids(self, nft_ids: list[NftId]) -> TokenRejectTransaction:
        """Set the list of NFT IDs to reject."""
        self._require_not_frozen()
        self.nft_ids = list(nft_ids)
        self._rejection_order = [
            *(entry for entry in self._rejection_order if entry[0] == "token"),
            *(("nft", nft_id) for nft_id in self.nft_ids),
        ]
        return self

    def add_nft_id(self, nft_id: NftId) -> TokenRejectTransaction:
        """
        Appends an NFT ID to the list of NFTs to reject.

        Args:
            nft_id (NftId): The NFT ID to add.

        Returns:
            TokenRejectTransaction: This transaction instance (for chaining).

        Raises:
            TypeError: If nft_id is not a NftId instance.
        """
        self._require_not_frozen()
        if not isinstance(nft_id, NftId):
            raise TypeError("nft_id must be a NftId instance.")
        self.nft_ids.append(nft_id)
        self._rejection_order.append(("nft", nft_id))
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the token reject transaction.

        Returns:
            TokenRejectTransactionBody: The protobuf body for this transaction.
        """
        ordered_tokens = [item for kind, item in self._rejection_order if kind == "token" and isinstance(item, TokenId)]
        ordered_nfts = [item for kind, item in self._rejection_order if kind == "nft" and isinstance(item, NftId)]

        if ordered_tokens == self.token_ids and ordered_nfts == self.nft_ids:
            token_references: list[TokenReference] = [
                TokenReference(fungible_token=item._to_proto())
                if kind == "token" and isinstance(item, TokenId)
                else TokenReference(nft=item._to_proto())
                for kind, item in self._rejection_order
            ]
        else:
            token_references = [TokenReference(fungible_token=token_id._to_proto()) for token_id in self.token_ids]
            token_references.extend(TokenReference(nft=nft_id._to_proto()) for nft_id in self.nft_ids)

        return TokenRejectTransactionBody(
            owner=self.owner_id and self.owner_id._to_proto(), rejections=token_references
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for token reject.

        Returns:
            TransactionBody: The protobuf transaction body containing the token reject details.
        """
        token_reject_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenReject.CopyFrom(token_reject_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this token reject transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_reject_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenReject.CopyFrom(token_reject_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the token reject transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to reject tokens.
        """
        return _Method(transaction_func=channel.token.rejectToken, query_func=None)

    @classmethod
    def _from_proto(cls, proto: TokenRejectTransactionBody) -> TokenRejectTransaction:
        """
        Deserializes a TokenRejectTransactionBody from a protobuf object.

        Args:
            proto (TokenRejectTransactionBody): The protobuf object to deserialize.

        Returns:
            TokenRejectTransaction: A new transaction instance with fields restored.
        """
        owner_id = AccountId._from_proto(proto.owner) if proto.HasField("owner") else None

        token_ids: list[TokenId] = []
        nft_ids: list[NftId] = []
        rejection_order: list[tuple[str, TokenId | NftId]] = []

        for entry in proto.rejections:
            if entry.HasField("fungible_token"):
                token_id = TokenId._from_proto(entry.fungible_token)
                token_ids.append(token_id)
                rejection_order.append(("token", token_id))
            elif entry.HasField("nft"):
                nft_id = NftId._from_proto(entry.nft)
                nft_ids.append(nft_id)
                rejection_order.append(("nft", nft_id))

        tx = cls(owner_id=owner_id, token_ids=token_ids, nft_ids=nft_ids)
        tx._rejection_order = rejection_order
        return tx

    @classmethod
    def _from_protobuf(cls, transaction_body: transaction_pb2.TransactionBody) -> TokenRejectTransaction:
        """
        Creates a TokenRejectTransaction instance from protobuf components.

        Args:
            transaction_body (TransactionBody): The parsed TransactionBody protobuf.

        Returns:
            TokenRejectTransaction: A new transaction instance with all fields restored.
        """
        transaction = super()._from_protobuf(transaction_body)

        if transaction_body.HasField("tokenReject"):
            token_reject_body = transaction_body.tokenReject
            proto_tx = cls._from_proto(token_reject_body)
            transaction.owner_id = proto_tx.owner_id
            transaction.token_ids = proto_tx.token_ids
            transaction.nft_ids = proto_tx.nft_ids
            transaction._rejection_order = proto_tx._rejection_order

        return transaction
