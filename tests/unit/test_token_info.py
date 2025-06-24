import pytest

import hiero_sdk_python.hapi.services.basic_types_pb2
from hiero_sdk_python import TokenInfo, TokenId, AccountId, Timestamp, PrivateKey, Duration
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
        tokenId=TokenId(0, 0, 100),
        name="TestToken",
        symbol="TST",
        decimals=2,
        totalSupply=1000000,
        treasury=AccountId(0, 0, 200),
        isDeleted=False,
        memo="Test token",
        tokenType=TokenType.FUNGIBLE_COMMON,
        maxSupply=10000000,
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
    assert token_info.tokenId == TokenId(0, 0, 100)
    assert token_info.name == "TestToken"
    assert token_info.symbol == "TST"
    assert token_info.decimals == 2
    assert token_info.totalSupply == 1000000
    assert token_info.treasury == AccountId(0, 0, 200)
    assert token_info.isDeleted is False
    assert token_info.memo == "Test token"
    assert token_info.tokenType == TokenType.FUNGIBLE_COMMON
    assert token_info.maxSupply == 10000000
    assert token_info.ledger_id == b"ledger123"
    assert token_info.metadata == b"Test metadata"
    assert token_info.supplyType == SupplyType.FINITE
    assert token_info.defaultKycStatus == TokenKycStatus.KYC_NOT_APPLICABLE
    assert token_info.defaultFreezeStatus == TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    assert token_info.pause_status == TokenPauseStatus.PAUSE_NOT_APPLICABLE
    assert token_info.adminKey is None
    assert token_info.kycKey is None
    assert token_info.freezeKey is None
    assert token_info.wipeKey is None
    assert token_info.supplyKey is None
    assert token_info.fee_schedule_key is None
    assert token_info.autoRenewAccount is None
    assert token_info.autoRenewPeriod is None
    assert token_info.expiry is None
    assert token_info.pause_key is None

def test_setters(token_info):
    public_key = PrivateKey.generate_ed25519().public_key()
    token_info.set_admin_key(public_key)
    assert token_info.adminKey == public_key

    token_info.set_kycKey(public_key)
    assert token_info.kycKey == public_key

    token_info.set_freezeKey(public_key)
    assert token_info.freezeKey == public_key

    token_info.set_wipeKey(public_key)
    assert token_info.wipeKey == public_key

    token_info.set_supplyKey(public_key)
    assert token_info.supplyKey == public_key

    token_info.set_fee_schedule_key(public_key)
    assert token_info.fee_schedule_key == public_key

    token_info.set_default_freeze_status(TokenFreezeStatus.FROZEN)
    assert token_info.defaultFreezeStatus == TokenFreezeStatus.FROZEN

    token_info.set_default_kyc_status(TokenKycStatus.GRANTED)
    assert token_info.defaultKycStatus == TokenKycStatus.GRANTED

    token_info.set_auto_renew_account(AccountId(0, 0, 300))
    assert token_info.autoRenewAccount == AccountId(0, 0, 300)

    token_info.set_auto_renew_period(Duration(3600))
    assert token_info.autoRenewPeriod == Duration(3600)

    expiry = Timestamp(1625097600, 0)
    token_info.set_expiry(expiry)
    assert token_info.expiry == expiry

    token_info.set_pause_key(public_key)
    assert token_info.pause_key == public_key

    token_info.set_pause_status(TokenPauseStatus.PAUSED)
    assert token_info.pause_status == TokenPauseStatus.PAUSED

    token_info.set_supply_type(SupplyType.INFINITE)
    assert token_info.supplyType == SupplyType.INFINITE

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

    assert token_info.tokenId == TokenId(0, 0, 100)
    assert token_info.name == "TestToken"
    assert token_info.symbol == "TST"
    assert token_info.decimals == 2
    assert token_info.totalSupply == 1000000
    assert token_info.treasury == AccountId(0, 0, 200)
    assert token_info.isDeleted is False
    assert token_info.memo == "Test token"
    assert token_info.tokenType == TokenType.FUNGIBLE_COMMON
    assert token_info.maxSupply == 10000000
    assert token_info.ledger_id == b"ledger123"
    assert token_info.metadata == b"Test metadata"
    assert token_info.adminKey.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.kycKey.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.freezeKey.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.wipeKey.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.supplyKey.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.fee_schedule_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.defaultFreezeStatus == TokenFreezeStatus.FROZEN
    assert token_info.defaultKycStatus == TokenKycStatus.GRANTED
    assert token_info.autoRenewAccount == AccountId(0, 0, 300)
    assert token_info.autoRenewPeriod == Duration(3600)
    assert token_info.expiry == Timestamp(1625097600, 0)
    assert token_info.pause_key.to_bytes_raw() == public_key.to_bytes_raw()
    assert token_info.pause_status == TokenPauseStatus.PAUSED.value
    assert token_info.supplyType.value == SupplyType.INFINITE.value

def test_to_proto(token_info):
    public_key = PrivateKey.generate_ed25519().public_key()
    token_info.set_admin_key(public_key)
    token_info.set_kycKey(public_key)
    token_info.set_freezeKey(public_key)
    token_info.set_wipeKey(public_key)
    token_info.set_supplyKey(public_key)
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
        f"TokenInfo(tokenId={token_info.tokenId}, name={token_info.name}, "
        f"symbol={token_info.symbol}, decimals={token_info.decimals}, "
        f"totalSupply={token_info.totalSupply}, treasury={token_info.treasury}, "
        f"isDeleted={token_info.isDeleted}, memo={token_info.memo}, "
        f"tokenType={token_info.tokenType}, maxSupply={token_info.maxSupply}, "
        f"ledger_id={token_info.ledger_id}, metadata={token_info.metadata})"
    )
    assert str(token_info) == expected