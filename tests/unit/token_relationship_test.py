import pytest

from hiero_sdk_python.tokens.token_relationship import TokenRelationship
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenRelationship as TokenRelationshipProto
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenFreezeStatus as TokenFreezeStatusProto
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenKycStatus as TokenKycStatusProto

pytestmark = pytest.mark.unit

@pytest.fixture
def token_relationship():
    return TokenRelationship(
        token_id=TokenId(0, 0, 100),
        symbol="TEST",
        balance=1000000,
        kyc_status=TokenKycStatus.GRANTED,
        freeze_status=TokenFreezeStatus.UNFROZEN,
        decimals=8,
        automatic_association=True
    )

@pytest.fixture
def proto_token_relationship():
    proto = TokenRelationshipProto(
        tokenId=TokenId(0, 0, 100)._to_proto(),
        symbol="TEST",
        balance=1000000,
        kycStatus=TokenKycStatusProto.Granted,
        freezeStatus=TokenFreezeStatusProto.Unfrozen,
        decimals=8,
        automatic_association=True
    )
    return proto

def test_token_relationship_initialization(token_relationship):
    """Test the initialization of the TokenRelationship class"""
    assert token_relationship.token_id == TokenId(0, 0, 100)
    assert token_relationship.symbol == "TEST"
    assert token_relationship.balance == 1000000
    assert token_relationship.kyc_status == TokenKycStatus.GRANTED
    assert token_relationship.freeze_status == TokenFreezeStatus.UNFROZEN
    assert token_relationship.decimals == 8
    assert token_relationship.automatic_association is True

def test_token_relationship_default_initialization():
    """Test the default initialization of the TokenRelationship class"""
    token_relationship = TokenRelationship()
    assert token_relationship.token_id is None
    assert token_relationship.symbol is None
    assert token_relationship.balance is None
    assert token_relationship.kyc_status is None
    assert token_relationship.freeze_status is None
    assert token_relationship.decimals is None
    assert token_relationship.automatic_association is None

def test_from_proto(proto_token_relationship):
    """Test the from_proto method of the TokenRelationship class"""
    token_relationship = TokenRelationship._from_proto(proto_token_relationship)
    
    assert token_relationship.token_id == TokenId(0, 0, 100)
    assert token_relationship.symbol == "TEST"
    assert token_relationship.balance == 1000000
    assert token_relationship.kyc_status == TokenKycStatus.GRANTED
    assert token_relationship.freeze_status == TokenFreezeStatus.UNFROZEN
    assert token_relationship.decimals == 8
    assert token_relationship.automatic_association is True

def test_from_proto_with_different_statuses():
    """Test the from_proto method of the TokenRelationship class with different statuses"""
    proto = TokenRelationshipProto(
        tokenId=TokenId(0, 0, 200)._to_proto(),
        symbol="OTHER",
        balance=500000,
        kycStatus=TokenKycStatusProto.Revoked,
        freezeStatus=TokenFreezeStatusProto.Frozen,
        decimals=2,
        automatic_association=False
    )
    
    token_relationship = TokenRelationship._from_proto(proto)
    assert token_relationship.token_id == TokenId(0, 0, 200)
    assert token_relationship.symbol == "OTHER"
    assert token_relationship.balance == 500000
    assert token_relationship.kyc_status == TokenKycStatus.REVOKED
    assert token_relationship.freeze_status == TokenFreezeStatus.FROZEN
    assert token_relationship.decimals == 2
    assert token_relationship.automatic_association is False

def test_from_proto_with_not_applicable_statuses():
    """Test the from_proto method of the TokenRelationship class with not applicable statuses"""
    proto = TokenRelationshipProto(
        tokenId=TokenId(0, 0, 300)._to_proto(),
        symbol="NA",
        balance=0,
        kycStatus=TokenKycStatusProto.KycNotApplicable,
        freezeStatus=TokenFreezeStatusProto.FreezeNotApplicable,
        decimals=0,
        automatic_association=False
    )
    
    token_relationship = TokenRelationship._from_proto(proto)
    assert token_relationship.kyc_status == TokenKycStatus.KYC_NOT_APPLICABLE
    assert token_relationship.freeze_status == TokenFreezeStatus.FREEZE_NOT_APPLICABLE

