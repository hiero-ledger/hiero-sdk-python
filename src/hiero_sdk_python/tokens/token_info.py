# pylint: disable=C901
# pylint: disable=too-many-arguments

from dataclasses import dataclass
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenInfo as proto_TokenInfo
from hiero_sdk_python.tokens.token_type import TokenType

@dataclass
class TokenInfo:
    tokenId: TokenId = None
    name: str = None
    symbol: str = None
    decimals: int = None
    totalSupply: int = None
    treasury: AccountId = None
    isDeleted: bool = None
    memo: str = None
    tokenType: TokenType = None
    maxSupply: int = None
    ledger_id: bytes = None
    metadata: bytes = None

    adminKey = None
    kycKey = None
    freezeKey = None
    wipeKey = None
    supplyKey = None
    metadata_key = None
    fee_schedule_key = None
    defaultFreezeStatus = TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    defaultKycStatus = TokenKycStatus.KYC_NOT_APPLICABLE
    autoRenewAccount = None
    autoRenewPeriod = None
    expiry = None
    pause_key = None
    pause_status = TokenPauseStatus.PAUSE_NOT_APPLICABLE
    supplyType = SupplyType.FINITE

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

    def set_metadata_key(self, metadata_key: PublicKey):
        self.metadata_key = metadata_key

    def set_fee_schedule_key(self, fee_schedule_key: PublicKey):
        self.fee_schedule_key = fee_schedule_key

    def set_default_freeze_status(self, freezeStatus: TokenFreezeStatus):
        self.defaultFreezeStatus = freezeStatus

    def set_default_kyc_status(self, kycStatus: TokenKycStatus):
        self.defaultKycStatus = kycStatus

    def set_auto_renew_account(self, autoRenewAccount: AccountId):
        self.autoRenewAccount = autoRenewAccount

    def set_auto_renew_period(self, autoRenewPeriod: Duration):
        self.autoRenewPeriod = autoRenewPeriod

    def set_expiry(self, expiry: Timestamp):
        self.expiry = expiry

    def set_pause_key(self, pause_key: PublicKey):
        self.pause_key = pause_key

    def set_pause_status(self, pauseStatus: TokenPauseStatus):
        self.pause_status = pauseStatus

    def set_supply_type(self, supplyType: SupplyType | int):
        self.supplyType = supplyType

    def set_metadata(self, metadata: bytes):
        self.metadata = metadata

    @classmethod
    def _from_proto(cls, proto_obj: proto_TokenInfo) -> "TokenInfo":
        tokenInfoObject = TokenInfo(
            tokenId=TokenId._from_proto(proto_obj.tokenId),
            name=proto_obj.name,
            symbol=proto_obj.symbol,
            decimals=proto_obj.decimals,
            totalSupply=proto_obj.totalSupply,
            treasury=AccountId._from_proto(proto_obj.treasury),
            isDeleted=proto_obj.deleted,
            memo=proto_obj.memo,
            tokenType=TokenType(proto_obj.tokenType),
            maxSupply=proto_obj.maxSupply,
            ledger_id=proto_obj.ledger_id,
            metadata=proto_obj.metadata
        )
        if proto_obj.adminKey.WhichOneof("key"):
            tokenInfoObject.set_admin_key(PublicKey._from_proto(proto_obj.adminKey))
        if proto_obj.kycKey.WhichOneof("key"):
            tokenInfoObject.set_kycKey(PublicKey._from_proto(proto_obj.kycKey))
        if proto_obj.freezeKey.WhichOneof("key"):
            tokenInfoObject.set_freezeKey(PublicKey._from_proto(proto_obj.freezeKey))
        if proto_obj.wipeKey.WhichOneof("key"):
            tokenInfoObject.set_wipeKey(PublicKey._from_proto(proto_obj.wipeKey))
        if proto_obj.supplyKey.WhichOneof("key"):
            tokenInfoObject.set_supplyKey(PublicKey._from_proto(proto_obj.supplyKey))
        if proto_obj.metadata_key.WhichOneof("key"):
            tokenInfoObject.set_metadata_key(PublicKey._from_proto(proto_obj.metadata_key))
        if proto_obj.fee_schedule_key.WhichOneof("key"):
            tokenInfoObject.set_fee_schedule_key(PublicKey._from_proto(proto_obj.fee_schedule_key))
        if proto_obj.defaultFreezeStatus:
            tokenInfoObject.set_default_freeze_status(TokenFreezeStatus._from_proto(proto_obj.defaultFreezeStatus))
        if proto_obj.defaultKycStatus:
            tokenInfoObject.set_default_kyc_status(TokenKycStatus._from_proto(proto_obj.defaultKycStatus))
        if proto_obj.autoRenewAccount:
            tokenInfoObject.set_auto_renew_account(AccountId._from_proto(proto_obj.autoRenewAccount))
        if proto_obj.autoRenewPeriod:
            tokenInfoObject.set_auto_renew_period(Duration._from_proto(proto_obj.autoRenewPeriod))
        if proto_obj.expiry:
            tokenInfoObject.set_expiry(Timestamp._from_protobuf(proto_obj.expiry))
        if proto_obj.pause_key.WhichOneof("key"):
            tokenInfoObject.set_pause_key(PublicKey._from_proto(proto_obj.pause_key))
        if proto_obj.pause_status:
            tokenInfoObject.set_pause_status(TokenPauseStatus._from_proto(proto_obj.pause_status))
        if proto_obj.supplyType is not None:
            tokenInfoObject.set_supply_type(SupplyType(proto_obj.supplyType))


        return tokenInfoObject

    def _to_proto(self) -> proto_TokenInfo:
        proto = proto_TokenInfo(
            tokenId=self.tokenId._to_proto(),
            name=self.name,
            symbol=self.symbol,
            decimals=self.decimals,
            totalSupply=self.totalSupply,
            treasury=self.treasury._to_proto(),
            deleted=self.isDeleted,
            memo=self.memo,
            tokenType=self.tokenType.value,
            supplyType=self.supplyType.value,
            maxSupply=self.maxSupply,
            expiry = self.expiry._to_protobuf(),
            ledger_id=self.ledger_id,
            metadata=self.metadata
        )
        if self.adminKey:
            proto.adminKey.CopyFrom(self.adminKey._to_proto())
        if self.kycKey:
            proto.kycKey.CopyFrom(self.kycKey._to_proto())
        if self.freezeKey:
            proto.freezeKey.CopyFrom(self.freezeKey._to_proto())
        if self.wipeKey:
            proto.wipeKey.CopyFrom(self.wipeKey._to_proto())
        if self.supplyKey:
            proto.supplyKey.CopyFrom(self.supplyKey._to_proto())
        if self.metadata_key:
            proto.metadata_key.CopyFrom(self.metadata_key._to_proto())
        if self.fee_schedule_key:
            proto.fee_schedule_key.CopyFrom(self.fee_schedule_key._to_proto())
        if self.defaultFreezeStatus:
            proto.defaultFreezeStatus = self.defaultFreezeStatus.value
        if self.defaultKycStatus:
            proto.defaultKycStatus = self.defaultKycStatus.value
        if self.autoRenewAccount:
            proto.autoRenewAccount.CopyFrom(self.autoRenewAccount._to_proto())
        if self.autoRenewPeriod:
            proto.autoRenewPeriod.CopyFrom(self.autoRenewPeriod._to_proto())
        if self.expiry:
            proto.expiry.CopyFrom(self.expiry._to_protobuf())
        if self.pause_key:
            proto.pause_key.CopyFrom(self.pause_key._to_proto())
        if self.pause_status:
            proto.pause_status = self.pause_status.value

        return proto

    def __str__(self):
        return (f"TokenInfo(tokenId={self.tokenId}, name={self.name}, symbol={self.symbol}, "
                f"decimals={self.decimals}, totalSupply={self.totalSupply}, treasury={self.treasury}, "
                f"isDeleted={self.isDeleted}, memo={self.memo}, tokenType={self.tokenType}, "
                f"maxSupply={self.maxSupply}, ledger_id={self.ledger_id}, metadata={self.metadata})")