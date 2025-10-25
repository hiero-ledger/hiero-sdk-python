"""
hiero_sdk_python.tokens.token_transfer.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenTransfer for representing Token transfer details and utility functions for operations.
"""

from typing import Optional
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_id import TokenId


class TokenTransfer:
    """
    Represents a single fungible token transfer.

    Attributes:
        token_id (TokenId): The ID of the token being transferred.
        account_id (AccountId): The account ID of the sender or receiver.
        amount (int): The amount of the token to send or receive.
        expected_decimals (Optional[int]): Number specifying the amount in the smallest denomination.
        is_approved (bool): Indicates whether this transfer is an approved allowance.
    """

    def __init__(
        self,
        token_id: TokenId,
        account_id: AccountId,
        amount: int,
        expected_decimals: Optional[int] = None,
        is_approved: bool = False
    ) -> None:
        self.token_id: TokenId = token_id
        self.account_id: AccountId = account_id
        self.amount: int = amount
        self.expected_decimals: Optional[int] = expected_decimals
        self.is_approved: bool = is_approved

    def __str__(self) -> str:
        return (
            f"TokenTransfer("
            f"token_id={self.token_id}, "
            f"account_id={self.account_id}, "
            f"amount={self.amount}, "
            f"expected_decimals={self.expected_decimals}, "
            f"is_approved={self.is_approved})"
        )


# --------------------------
# Helper functions / utilities
# --------------------------

def create_token_transfer(
    token_id: TokenId,
    account_id: AccountId,
    amount: int,
    expected_decimals: Optional[int] = None,
    is_approved: bool = False
) -> TokenTransfer:
    """
    Factory function to create a TokenTransfer instance.
    """
    return TokenTransfer(token_id, account_id, amount, expected_decimals, is_approved)


def token_transfer_to_proto(transfer: TokenTransfer) -> basic_types_pb2.AccountAmount:
    """
    Converts a TokenTransfer instance to its protobuf representation.

    Args:
        transfer (TokenTransfer): The TokenTransfer instance to convert.

    Returns:
        AccountAmount: The protobuf representation of this TokenTransfer.
    """
    return basic_types_pb2.AccountAmount(
        accountID=transfer.account_id._to_proto(),
        amount=transfer.amount,
        is_approval=transfer.is_approved
    )
