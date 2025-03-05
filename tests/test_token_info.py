import pytest
import random
from hiero_sdk_python import TokenId, AccountId, PrivateKey, PublicKey
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_info import TokenInfo, TokenFreezeStatus, TokenPauseStatus

# Helper function to create a valid TokenInfo instance
def create_valid_token_info():
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    return TokenInfo(
        tokenId=TokenId(0, 0, 123),
        name="TestToken",
        symbol="TTK",
        decimals=8,
        totalSupply=1000000,
        treasury=AccountId(0, 0, 456),
        adminKey=public_key,
        isDeleted=False,
        autoRenewAccount=AccountId(0, 0, 789),
        autoRenewPeriod=7890000,
        expiry=1234567890,
        memo="Test memo",
        maxSupply=10000000,
        pause_key=None,  # Optional field
        ledger_id=b"Hedera",
        kycKey=public_key,
        freezeKey=public_key,
        supplyKey=public_key,
        fee_schedule_key=public_key
    )

# 1. Test valid initialization
def test_valid_initialization():
    token_info = create_valid_token_info()
    assert token_info.tokenId == TokenId(0, 0, 123)
    assert token_info.name == "TestToken"
    assert token_info.symbol == "TTK"
    assert token_info.decimals == 8
    assert token_info.totalSupply == 1000000
    assert token_info.treasury == AccountId(0, 0, 456)
    assert isinstance(token_info.adminKey, PublicKey)
    assert token_info.defaultFreezeStatus is TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    assert token_info.defaultKycStatus is TokenKycStatus.KYC_NOT_APPLICABLE
    assert token_info.isDeleted is False
    assert token_info.autoRenewAccount == AccountId(0, 0, 789)
    assert token_info.autoRenewPeriod == 7890000
    assert token_info.expiry == 1234567890
    assert token_info.memo == "Test memo"
    assert token_info.maxSupply == 10000000
    assert token_info.pause_key is None
    assert token_info.pause_status is TokenPauseStatus.PAUSE_NOT_APPLICABLE
    assert token_info.ledger_id == b"Hedera"

# 2. Test wrong type for tokenId
def test_tokenId_wrong_type():
    with pytest.raises(TypeError, match="tokenId must be TokenId"):
        TokenInfo(
            tokenId="0.0.123",  # Wrong type
            name="TestToken",
            symbol="TTK",
            decimals=8,
            totalSupply=1000000,
            treasury=AccountId(0, 0, 456),
            adminKey=PrivateKey.generate().public_key(),
            defaultFreezeStatus=TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
            isDeleted=False,
            autoRenewAccount=AccountId(0, 0, 789),
            autoRenewPeriod=7890000,
            expiry=1234567890,
            memo="Test memo",
            maxSupply=10000000,
            pause_key=None,
            pause_status=TokenPauseStatus.PAUSE_NOT_APPLICABLE,
            ledger_id=b"Hedera"
        )

# 3. Test wrong type for treasury
def test_treasury_wrong_type():
    with pytest.raises(TypeError, match="treasury must be AccountId"):
        TokenInfo(
            tokenId=TokenId(0, 0, 123),
            name="TestToken",
            symbol="TTK",
            decimals=8,
            totalSupply=1000000,
            treasury=123,  # Wrong type
            adminKey=PrivateKey.generate().public_key(),
            defaultFreezeStatus=TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
            isDeleted=False,
            autoRenewAccount=AccountId(0, 0, 789),
            autoRenewPeriod=7890000,
            expiry=1234567890,
            memo="Test memo",
            maxSupply=10000000,
            pause_key=None,
            pause_status=TokenPauseStatus.PAUSE_NOT_APPLICABLE,
            ledger_id=b"Hedera"
        )

