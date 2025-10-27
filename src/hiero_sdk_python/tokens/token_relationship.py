"""hiero_sdk_python.tokens.token_relationship.py

Provides TokenRelationship, a dataclass modeling an account’s relationship to a token,
including ID, symbol, balance, KYC status, freeze status, decimals, and auto-association flag.
This class is primarily used for parsing and representing data returned by queries like
CryptoGetAccountInfoQuery.
"""
from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.hapi.services.basic_types_pb2 import (
    TokenRelationship     as TokenRelationshipProto,
    TokenFreezeStatus     as TokenFreezeStatusProto,
    TokenKycStatus        as TokenKycStatusProto,
)
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus

@dataclass
class TokenRelationship:
    """
    Represents a relationship between an account and a token.

    Attributes:
        token_id (Optional[TokenId]): The ID of the token.
        symbol (Optional[str]): The symbol of the token.
        balance (Optional[int]): The balance of tokens held by the account.
        kyc_status (Optional[TokenKycStatus]): The KYC status of the account for this token.
        freeze_status (Optional[TokenFreezeStatus]): 
            The freeze status of the account for this token.
        decimals (Optional[int]): The number of decimal places used by the token.
        automatic_association (Optional[bool]): 
            Whether the token was automatically associated with the account.
    """
    token_id: Optional[TokenId] = None
    symbol: Optional[str] = None
    balance: Optional[int] = None
    kyc_status: Optional[TokenKycStatus] = None
    freeze_status: Optional[TokenFreezeStatus] = None
    decimals: Optional[int] = None
    automatic_association: Optional[bool] = None

    @classmethod
    def _from_proto(cls, proto: Optional[TokenRelationshipProto]) -> 'TokenRelationship':
        """Creates a TokenRelationship instance from a protobuf TokenRelationship message.

        Parses the protobuf fields, converting enum types (KYC, Freeze status) and 
        TokenId objects into their corresponding Python representations.

        Args:
            proto (Optional[TokenRelationshipProto]): The protobuf TokenRelationship message.

        Returns:
            TokenRelationship: The corresponding Python dataclass instance.

        Raises:
            ValueError: If the input `proto` object is None.
        """
        if proto is None:
            raise ValueError("Token relationship proto is None")

        token_id: Optional[TokenId] = (
            TokenId._from_proto(proto.tokenId)
            if proto.tokenId
            else None
        )
        # Convert HAPI protobuf enums to SDK enums
        kyc_status: TokenKycStatus = TokenKycStatus._from_proto(proto.kycStatus)
        freeze_status: TokenFreezeStatus = TokenFreezeStatus._from_proto(proto.freezeStatus)

        return cls(
            token_id=token_id,
            symbol=proto.symbol,
            balance=proto.balance,
            kyc_status=kyc_status,
            freeze_status=freeze_status,
            decimals=proto.decimals,
            automatic_association=proto.automatic_association
        )

    def _to_proto(self) -> TokenRelationshipProto:
        """Converts this TokenRelationship instance into its protobuf representation.

        Converts SDK enums (TokenFreezeStatus, TokenKycStatus) back into their 
        HAPI protobuf integer enum values for transmission.

        Returns:
            TokenRelationshipProto: The corresponding protobuf message.
        """
        # Determine protobuf enum value for freeze status
        freeze_status = TokenFreezeStatusProto.FreezeNotApplicable
        if self.freeze_status == TokenFreezeStatus.FROZEN:
            freeze_status = TokenFreezeStatusProto.Frozen
        elif self.freeze_status == TokenFreezeStatus.UNFROZEN:
            freeze_status = TokenFreezeStatusProto.Unfrozen

        # Determine protobuf enum value for KYC status
        kyc_status = TokenKycStatusProto.KycNotApplicable
        if self.kyc_status == TokenKycStatus.GRANTED:
            kyc_status = TokenKycStatusProto.Granted
        elif self.kyc_status == TokenKycStatus.REVOKED:
            kyc_status = TokenKycStatusProto.Revoked

        proto = TokenRelationshipProto(
            symbol=self.symbol,
            balance=self.balance,
            kycStatus=kyc_status,
            freezeStatus=freeze_status,
            decimals=self.decimals,
            )

        if self.token_id:
            proto.tokenId.CopyFrom(self.token_id._to_proto())

        if self.automatic_association is not None:
            proto.automatic_association = self.automatic_association

        return proto