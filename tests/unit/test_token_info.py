import pytest

import hiero_sdk_python.hapi.services.basic_types_pb2
from hiero_sdk_python.tokens.token_info import TokenInfo, TokenId, AccountId, Timestamp
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenInfo as proto_TokenInfo

pytestmark = pytest.mark.unit

@pytest.fixture
def token_info():
    return TokenInfo(
        token_id=TokenId(0, 0, 100),
        name="TestToken",
        symbol="TST",
        decimals=2,
        total_supply=1000000,
        treasury=AccountId(0, 0, 200),
        is_deleted=False,
        memo="Test token",
        token_type=TokenType.FUNGIBLE_COMMON,
        max_supply=10000000,
        ledger_id=b"ledger123",
        metadata=b"Test metadata"
    )

@pytest.fixture
def proto_token_info():
    proto = proto_TokenInfo(
        tokenId=TokenId(0, 0, 100)._to_proto(),
        name="TestToken",
        symbol="TST",
        decimals=2,
        totalSupply=1000000,
        treasury=AccountId(0, 0, 200)._to_proto(),
        deleted=False,
        memo="Test token",
        tokenType=TokenType.FUNGIBLE_COMMON.value,
        maxSupply=10000000,
        ledger_id=b"ledger123",
        supplyType=SupplyType.FINITE.value,
        metadata=b"Test metadata"
    )
    return proto

def test_token_info_initialization(token_info):
    assert token_info.token_id == TokenId(0, 0, 100)
    assert token_info.name == "TestToken"
    assert token_info.symbol == "TST"
    assert token_info.decimals == 2
    assert token_info.total_supply == 1000000
    assert token_info.treasury == AccountId(0, 0, 200)
    assert token_info.is_deleted is False
    assert token_info.memo == "Test token"
    assert token_info.token_type == TokenType.FUNGIBLE_COMMON
    assert token_info.max_supply == 10000000
    assert token_info.ledger_id == b"ledger123"
    assert token_info.metadata == b"Test metadata"
    assert token_info.supply_type == SupplyType.FINITE
    assert token_info.default_kyc_status == TokenKycStatus.KYC_NOT_APPLICABLE
    assert token_info.default_freeze_status == TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    assert token_info.pause_status == TokenPauseStatus.PAUSE_NOT_APPLICABLE
    assert token_info.admin_key is None
    assert token_info.kyc_key is None
    assert token_info.freeze_key is None
    assert token_info.wipe_key is None
    assert token_info.supply_key is None
    assert token_info.fee_schedule_key is None
    assert token_info.auto_renew_account is None
    assert token_info.auto_renew_period is None
    assert token_info.expiry is None
    assert token_info.pause_key is None

def test_setters(token_info):
    public_key = PrivateKey.generate_ed25519().public_key()
    token_info.set_admin_key(public_key)
    assert token_info.admin_key == public_key

    token_info.set_kyc_key(public_key)
    assert token_info.kyc_key == public_key

    token_info.set_freeze_key(public_key)
    assert token_info.freeze_key == public_key

    token_info.set_wipe_key(public_key)
    assert token_info.wipe_key == public_key

    token_info.set_supply_key(public_key)
    assert token_info.supply_key == public_key

    token_info.set_fee_schedule_key(public_key)
    assert token_info.fee_schedule_key == public_key

    token_info.set_default_freeze_status(TokenFreezeStatus.FROZEN)
    assert token_info.default_freeze_status == TokenFreezeStatus.FROZEN

    token_info.set_default_kyc_status(TokenKycStatus.GRANTED)
    assert token_info.default_kyc_status == TokenKycStatus.GRANTED

    token_info.set_auto_renew_account(AccountId(0, 0, 300))
    assert token_info.auto_renew_account == AccountId(0, 0, 300)

    token_info.set_auto_renew_period(Duration(3600))
    assert token_info.auto_renew_period == Duration(3600)

    expiry = Timestamp(1625097600, 0)
    token_info.set_expiry(expiry)
    assert token_info.expiry == expiry

    token_info.set_pause_key(public_key)
    assert token_info.pause_key == public_key

    token_info.set_pause_status(TokenPauseStatus.PAUSED)
    assert token_info.pause_status == TokenPauseStatus.PAUSED

    token_info.set_supply_type(SupplyType.INFINITE)
    assert token_info.supply_type == SupplyType.INFINITE