# 4. Test wrong type for decimals
def test_decimals_wrong_type():
    with pytest.raises(TypeError, match="decimals must be int"):
        TokenInfo(
            tokenId=TokenId(0, 0, 123),
            name="TestToken",
            symbol="TTK",
            decimals="8",  # Wrong type
            totalSupply=1000000,
            treasury=AccountId(0, 0, 456),
            adminKey=PrivateKey.generate().public_key(),
            defaultFreezeStatus=TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
            isDeleted=False,
            autoRenewAccount=AccountId(0, 0, 789),
            autoRenewPeriod=7890000,
            expiry=1234567890,
            memo="Test memo",
            maxSupply=10000000,
            pause_key=None,
            pause_status=TokenPauseStatus.PAUSE_NOT_APPLICABLE,
            ledger_id=b"Hedera"
        )

# 5. Test wrong type for isDeleted
def test_deleted_wrong_type():
    with pytest.raises(TypeError, match="isDeleted must be bool"):
        TokenInfo(
            tokenId=TokenId(0, 0, 123),
            name="TestToken",
            symbol="TTK",
            decimals=8,
            totalSupply=1000000,
            treasury=AccountId(0, 0, 456),
            adminKey=PrivateKey.generate().public_key(),
            defaultFreezeStatus=TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
            defaultKycStatus=TokenKycStatus.KYC_NOT_APPLICABLE,
            isDeleted=0,  # Wrong type
            autoRenewAccount=AccountId(0, 0, 789),
            autoRenewPeriod=7890000,
            expiry=1234567890,
            memo="Test memo",
            maxSupply=10000000,
            pause_key=None,
            pause_status=TokenPauseStatus.PAUSE_NOT_APPLICABLE,
            ledger_id=b"Hedera"
        )

# 6. Fuzz test for name with wrong types
def test_fuzz_name_wrong_type():
    invalid_types = [123, 45.67, True, ["list"], {"dict": 1}, TokenId(0, 0, 123)]
    for invalid_value in invalid_types:
        with pytest.raises(TypeError, match="name must be str"):
            TokenInfo(
                tokenId=TokenId(0, 0, 123),
                name=invalid_value,
                symbol="TTK",
                decimals=8,
                totalSupply=1000000,
                treasury=AccountId(0, 0, 456),
                adminKey=PrivateKey.generate().public_key(),
                defaultFreezeStatus=TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
                isDeleted=False,
                autoRenewAccount=AccountId(0, 0, 789),
                autoRenewPeriod=7890000,
                expiry=1234567890,
                memo="Test memo",
                maxSupply=10000000,
                pause_key=None,
                pause_status=TokenPauseStatus.PAUSE_NOT_APPLICABLE,
                ledger_id=b"Hedera"
            )

# 7. Fuzz test for integer fields with wrong types
def test_fuzz_integers_wrong_type():
    invalid_types = ["string", 3.14, True, ["list"], {"dict": 1}]
    integer_fields = ["decimals", "totalSupply", "autoRenewPeriod", "expiry", "maxSupply"]

    for field in integer_fields:
        for invalid_value in invalid_types:
            kwargs = {
                "tokenId": TokenId(0, 0, 123),
                "name": "TestToken",
                "symbol": "TTK",
                "decimals": 8,
                "totalSupply": 1000000,
                "treasury": AccountId(0, 0, 456),
                "adminKey": PrivateKey.generate().public_key(),
                "defaultFreezeStatus": TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
                "defaultKycStatus": TokenKycStatus.KYC_NOT_APPLICABLE,
                "isDeleted": False,
                "autoRenewAccount": AccountId(0, 0, 789),
                "autoRenewPeriod": 7890000,
                "expiry": 1234567890,
                "memo": "Test memo",
                "maxSupply": 10000000,
                "pause_key": None,
                "pause_status": TokenPauseStatus.PAUSE_NOT_APPLICABLE,
                "ledger_id": b"Hedera",
                field: invalid_value
            }
            with pytest.raises(TypeError, match=f"{field} must be int"):
                TokenInfo(**kwargs)

