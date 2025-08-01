from __future__ import annotations
import typing
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.hbar import Hbar

if typing.TYPE_CHECKING:
    from hiero_sdk_python.account.account_id import AccountId
    from hiero_sdk_python.client import Client
    from hiero_sdk_python.tokens.token_id import TokenId
    from hiero_sdk_python.hapi.services import custom_fees_pb2


class CustomFixedFee(CustomFee):
    """
    Represents a custom fixed fee.
    """

    def __init__(
        self,
        amount: int = 0,
        denominating_token_id: typing.Optional["TokenId"] = None,
        fee_collector_account_id: typing.Optional["AccountId"] = None,
        all_collectors_are_exempt: bool = False,
    ):
        super().__init__(fee_collector_account_id, all_collectors_are_exempt)
        self.amount = amount
        self.denominating_token_id = denominating_token_id

    def set_amount_in_tinybars(self, amount: int) -> "CustomFixedFee":
        self.amount = amount
        return self

    def set_hbar_amount(self, amount: Hbar) -> "CustomFixedFee":
        self.denominating_token_id = None
        self.amount = amount.to_tinybars()
        return self

    def set_denominating_token_id(self, token_id: typing.Optional["TokenId"]) -> "CustomFixedFee":
        self.denominating_token_id = token_id
        return self
    
    def set_denominating_token_to_same_token(self) -> "CustomFixedFee":
        from hiero_sdk_python.tokens.token_id import TokenId
        self.denominating_token_id = TokenId(0, 0, 0)
        return self

    @staticmethod
    def _from_protobuf(custom_fee: "custom_fees_pb2.CustomFee") -> CustomFixedFee:
        from hiero_sdk_python.account.account_id import AccountId
        
        fee = CustomFixedFee._from_fixed_fee_proto(custom_fee.fixed_fee)
        if custom_fee.HasField("fee_collector_account_id"):
            fee.fee_collector_account_id = AccountId._from_proto(
                custom_fee.fee_collector_account_id
            )
        fee.all_collectors_are_exempt = custom_fee.all_collectors_are_exempt
        return fee

    @staticmethod
    def _from_fixed_fee_proto(fixed_fee: "custom_fees_pb2.FixedFee") -> "CustomFixedFee":
        from hiero_sdk_python.tokens.token_id import TokenId
        fee = CustomFixedFee()
        fee.amount = fixed_fee.amount
        if fixed_fee.HasField("denominating_token_id"):
            fee.denominating_token_id = TokenId._from_proto(
                fixed_fee.denominating_token_id
            )
        return fee

    def _to_protobuf(self) -> "custom_fees_pb2.CustomFee":
        from hiero_sdk_python.hapi.services import custom_fees_pb2

        return custom_fees_pb2.CustomFee(
            fee_collector_account_id=self._get_fee_collector_account_id_protobuf(),
            all_collectors_are_exempt=self.all_collectors_are_exempt,
            fixed_fee=custom_fees_pb2.FixedFee(
                amount=self.amount,
                denominating_token_id=self.denominating_token_id._to_proto()
                if self.denominating_token_id is not None
                else None,
            ),
        )

    def _validate_checksums(self, client: "Client") -> None:
        super()._validate_checksums(client)
        if self.denominating_token_id is not None:
            self.denominating_token_id.validate_checksum(client)