"""
Module for updating token fee schedules.
"""

from typing import List, Optional
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_fee_schedule_update_pb2
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.hbar import Hbar


class TokenFeeScheduleUpdateTransaction(Transaction):
    """
    Update the custom fees for a given token. If the token does not have a
    fee schedule, the network response returned will be
    CUSTOM_SCHEDULE_ALREADY_HAS_NO_FEES. The user must sign the transaction
    with the fee schedule key to update the fee schedule for the token. If the user
    does not have a fee schedule key set for the token, they will not be able to
    update the fee schedule.
    """

    def __init__(
        self,
        token_id: Optional[TokenId] = None,
        custom_fees: Optional[List[CustomFee]] = None,
    ):
        """
        Initialize a TokenFeeScheduleUpdateTransaction.

        Args:
            token_id: The token ID to update the fee schedule for
            custom_fees: List of custom fees to set for the token
        """
        super().__init__()
        
        self._token_id: Optional[TokenId] = token_id
        self._custom_fees: List[CustomFee] = custom_fees if custom_fees is not None else []

        # Set default transaction fee to 2 HBAR for token fee schedule update transactions
        self._default_transaction_fee = Hbar(2).to_tinybars()

    def get_token_id(self) -> Optional[TokenId]:
        """Get the token ID."""
        return self._token_id

    def set_token_id(self, token_id: TokenId) -> "TokenFeeScheduleUpdateTransaction":
        """
        Set the token ID.
        
        A token identifier.
        This shall identify the token type to modify with an updated
        custom fee schedule. The identified token MUST exist, and MUST NOT be deleted.

        Args:
            token_id: The token ID to update the fee schedule for

        Returns:
            This transaction object for method chaining
        """
        self._require_not_frozen()
        self._token_id = token_id
        return self

    def get_custom_fees(self) -> List[CustomFee]:
        """Get the list of custom fees."""
        return self._custom_fees.copy()

    def set_custom_fees(self, custom_fees: List[CustomFee]) -> "TokenFeeScheduleUpdateTransaction":
        """
        Set the custom fees.
        
        A list of custom fees representing a fee schedule.
        This list may be empty to remove custom fees from a token.
        If the identified token is a non-fungible/unique type, the entries
        in this list MUST NOT declare a `fractional_fee`.
        If the identified token is a fungible/common type, the entries in this
        list MUST NOT declare a `royalty_fee`.
        Any token type may include entries that declare a `fixed_fee`.

        Args:
            custom_fees: List of custom fees to set for the token

        Returns:
            This transaction object for method chaining
        """
        self._require_not_frozen()
        self._custom_fees = custom_fees if custom_fees is not None else []
        return self

    def build_transaction_body(self):
        """Build the transaction body for the token fee schedule update."""
        if self._token_id is None:
            raise ValueError("Token ID is required for TokenFeeScheduleUpdateTransaction")

        token_fee_schedule_update_body = token_fee_schedule_update_pb2.TokenFeeScheduleUpdateTransactionBody(
            token_id=self._token_id._to_proto(),
            custom_fees=[fee._to_proto() for fee in self._custom_fees],
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.token_fee_schedule_update.CopyFrom(token_fee_schedule_update_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """Get the gRPC method for token fee schedule update."""
        return channel.token.updateTokenFeeSchedule

    def _validate_checksums(self, client):
        """Validate checksums for all account and token IDs."""
        if self._token_id is not None:
            self._token_id.validate_checksum(client)
        
        for fee in self._custom_fees:
            fee._validate_checksums(client)