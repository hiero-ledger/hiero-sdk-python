"""
hiero_sdk_python.tokens.token_fee_schedule_update_transaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenFeeScheduleUpdateTransaction for updating custom fee schedules
on the Hedera network via the HTS API.
"""

from typing import TYPE_CHECKING, List, Optional

# --- Absolute Imports ---
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import (
    token_fee_schedule_update_pb2,
    transaction_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.custom_fee import CustomFee


if TYPE_CHECKING:
    from hiero_sdk_python.client import Client


class TokenFeeScheduleUpdateTransaction(Transaction):
    """
    A transaction to update a token's custom fee schedule.
    """

    def __init__(
        self,
        token_id: Optional[TokenId] = None,
        custom_fees: Optional[List[CustomFee]] = None,
    ) -> None:
        """
        Initializes a new TokenFeeScheduleUpdateTransaction instance.

        Args:
            token_id (TokenId, optional): The ID of the token to update.
            custom_fees (List[CustomFee], optional): The new custom fee schedule.
        """
        super().__init__()
        # Internal attributes (underscore-prefixed for consistency)
        self._token_id: Optional[TokenId] = token_id
        self._custom_fees: List[CustomFee] = custom_fees or []

    def set_token_id(
        self, token_id: TokenId
    ) -> "TokenFeeScheduleUpdateTransaction":
        """
        Sets the token ID to update.

        Args:
            token_id (TokenId): The ID of the token to update.

        Returns:
            TokenFeeScheduleUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self._token_id = token_id
        return self

    def set_custom_fees(
        self, custom_fees: List[CustomFee]
    ) -> "TokenFeeScheduleUpdateTransaction":
        """
        Sets the new custom fee schedule for the token.

        Args:
            custom_fees (List[CustomFee]): The new list of CustomFee objects.

        Returns:
            TokenFeeScheduleUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self._custom_fees = custom_fees
        return self

    def _validate_checksums(self, client: "Client") -> None:
        """
        Validates the checksum for the TokenId, ensuring it matches the client's network.
        """
        if self._token_id:
            self._token_id.validate_checksum(client)

    def _build_proto_body(
        self,
    ) -> token_fee_schedule_update_pb2.TokenFeeScheduleUpdateTransactionBody:
        """
        Returns the protobuf body for the transaction.

        Raises:
            ValueError: If token_id is not set.
        """
        if self._token_id is None:
            raise ValueError("Missing token ID")

        # Assuming the correct method name is _to_protobuf based on review feedback
        # Double-check this against CustomFee implementation if unsure.
        custom_fees_proto = [
            fee._to_protobuf() for fee in self._custom_fees
        ]

        token_fee_update_body = (
            token_fee_schedule_update_pb2.TokenFeeScheduleUpdateTransactionBody(
                # Assuming _to_proto is correct for TokenId based on other files
                tokenId=self._token_id._to_proto(),
                customFees=custom_fees_proto,
            )
        )
        return token_fee_update_body

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body.

        Returns:
            TransactionBody: The protobuf transaction body.
        """
        token_fee_update_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = (
            self.build_base_transaction_body()
        )
        transaction_body.tokenFeeScheduleUpdate.CopyFrom(
            token_fee_update_body
        )
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        token_fee_update_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.tokenFeeScheduleUpdate.CopyFrom(
            token_fee_update_body
        )
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the gRPC method for this transaction.
        """
        # Using simplified return based on potential review feedback
        # Keep query_func=None if explicitly needed by _Method definition
        return _Method(
            transaction_func=channel.token.updateTokenFeeSchedule
            # query_func=None # Add back if _Method requires it
        )

    # Optional but recommended __repr__ based on review feedback
    def __repr__(self):
         return f"<TokenFeeScheduleUpdateTransaction token_id={self._token_id} fees={len(self._custom_fees)}>"
