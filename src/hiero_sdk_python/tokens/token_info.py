from dataclasses import dataclass, fields
from typing import get_origin, get_args, Union

from hiero_sdk_python import TokenId, AccountId, PublicKey
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.hapi.services.duration_pb2 import Duration
from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenGetInfoResponse, TokenInfo as pb_TokenInfo

def validate_optional_type(value, expected_type):
    # If value is None, it's valid for Union types
    if value is None:
        return True

    # For Union[SomeType], check if value matches the unwrapped type
    if get_origin(expected_type) is not None and get_origin(expected_type) is Union:
        # Get the actual type inside Union
        inner_type = get_args(expected_type)[0]
        return type(value) is inner_type

    # For non-Union types, do standard type checking
    return type(value) is expected_type


# noinspection PyTypeChecker
@dataclass(frozen=True, init=True)
class TokenInfo:
    tokenId: TokenId
    name: str
    symbol: str
    decimals: int  # uint32
    totalSupply: int  # uint64
    treasury: AccountId
    # kycKey
    # freezeKey
    # wipeKey
    # supplyKey
    # fee_schedule_key
    # custom_fees: List[CustomFee]
    isDeleted: bool
    memo: str
    # tokenType: TokenType
    # supplyType: TokenSupplyType = TokenSupplyType.NONE
    maxSupply: int  # int64
    ledger_id: bytes

    adminKey: Union[PublicKey, None] = None
    defaultFreezeStatus: TokenFreezeStatus = TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    defaultKycStatus: TokenKycStatus = TokenKycStatus.KYC_NOT_APPLICABLE
    autoRenewAccount: Union[AccountId, None] = None
    autoRenewPeriod: Union[int, None] = None
    expiry: Union[int, None] = None
    pause_key: Union[PublicKey, None] = None
    pause_status: TokenPauseStatus = TokenPauseStatus.PAUSE_NOT_APPLICABLE

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            expected_type = field.type

            if not validate_optional_type(value, expected_type):
                # Extract inner type for Union[T]
                if get_origin(expected_type) is Union:
                    type_str = get_args(expected_type)[0].__name__
                else:
                    type_str = expected_type.__name__
                raise TypeError(f"{field.name} must be {type_str}, got {type(value).__name__}")

        # Validate ranges for integer fields (only for non-None values)
        int_fields = {
            'decimals': (0, 2**32 - 1),        # uint32
            'totalSupply': (0, 2**64 - 1),     # uint64
            'autoRenewPeriod': (0, 2**64 - 1), # uint64
            'expiry': (0, 2**64 - 1),          # uint64
            'maxSupply': (-2**63, 2**63 - 1),  # int64
        }

        for field, (min_val, max_val) in int_fields.items():
            value = getattr(self, field)
            # Only validate if the value is not None
            if value is not None:
                if not min_val <= value <= max_val:
                    raise ValueError(f"{field} must be between {min_val} and {max_val}, got {value}")

        # Validate string fields (only for non-None values)
        string_fields = ['name', 'symbol', 'memo']
        for field in string_fields:
            value = getattr(self, field)
            if value is not None:
                if len(value.encode('utf-8')) > 100:
                    raise ValueError(f"{field} must not exceed 100 UTF-8 bytes, got {len(value.encode('utf-8'))} bytes")

                if field == 'name' and not value.isascii():
                    raise ValueError("name must contain only ASCII characters")

                if field == 'symbol' and not (value.isalpha() and value.isupper()):
                    raise ValueError("symbol must be an uppercase alphabetical string")


    # TODO: Likely needs a TokenGetInfoResponse class
    @classmethod
    def from_proto(cls, token_info: TokenGetInfoResponse):
        # info = token_info.getTokenInfo()
        pass

    # TODO: Java uses fromProtobuf(response.parsefrom(bytes)) may not be possible or necessary here
    @classmethod
    def from_bytes(cls, token_info: bytes):
        pass

    # TODO: Also uses protobuf class in java, the protobuf I have does not use this
    def to_proto(self):
        return TokenGetInfoResponse(
            tokenInfo = pb_TokenInfo(
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
                # WARNING: nanos really shouldn't be 0, but im not sure if I can set expiry to a Timestamp object (although it really should be)
                expiry = Timestamp(seconds = self.expiry, nanos = 0),
                # memo = self.memo,
                # TODO: missing stuff
                maxSupply = self.maxSupply,
                # TODO: missing stuff
                ledger_id = self.ledger_id
            )
        )

    def __str__(self):
        return f"{self.name}({self.tokenId}, {self.name}, {self.symbol}, {self.decimals}, {self.totalSupply}, {self.treasury}, {self.adminKey}, {self.isDeleted}, {self.autoRenewAccount}, {self.autoRenewPeriod}, {self.expiry}, {self.memo}, {self.maxSupply}, {self.ledger_id})"