# 8. Test optional fields with valid values
def test_optional_fields_valid():
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    token_info = TokenInfo(
        tokenId=TokenId(0, 0, 123),
        name="TestToken",
        symbol="TTK",
        decimals=8,
        totalSupply=1000000,
        treasury=AccountId(0, 0, 456),
        adminKey=public_key,
        defaultFreezeStatus=TokenFreezeStatus.FROZEN,
        defaultKycStatus=TokenKycStatus.REVOKED,
        isDeleted=False,
        autoRenewAccount=AccountId(0, 0, 789),
        autoRenewPeriod=7890000,
        expiry=1234567890,
        memo="Test memo",
        maxSupply=10000000,
        pause_key=public_key,
        pause_status=TokenPauseStatus.PAUSED,
        ledger_id=b"Hedera"
    )
    assert token_info.defaultFreezeStatus == TokenFreezeStatus.FROZEN
    assert isinstance(token_info.pause_key, PublicKey)
    assert token_info.pause_status == TokenPauseStatus.PAUSED

# 9. Fuzz test for random fields with wrong types
def test_fuzz_random_types():
    field_types = {
        "tokenId": TokenId,
        "name": str,
        "symbol": str,
        "decimals": int,
        "totalSupply": int,
        "treasury": AccountId,
        "adminKey": PublicKey,
        "defaultFreezeStatus": TokenFreezeStatus,
        "defaultKycStatus": TokenKycStatus,
        "isDeleted": bool,
        "autoRenewAccount": AccountId,
        "autoRenewPeriod": int,
        "expiry": int,
        "memo": str,
        "maxSupply": int,
        "pause_key": PublicKey,
        "pause_status": TokenPauseStatus,
        "ledger_id": bytes,
        "kycKey": PublicKey,
        "freezeKey": PublicKey,
        "supplyKey": PublicKey,
        "fee_schedule_key": PublicKey,
    }

    invalid_values = [123, "string", 3.14, True, ["list"], b"bytes", TokenId(0, 0, 1), AccountId(0, 0, 2)]

    for _ in range(100):  # 50 random iterations
        field_to_test = random.choice(list(field_types.keys()))
        expected_type = field_types[field_to_test]
        invalid_value = random.choice([v for v in invalid_values if not isinstance(v, expected_type)])

        kwargs = create_valid_token_info().__dict__
        kwargs[field_to_test] = invalid_value
        with pytest.raises(TypeError, match=f"{field_to_test} must be {expected_type.__name__}"):
            TokenInfo(**kwargs)

def test_from_proto():
    from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenInfo as proto_TokenInfo
    from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenID as proto_TokenId, AccountID as proto_AccountId, Key as proto_Key

    # Assuming proto_TokenInfo is populated
    token_info = proto_TokenInfo(
        tokenId=proto_TokenId(shardNum=0, realmNum=1, tokenNum=123),
        name="TestToken",
        symbol="TTK",
        decimals=2,
        totalSupply=1000000,
        treasury=proto_AccountId(shardNum=0, realmNum=0, accountNum=456),
        adminKey=proto_Key(ed25519=PrivateKey.generate_ed25519().public_key().to_bytes_raw()),
        deleted=False,
        memo="Test token",
        maxSupply=10000000,
        ledger_id=b"test_ledger"
    )
    token = TokenInfo.from_proto(token_info)

    print(token_info.tokenId.tokenNum)

    assert token.tokenId.shard == token_info.tokenId.shardNum
    assert token.tokenId.realm == token_info.tokenId.realmNum
    assert token.tokenId.num == token_info.tokenId.tokenNum
    assert token.name == token_info.name
    assert token.symbol == token_info.symbol
    assert token.decimals == token_info.decimals
    assert token.totalSupply == token_info.totalSupply
    assert token.treasury.shard == token_info.treasury.shardNum
    assert token.treasury.realm == token_info.treasury.realmNum
    assert token.treasury.num == token_info.treasury.accountNum
    assert token.adminKey == PublicKey.from_proto(token_info.adminKey)
    assert token.defaultFreezeStatus == token_info.defaultFreezeStatus
    assert token.defaultKycStatus == token_info.defaultKycStatus
    assert token.isDeleted == token_info.deleted
    assert token.memo == token_info.memo
    assert token.maxSupply == token_info.maxSupply
    assert token.ledger_id == token_info.ledger_id
