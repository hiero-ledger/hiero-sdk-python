from dataclasses import dataclass, field
from typing import List, Optional

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

    fee_collector_account_id: AccountId = None  # required – typically set via constructor/from_proto

    effective_payer_account_ids: List[AccountId] = field(default_factory=list)
    """The list of accounts that effectively paid this assessed fee (repeated field)."""

    def __post_init__(self) -> None:
        if self.fee_collector_account_id is None:
            raise ValueError("fee_collector_account_id is required for AssessedCustomFee")