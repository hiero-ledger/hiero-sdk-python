from __future__ import annotations
import typing
from hiero_sdk_python.tokens.custom_fee import CustomFee

if typing.TYPE_CHECKING:
    from hiero_sdk_python.account.account_id import AccountId
    from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
    from hiero_sdk_python.hapi.services import custom_fees_pb2

"""Manages custom royalty fees for Non-Fungible Token (NFT) transactions.

This module defines the CustomRoyaltyFee class, which allows a percentage-based 
fee (with an optional fixed fee fallback) to be collected upon NFT transfer.
"""


class CustomRoyaltyFee(CustomFee):
    """Represents a custom royalty fee assessed during NFT transfers.

    The royalty fee is defined by a fractional exchange value (numerator/denominator) 
    and an optional fixed fee that applies if the NFT is exchanged for HBAR 
    or a token not specified in the fee schedule.

    Inherits common properties like fee_collector_account_id from CustomFee.
    """

    def __init__(
        self,
        numerator: int = 0,
        denominator: int = 1,
        fallback_fee: typing.Optional["CustomFixedFee"] = None,
        fee_collector_account_id: typing.Optional["AccountId"] = None,
        all_collectors_are_exempt: bool = False,
    ):
        """Initializes the CustomRoyaltyFee.

        Args:
            numerator (int): The numerator of the fraction defining the royalty amount. 
                Defaults to 0.
            denominator (int): The denominator of the fraction defining the royalty 
                amount. Defaults to 1.
            fallback_fee (typing.Optional[CustomFixedFee]): The fixed fee to be 
                collected if the exchange is not in the token's unit (e.g., if sold 
                for HBAR). Defaults to None.
            fee_collector_account_id (typing.Optional[AccountId]): The account ID of 
                the fee collector. Inherited from CustomFee. Defaults to None.
            all_collectors_are_exempt (bool): If true, all collectors for this fee 
                are exempt from custom fees. Inherited from CustomFee. Defaults to False.
        """
        super().__init__(fee_collector_account_id, all_collectors_are_exempt)
        self.numerator = numerator
        self.denominator = denominator
        self.fallback_fee = fallback_fee

    def set_numerator(self, numerator: int) -> "CustomRoyaltyFee":
        """Sets the numerator of the royalty fraction.

        Args:
            numerator (int): The numerator value (e.g., 5 for 5/100).

        Returns:
            CustomRoyaltyFee: This CustomRoyaltyFee instance for chaining.
        """
        self.numerator = numerator
        return self

    def set_denominator(self, denominator: int) -> "CustomRoyaltyFee":
        """Sets the denominator of the royalty fraction.

        Args:
            denominator (int): The denominator value (e.g., 100 for 5/100).

        Returns:
            CustomRoyaltyFee: This CustomRoyaltyFee instance for chaining.
        """
        self.denominator = denominator
        return self

    def set_fallback_fee(self, fallback_fee: typing.Optional["CustomFixedFee"]) -> "CustomRoyaltyFee":
        """Sets the optional fixed fee that applies if the royalty is paid in HBAR.

        Args:
            fallback_fee (typing.Optional[CustomFixedFee]): A CustomFixedFee object 
                to use as the fixed fallback fee, or None to remove it.

        Returns:
            CustomRoyaltyFee: This CustomRoyaltyFee instance for chaining.
        """
        self.fallback_fee = fallback_fee
        return self

    def _to_proto(self) -> "custom_fees_pb2.CustomFee":
        """Converts this CustomRoyaltyFee object to its protobuf representation.

        Builds the RoyaltyFee message and integrates it with the common fields
        from the CustomFee parent class into a CustomFee protobuf message.

        Returns:
            custom_fees_pb2.CustomFee: The protobuf CustomFee message.
        """
        from hiero_sdk_python.hapi.services import custom_fees_pb2
        from hiero_sdk_python.hapi.services.basic_types_pb2 import Fraction

        fallback_fee_proto = None
        if self.fallback_fee:
            fallback_fee_proto = self.fallback_fee._to_proto().fixed_fee

        return custom_fees_pb2.CustomFee(
            fee_collector_account_id=self._get_fee_collector_account_id_protobuf(),
            all_collectors_are_exempt=self.all_collectors_are_exempt,
            royalty_fee=custom_fees_pb2.RoyaltyFee(
                exchange_value_fraction=Fraction(
                    numerator=self.numerator,
                    denominator=self.denominator,
                ),
                fallback_fee=fallback_fee_proto,
            ),
        )
    
    @classmethod
    def _from_proto(cls, proto_fee) -> "CustomRoyaltyFee":
        """Creates a CustomRoyaltyFee instance from a CustomFee protobuf message.

        Extracts the royalty fee details, optional fallback fee, and common fee 
        properties from the protobuf message.

        Args:
            proto_fee: The protobuf CustomFee message. It is expected that the 
                `royalty_fee` field is set.

        Returns:
            CustomRoyaltyFee: The corresponding CustomRoyaltyFee object.
        """
        from hiero_sdk_python.account.account_id import AccountId
        from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
        
        royalty_fee_proto = proto_fee.royalty_fee
        
        fallback_fee = None
        if royalty_fee_proto.HasField("fallback_fee"):
            fallback_fee = CustomFixedFee._from_fixed_fee_proto(royalty_fee_proto.fallback_fee)
        
        fee_collector_account_id = None
        if proto_fee.HasField("fee_collector_account_id"):
            fee_collector_account_id = AccountId._from_proto(proto_fee.fee_collector_account_id)
        
        return cls(
            numerator=royalty_fee_proto.exchange_value_fraction.numerator,
            denominator=royalty_fee_proto.exchange_value_fraction.denominator,
            fallback_fee=fallback_fee,
            fee_collector_account_id=fee_collector_account_id,
            all_collectors_are_exempt=proto_fee.all_collectors_are_exempt
        )