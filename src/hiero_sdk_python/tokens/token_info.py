# pylint: disable=C901
# pylint: disable=too-many-arguments
"""
hiero_sdk_python.tokens.token_info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenInfo, a dataclass representing Hedera token metadata (IDs, keys,
statuses, supply details, and timing), with conversion to and from protobuf messages.
"""

import warnings
from dataclasses import dataclass, field, fields, MISSING
from typing import Optional, ClassVar, Dict, Any, Callable

from dataclasses import dataclass, field
from typing import Optional
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.hapi.services import token_get_info_pb2
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python._deprecated import _DeprecatedAliasesMixin

@dataclass(init=False)
class TokenInfo(_DeprecatedAliasesMixin):
    """Data class for basic token details: ID, name, and symbol inheriting deprecated aliases."""
    token_id: Optional[TokenId]      = None
    name:     Optional[str]          = None
    symbol:   Optional[str]          = None
    decimals: Optional[int]          = None
    total_supply: Optional[int]      = None
    treasury: Optional[AccountId]    = None
    is_deleted: Optional[bool]       = None
    memo:      Optional[str]         = None
    token_type: Optional[TokenType]  = None
    max_supply: Optional[int]        = None
    ledger_id: Optional[bytes]       = None
    metadata:  Optional[bytes]       = None

    admin_key: Optional[PublicKey]         = None
    kyc_key: Optional[PublicKey]           = None
    freeze_key: Optional[PublicKey]        = None
    wipe_key: Optional[PublicKey]          = None
    supply_key: Optional[PublicKey]        = None
    metadata_key: Optional[PublicKey]      = None
    fee_schedule_key: Optional[PublicKey]  = None
    default_freeze_status: TokenFreezeStatus = field(
        default_factory=lambda: TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    )    
    default_kyc_status: TokenKycStatus = field(
        default_factory=lambda: TokenKycStatus.KYC_NOT_APPLICABLE
    )
    auto_renew_account: Optional[AccountId]  = None
    auto_renew_period: Optional[Duration]    = None
    expiry: Optional[Timestamp]              = None
    pause_key: Optional[PublicKey]           = None
    pause_status: TokenPauseStatus = field(
        default_factory=lambda: TokenPauseStatus.PAUSE_NOT_APPLICABLE
    )    
    supply_type: SupplyType = field(
        default_factory=lambda: SupplyType.FINITE
    )

    # map legacy camelCase → snake_case
    LEGACY_MAP: ClassVar[Dict[str, str]] = {
        "tokenId":             "token_id",
        "totalSupply":         "total_supply",
        "isDeleted":           "is_deleted",
        "tokenType":           "token_type",
        "maxSupply":           "max_supply",
        "adminKey":            "admin_key",
        "kycKey":              "kyc_key",
        "freezeKey":           "freeze_key",
        "wipeKey":             "wipe_key",
        "supplyKey":           "supply_key",
        "defaultFreezeStatus": "default_freeze_status",
        "defaultKycStatus":    "default_kyc_status",
        "autoRenewAccount":    "auto_renew_account",
        "autoRenewPeriod":     "auto_renew_period",
        "pauseStatus":         "pause_status",
        "supplyType":          "supply_type",
    } 

    def __init__(self, **kwargs: Any) -> None:
        # 1) Translate deprecated camelCase names → snake_case, with warnings
        for legacy, snake in self.LEGACY_MAP.items():
            if legacy in kwargs:
                warnings.warn(
                    f"TokenInfo({legacy}=...) is deprecated; use {snake}",
                    FutureWarning,
                    stacklevel=2,
                )
                # only set snake-case if not already provided
                if snake not in kwargs:
                    kwargs[snake] = kwargs.pop(legacy)
                else:
                    kwargs.pop(legacy)

        # 2) for *every* field, pick either the passed‑in value or the field’s own default/default_factory
        for f in fields(self):
            if f.name in kwargs:
                value = kwargs[f.name]
            else:
                # dataclass default_factory lives in f.default_factory, default in f.default
                if getattr(f, "default_factory", MISSING) is not MISSING:
                    value = f.default_factory()
                elif f.default is not MISSING:
                    value = f.default
                else:
                    value = None
            setattr(self, f.name, value)

    # === setter methods ===
    def set_admin_key(self, admin_key: PublicKey) -> None:
        """Set the admin key."""
        self.admin_key = admin_key
    # alias for backwards compatibility
    set_adminKey = set_admin_key

    def set_kyc_key(self, kyc_key: PublicKey) -> None:
        """Set the KYC key."""
        self.kyc_key = kyc_key
    # alias for backwards compatibility
    set_kycKey = set_kyc_key

    def set_freeze_key(self, freeze_key: PublicKey) -> None:
        """Set the freeze key."""
        self.freeze_key = freeze_key
    # alias for backwards compatibility
    set_freezeKey = set_freeze_key

    def set_wipe_key(self, wipe_key: PublicKey) -> None:
        """Set the wipe key."""
        self.wipe_key = wipe_key
    # alias for backwards compatibility
    set_wipeKey = set_wipe_key

    def set_supply_key(self, supply_key: PublicKey) -> None:
        """Set the supply key."""
        self.supply_key = supply_key
    # alias for backwards compatibility
    set_supplyKey = set_supply_key

    def set_metadata_key(self, metadata_key: PublicKey) -> None:
        """Set the metadata key."""
        self.metadata_key = metadata_key

    def set_fee_schedule_key(self, fee_schedule_key: PublicKey):
        """Set the fee schedule key."""
        self.fee_schedule_key = fee_schedule_key

    def set_default_freeze_status(self, freeze_status: TokenFreezeStatus) -> None:
        """Set the default freeze status."""
        self.default_freeze_status = freeze_status
    # alias for backwards compatibility
    set_defaultFreezeStatus = set_default_freeze_status

    def set_default_kyc_status(self, kyc_status: TokenKycStatus) -> None:
        """Set the default KYC status."""
        self.default_kyc_status = kyc_status
    # alias for backwards compatibility
    set_defaultKycStatus = set_default_kyc_status

    def set_auto_renew_account(self, account: AccountId) -> None:
        """Set the auto-renew account."""
        self.auto_renew_account = account
    # alias for backwards compatibility
    set_autoRenewAccount = set_auto_renew_account

    def set_auto_renew_period(self, period: Duration) -> None:
        """Set the auto-renew period."""
        self.auto_renew_period = period
    # alias for backwards compatibility
    set_autoRenewPeriod = set_auto_renew_period

    def set_expiry(self, expiry: Timestamp) -> None:
        """Set the token expiry."""
        self.expiry = expiry

    def set_pause_key(self, pause_key: PublicKey) -> None:
        """Set the pause key."""
        self.pause_key = pause_key

    def set_pause_status(self, pause_status: TokenPauseStatus) -> None:
        """Set the pause status."""
        self.pause_status = pause_status
    # alias for backwards compatibility
    set_pauseStatus = set_pause_status

    def set_supply_type(self, supply_type: SupplyType | int) -> None:
        """Set the supply type."""
        self.supply_type = (
            supply_type
            if isinstance(supply_type, SupplyType)
            else SupplyType(supply_type)
        )
    # alias for backwards compatibility
    set_supplyType = set_supply_type

    def set_metadata(self, metadata: bytes) -> None:
        """Set the token metadata."""
        self.metadata = metadata

    @classmethod
    def _from_proto(cls, proto_obj: token_get_info_pb2.TokenInfo) -> "TokenInfo":
        """
        Creates a TokenInfo instance from a protobuf TokenInfo object.
        :param proto_obj: The token_get_info_pb2.TokenInfo object.
        :return: An instance of TokenInfo.
        """
        tokenInfoObject = TokenInfo(
            token_id=TokenId._from_proto(proto_obj.tokenId),
            name=proto_obj.name,
            symbol=proto_obj.symbol,
            decimals=proto_obj.decimals,
            total_supply=proto_obj.totalSupply,
            treasury=AccountId._from_proto(proto_obj.treasury),
            is_deleted=proto_obj.deleted,
            memo=proto_obj.memo,
            token_type=TokenType(proto_obj.tokenType),
            max_supply=proto_obj.maxSupply,
            ledger_id=proto_obj.ledger_id,
            metadata=proto_obj.metadata,
        )
        if proto_obj.adminKey.WhichOneof("key"):
            admin_key = PublicKey._from_proto(proto_obj.adminKey)
            tokenInfoObject.set_admin_key(admin_key)

        if proto_obj.kycKey.WhichOneof("key"):
            kyc_key = PublicKey._from_proto(proto_obj.kycKey)
            tokenInfoObject.set_kyc_key(kyc_key)

        if proto_obj.freezeKey.WhichOneof("key"):
            freeze_key = PublicKey._from_proto(proto_obj.freezeKey)
            tokenInfoObject.set_freeze_key(freeze_key)

        if proto_obj.wipeKey.WhichOneof("key"):
            wipe_key = PublicKey._from_proto(proto_obj.wipeKey)
            tokenInfoObject.set_wipe_key(wipe_key)

        if proto_obj.supplyKey.WhichOneof("key"):
            supply_key = PublicKey._from_proto(proto_obj.supplyKey)
            tokenInfoObject.set_supply_key(supply_key)

        if proto_obj.metadata_key.WhichOneof("key"):
            metadata_key = PublicKey._from_proto(proto_obj.metadata_key)
            tokenInfoObject.set_metadata_key(metadata_key)

        if proto_obj.fee_schedule_key.WhichOneof("key"):
            fee_schedule_key = PublicKey._from_proto(proto_obj.fee_schedule_key)
            tokenInfoObject.set_fee_schedule_key(fee_schedule_key)

        if proto_obj.defaultFreezeStatus is not None:
            freeze_status = TokenFreezeStatus._from_proto(proto_obj.defaultFreezeStatus)
            tokenInfoObject.set_default_freeze_status(freeze_status)

        if proto_obj.defaultKycStatus is not None:
            kyc_status = TokenKycStatus._from_proto(proto_obj.defaultKycStatus)
            tokenInfoObject.set_default_kyc_status(kyc_status)

        if proto_obj.autoRenewAccount is not None:
            auto_renew_account = AccountId._from_proto(proto_obj.autoRenewAccount)
            tokenInfoObject.set_auto_renew_account(auto_renew_account)

        if proto_obj.autoRenewPeriod is not None:
            auto_renew_period = Duration._from_proto(proto_obj.autoRenewPeriod)
            tokenInfoObject.set_auto_renew_period(auto_renew_period)

        if proto_obj.expiry is not None:
            expiry_timestamp = Timestamp._from_protobuf(proto_obj.expiry)
            tokenInfoObject.set_expiry(expiry_timestamp)

        if proto_obj.pause_key.WhichOneof("key"):
            pause_key_obj = PublicKey._from_proto(proto_obj.pause_key)
            tokenInfoObject.set_pause_key(pause_key_obj)

        if proto_obj.pause_status is not None:
            pause_status = TokenPauseStatus._from_proto(proto_obj.pause_status)
            tokenInfoObject.set_pause_status(pause_status)

        if proto_obj.supplyType is not None:
            supply_type = SupplyType(proto_obj.supplyType)
            tokenInfoObject.set_supply_type(supply_type)
        return tokenInfoObject

    def _to_proto(self) -> token_get_info_pb2.TokenInfo:
        """
        Converts the TokenInfo instance to a protobuf TokenInfo object.
        :return: A token_get_info_pb2.TokenInfo object.
        """
        proto = token_get_info_pb2.TokenInfo(
            tokenId=self.tokenId._to_proto(),
            name=self.name,
            symbol=self.symbol,
            decimals=self.decimals,
            totalSupply=self.total_supply,
            treasury=self.treasury._to_proto(),
            deleted=self.is_deleted,
            memo=self.memo,
            tokenType=self.token_type.value,
            supplyType=self.supply_type.value,
            maxSupply=self.max_supply,
            expiry=self.expiry._to_protobuf(),
            ledger_id=self.ledger_id,
            metadata=self.metadata
        )
        if self.admin_key:
            proto.adminKey.CopyFrom(self.admin_key._to_proto())
        if self.kyc_key:
            proto.kycKey.CopyFrom(self.kyc_key._to_proto())
        if self.freeze_key:
            proto.freezeKey.CopyFrom(self.freeze_key._to_proto())
        if self.wipe_key:
            proto.wipeKey.CopyFrom(self.wipe_key._to_proto())
        if self.supply_key:
            proto.supplyKey.CopyFrom(self.supply_key._to_proto())
        if self.metadata_key:
            proto.metadata_key.CopyFrom(self.metadata_key._to_proto())
        if self.fee_schedule_key:
            proto.fee_schedule_key.CopyFrom(self.fee_schedule_key._to_proto())
        if self.default_freeze_status:
            proto.defaultFreezeStatus = self.default_freeze_status.value
        if self.default_kyc_status:
            proto.defaultKycStatus = self.default_kyc_status.value
        if self.auto_renew_account:
            proto.autoRenewAccount.CopyFrom(self.auto_renew_account._to_proto())
        if self.auto_renew_period:
            proto.autoRenewPeriod.CopyFrom(self.auto_renew_period._to_proto())
        if self.expiry:
            proto.expiry.CopyFrom(self.expiry._to_protobuf())
        if self.pause_key:
            proto.pause_key.CopyFrom(self.pause_key._to_proto())
        if self.pause_status:
            proto.pause_status = self.pause_status.value
        return proto

    def __str__(self) -> str:
        parts = [
            f"token_id={self.token_id}",
            f"name={self.name!r}",
            f"symbol={self.symbol!r}",
            f"decimals={self.decimals}",
            f"total_supply={self.total_supply}",
            f"treasury={self.treasury}",
            f"is_deleted={self.is_deleted}",
            f"memo={self.memo!r}",
            f"token_type={self.token_type}",
            f"max_supply={self.max_supply}",
            f"ledger_id={self.ledger_id!r}",
            f"metadata={self.metadata!r}",
        ]
        return f"TokenInfo({', '.join(parts)})"

