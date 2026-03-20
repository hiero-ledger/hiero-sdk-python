from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services.basic_types_pb2 import (
    TokenAssociation as TokenAssociationProto,
)

@dataclass
class TokenAssociation:
    """Represents an automatic token association between a token and an account.

    This class appears in `TransactionRecord.automatic_token_associations` (repeated field)
    when the network creates associations automatically (e.g., during token transfers
    or airdrops to unassociated accounts).

    These associations are informational only and cannot be used to create new associations
    on the ledger — use TokenAssociateTransaction for that.
    """

    token_id: Optional[TokenId] = None
    """The ID of the token that was automatically associated."""

    account_id: Optional[AccountId] = None
    """The ID of the account that received the automatic association."""

    @classmethod
    def _from_proto(cls, proto: TokenAssociationProto) -> "TokenAssociation":
        """Create a TokenAssociation instance from the protobuf message."""
        return cls(
            token_id=(
                TokenId._from_proto(proto.token_id)
                if proto.HasField("token_id")
                else None
            ),
            account_id=(
                AccountId._from_proto(proto.account_id)
                if proto.HasField("account_id")
                else None
            ),
        )

    def _to_proto(self) -> TokenAssociationProto:
        """Convert this TokenAssociation instance back to a protobuf message."""
        proto = TokenAssociationProto()

        if self.token_id is not None:
            proto.token_id.CopyFrom(self.token_id._to_proto())

        if self.account_id is not None:
            proto.account_id.CopyFrom(self.account_id._to_proto())

        return proto

    def to_bytes(self) -> bytes:
        """Serialize this TokenAssociation to raw protobuf bytes."""
        return self._to_proto().SerializeToString()

    @classmethod
    def from_bytes(cls, data: bytes) -> "TokenAssociation":
        """Deserialize a TokenAssociation from raw protobuf bytes."""
        proto = TokenAssociationProto()
        proto.ParseFromString(data)
        return cls._from_proto(proto)
    
    def __str__(self) -> str:
        """Returns a human-readable string representation."""
        return (
            f"TokenAssociation("
            f"token_id={self.token_id}, "
            f"account_id={self.account_id}"
            f")"
        )
    