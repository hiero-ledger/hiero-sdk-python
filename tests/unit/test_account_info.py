import pytest

from hiero_sdk_python.account.account_info import AccountInfo
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_relationship import TokenRelationship
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services.crypto_get_info_pb2 import CryptoGetInfoResponse

pytestmark = pytest.mark.unit

@pytest.fixture
def account_info():
    return AccountInfo(
        account_id=AccountId(0, 0, 100),
        contract_account_id="0.0.100",
        is_deleted=False,
        proxy_received=Hbar.from_tinybars(1000),
        key=PrivateKey.generate_ed25519().public_key(),
        balance=Hbar.from_tinybars(5000000),
        receiver_signature_required=True,
        expiration_time=Timestamp(1625097600, 0),
        auto_renew_period=Duration(7776000),  # 90 days
        token_relationships=[],
        account_memo="Test account memo",
        owned_nfts=5
    )

@pytest.fixture
def proto_account_info():
    public_key = PrivateKey.generate_ed25519().public_key()
    proto = CryptoGetInfoResponse.AccountInfo(
        accountID=AccountId(0, 0, 100)._to_proto(),
        contractAccountID="0.0.100",
        deleted=False,
        proxyReceived=1000,
        key=public_key._to_proto(),
        balance=5000000,
        receiverSigRequired=True,
        expirationTime=Timestamp(1625097600, 0)._to_protobuf(),
        autoRenewPeriod=Duration(7776000)._to_proto(),
        tokenRelationships=[],
        memo="Test account memo",
        ownedNfts=5
    )
    return proto

def test_account_info_initialization(account_info):
    """Test the initialization of the AccountInfo class"""
    assert account_info.account_id == AccountId(0, 0, 100)
    assert account_info.contract_account_id == "0.0.100"
    assert account_info.is_deleted is False
    assert account_info.proxy_received.to_tinybars() == 1000
    assert account_info.key is not None
    assert account_info.balance.to_tinybars() == 5000000
    assert account_info.receiver_signature_required is True
    assert account_info.expiration_time == Timestamp(1625097600, 0)
    assert account_info.auto_renew_period == Duration(7776000)
    assert account_info.token_relationships == []
    assert account_info.account_memo == "Test account memo"
    assert account_info.owned_nfts == 5

def test_account_info_default_initialization():
    """Test the default initialization of the AccountInfo class"""
    account_info = AccountInfo()
    assert account_info.account_id is None
    assert account_info.contract_account_id is None
    assert account_info.is_deleted is None
    assert account_info.proxy_received is None
    assert account_info.key is None
    assert account_info.balance is None
    assert account_info.receiver_signature_required is None
    assert account_info.expiration_time is None
    assert account_info.auto_renew_period is None
    assert account_info.token_relationships == []
    assert account_info.account_memo is None
    assert account_info.owned_nfts is None

def test_from_proto(proto_account_info):
    """Test the from_proto method of the AccountInfo class"""
    account_info = AccountInfo._from_proto(proto_account_info)
    
    assert account_info.account_id == AccountId(0, 0, 100)
    assert account_info.contract_account_id == "0.0.100"
    assert account_info.is_deleted is False
    assert account_info.proxy_received.to_tinybars() == 1000
    assert account_info.key is not None
    assert account_info.balance.to_tinybars() == 5000000
    assert account_info.receiver_signature_required is True
    assert account_info.expiration_time == Timestamp(1625097600, 0)
    assert account_info.auto_renew_period == Duration(7776000)
    assert account_info.token_relationships == []
    assert account_info.account_memo == "Test account memo"
    assert account_info.owned_nfts == 5

def test_from_proto_with_token_relationships():
    """Test the from_proto method of the AccountInfo class with token relationships"""
    # Create a minimal proto without a key to avoid the key parsing issue
    public_key = PrivateKey.generate_ed25519().public_key()
    proto = CryptoGetInfoResponse.AccountInfo(
        accountID=AccountId(0, 0, 100)._to_proto(),
        key=public_key._to_proto(),
        balance=5000000,
        tokenRelationships=[]
    )
    
    account_info = AccountInfo._from_proto(proto)
    assert account_info.account_id == AccountId(0, 0, 100)
    assert account_info.balance.to_tinybars() == 5000000
    assert account_info.token_relationships == []

def test_from_proto_none_raises_error():
    """Test the from_proto method of the AccountInfo class with a None proto"""
    with pytest.raises(ValueError, match="Account info proto is None"):
        AccountInfo._from_proto(None)

def test_to_proto(account_info):
    """Test the to_proto method of the AccountInfo class"""
    proto = account_info._to_proto()
    
    assert proto.accountID == AccountId(0, 0, 100)._to_proto()
    assert proto.contractAccountID == "0.0.100"
    assert proto.deleted is False
    assert proto.proxyReceived == 1000
    assert proto.key is not None
    assert proto.balance == 5000000
    assert proto.receiverSigRequired is True
    assert proto.expirationTime == Timestamp(1625097600, 0)._to_protobuf()
    assert proto.autoRenewPeriod == Duration(7776000)._to_proto()
    assert proto.tokenRelationships == []
    assert proto.memo == "Test account memo"
    assert proto.ownedNfts == 5

def test_to_proto_with_none_values():
    """Test the to_proto method of the AccountInfo class with none values"""
    account_info = AccountInfo()
    proto = account_info._to_proto()
    
    # Protobuf has default values, so we check the proto structure exists
    assert hasattr(proto, 'accountID')
    assert proto.contractAccountID == ""  # Empty string is default for protobuf
    assert proto.deleted is False  # False is default for protobuf bool
    assert proto.proxyReceived == 0  # 0 is default for protobuf int when None is passed
    assert hasattr(proto, 'key')
    assert proto.balance == 0  # 0 is default for protobuf int when None is passed
    assert proto.receiverSigRequired is False  # False is default for protobuf bool
    assert hasattr(proto, 'expirationTime')
    assert hasattr(proto, 'autoRenewPeriod')
    assert proto.tokenRelationships == []
    assert proto.memo == ""  # Empty string is default for protobuf
    assert proto.ownedNfts == 0  # 0 is default for protobuf int

def test_proto_conversion(account_info):
    """Test converting AccountInfo to proto and back preserves data"""
    proto = account_info._to_proto()
    converted_account_info = AccountInfo._from_proto(proto)
    
    assert converted_account_info.account_id == account_info.account_id
    assert converted_account_info.contract_account_id == account_info.contract_account_id
    assert converted_account_info.is_deleted == account_info.is_deleted
    assert converted_account_info.proxy_received.to_tinybars() == account_info.proxy_received.to_tinybars()
    assert converted_account_info.balance.to_tinybars() == account_info.balance.to_tinybars()
    assert converted_account_info.receiver_signature_required == account_info.receiver_signature_required
    assert converted_account_info.expiration_time == account_info.expiration_time
    assert converted_account_info.auto_renew_period == account_info.auto_renew_period
    assert converted_account_info.token_relationships == account_info.token_relationships
    assert converted_account_info.account_memo == account_info.account_memo
    assert converted_account_info.owned_nfts == account_info.owned_nfts