def test_from_proto_none_raises_error():
    """Test the from_proto method of the TokenRelationship class with a None proto"""
    with pytest.raises(ValueError, match="Token relationship proto is None"):
        TokenRelationship._from_proto(None)

def test_to_proto(token_relationship):
    """Test the to_proto method of the TokenRelationship class"""
    proto = token_relationship._to_proto()
    
    assert proto.tokenId == TokenId(0, 0, 100)._to_proto()
    assert proto.symbol == "TEST"
    assert proto.balance == 1000000
    assert proto.kycStatus == TokenKycStatusProto.Granted
    assert proto.freezeStatus == TokenFreezeStatusProto.Unfrozen
    assert proto.decimals == 8
    assert proto.automatic_association is True

def test_to_proto_with_different_statuses():
    """Test the to_proto method of the TokenRelationship class with different statuses"""
    token_relationship = TokenRelationship(
        token_id=TokenId(0, 0, 200),
        symbol="OTHER",
        balance=500000,
        kyc_status=TokenKycStatus.REVOKED,
        freeze_status=TokenFreezeStatus.FROZEN,
        decimals=2,
        automatic_association=False
    )
    
    proto = token_relationship._to_proto()
    assert proto.kycStatus == TokenKycStatusProto.Revoked
    assert proto.freezeStatus == TokenFreezeStatusProto.Frozen

def test_to_proto_with_not_applicable_statuses():
    """Test the to_proto method of the TokenRelationship class with not applicable statuses"""
    token_relationship = TokenRelationship(
        token_id=TokenId(0, 0, 300),
        symbol="NA",
        balance=0,
        kyc_status=TokenKycStatus.KYC_NOT_APPLICABLE,
        freeze_status=TokenFreezeStatus.FREEZE_NOT_APPLICABLE,
        decimals=0,
        automatic_association=False
    )
    
    proto = token_relationship._to_proto()
    assert proto.kycStatus == TokenKycStatusProto.KycNotApplicable
    assert proto.freezeStatus == TokenFreezeStatusProto.FreezeNotApplicable

def test_proto_conversion(token_relationship):
    """Test converting TokenRelationship to proto and back preserves data"""
    proto = token_relationship._to_proto()
    converted_token_relationship = TokenRelationship._from_proto(proto)
    
    assert converted_token_relationship.token_id == token_relationship.token_id
    assert converted_token_relationship.symbol == token_relationship.symbol
    assert converted_token_relationship.balance == token_relationship.balance
    assert converted_token_relationship.kyc_status == token_relationship.kyc_status
    assert converted_token_relationship.freeze_status == token_relationship.freeze_status
    assert converted_token_relationship.decimals == token_relationship.decimals
    assert converted_token_relationship.automatic_association == token_relationship.automatic_association

def test_proto_conversion_with_all_statuses():
    """Test converting TokenRelationship to proto and back preserves all status combinations"""
    test_cases = [
        (TokenKycStatus.GRANTED, TokenFreezeStatus.UNFROZEN),
        (TokenKycStatus.REVOKED, TokenFreezeStatus.FROZEN),
        (TokenKycStatus.KYC_NOT_APPLICABLE, TokenFreezeStatus.FREEZE_NOT_APPLICABLE),
    ]
    
    for kyc_status, freeze_status in test_cases:
        token_relationship = TokenRelationship(
            token_id=TokenId(0, 0, 400),
            symbol="ROUND",
            balance=123456,
            kyc_status=kyc_status,
            freeze_status=freeze_status,
            decimals=6,
            automatic_association=True
        )
        
        proto = token_relationship._to_proto()
        converted = TokenRelationship._from_proto(proto)
        
        assert converted.kyc_status == kyc_status
        assert converted.freeze_status == freeze_status 