# pylint: disable=C901
# pylint: disable=too-many-arguments
"""
hiero_sdk_python.tokens.token_info.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides TokenInfo, a dataclass representing Hedera token metadata (IDs, keys,
statuses, supply details, and timing), with conversion to and from protobuf messages.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List

from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.hapi.services import token_get_info_pb2 as hapi_pb


@dataclass
class TokenInfo:
    """Data class for basic token details: ID, name, and symbol."""
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
    custom_fees: List[Any]           = field(default_factory=list)

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


    # === setter methods ===
    def set_admin_key(self, admin_key: PublicKey) -> "TokenInfo":
        """Set the admin key."""
        self.admin_key = admin_key
        return self


    def set_kyc_key(self, kyc_key: PublicKey) -> "TokenInfo":
        """Set the KYC key."""
        self.kyc_key = kyc_key
        return self


    def set_freeze_key(self, freeze_key: PublicKey) -> "TokenInfo":
        """Set the freeze key."""
        self.freeze_key = freeze_key
        return self


    def set_wipe_key(self, wipe_key: PublicKey) -> "TokenInfo":
        """Set the wipe key."""
        self.wipe_key = wipe_key
        return self


    def set_supply_key(self, supply_key: PublicKey) -> "TokenInfo":
        """Set the supply key."""
        self.supply_key = supply_key
        return self


    def set_metadata_key(self, metadata_key: PublicKey) -> "TokenInfo":
        """Set the metadata key."""
        self.metadata_key = metadata_key
        return self

    def set_fee_schedule_key(self, fee_schedule_key: PublicKey) -> "TokenInfo":
        """Set the fee schedule key."""
        self.fee_schedule_key = fee_schedule_key
        return self

    def set_default_freeze_status(self, freeze_status: TokenFreezeStatus) -> "TokenInfo":
        """Set the default freeze status."""
        self.default_freeze_status = freeze_status
        return self


    def set_default_kyc_status(self, kyc_status: TokenKycStatus) -> "TokenInfo":
        """Set the default KYC status."""
        self.default_kyc_status = kyc_status
        return self


    def set_auto_renew_account(self, account: AccountId) -> "TokenInfo":
        """Set the auto-renew account."""
        self.auto_renew_account = account
        return self


    def set_auto_renew_period(self, period: Duration) -> "TokenInfo":
        """Set the auto-renew period."""
        self.auto_renew_period = period
        return self


    def set_expiry(self, expiry: Timestamp) -> "TokenInfo":
        """Set the token expiry."""
        self.expiry = expiry
        return self

    def set_pause_key(self, pause_key: PublicKey) -> "TokenInfo":
        """Set the pause key."""
        self.pause_key = pause_key
        return self

    def set_pause_status(self, pause_status: TokenPauseStatus) -> "TokenInfo":
        """Set the pause status."""
        self.pause_status = pause_status
        return self


    def set_supply_type(self, supply_type: SupplyType | int) -> "TokenInfo":
        """Set the supply type."""
        self.supply_type = (
            supply_type
            if isinstance(supply_type, SupplyType)
            else SupplyType(supply_type)
        )
        return self


    def set_metadata(self, metadata: bytes) -> "TokenInfo":
        """Set the token metadata."""
        self.metadata = metadata
        return self

    def set_custom_fees(self, custom_fees: List[Any]) -> "TokenInfo":
        """Set the custom fees."""
        self.custom_fees = custom_fees
        return self


    # === helpers ===

    

   
    @staticmethod
    def _get(proto_obj, *names):
        """Get the first present attribute from a list of possible names (camelCase/snake_case)."""
        for n in names:
            if hasattr(proto_obj, n):
                return getattr(proto_obj, n)
        return None

    # === conversions ===
    @classmethod
    def _from_proto(cls, proto_obj: hapi_pb.TokenInfo) -> "TokenInfo":
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

        tokenInfoObject.set_custom_fees(cls._parse_custom_fees(proto_obj))

        key_sources = [
            (("adminKey",),                         "set_admin_key"),
            (("kycKey",),                           "set_kyc_key"),
            (("freezeKey",),                        "set_freeze_key"),
            (("wipeKey",),                          "set_wipe_key"),
            (("supplyKey",),                        "set_supply_key"),
            (("metadataKey", "metadata_key"),       "set_metadata_key"),
            (("feeScheduleKey", "fee_schedule_key"),"set_fee_schedule_key"),
            (("pauseKey", "pause_key"),             "set_pause_key"),
        ]
        for names, setter in key_sources:
            key_msg = cls._get(proto_obj, *names)
            cls._copy_key_if_present(tokenInfoObject, setter, key_msg)

        conv_map = [
            (("defaultFreezeStatus",), tokenInfoObject.set_default_freeze_status, TokenFreezeStatus._from_proto),
            (("defaultKycStatus",),    tokenInfoObject.set_default_kyc_status,    TokenKycStatus._from_proto),
            (("autoRenewAccount",),    tokenInfoObject.set_auto_renew_account,    AccountId._from_proto),
            (("autoRenewPeriod",),     tokenInfoObject.set_auto_renew_period,     Duration._from_proto),
            (("expiry",),              tokenInfoObject.set_expiry,                Timestamp._from_protobuf),
            (("pauseStatus", "pause_status"), tokenInfoObject.set_pause_status,   TokenPauseStatus._from_proto),
            (("supplyType",),          tokenInfoObject.set_supply_type,           SupplyType),
        ]
        for names, setter, conv in conv_map:
            val = cls._get(proto_obj, *names)
            if val is not None:
                setter(conv(val))

        return tokenInfoObject

    # === helpers ===
    @staticmethod
    def _copy_key_if_present(dst: "TokenInfo", setter: str, key_msg) -> None:
        # In proto3, keys are a oneof; check presence via WhichOneof
        if key_msg is not None and hasattr(key_msg, "WhichOneof") and key_msg.WhichOneof("key"):
            getattr(dst, setter)(PublicKey._from_proto(key_msg))

    @staticmethod
    def _parse_custom_fees(proto_obj) -> List[CustomFee]:
        out: List[CustomFee] = []
        for fee_proto in getattr(proto_obj, "custom_fees", []):  # snake_case matches your generated proto
            if fee_proto.HasField("fixed_fee"):
                out.append(CustomFixedFee._from_proto(fee_proto))
            elif fee_proto.HasField("fractional_fee"):
                out.append(CustomFractionalFee._from_proto(fee_proto))
            elif fee_proto.HasField("royalty_fee"):
                out.append(CustomRoyaltyFee._from_proto(fee_proto))
        return out

    @staticmethod
    def _copy_msg_to_proto(src_obj, dst_proto, src_attr: str, dst_field: str) -> None:
        """Copy a submessage if present, using _to_proto or _to_protobuf as available."""
        val = getattr(src_obj, src_attr)
        if not val:
            return
        to_fn = getattr(val, "_to_proto", None) or getattr(val, "_to_protobuf", None)
        if to_fn is None:
            raise AttributeError(f"{type(val).__name__} has neither _to_proto nor _to_protobuf")
        getattr(dst_proto, dst_field).CopyFrom(to_fn())

    @staticmethod
    def _set_bool(dst_proto, field_name: str, value: Optional[bool], default: bool = False) -> None:
        """Assign a boolean, using default when value is None."""
        setattr(dst_proto, field_name, default if value is None else bool(value))

    @staticmethod
    def _set_enum(dst_proto, field_name: str, enum_val) -> None:
        """Assign an enum value or 0 if None."""
        setattr(dst_proto, field_name, (enum_val.value if enum_val is not None else 0))

    @staticmethod
    def _append_custom_fees(dst_proto, fees: Optional[List[Any]]) -> None:
        """Append serialized custom fees if any."""
        if fees:
            dst_proto.custom_fees.extend(fee._to_proto() for fee in fees)

    def _to_proto(self) -> hapi_pb.TokenInfo:
        """
        Converts the TokenInfo instance to a protobuf TokenInfo object.
        """
        proto: hapi_pb.TokenInfo = hapi_pb.TokenInfo(
            tokenId=self.token_id._to_proto() if self.token_id else None,
            name=self.name,
            symbol=self.symbol,
            decimals=self.decimals,
            totalSupply=self.total_supply,
            treasury=self.treasury._to_proto() if self.treasury else None,
            memo=self.memo,
            tokenType=(self.token_type.value if self.token_type else None),
            supplyType=(self.supply_type.value if self.supply_type else None),
            maxSupply=self.max_supply,
            ledger_id=self.ledger_id,
            metadata=self.metadata,
        )

        # Custom fees
        self._append_custom_fees(proto, self.custom_fees)

        msg_fields = [
            ("admin_key",          "adminKey"),
            ("kyc_key",            "kycKey"),
            ("freeze_key",         "freezeKey"),
            ("wipe_key",           "wipeKey"),
            ("supply_key",         "supplyKey"),
            ("metadata_key",       "metadata_key"),
            ("fee_schedule_key",   "fee_schedule_key"),
            ("pause_key",          "pause_key"),
            ("auto_renew_account", "autoRenewAccount"),
            ("auto_renew_period",  "autoRenewPeriod"),
            ("expiry",             "expiry"),
        ]
        for src_attr, dst_field in msg_fields:
            self._copy_msg_to_proto(self, proto, src_attr, dst_field)

        self._set_bool(proto, "deleted", self.is_deleted, default=False)
        self._set_enum(proto, "defaultFreezeStatus", self.default_freeze_status)
        self._set_enum(proto, "defaultKycStatus", self.default_kyc_status)
        self._set_enum(proto, "pause_status", self.pause_status)

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
