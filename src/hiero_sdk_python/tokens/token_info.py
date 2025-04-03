from dataclasses import dataclass, fields, field
from typing import get_origin, get_args, Union

from hiero_sdk_python import TokenId, AccountId, PublicKey
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.hapi.services.duration_pb2 import Duration
from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenInfo as proto_TokenInfo
from hiero_sdk_python.tokens.token_type import TokenType


def validate_optional_type(value, expected_type):
    if value is None:
        return True
    # For Union[SomeType], check if value matches the unwrapped type
    if get_origin(expected_type) is not None and get_origin(expected_type) is Union:
        # Get the actual type inside Union
        inner_type = get_args(expected_type)[0]
        return type(value) is inner_type

    # For non-Union types, do standard type checking
    return type(value) is expected_type


class TokenInfo:
    # tokenId: TokenId
    # name: str
    # symbol: str
    # decimals: int  # uint32
    # totalSupply: int  # uint64
    # treasury: AccountId
    # # custom_fees: List[CustomFee]
    # isDeleted: bool
    # memo: str
    # # tokenType: TokenType
    # # supplyType: TokenSupplyType = TokenSupplyType.NONE
    # maxSupply: int  # int64
    # ledger_id: bytes

    def __init__(self, tokenId: TokenId, name: str, symbol: str, decimals: int, totalSupply: int, treasury: AccountId, isDeleted: bool, memo: str, tokenType: TokenType, maxSupply: int, ledger_id: bytes):
        self.tokenId = tokenId
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.totalSupply = totalSupply
        self.treasury = treasury
        self.isDeleted = isDeleted
        self.memo = memo
        self.tokenType = tokenType
        self.maxSupply = maxSupply
        self.ledger_id = ledger_id

        self.adminKey = None
        self.kycKey = None
        self.freezeKey = None
        self.wipeKey = None
        self.supplyKey = None
        self.fee_schedule_key = None
        self.defaultFreezeStatus = TokenFreezeStatus.FREEZE_NOT_APPLICABLE
        self.defaultKycStatus = TokenKycStatus.KYC_NOT_APPLICABLE
        self.autoRenewAccount = None
        self.autoRenewPeriod = None
        self.expiry = None
        self.pause_key = None
        self.pause_status = TokenPauseStatus.PAUSE_NOT_APPLICABLE

    def set_admin_key(self, adminKey: PublicKey):
        self.adminKey = adminKey

    def set_kycKey(self, kycKey: PublicKey):
        self.kycKey = kycKey

    def set_freezeKey(self, freezeKey: PublicKey):
        self.freezeKey = freezeKey

    def set_wipeKey(self, wipeKey: PublicKey):
        self.wipeKey = wipeKey

    def set_supplyKey(self, supplyKey: PublicKey):
        self.supplyKey = supplyKey

    def set_fee_schedule_key(self, fee_schedule_key: PublicKey):
        self.fee_schedule_key = fee_schedule_key

    def set_default_freeze_status(self, freezeStatus: TokenFreezeStatus):
        self.defaultFreezeStatus = freezeStatus

    def set_default_kyc_status(self, kycStatus: TokenKycStatus):
        self.defaultKycStatus = kycStatus

    def set_auto_renew_account(self, autoRenewAccount: AccountId):
        self.autoRenenewAccount = autoRenewAccount

    def set_auto_renew_period(self, autoRenewPeriod: Duration):
        self.autoRenewPeriod = autoRenewPeriod

    def set_expiry(self, expiry: Timestamp):
        self.expiry = expiry

    def set_pause_key(self, pauseKey: PublicKey):
        self.pause_key = pauseKey

    def set_pause_status(self, pauseStatus: TokenPauseStatus):
        self.pause_status = pauseStatus


    @classmethod
    def from_proto(cls, proto_obj: proto_TokenInfo) -> proto_TokenInfo:
        tokenInfoObject = TokenInfo(
           tokenId=TokenId.from_proto(proto_obj.tokenId),
           name=proto_obj.name,
           symbol=proto_obj.symbol,
           decimals=proto_obj.decimals,
           totalSupply=proto_obj.totalSupply,
           treasury=AccountId.from_proto(proto_obj.treasury),
           isDeleted=proto_obj.deleted,
           memo=proto_obj.memo,
           tokenType=proto_obj.tokenType,
           maxSupply=proto_obj.maxSupply,
           ledger_id=proto_obj.ledger_id,
        )
        tokenInfoObject.set_admin_key(PublicKey.from_proto(proto_obj.adminKey))
        tokenInfoObject.set_kycKey(PublicKey.from_proto(proto_obj.kycKey))
        tokenInfoObject.set_freezeKey(PublicKey.from_proto(proto_obj.freezeKey))
        tokenInfoObject.set_wipeKey(PublicKey.from_proto(proto_obj.wipeKey))
        tokenInfoObject.set_supplyKey(PublicKey.from_proto(proto_obj.supplyKey))
        tokenInfoObject.set_fee_schedule_key(PublicKey.from_proto(proto_obj.fee_schedule_key))
        tokenInfoObject.set_default_freeze_status(TokenFreezeStatus.from_proto(proto_obj.defaultFreezeStatus))
        tokenInfoObject.set_default_kyc_status(TokenKycStatus.from_proto(proto_obj.defaultKycStatus))
        tokenInfoObject.set_auto_renew_account(AccountId.from_proto(proto_obj.autoRenewAccount))
        # TODO: Duration from_proto
        tokenInfoObject.set_auto_renew_period(Duration(proto_obj.autoRenewPeriod.seconds))
        tokenInfoObject.set_expiry(Timestamp.from_protobuf(proto_obj.expiry))
        tokenInfoObject.set_pause_key(PublicKey.from_proto(proto_obj.pause_key))
        tokenInfoObject.set_pause_status(TokenPauseStatus.from_proto(proto_obj.pause_status))

        return tokenInfoObject

    # TODO: Also uses protobuf class in java, the protobuf I have does not use this
    def to_proto(self) -> proto_TokenInfo:
        return proto_TokenInfo(
                tokenId = self.tokenId.to_proto(),
                name = self.name,
                symbol = self.symbol,
                decimals = self.decimals,
                totalSupply = self.totalSupply,
                treasury = self.treasury.to_proto(),
                adminKey = self.adminKey.to_proto(),
                # TODO: missing stuff here
                # defaultFreezeStatus = self.defaultFreezeStatus.to_proto(),
                deleted=self.isDeleted,
                autoRenewAccount = self.autoRenewAccount.to_proto(),
                autoRenewPeriod = Duration(seconds = self.autoRenewPeriod),
                expiry = self.expiry.to_proto(),
                memo = self.memo,
                tokenType = self.tokenType,
                # TODO: missing stuff
                maxSupply = self.maxSupply,
                # TODO: missing stuff
                ledger_id = self.ledger_id
            )

    # TODO: Java uses fromProtobuf(response.parsefrom(bytes)) may not be possible or necessary here
    @classmethod
    def from_bytes(cls, token_info: bytes):
        pass


    def __str__(self):
        return f"{self.name}({self.tokenId}, {self.name}, {self.symbol}, {self.decimals}, {self.totalSupply}, {self.treasury}, {self.adminKey}, {self.isDeleted}, {self.autoRenewAccount}, {self.autoRenewPeriod}, {self.expiry}, {self.tokenType}, {self.memo}, {self.maxSupply}, {self.ledger_id})"
