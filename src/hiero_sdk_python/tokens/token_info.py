# pylint: skip-file

from hiero_sdk_python import TokenId, AccountId, PublicKey, Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenInfo as proto_TokenInfo
from hiero_sdk_python.tokens.token_type import TokenType

class TokenInfo:
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
        self.supplyType = SupplyType.FINITE

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
        self.autoRenewAccount = autoRenewAccount

    def set_auto_renew_period(self, autoRenewPeriod: Duration):
        self.autoRenewPeriod = autoRenewPeriod

    def set_expiry(self, expiry: Timestamp):
        self.expiry = expiry

    def set_pause_key(self, pauseKey: PublicKey):
        self.pause_key = pauseKey

    def set_pause_status(self, pauseStatus: TokenPauseStatus):
        self.pause_status = pauseStatus

    def set_supply_type(self, supplyType: SupplyType | int):
        self.supplyType = supplyType

    @classmethod
    def _from_proto(cls, proto_obj: proto_TokenInfo) -> "TokenInfo":
        tokenInfoObject = TokenInfo(
            tokenId=TokenId.from_proto(proto_obj.tokenId),
            name=proto_obj.name,
            symbol=proto_obj.symbol,
            decimals=proto_obj.decimals,
            totalSupply=proto_obj.totalSupply,
            treasury=AccountId.from_proto(proto_obj.treasury),
            isDeleted=proto_obj.deleted,
            memo=proto_obj.memo,
            tokenType=TokenType(proto_obj.tokenType),
            maxSupply=proto_obj.maxSupply,
            ledger_id=proto_obj.ledger_id
        )
        if proto_obj.adminKey.ECDSA_secp256k1 or proto_obj.adminKey.ed25519:
            tokenInfoObject.set_admin_key(PublicKey.from_proto(proto_obj.adminKey))
        if proto_obj.kycKey.ECDSA_secp256k1 or proto_obj.kycKey.ed25519:
            tokenInfoObject.set_kycKey(PublicKey.from_proto(proto_obj.kycKey))
        if proto_obj.freezeKey.ECDSA_secp256k1 or proto_obj.freezeKey.ed25519:
            tokenInfoObject.set_freezeKey(PublicKey.from_proto(proto_obj.freezeKey))
        if proto_obj.wipeKey.ECDSA_secp256k1 or proto_obj.wipeKey.ed25519:
            tokenInfoObject.set_wipeKey(PublicKey.from_proto(proto_obj.wipeKey))
        if proto_obj.supplyKey.ECDSA_secp256k1 or proto_obj.supplyKey.ed25519:
            tokenInfoObject.set_supplyKey(PublicKey.from_proto(proto_obj.supplyKey))
        if proto_obj.fee_schedule_key.ECDSA_secp256k1 or proto_obj.fee_schedule_key.ed25519:
            tokenInfoObject.set_fee_schedule_key(PublicKey.from_proto(proto_obj.fee_schedule_key))
        if proto_obj.defaultFreezeStatus:
            tokenInfoObject.set_default_freeze_status(TokenFreezeStatus.from_proto(proto_obj.defaultFreezeStatus))
        if proto_obj.defaultKycStatus:
            tokenInfoObject.set_default_kyc_status(TokenKycStatus.from_proto(proto_obj.defaultKycStatus))
        if proto_obj.autoRenewAccount:
            tokenInfoObject.set_auto_renew_account(AccountId.from_proto(proto_obj.autoRenewAccount))
        if proto_obj.autoRenewPeriod:
            tokenInfoObject.set_auto_renew_period(Duration.from_proto(proto_obj.autoRenewPeriod))
        if proto_obj.expiry:
            tokenInfoObject.set_expiry(Timestamp.from_protobuf(proto_obj.expiry))
        if proto_obj.pause_key.ECDSA_secp256k1 or proto_obj.pause_key.ed25519:
            tokenInfoObject.set_pause_key(PublicKey.from_proto(proto_obj.pause_key))
        if proto_obj.pause_status:
            tokenInfoObject.set_pause_status(TokenPauseStatus.from_proto(proto_obj.pause_status))
        if proto_obj.supplyType is not None:
            tokenInfoObject.set_supply_type(SupplyType(proto_obj.supplyType))


        return tokenInfoObject

    def _to_proto(self) -> proto_TokenInfo:
        proto = proto_TokenInfo(
            tokenId=self.tokenId.to_proto(),
            name=self.name,
            symbol=self.symbol,
            decimals=self.decimals,
            totalSupply=self.totalSupply,
            treasury=self.treasury.to_proto(),
            deleted=self.isDeleted,
            memo=self.memo,
            tokenType=self.tokenType.value,
            supplyType=self.supplyType.value,
            maxSupply=self.maxSupply,
            expiry = self.expiry.to_protobuf(),
            ledger_id=self.ledger_id
        )
        if self.adminKey:
            proto.adminKey.CopyFrom(self.adminKey.to_proto())
        if self.kycKey:
            proto.kycKey.CopyFrom(self.kycKey.to_proto())
        if self.freezeKey:
            proto.freezeKey.CopyFrom(self.freezeKey.to_proto())
        if self.wipeKey:
            proto.wipeKey.CopyFrom(self.wipeKey.to_proto())
        if self.supplyKey:
            proto.supplyKey.CopyFrom(self.supplyKey.to_proto())
        if self.fee_schedule_key:
            proto.fee_schedule_key.CopyFrom(self.fee_schedule_key.to_proto())
        if self.defaultFreezeStatus:
            proto.defaultFreezeStatus = self.defaultFreezeStatus.value
        if self.defaultKycStatus:
            proto.defaultKycStatus = self.defaultKycStatus.value
        if self.autoRenewAccount:
            proto.autoRenewAccount.CopyFrom(self.autoRenewAccount.to_proto())
        if self.autoRenewPeriod:
            proto.autoRenewPeriod.CopyFrom(self.autoRenewPeriod.to_proto())
        if self.expiry:
            proto.expiry.CopyFrom(self.expiry.to_protobuf())
        if self.pause_key:
            proto.pause_key.CopyFrom(self.pause_key.to_proto())
        if self.pause_status:
            proto.pause_status = self.pause_status.value

        return proto

    def __str__(self):
        return (f"TokenInfo(tokenId={self.tokenId}, name={self.name}, symbol={self.symbol}, "
                f"decimals={self.decimals}, totalSupply={self.totalSupply}, treasury={self.treasury}, "
                f"isDeleted={self.isDeleted}, memo={self.memo}, tokenType={self.tokenType}, "
                f"maxSupply={self.maxSupply}, ledger_id={self.ledger_id})")