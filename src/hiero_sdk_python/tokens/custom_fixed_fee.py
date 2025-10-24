from __future__ import annotations
import typing
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.hbar import Hbar

if typing.TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client
    from hiero_sdk_python.hapi.services import custom_fees_pb2

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services import custom_fees_pb2

"""Manages custom fixed fees assessed during transactions on the Hedera network.

This module defines the CustomFixedFee class, allowing fees to be specified
in HBAR or a specific fungible token. It provides methods for setting fee
amounts, denominating tokens, and converting to/from protobuf formats.
"""

class CustomFixedFee(CustomFee):
    """Represents a fixed fee assessed as part of a custom fee schedule.

    The fee can be denominated in HBAR or in a specific fungible token ID.
    If denominated in a token, it must typically be a token other than the
    one the custom fee is attached to, unless set to the special 0.0.0 ID.

    Inherits common properties like fee_collector_account_id from CustomFee.

    Attributes:
        amount (int): The fixed amount of the fee in the smallest denomination
            (tinybars if HBAR, or the smallest unit if a token).
        denominating_token_id (typing.Optional[TokenId]): The ID of the token
            used to pay the fee. If None, the fee is paid in HBAR. A special
            value of 0.0.0 indicates the fee is paid in the same token the
            custom fee is attached to.
    """

    def __init__(
        self,
        amount: int = 0,
        denominating_token_id: typing.Optional["TokenId"] = None,
        fee_collector_account_id: typing.Optional["AccountId"] = None,
        all_collectors_are_exempt: bool = False,
    ):
        """Initializes the CustomFixedFee.

        Args:
            amount (int): The fixed fee amount. If the fee is in HBAR, this is
                in tinybars. If the fee is in a token, this is in the token's
                smallest denomination. Defaults to 0.
            denominating_token_id (typing.Optional[TokenId]): The token ID to
                denominate the fee in. If None, the fee is denominated in HBAR.
                Defaults to None.
            fee_collector_account_id (typing.Optional[AccountId]): The account ID
                of the fee collector. Inherited from CustomFee. Defaults to None.
            all_collectors_are_exempt (bool): If true, all collectors for this
                fee are exempt from custom fees. Inherited from CustomFee.
                Defaults to False.
        """
        super().__init__(fee_collector_account_id, all_collectors_are_exempt)
        self.amount = amount
        self.denominating_token_id = denominating_token_id

    def set_amount_in_tinybars(self, amount: int) -> "CustomFixedFee":
        """Sets the fee amount in tinybars.

        Clears any previously set denominating token ID, implying the fee is in HBAR.

        Args:
            amount (int): The fee amount in tinybars. Must be non-negative.

        Returns:
            CustomFixedFee: This CustomFixedFee instance for chaining.
        """
        self.amount = amount
        return self

    def set_hbar_amount(self, amount: Hbar) -> "CustomFixedFee":
        """Sets the fee amount using an Hbar object.

        Converts the Hbar amount to tinybars and clears any previously set
        denominating token ID.

        Args:
            amount (Hbar): The fee amount as an Hbar object.

        Returns:
            CustomFixedFee: This CustomFixedFee instance for chaining.
        """
        self.denominating_token_id = None
        self.amount = amount.to_tinybars()
        return self

    def set_denominating_token_id(self, token_id: typing.Optional["TokenId"]) -> "CustomFixedFee":
        """Sets the fungible token used to pay the fee.

        If set to None, the fee defaults to being paid in HBAR.

        Args:
            token_id (typing.Optional[TokenId]): The ID of the token to use for
                assessing the fee, or None for HBAR.

        Returns:
            CustomFixedFee: This CustomFixedFee instance for chaining.
        """
        self.denominating_token_id = token_id
        return self
    
    def set_denominating_token_to_same_token(self) -> "CustomFixedFee":
        """Configures the fee to be paid in the same token the custom fee is attached to.

        This sets the denominating_token_id to the sentinel value 0.0.0.

        Returns:
            CustomFixedFee: This CustomFixedFee instance for chaining.
        """
        from hiero_sdk_python.tokens.token_id import TokenId
        self.denominating_token_id = TokenId(0, 0, 0)
        return self

    @staticmethod
    def _from_fixed_fee_proto(fixed_fee: "custom_fees_pb2.FixedFee") -> "CustomFixedFee":
        """Creates a CustomFixedFee instance from a FixedFee protobuf object.

        Internal helper method.

        Args:
            fixed_fee (custom_fees_pb2.FixedFee): The protobuf FixedFee object.

        Returns:
            CustomFixedFee: The corresponding CustomFixedFee object.
        """
        from hiero_sdk_python.tokens.token_id import TokenId
        fee = CustomFixedFee()
        fee.amount = fixed_fee.amount
        if fixed_fee.HasField("denominating_token_id"):
            fee.denominating_token_id = TokenId._from_proto(
                fixed_fee.denominating_token_id
            )
        return fee

    def _to_proto(self) -> "custom_fees_pb2.CustomFee":
        """Converts this CustomFixedFee object to its protobuf representation.

        Builds the `FixedFee` part and integrates it with the common fields
        from the `CustomFee` parent class into a `CustomFee` protobuf message.

        Returns:
            custom_fees_pb2.CustomFee: The protobuf CustomFee message.

        Raises:
            ValueError: If the fee amount is negative (or validation fails).
                (Note: Current implementation doesn't explicitly check amount >= 0).
        """
        from hiero_sdk_python.hapi.services import custom_fees_pb2

        fixed = custom_fees_pb2.FixedFee()
        fixed.amount = self.amount

        if self.denominating_token_id is not None:
            fixed.denominating_token_id.CopyFrom(self.denominating_token_id._to_proto())

        cf = custom_fees_pb2.CustomFee()
        cf.fixed_fee.CopyFrom(fixed)

        collector = self._get_fee_collector_account_id_protobuf()
        if collector is not None:
            cf.fee_collector_account_id.CopyFrom(collector)

        cf.all_collectors_are_exempt = self.all_collectors_are_exempt
        return cf

    def _to_topic_fee_proto(self) -> "custom_fees_pb2.FixedCustomFee":
        """Converts this CustomFixedFee object to a FixedCustomFee protobuf object.

        Specifically used for fee schedules related to Hedera Consensus Service topics.

        Returns:
            custom_fees_pb2.FixedCustomFee: The protobuf FixedCustomFee message.

        Raises:
            ValueError: If the fee amount is negative or potentially if IDs are invalid.
                 (Note: Current implementation doesn't explicitly check amount >= 0).
        """
        from hiero_sdk_python.hapi.services import custom_fees_pb2
        
        return custom_fees_pb2.FixedCustomFee(
            fixed_fee=custom_fees_pb2.FixedFee(
                amount=self.amount,
                denominating_token_id=self.denominating_token_id._to_proto()
                if self.denominating_token_id is not None
                else None,
            ),
            fee_collector_account_id=self._get_fee_collector_account_id_protobuf(),
        )

    def _validate_checksums(self, client: "Client") -> None:
        """Validates checksums for configured account and token IDs.

        Ensures that the fee collector account ID and the denominating token ID
        (if set) have valid checksums against the provided client's network.

        Args:
            client (Client): The client instance representing the target network.

        Raises:
            HederaPreCheckStatusError: If any checksum validation fails.
        """
        super()._validate_checksums(client)
        if self.denominating_token_id is not None:
            self.denominating_token_id.validate_checksum(client)

    @classmethod
    def _from_proto(cls, proto_fee: custom_fees_pb2.CustomFee) -> "CustomFixedFee":
        """Creates a CustomFixedFee instance from a CustomFee protobuf object.

        Extracts the fixed fee details and common fee properties from the
        protobuf message.

        Args:
            proto_fee (custom_fees_pb2.CustomFee): The protobuf CustomFee message.
                It is expected that the `fixed_fee` field is set.

        Returns:
            CustomFixedFee: The corresponding CustomFixedFee object.

        Raises:
            ValueError: If the `fixed_fee` field is not set in the protobuf message.
        """
        
        fixed_fee_proto = proto_fee.fixed_fee
        
        denominating_token_id = None
        if fixed_fee_proto.HasField("denominating_token_id"):
            denominating_token_id = TokenId._from_proto(fixed_fee_proto.denominating_token_id)
        
        fee_collector_account_id = None
        if proto_fee.HasField("fee_collector_account_id"):
            fee_collector_account_id = AccountId._from_proto(proto_fee.fee_collector_account_id)
        
        collectors_are_exempt = getattr(proto_fee, 'all_collectors_are_exempt', False)
        
        return cls(
            amount=fixed_fee_proto.amount,
            denominating_token_id=denominating_token_id,
            fee_collector_account_id=fee_collector_account_id,
            all_collectors_are_exempt=collectors_are_exempt
        )
        
    def __eq__(self, other: "CustomFixedFee") -> bool:
        """Compares this CustomFixedFee instance with another object for equality.

        Checks if the other object is also a CustomFixedFee and if all
        relevant fields (amount, denominating token ID, fee collector ID,
        and exemption status) are identical.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are considered equal, False otherwise.
        """
        return super().__eq__(other) and self.amount == other.amount and self.denominating_token_id == other.denominating_token_id