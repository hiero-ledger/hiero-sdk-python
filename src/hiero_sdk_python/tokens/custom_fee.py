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
    Base class for custom fees.
    """

    def __init__(
        self,
        fee_collector_account_id: typing.Optional[AccountId] = None,
        all_collectors_are_exempt: bool = False,
    ):
        self.fee_collector_account_id = fee_collector_account_id
        self.all_collectors_are_exempt = all_collectors_are_exempt

    def set_fee_collector_account_id(self, account_id: AccountId) -> "CustomFee":
        self.fee_collector_account_id = account_id
        return self

    def set_all_collectors_are_exempt(self, exempt: bool) -> "CustomFee":
        self.all_collectors_are_exempt = exempt
        return self

    @staticmethod
    def _from_proto(custom_fee: "CustomFeeProto") -> "CustomFee":  # Changed from _from_protobuf
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
        return (
            self.fee_collector_account_id._to_proto()
            if self.fee_collector_account_id is not None
            else None
        )

    @abstractmethod
    def _to_proto(self) -> "CustomFeeProto":  # Changed from _to_protobuf
        ...

    def _validate_checksums(self, client: Client) -> None:
        if self.fee_collector_account_id is not None:
            self.fee_collector_account_id.validate_checksum(client)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CustomFee):
            return NotImplemented
        
        return self.fee_collector_account_id == other.fee_collector_account_id and self.all_collectors_are_exempt == other.all_collectors_are_exempt