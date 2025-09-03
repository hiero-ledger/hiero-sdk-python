"""
This module contains the CustomFeeLimit class to store information about custom fee limits.
"""

from dataclasses import dataclass, field
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.custom_fees_pb2 import (
    CustomFeeLimit as CustomFeeLimitProto,
)
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee


@dataclass
class CustomFeeLimit:
    """
    Information about custom fee limits stored on the network.

    Attributes:
        payer_id (Optional[AccountId]): The ID of the account that pays the custom fees
        custom_fees (list[CustomFixedFee]): The list of custom fixed fees associated with this limit
    """

    payer_id: Optional[AccountId] = None
    custom_fees: list[CustomFixedFee] = field(default_factory=list)

    def set_payer_id(self, payer_id: Optional[AccountId]) -> "CustomFeeLimit":
        """
        Sets the payer account ID for this custom fee limit.

        Args:
            payer_id (Optional[AccountId]): The ID of the account that pays the custom fees.

        Returns:
            CustomFeeLimit: This instance for method chaining.
        """
        self.payer_id = payer_id
        return self

    def add_custom_fee(self, custom_fee: CustomFixedFee) -> "CustomFeeLimit":
        """
        Adds a custom fixed fee to this custom fee limit.

        Args:
            custom_fee (CustomFixedFee): The custom fixed fee to add.

        Returns:
            CustomFeeLimit: This instance for method chaining.
        """
        self.custom_fees.append(custom_fee)
        return self

    def set_custom_fees(self, custom_fees: list[CustomFixedFee]) -> "CustomFeeLimit":
        """
        Sets the list of custom fixed fees for this custom fee limit.

        Args:
            custom_fees (list[CustomFixedFee]): The list of custom fixed fees to set.

        Returns:
            CustomFeeLimit: This instance for method chaining.
        """
        self.custom_fees = custom_fees
        return self

    def _to_proto(self) -> "CustomFeeLimitProto":
        """
        Converts this CustomFeeLimit instance to its protobuf representation.

        Returns:
            CustomFeeLimitProto: The protobuf representation of this CustomFeeLimit.
        """
        return CustomFeeLimitProto(
            account_id=self.payer_id._to_proto() if self.payer_id else None,
            fees=[custom_fee._to_proto().fixed_fee for custom_fee in self.custom_fees],
        )

    @classmethod
    def _from_proto(cls, proto: "CustomFeeLimitProto") -> "CustomFeeLimit":
        """
        Creates a CustomFeeLimit instance from its protobuf representation.

        Args:
            proto (CustomFeeLimitProto): The protobuf to convert from.

        Returns:
            CustomFeeLimit: A new CustomFeeLimit instance.

        Raises:
            ValueError: If the proto is None.
        """
        if proto is None:
            raise ValueError("Custom fee limit proto is None")

        return cls(
            payer_id=(
                AccountId._from_proto(proto.account_id)
                if proto.HasField("account_id")
                else None
            ),
            custom_fees=[
                CustomFixedFee._from_fixed_fee_proto(custom_fee)
                for custom_fee in proto.fees
            ],
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the CustomFeeLimit object.

        Returns:
            str: A string representation of the CustomFeeLimit object.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the CustomFeeLimit.
        """
        custom_fees_str = (
            [str(fee) for fee in self.custom_fees] if self.custom_fees else []
        )

        return (
            "CustomFeeLimit(\n"
            f"  payer_id={self.payer_id},\n"
            f"  custom_fees={custom_fees_str}\n"
            ")"
        )
