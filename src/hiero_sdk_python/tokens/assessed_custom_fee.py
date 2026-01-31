from dataclasses import dataclass, field
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.custom_fees_pb2 import AssessedCustomFee as AssessedCustomFeeProto
from hiero_sdk_python.tokens.token_id import TokenId


@dataclass
class AssessedCustomFee:
    """
    Represents an assessed custom fee as returned in transaction records.
    Mirrors the AssessedCustomFee protobuf message from Hedera/Hiero.
    """
    amount: int
    """The amount of the fee assessed, in the smallest units of the token (or tinybars for HBAR)."""

    token_id: Optional[TokenId] = None
    """The ID of the token used to pay the fee; None if paid in HBAR."""

    fee_collector_account_id: Optional[AccountId] = None
    """The account ID that collects/receives this assessed custom fee (required field)."""

    effective_payer_account_ids: list[AccountId] = field(default_factory=list)
    """The list of accounts that effectively paid this assessed fee (repeated field)."""

    def __post_init__(self) -> None:
        if self.fee_collector_account_id is None:
            raise ValueError("fee_collector_account_id is required for AssessedCustomFee")

    @classmethod
    def _from_proto(cls, proto: AssessedCustomFeeProto) -> "AssessedCustomFee":
        """Create an AssessedCustomFee instance from the protobuf message."""
        token_id = (
            TokenId._from_proto(proto.token_id)
            if proto.HasField("token_id")
            else None
        )

        if not proto.HasField("fee_collector_account_id"):
            raise ValueError("fee_collector_account_id is required in AssessedCustomFee proto")
        
        return cls(
            amount=proto.amount,
            token_id=token_id,
            fee_collector_account_id=AccountId._from_proto(proto.fee_collector_account_id),
            effective_payer_account_ids=[
                AccountId._from_proto(payer_proto)
                for payer_proto in proto.effective_payer_account_id
            ],
        )

    def _to_proto(self) -> AssessedCustomFeeProto:
        """Convert this AssessedCustomFee instance back to a protobuf message."""
        proto = AssessedCustomFeeProto(
            amount=self.amount,
            fee_collector_account_id=self.fee_collector_account_id._to_proto(),
        )

        if self.token_id is not None:
            proto.token_id.CopyFrom(self.token_id._to_proto())

        for payer in self.effective_payer_account_ids:
            proto.effective_payer_account_id.append(payer._to_proto())

        return proto
        
    def __str__(self) -> str:
        """Returns a human-readable string representation."""
        return (
            f"AssessedCustomFee("
            f"amount={self.amount}, "
            f"token_id={self.token_id}, "
            f"fee_collector_account_id={self.fee_collector_account_id}, "
            f"effective_payer_account_ids={self.effective_payer_account_ids}"
            f")"
        )  
    