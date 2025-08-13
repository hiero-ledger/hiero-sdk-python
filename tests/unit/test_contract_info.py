"""
Unit tests for the ContractInfo class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info import ContractInfo
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services.contract_get_info_pb2 import ContractGetInfoResponse
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_relationship import TokenRelationship

pytestmark = pytest.mark.unit


@pytest.fixture
def token_relationship():
    """Fixture for a single TokenRelationship object"""
    return TokenRelationship(
        token_id=TokenId(0, 0, 500),
        symbol="TEST",
        balance=1000000,
        kyc_status=TokenKycStatus.GRANTED,
        freeze_status=TokenFreezeStatus.UNFROZEN,
        decimals=8,
        automatic_association=True,
    )


@pytest.fixture
def multiple_token_relationships():
    """Fixture for multiple TokenRelationship objects"""
    return [
        TokenRelationship(
            token_id=TokenId(0, 0, 500),
            symbol="TEST1",
            balance=1000000,
            kyc_status=TokenKycStatus.GRANTED,
            freeze_status=TokenFreezeStatus.UNFROZEN,
            decimals=8,
            automatic_association=True,
        ),
        TokenRelationship(
            token_id=TokenId(0, 0, 600),
            symbol="TEST2",
            balance=2000000,
            kyc_status=TokenKycStatus.KYC_NOT_APPLICABLE,
            freeze_status=TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
            decimals=6,
            automatic_association=False,
        ),
    ]


@pytest.fixture
def contract_info(token_relationship):
    """Fixture for a ContractInfo object"""
    return ContractInfo(
        contract_id=ContractId(0, 0, 200),
        account_id=AccountId(0, 0, 300),
        contract_account_id="0.0.300",
        admin_key=PrivateKey.generate_ed25519().public_key(),
        expiration_time=Timestamp(1625097600, 0),
        auto_renew_period=Duration(7776000),  # 90 days
        auto_renew_account_id=AccountId(0, 0, 400),
        storage=1024,
        contract_memo="Test contract memo",
        balance=5000000,
        is_deleted=False,
        ledger_id=b"test_ledger_id",
        max_automatic_token_associations=10,
        token_relationships=[token_relationship],
    )


@pytest.fixture
def proto_contract_info(token_relationship):
    """Fixture for a proto ContractInfo object"""
    public_key = PrivateKey.generate_ed25519().public_key()

    proto = ContractGetInfoResponse.ContractInfo(
        contractID=ContractId(0, 0, 200)._to_proto(),
        accountID=AccountId(0, 0, 300)._to_proto(),
        contractAccountID="0.0.300",
        adminKey=public_key._to_proto(),
        expirationTime=Timestamp(1625097600, 0)._to_protobuf(),
        autoRenewPeriod=Duration(7776000)._to_proto(),
        auto_renew_account_id=AccountId(0, 0, 400)._to_proto(),
        storage=1024,
        memo="Test contract memo",
        balance=5000000,
        deleted=False,
        ledger_id=b"test_ledger_id",
        max_automatic_token_associations=10,
        tokenRelationships=[token_relationship._to_proto()],
    )
    return proto


def test_contract_info_initialization(contract_info):
    """Test the initialization of the ContractInfo class"""
    assert contract_info.contract_id == ContractId(0, 0, 200)
    assert contract_info.account_id == AccountId(0, 0, 300)
    assert contract_info.contract_account_id == "0.0.300"
    assert contract_info.admin_key is not None
    assert contract_info.expiration_time == Timestamp(1625097600, 0)
    assert contract_info.auto_renew_period == Duration(7776000)
    assert contract_info.auto_renew_account_id == AccountId(0, 0, 400)
    assert contract_info.storage == 1024
    assert contract_info.contract_memo == "Test contract memo"
    assert contract_info.balance == 5000000
    assert contract_info.is_deleted is False
    assert contract_info.ledger_id == b"test_ledger_id"
    assert contract_info.max_automatic_token_associations == 10
    assert len(contract_info.token_relationships) == 1
    assert contract_info.token_relationships[0].token_id == TokenId(0, 0, 500)


def test_contract_info_default_initialization():
    """Test the default initialization of the ContractInfo class"""
    contract_info = ContractInfo()
    assert contract_info.contract_id is None
    assert contract_info.account_id is None
    assert contract_info.contract_account_id is None
    assert contract_info.admin_key is None
    assert contract_info.expiration_time is None
    assert contract_info.auto_renew_period is None
    assert contract_info.auto_renew_account_id is None
    assert contract_info.storage is None
    assert contract_info.contract_memo is None
    assert contract_info.balance is None
    assert contract_info.is_deleted is None
    assert contract_info.ledger_id is None
    assert contract_info.max_automatic_token_associations is None
    assert not contract_info.token_relationships


def test_from_proto(proto_contract_info):
    """Test the from_proto method of the ContractInfo class"""
    contract_info = ContractInfo._from_proto(proto_contract_info)

    assert contract_info.contract_id == ContractId(0, 0, 200)
    assert contract_info.account_id == AccountId(0, 0, 300)
    assert contract_info.contract_account_id == "0.0.300"
    assert contract_info.admin_key is not None
    assert contract_info.expiration_time == Timestamp(1625097600, 0)
    assert contract_info.auto_renew_period == Duration(7776000)
    assert contract_info.auto_renew_account_id == AccountId(0, 0, 400)
    assert contract_info.storage == 1024
    assert contract_info.contract_memo == "Test contract memo"
    assert contract_info.balance == 5000000
    assert contract_info.is_deleted is False
    assert contract_info.ledger_id == b"test_ledger_id"
    assert contract_info.max_automatic_token_associations == 10
    assert len(contract_info.token_relationships) == 1
    assert contract_info.token_relationships[0].token_id == TokenId(0, 0, 500)


def test_from_proto_with_empty_token_relationships():
    """Test the from_proto method of the ContractInfo class with empty token relationships"""
    public_key = PrivateKey.generate_ed25519().public_key()
    proto = ContractGetInfoResponse.ContractInfo(
        contractID=ContractId(0, 0, 200)._to_proto(),
        accountID=AccountId(0, 0, 300)._to_proto(),
        contractAccountID="0.0.300",
        adminKey=public_key._to_proto(),
        expirationTime=Timestamp(1625097600, 0)._to_protobuf(),
        autoRenewPeriod=Duration(7776000)._to_proto(),
        auto_renew_account_id=AccountId(0, 0, 400)._to_proto(),
        storage=1024,
        memo="Test contract memo",
        balance=5000000,
        deleted=False,
        ledger_id=b"test_ledger_id",
        max_automatic_token_associations=10,
        tokenRelationships=[],
    )

    contract_info = ContractInfo._from_proto(proto)
    assert contract_info.contract_id == ContractId(0, 0, 200)
    assert contract_info.account_id == AccountId(0, 0, 300)
    assert contract_info.storage == 1024
    assert not contract_info.token_relationships


def test_from_proto_none_raises_error():
    """Test the from_proto method of the ContractInfo class with a None proto"""
    with pytest.raises(ValueError, match="Contract info proto is None"):
        ContractInfo._from_proto(None)


def test_to_proto(contract_info):
    """Test the to_proto method of the ContractInfo class"""
    proto = contract_info._to_proto()

    assert proto.contractID == ContractId(0, 0, 200)._to_proto()
    assert proto.accountID == AccountId(0, 0, 300)._to_proto()
    assert proto.contractAccountID == "0.0.300"
    assert proto.adminKey is not None
    assert proto.expirationTime == Timestamp(1625097600, 0)._to_protobuf()
    assert proto.autoRenewPeriod == Duration(7776000)._to_proto()
    assert proto.auto_renew_account_id == AccountId(0, 0, 400)._to_proto()
    assert proto.storage == 1024
    assert proto.memo == "Test contract memo"
    assert proto.balance == 5000000
    assert proto.deleted is False
    assert proto.ledger_id == b"test_ledger_id"
    assert proto.max_automatic_token_associations == 10
    assert len(proto.tokenRelationships) == 1


def test_to_proto_with_none_values():
    """Test the to_proto method of the ContractInfo class with none values"""
    contract_info = ContractInfo()
    proto = contract_info._to_proto()

    # Protobuf has default values, so we check the proto structure exists
    assert hasattr(proto, "contractID")
    assert hasattr(proto, "accountID")
    assert proto.contractAccountID == ""  # Empty string is default for protobuf
    assert hasattr(proto, "adminKey")
    assert hasattr(proto, "expirationTime")
    assert hasattr(proto, "autoRenewPeriod")
    assert proto.storage == 0  # 0 is default for protobuf int when None is passed
    assert proto.memo == ""  # Empty string is default for protobuf
    assert proto.balance == 0  # 0 is default for protobuf int
    assert proto.deleted is False  # False is default for protobuf bool
    assert not proto.tokenRelationships  # Empty list for token relationships
    assert proto.ledger_id == b""  # Empty bytes is default for protobuf
    assert proto.max_automatic_token_associations == 0  # 0 is default for protobuf int


def test_to_proto_with_empty_token_relationships():
    """Test the to_proto method of the ContractInfo class with empty token relationships list"""
    contract_info = ContractInfo(
        contract_id=ContractId(0, 0, 200),
        account_id=AccountId(0, 0, 300),
        storage=1024,
        token_relationships=[],
    )
    proto = contract_info._to_proto()

    assert proto.contractID == ContractId(0, 0, 200)._to_proto()
    assert proto.accountID == AccountId(0, 0, 300)._to_proto()
    assert proto.storage == 1024
    assert proto.tokenRelationships == []


def test_proto_conversion_full_object(contract_info):
    """Test proto conversion with fully populated object"""
    converted = ContractInfo._from_proto(contract_info._to_proto())

    assert converted.contract_id == contract_info.contract_id
    assert converted.account_id == contract_info.account_id
    assert converted.contract_account_id == contract_info.contract_account_id
    assert converted.expiration_time == contract_info.expiration_time
    assert converted.auto_renew_period == contract_info.auto_renew_period
    assert converted.auto_renew_account_id == contract_info.auto_renew_account_id
    assert converted.storage == contract_info.storage
    assert converted.contract_memo == contract_info.contract_memo
    assert converted.balance == contract_info.balance
    assert converted.is_deleted == contract_info.is_deleted
    assert converted.ledger_id == contract_info.ledger_id
    assert (
        converted.max_automatic_token_associations
        == contract_info.max_automatic_token_associations
    )
    assert len(converted.token_relationships) == len(contract_info.token_relationships)


def test_proto_conversion_multiple_token_relationships(multiple_token_relationships):
    """Test proto conversion with multiple token relationships"""
    contract_info = ContractInfo(
        contract_id=ContractId(0, 0, 200),
        token_relationships=multiple_token_relationships,
    )
    converted = ContractInfo._from_proto(contract_info._to_proto())

    assert len(converted.token_relationships) == 2

    first = converted.token_relationships[0]
    second = converted.token_relationships[1]

    assert first.token_id == TokenId(0, 0, 500)
    assert first.symbol == "TEST1"
    assert second.token_id == TokenId(0, 0, 600)
    assert second.symbol == "TEST2"

def test_proto_conversion_minimal_fields():
    """Test proto conversion with minimal fields"""
    contract_info = ContractInfo(
        contract_id=ContractId(0, 0, 200),
        contract_memo="Minimal contract",
        balance=1000000,
    )
    converted = ContractInfo._from_proto(contract_info._to_proto())

    assert converted.contract_id == contract_info.contract_id
    assert converted.contract_memo == contract_info.contract_memo
    assert converted.balance == contract_info.balance
    assert converted.admin_key is None
    assert not converted.token_relationships