def test_from_proto(proto_token_info):
    public_key = PrivateKey.generate_ed25519().public_key()
    proto_token_info.adminKey.ed25519 = public_key.to_bytes_raw()
    proto_token_info.kycKey.ed25519 = public_key.to_bytes_raw()
    proto_token_info.freezeKey.ed25519 = public_key.to_bytes_raw()
    proto_token_info.wipeKey.ed25519 = public_key.to_bytes_raw()
    proto_token_info.supplyKey.ed25519 = public_key.to_bytes_raw()
    proto_token_info.fee_schedule_key.ed25519 = public_key.to_bytes_raw()
    proto_token_info.pause_key.ed25519 = public_key.to_bytes_raw()
    proto_token_info.defaultFreezeStatus = TokenFreezeStatus.FROZEN.value
    proto_token_info.defaultKycStatus = TokenKycStatus.GRANTED.value
    proto_token_info.autoRenewAccount.CopyFrom(AccountId(0, 0, 300)._to_proto())
    proto_token_info.autoRenewPeriod.CopyFrom(Duration(3600)._to_proto())
    proto_token_info.expiry.CopyFrom(Timestamp(1625097600, 0)._to_protobuf())
    proto_token_info.pause_status = hiero_sdk_python.hapi.services.basic_types_pb2.Paused
    proto_token_info.supplyType = hiero_sdk_python.hapi.services.basic_types_pb2.INFINITE

    token_info = TokenInfo._from_proto(proto_token_info)

    assert token_info.token_id == TokenId(0, 0, 100)
    assert token_info.name == "TestToken"
    assert token_info.symbol == "TST"
    assert token_info.decimals == 2
    assert token_info.total_supply == 1000000
    assert token_info.treasury == AccountId(0, 0, 200)
    assert token_info.is_deleted is False
    assert token_info.memo == "Test token"
    assert token_info.token_type == TokenType.FUNGIBLE_COMMON
    assert token_info.max_supply == 10000000
    assert token_info.ledger_id == b"ledger123"
    assert token_info.metadata == b"Test metadata"
    assert token_info.admin_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.kyc_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.freeze_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.wipe_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.supply_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.fee_schedule_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.default_freeze_status == TokenFreezeStatus.FROZEN
    assert token_info.default_kyc_status == TokenKycStatus.GRANTED
    assert token_info.auto_renew_account == AccountId(0, 0, 300)
    assert token_info.auto_renew_period == Duration(3600)
    assert token_info.expiry == Timestamp(1625097600, 0)
    assert token_info.pause_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.pause_status == TokenPauseStatus.PAUSED.value
    assert token_info.supply_type.value == SupplyType.INFINITE.value

def test_to_proto(token_info):
    public_key = PrivateKey.generate_ed25519().public_key()
    token_info.set_admin_key(public_key)
    token_info.set_kyc_key(public_key)
    token_info.set_freeze_key(public_key)
    token_info.set_wipe_key(public_key)
    token_info.set_supply_key(public_key)
    token_info.set_fee_schedule_key(public_key)
    token_info.set_pause_key(public_key)
    token_info.set_default_freeze_status(TokenFreezeStatus.FROZEN)
    token_info.set_default_kyc_status(TokenKycStatus.GRANTED)
    token_info.set_auto_renew_account(AccountId(0, 0, 300))
    token_info.set_auto_renew_period(Duration(3600))
    token_info.set_expiry(Timestamp(1625097600, 0))
    token_info.set_pause_status(TokenPauseStatus.PAUSED)
    token_info.set_supply_type(SupplyType.INFINITE)

    proto = token_info._to_proto()

    assert proto.tokenId == TokenId(0, 0, 100)._to_proto()
    assert proto.name == "TestToken"
    assert proto.symbol == "TST"
    assert proto.decimals == 2
    assert proto.totalSupply == 1000000
    assert proto.treasury == AccountId(0, 0, 200)._to_proto()
    assert proto.deleted is False
    assert proto.memo == "Test token"
    assert proto.tokenType == TokenType.FUNGIBLE_COMMON.value
    assert proto.supplyType == SupplyType.INFINITE.value
    assert proto.maxSupply == 10000000
    assert proto.ledger_id == b"ledger123"
    assert proto.metadata == b"Test metadata"
    assert proto.adminKey.ed25519 == public_key.to_bytes_raw()
    assert proto.kycKey.ed25519 == public_key.to_bytes_raw()
    assert proto.freezeKey.ed25519 == public_key.to_bytes_raw()
    assert proto.wipeKey.ed25519 == public_key.to_bytes_raw()
    assert proto.supplyKey.ed25519 == public_key.to_bytes_raw()
    assert proto.fee_schedule_key.ed25519 == public_key.to_bytes_raw()
    assert proto.defaultFreezeStatus == TokenFreezeStatus.FROZEN.value
    assert proto.defaultKycStatus == TokenKycStatus.GRANTED.value
    assert proto.autoRenewAccount == AccountId(0, 0, 300)._to_proto()
    assert proto.autoRenewPeriod == Duration(3600)._to_proto()
    assert proto.expiry == Timestamp(1625097600, 0)._to_protobuf()
    assert proto.pause_key.ed25519 == public_key.to_bytes_raw()
    assert proto.pause_status == TokenPauseStatus.PAUSED.value

def test_str_representation(token_info):
    expected = (
        f"TokenInfo(token_id={token_info.token_id}, name={token_info.name!r}, "
        f"symbol={token_info.symbol!r}, decimals={token_info.decimals}, "
        f"total_supply={token_info.total_supply}, treasury={token_info.treasury}, "
        f"is_deleted={token_info.is_deleted}, memo={token_info.memo!r}, "
        f"token_type={token_info.token_type}, max_supply={token_info.max_supply}, "
        f"ledger_id={token_info.ledger_id!r}, metadata={token_info.metadata!r})"
    )
    assert str(token_info) == expected