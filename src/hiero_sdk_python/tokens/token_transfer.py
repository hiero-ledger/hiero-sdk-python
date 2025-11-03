"""
hiero_sdk_python.tokens.token_transfer.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenTransfer for representing Token transfer details.
"""

from typing import List, Optional
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.tokens.token_id import TokenId

class TokenTransfer:
    """
    Represents a single fungible token transfer, detailing the token, the account involved,
    the amount, and optional approval status and decimal expectations.
    """
    def __init__(
            self,
            token_id: TokenId,
            account_id: AccountId,
            amount: int,
            expected_decimals: Optional[int]=None,
            is_approved: bool=False
        ) ->None:
        """
        Initializes a new TokenTransfer instance.

        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The account ID of the sender or receiver.
            amount (int): The amount of the token to send or receive.
            expected_decimals (optional, int): 
                The number specifying the amount in the smallest denomination.
            is_approved (optional, bool): Indicates whether this transfer is an approved allowance.
        """
        self.token_id: TokenId = token_id
        self.account_id: AccountId = account_id
        self.amount: int = amount
        self.expected_decimals: Optional[int] = expected_decimals
        self.is_approved: bool = is_approved

    def _to_proto(self) -> basic_types_pb2.AccountAmount:
        """
        Converts this TokenTransfer instance to its protobuf representation, AccountAmount.

        Returns:
            AccountAmount: The protobuf representation of this TokenTransfer.
        """
        return basic_types_pb2.AccountAmount(
            accountID=self.account_id._to_proto(),
            amount=self.amount,
            is_approval=self.is_approved
        )

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.TokenTransferList) -> List["TokenTransfer"]:
        """
        Construct a list of TokenTransfer from the protobuf of TokenTransferList.

        Args:
        proto (basic_types_pb2.TokenTransferList: 
            The protobuf representation of a TokenTransferList
        """
        token_transfer: List[TokenTransfer] = []

        expected_decimals = (
            proto.expected_decimals.value if proto.HasField('expected_decimals') else None
        )

        for transfer in proto.transfers:
            token_transfer.append(
                TokenTransfer(
                    token_id=TokenId._from_proto(proto.token),
                    account_id=AccountId._from_proto(transfer.accountID),
                    amount=transfer.amount,
                    expected_decimals=expected_decimals,
                    is_approved=transfer.is_approval
                )
            )

        return token_transfer

    def __str__(self) -> str:
        """
        Returns a string representation of this TokenTransfer instance.

        Returns:
            str: A string representation of this TokenTransfer.
        """
        return (
            f"TokenTransfer("
            f"token_id={self.token_id}, "
            f"account_id={self.account_id}, "
            f"amount={self.amount}, "
            f"expected_decimals={self.expected_decimals}, "
            f"is_approved={self.is_approved})"
        )
