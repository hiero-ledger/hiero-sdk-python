"""
TokenAllowance class for handling fungible token allowances.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    TokenAllowance as TokenAllowanceProto,
)
from hiero_sdk_python.tokens.token_id import TokenId


@dataclass
class TokenAllowance:
    """
    Represents a fungible token allowance for the network.

    This class encapsulates fungible token allowance information including the token ID,
    owner account, spender account, and amount.

    Attributes:
        token_id (Optional[TokenId]): The ID of the fungible token.
        owner_account_id (Optional[AccountId]): The account that owns the tokens.
        spender_account_id (Optional[AccountId]): The account permitted to transfer the tokens.
        amount (int): The amount of tokens allowed for transfer.
    """

    token_id: Optional[TokenId] = None
    owner_account_id: Optional[AccountId] = None
    spender_account_id: Optional[AccountId] = None
    amount: int = 0

    @classmethod
    def _from_proto(cls, proto: TokenAllowanceProto) -> "TokenAllowance":
        """
        Creates a TokenAllowance instance from its protobuf representation.

        Args:
            proto (TokenAllowanceProto): The protobuf TokenAllowance object to convert.

        Returns:
            TokenAllowance: A new TokenAllowance instance.

        Raises:
            ValueError: If the proto is None.
        """
        if proto is None:
            raise ValueError("TokenAllowance proto is None")

        return cls(
            token_id=(cls._from_proto_field(proto, "tokenId", TokenId._from_proto)),
            owner_account_id=(cls._from_proto_field(proto, "owner", AccountId._from_proto)),
            spender_account_id=(cls._from_proto_field(proto, "spender", AccountId._from_proto)),
            amount=proto.amount,
        )

    def _to_proto(self) -> TokenAllowanceProto:
        """
        Converts this TokenAllowance instance to its protobuf representation.

        Returns:
            TokenAllowanceProto: The protobuf representation of this TokenAllowance.
        """
        proto = TokenAllowanceProto()

        if self.token_id is not None:
            proto.tokenId.CopyFrom(self.token_id._to_proto())

        if self.owner_account_id is not None:
            proto.owner.CopyFrom(self.owner_account_id._to_proto())

        if self.spender_account_id is not None:
            proto.spender.CopyFrom(self.spender_account_id._to_proto())

        proto.amount = self.amount

        return proto

    def __str__(self) -> str:
        """
        Returns a string representation of the TokenAllowance object.

        Returns:
            str: A string representation of the TokenAllowance object.
        """
        owner_str = str(self.owner_account_id) if self.owner_account_id else "None"
        spender_str = str(self.spender_account_id) if self.spender_account_id else "None"
        token_str = str(self.token_id) if self.token_id else "None"

        return (
            f"TokenAllowance("
            f"owner_account_id={owner_str}, "
            f"spender_account_id={spender_str}, "
            f"token_id={token_str}, "
            f"amount={self.amount}"
            f")"
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the TokenAllowance object.

        Returns:
            str: A string representation of the TokenAllowance object.
        """
        return self.__str__()

    @classmethod
    def _from_proto_field(
        cls,
        proto: Any,
        field_name: str,
        from_proto: Callable,
    ):
        """
        Helper to extract and convert proto fields to a python object.

        Args:
            proto: The protobuf object to extract the field from.
            field_name: The name of the field to extract.
            from_proto: A callable to convert the field from protobuf to a python object.

        Returns:
            The converted field value or None if the field doesn't exist.
        """
        if not proto.HasField(field_name):
            return None

        value = getattr(proto, field_name)
        return from_proto(value)
