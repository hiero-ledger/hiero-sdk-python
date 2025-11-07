"""
Defines TokenFeeScheduleUpdateTransaction for updating custom fee schedules
"""

from typing import TYPE_CHECKING, List, Optional

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
    """Updates a token's custom fee schedule."""

    def __init__(
        self,
        token_id: Optional[TokenId] = None,
        custom_fees: Optional[List[CustomFee]] = None,
    ) -> None:
        """
        Initializes a new TokenFeeScheduleUpdateTransaction instance.
        Sets a default transaction fee.
        """
        super().__init__()
        self._default_transaction_fee: int = 100_000_000 # 1 Hbar in tinybars
        self.token_id: Optional[TokenId] = token_id
        self.custom_fees: List[CustomFee] = custom_fees or []

    def set_token_id(
        self, token_id: TokenId
    ) -> "TokenFeeScheduleUpdateTransaction":
        """Sets the token ID to update."""
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def set_custom_fees(
        self, custom_fees: List[CustomFee]
    ) -> "TokenFeeScheduleUpdateTransaction":
        """Sets the new custom fee schedule for the token."""
        self._require_not_frozen()
        self.custom_fees = custom_fees
        return self

    def _validate_checksums(self, client: "Client") -> None:
        """Validates checksums for token ID and account IDs within custom fees."""
        if self.token_id:
            self.token_id.validate_checksum(client)
        for fee in self.custom_fees:
            fee._validate_checksums(client)

    def _build_proto_body(
        self,
    ) -> token_fee_schedule_update_pb2.TokenFeeScheduleUpdateTransactionBody:
        """Builds the protobuf body for the transaction."""
        if self.token_id is None:
            raise ValueError("Missing token ID")

        custom_fees_proto = [fee._to_proto() for fee in self.custom_fees]

        return token_fee_schedule_update_pb2.TokenFeeScheduleUpdateTransactionBody(
            token_id=self.token_id._to_proto(),
            custom_fees=custom_fees_proto,
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """Builds and returns the protobuf transaction body."""
        token_fee_update_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = (
            self.build_base_transaction_body()
        )
        transaction_body.token_fee_schedule_update.CopyFrom(token_fee_update_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """Builds the scheduled transaction body."""
        token_fee_update_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.token_fee_schedule_update.CopyFrom(token_fee_update_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """Gets the gRPC method for this transaction."""
        return _Method(transaction_func=channel.token.updateTokenFeeSchedule)

    def __repr__(self):
        """Readable representation for debugging."""
        return f"<TokenFeeScheduleUpdateTransaction token_id={self.token_id} fees={len(self.custom_fees)}>"
