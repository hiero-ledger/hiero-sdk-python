from __future__ import annotations
import typing
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod

if typing.TYPE_CHECKING:
    from hiero_sdk_python.account.account_id import AccountId
    from hiero_sdk_python.hapi.services import custom_fees_pb2


class CustomFractionalFee(CustomFee):
    """
    Represents a custom fractional fee.
    """

    def __init__(
        self,
        numerator: int = 0,
        denominator: int = 1,
        min_amount: int = 0,
        max_amount: int = 0,
        assessment_method: FeeAssessmentMethod = FeeAssessmentMethod.INCLUSIVE,
        fee_collector_account_id: typing.Optional["AccountId"] = None,
        all_collectors_are_exempt: bool = False,
    ):
        super().__init__(fee_collector_account_id, all_collectors_are_exempt)
        self.numerator = numerator
        self.denominator = denominator
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.assessment_method = assessment_method

    def set_numerator(self, numerator: int) -> "CustomFractionalFee":
        self.numerator = numerator
        return self

    def set_denominator(self, denominator: int) -> "CustomFractionalFee":
        self.denominator = denominator
        return self

    def set_min_amount(self, min_amount: int) -> "CustomFractionalFee":
        self.min_amount = min_amount
        return self

    def set_max_amount(self, max_amount: int) -> "CustomFractionalFee":
        self.max_amount = max_amount
        return self

    def set_assessment_method(self, assessment_method: FeeAssessmentMethod) -> "CustomFractionalFee":
        self.assessment_method = assessment_method
        return self

    def _to_proto(self) -> "custom_fees_pb2.CustomFee":
        from hiero_sdk_python.hapi.services import custom_fees_pb2
        from hiero_sdk_python.hapi.services.basic_types_pb2 import Fraction

        return custom_fees_pb2.CustomFee(
            fee_collector_account_id=self._get_fee_collector_account_id_protobuf(),
            all_collectors_are_exempt=self.all_collectors_are_exempt,
            fractional_fee=custom_fees_pb2.FractionalFee(
                fractional_amount=Fraction(
                    numerator=self.numerator,
                    denominator=self.denominator,
                ),
                minimum_amount=self.min_amount,
                maximum_amount=self.max_amount,
                net_of_transfers=self.assessment_method.value,
            ),
        )

    @classmethod
    def _from_proto(cls, proto_fee) -> "CustomFractionalFee":
        """Create CustomFractionalFee from protobuf CustomFee message."""
        from hiero_sdk_python.account.account_id import AccountId
        
        fractional_fee_proto = proto_fee.fractional_fee
        
        fee_collector_account_id = None
        if proto_fee.HasField("fee_collector_account_id"):  # Changed from WhichOneof
            fee_collector_account_id = AccountId._from_proto(proto_fee.fee_collector_account_id)
        
        return cls(
            numerator=fractional_fee_proto.fractional_amount.numerator,
            denominator=fractional_fee_proto.fractional_amount.denominator,
            min_amount=fractional_fee_proto.minimum_amount,
            max_amount=fractional_fee_proto.maximum_amount,
            assessment_method=FeeAssessmentMethod(fractional_fee_proto.net_of_transfers),
            fee_collector_account_id=fee_collector_account_id,
            all_collectors_are_exempt=proto_fee.all_collectors_are_exempt
        )