"""Module defining the base CustomFee abstract class.

This module provides the foundational CustomFee abstract base class, which serves as the parent
for various custom fee types (e.g., fixed, fractional, royalty fees) in the Hiero SDK. It defines
common attributes and methods for fee collection, validation, and protobuf conversion.

Subclasses:
    - CustomFixedFee
    - CustomFractionalFee
    - CustomRoyaltyFee
"""

from __future__ import annotations
import typing
from abc import ABC, abstractmethod

if typing.TYPE_CHECKING:
    from hiero_sdk_python.account.account_id import AccountId
    from hiero_sdk_python.client.client import Client
    from hiero_sdk_python.hapi.services.basic_types_pb2 import AccountID
    from hiero_sdk_python.hapi.services.custom_fees_pb2 import CustomFee as CustomFeeProto


class CustomFee(ABC):
    """
    Abstract base class for custom fees in the Hiero network.

    This class defines the common structure and behavior for different types of custom fees,
    including attributes for the fee collector account and exemption settings. Subclasses must
    implement the _to_proto method to serialize the fee to protobuf format.
    """

    def __init__(
        self,
        fee_collector_account_id: typing.Optional[AccountId] = None,
        all_collectors_are_exempt: bool = False,
    ):
        """Initializes a CustomFee instance.

        Args:
            fee_collector_account_id (Optional[AccountId]): The account ID that collects
                the fee. If None, no collector is specified.
            all_collectors_are_exempt (bool): If True, all collectors are exempt from this fee.
                Defaults to False.
        """
        self.fee_collector_account_id = fee_collector_account_id
        self.all_collectors_are_exempt = all_collectors_are_exempt

    def set_fee_collector_account_id(self, account_id: AccountId) -> "CustomFee":
        """Sets the fee collector account ID.

        Args:
            account_id (AccountId): The account ID to set as the fee collector.

        Returns:
            CustomFee: This instance for method chaining.
        """
        self.fee_collector_account_id = account_id
        return self

    def set_all_collectors_are_exempt(self, exempt: bool) -> "CustomFee":
        """Sets the exemption status for all collectors.

        Args:
            exempt (bool): If True, all collectors are exempt from this fee.

        Returns:
            CustomFee: This instance for method chaining.
        """
        self.all_collectors_are_exempt = exempt
        return self

    @staticmethod
    def _from_proto(custom_fee: "CustomFeeProto") -> "CustomFee":  # Changed from _from_protobuf
        """Creates a CustomFee instance from a protobuf message.

        This factory method dynamically instantiates the appropriate subclass based on the
        protobuf's fee type (fixed, fractional, or royalty).

        Args:
            custom_fee (CustomFeeProto): The protobuf CustomFee message to deserialize.

        Returns:
            CustomFee: An instance of the appropriate CustomFee subclass.

        Raises:
            ValueError: If the protobuf contains an unrecognized fee type.
        """
        from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
        from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
        from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee

        fee_case = custom_fee.WhichOneof("fee")
        if fee_case == "fixed_fee":
            return CustomFixedFee._from_proto(custom_fee)  # Changed from _from_protobuf
        if fee_case == "fractional_fee":
            return CustomFractionalFee._from_proto(custom_fee)  # Changed from _from_protobuf
        if fee_case == "royalty_fee":
            return CustomRoyaltyFee._from_proto(custom_fee)  # Changed from _from_protobuf

        raise ValueError(f"Unrecognized fee case: {fee_case}")

    def _get_fee_collector_account_id_protobuf(self) -> typing.Optional[AccountID]:
        """Retrieves the fee collector account ID in protobuf format.

        Returns:
            Optional[AccountID]: The protobuf AccountID if the fee collector is set,
            otherwise None.
        """
        return (
            self.fee_collector_account_id._to_proto()
            if self.fee_collector_account_id is not None
            else None
        )

    @abstractmethod
    def _to_proto(self) -> "CustomFeeProto":  # Changed from _to_protobuf
        """Converts this CustomFee to its protobuf representation.

        Subclasses must implement this method to serialize their specific fee details.

        Returns:
            CustomFeeProto: The protobuf CustomFee message.
        """
        ...

    def _validate_checksums(self, client: Client) -> None:
        """Validates checksums for the fee collector account ID.

        Args:
            client (Client): The client used for validation, which provides network context.
        """
        if self.fee_collector_account_id is not None:
            self.fee_collector_account_id.validate_checksum(client)

    def __eq__(self, other: object) -> bool:
        """Checks equality with another CustomFee instance.

        Equality is based on both the `fee_collector_account_id` and
        the `all_collectors_are_exempt` flag.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: `True` if the instances are equal, `False` otherwise.
        """
        if not isinstance(other, CustomFee):
            return NotImplemented
        
        return self.fee_collector_account_id == other.fee_collector_account_id and self.all_collectors_are_exempt == other.all_collectors_are_exempt