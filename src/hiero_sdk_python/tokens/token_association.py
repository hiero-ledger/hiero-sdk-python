"""
Module defining the TokenAssociation class.

This class represents an association between a token and an account,
typically appearing in TransactionRecord.automatic_token_associations
when the network automatically creates token associations (e.g. during
token airdrops or transfers to unassociated accounts in certain conditions).
"""

from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenAssociation as TokenAssociationProto


@dataclass(frozen=True)
class TokenAssociation:
    """
    A lightweight immutable representation of a token ↔ account association.

    Used in:
    - TransactionRecord.automatic_token_associations (list of associations
      created automatically during transaction execution)

    Attributes:
        token_id: The identifier of the token being associated.
        account_id: The identifier of the account receiving the association.

    Examples:
        Creating a simple association:
        >>> from hiero_sdk_python.tokens.token_id import TokenId
        >>> from hiero_sdk_python.account.account_id import AccountId
        >>> assoc = TokenAssociation(
        ...     token_id=TokenId.from_string("0.0.1234"),
        ...     account_id=AccountId.from_string("0.0.5678")
        ... )
        >>> str(assoc)
        'TokenAssociation(token_id=0.0.1234, account_id=0.0.5678)'

        Immutability (frozen=True):
        >>> assoc.token_id = TokenId.from_string("0.0.9999")
        Traceback (most recent call last):
            ...
        dataclasses.FrozenInstanceError: cannot assign to field 'token_id'

        Round-trip via protobuf:
        >>> proto = assoc._to_proto()
        >>> restored = TokenAssociation._from_proto(proto)
        >>> restored == assoc
        True

        >>> # Typical usage in TransactionRecord context:
        >>> # record = client.get_transaction_record(...)
        >>> # for assoc in record.automatic_token_associations:
        >>> #     print(f"Auto-associated {assoc.token_id} to {assoc.account_id}")
    """

    token_id: Optional[TokenId] = None
    """The identifier of the token being associated."""

    account_id: Optional[AccountId] = None
    """The identifier of the account receiving the association."""

    @classmethod
    def _from_proto(cls, proto: TokenAssociationProto) -> "TokenAssociation":
        """
        Construct a TokenAssociation object from the protobuf representation.
        """
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
        """
        Convert this TokenAssociation back into a protobuf message.
        """
        proto = TokenAssociationProto()

        if self.token_id is not None:
            proto.token_id.CopyFrom(self.token_id._to_proto())

        if self.account_id is not None:
            proto.account_id.CopyFrom(self.account_id._to_proto())

        return proto

    def __str__(self) -> str:
        return f"TokenAssociation(token_id={self.token_id}, account_id={self.account_id})"

    def __repr__(self) -> str:
        return self.__str__()
    