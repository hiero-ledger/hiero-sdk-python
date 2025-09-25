"""
TokenNftAllowance class for handling NFT token allowances.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from google.protobuf.wrappers_pb2 import BoolValue

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    NftAllowance as NftAllowanceProto,
)
from hiero_sdk_python.hapi.services.crypto_delete_allowance_pb2 import (
    NftRemoveAllowance as NftRemoveAllowanceProto,
)
from hiero_sdk_python.tokens.token_id import TokenId


@dataclass
class TokenNftAllowance:
    """
    Represents an NFT token allowance for the network.

    This class encapsulates NFT allowance information including the token ID,
    owner account, spender account, specific serial numbers, approval for all
    tokens flag, and optional delegating spender.

    Attributes:
        token_id (Optional[TokenId]): The ID of the NFT token.
        owner_account_id (Optional[AccountId]): The account that owns the NFTs.
        spender_account_id (Optional[AccountId]): The account permitted to transfer the NFTs.
        serial_numbers (List[int]): List of specific NFT serial numbers allowed for transfer.
        approved_for_all (Optional[bool]): Whether the spender can transfer all NFTs of this type.
        delegating_spender (Optional[AccountId]): Account that can delegate NFT transfers.
    """

    token_id: Optional[TokenId] = None
    owner_account_id: Optional[AccountId] = None
    spender_account_id: Optional[AccountId] = None
    serial_numbers: List[int] = field(default_factory=list)
    approved_for_all: Optional[bool] = None
    delegating_spender: Optional[AccountId] = None

    @classmethod
    def _from_proto(cls, proto: NftAllowanceProto) -> "TokenNftAllowance":
        """
        Creates a TokenNftAllowance instance from its protobuf representation.

        Args:
            proto (NftAllowanceProto): The protobuf NftAllowance object to convert.

        Returns:
            TokenNftAllowance: A new TokenNftAllowance instance.

        Raises:
            ValueError: If the proto is None.
        """
        if proto is None:
            raise ValueError("NftAllowance proto is None")

        return cls(
            token_id=(cls._from_proto_field(proto, "tokenId", TokenId._from_proto)),
            owner_account_id=(cls._from_proto_field(proto, "owner", AccountId._from_proto)),
            spender_account_id=(cls._from_proto_field(proto, "spender", AccountId._from_proto)),
            serial_numbers=list(proto.serial_numbers),
            approved_for_all=(
                proto.approved_for_all.value if proto.HasField("approved_for_all") else False
            ),
            delegating_spender=(
                cls._from_proto_field(proto, "delegating_spender", AccountId._from_proto)
            ),
        )

    @classmethod
    def _from_wipe_proto(cls, proto: NftRemoveAllowanceProto) -> "TokenNftAllowance":
        """
        Creates a TokenNftAllowance instance from an NftRemoveAllowance protobuf.

        Args:
            proto (NftRemoveAllowanceProto): The protobuf NftRemoveAllowance object to convert.

        Returns:
            TokenNftAllowance: A new TokenNftAllowance instance.

        Raises:
            ValueError: If the proto is None.
        """
        if proto is None:
            raise ValueError("NftRemoveAllowance proto is None")

        return cls(
            token_id=(cls._from_proto_field(proto, "token_id", TokenId._from_proto)),
            owner_account_id=(cls._from_proto_field(proto, "owner", AccountId._from_proto)),
            serial_numbers=list(proto.serial_numbers),
        )

    def _to_proto(self) -> NftAllowanceProto:
        """
        Converts this TokenNftAllowance instance to its protobuf representation.

        Returns:
            NftAllowanceProto: The protobuf representation of this TokenNftAllowance.
        """
        proto = NftAllowanceProto()

        if self.token_id is not None:
            proto.tokenId.CopyFrom(self.token_id._to_proto())

        if self.owner_account_id is not None:
            proto.owner.CopyFrom(self.owner_account_id._to_proto())

        if self.spender_account_id is not None:
            proto.spender.CopyFrom(self.spender_account_id._to_proto())

        proto.serial_numbers.extend(self.serial_numbers)

        if self.approved_for_all is not None:
            proto.approved_for_all.CopyFrom(BoolValue(value=self.approved_for_all))

        if self.delegating_spender is not None:
            proto.delegating_spender.CopyFrom(self.delegating_spender._to_proto())

        return proto

    def _to_wipe_proto(self) -> NftRemoveAllowanceProto:
        """
        Converts this TokenNftAllowance instance to an NftRemoveAllowance protobuf.

        Returns:
            NftRemoveAllowanceProto: The protobuf representation for allowance removal.
        """
        proto = NftRemoveAllowanceProto()

        if self.token_id is not None:
            proto.token_id.CopyFrom(self.token_id._to_proto())

        if self.owner_account_id is not None:
            proto.owner.CopyFrom(self.owner_account_id._to_proto())

        proto.serial_numbers.extend(self.serial_numbers)

        return proto

    def __str__(self) -> str:
        """
        Returns a string representation of the TokenNftAllowance object.

        Returns:
            str: A string representation of the TokenNftAllowance object.
        """
        owner_str = str(self.owner_account_id) if self.owner_account_id else "None"
        spender_str = str(self.spender_account_id) if self.spender_account_id else "None"
        token_str = str(self.token_id) if self.token_id else "None"
        serials_str = str(self.serial_numbers) if self.serial_numbers else "[]"
        delegating_str = (
            f", delegating_spender={self.delegating_spender}" if self.delegating_spender else ""
        )

        return (
            f"TokenNftAllowance("
            f"owner_account_id={owner_str}, "
            f"spender_account_id={spender_str}, "
            f"token_id={token_str}, "
            f"serial_numbers={serials_str}, "
            f"approved_for_all={self.approved_for_all}"
            f"{delegating_str}"
            f")"
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the TokenNftAllowance object.

        Returns:
            str: A string representation of the TokenNftAllowance object.
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
