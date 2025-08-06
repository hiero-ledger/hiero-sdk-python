from __future__ import annotations
import typing
from hiero_sdk_python.tokens.custom_fee import CustomFee

if typing.TYPE_CHECKING:
    from hiero_sdk_python.account.account_id import AccountId
    from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
    from hiero_sdk_python.hapi.services import custom_fees_pb2


class CustomRoyaltyFee(CustomFee):
    """
    Represents a custom royalty fee.
    """

    def __init__(
        self,
        numerator: int = 0,
        denominator: int = 1,
        fallback_fee: typing.Optional["CustomFixedFee"] = None,
        fee_collector_account_id: typing.Optional["AccountId"] = None,
        all_collectors_are_exempt: bool = False,
    ):
        super().__init__(fee_collector_account_id, all_collectors_are_exempt)
        self.numerator = numerator
        self.denominator = denominator
        self.fallback_fee = fallback_fee

    def set_numerator(self, numerator: int) -> "CustomRoyaltyFee":
        self.numerator = numerator
        return self

    def set_denominator(self, denominator: int) -> "CustomRoyaltyFee":
        self.denominator = denominator
        return self

    def set_fallback_fee(self, fallback_fee: typing.Optional["CustomFixedFee"]) -> "CustomRoyaltyFee":
        self.fallback_fee = fallback_fee
        return self

    def _to_proto(self) -> "custom_fees_pb2.CustomFee":
        from hiero_sdk_python.hapi.services import custom_fees_pb2
        from hiero_sdk_python.hapi.services.basic_types_pb2 import Fraction

        fallback_fee_proto = None
        if self.fallback_fee:
            # Use _to_proto instead of _to_protobuf
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
        """Create CustomRoyaltyFee from protobuf CustomFee message."""
        from hiero_sdk_python.account.account_id import AccountId
        from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
        
        royalty_fee_proto = proto_fee.royalty_fee
        
        fallback_fee = None
        if royalty_fee_proto.HasField("fallback_fee"):
            # Use the existing _from_fixed_fee_proto method
            fallback_fee = CustomFixedFee._from_fixed_fee_proto(royalty_fee_proto.fallback_fee)
        
        fee_collector_account_id = None
        if proto_fee.HasField("fee_collector_account_id"):  # Changed from WhichOneof
            fee_collector_account_id = AccountId._from_proto(proto_fee.fee_collector_account_id)
        
        return cls(
            numerator=royalty_fee_proto.exchange_value_fraction.numerator,
            denominator=royalty_fee_proto.exchange_value_fraction.denominator,
            fallback_fee=fallback_fee,
            fee_collector_account_id=fee_collector_account_id,
            all_collectors_are_exempt=proto_fee.all_collectors_are_exempt
        )