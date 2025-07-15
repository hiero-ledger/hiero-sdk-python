import pytest
from unittest.mock import MagicMock
import warnings

from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_info import TokenInfo
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_pause_status import TokenPauseStatus
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenID, AccountID, Key
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt


def test_nftid_deprecated_alias_access():
    token = TokenId.from_string("0.0.123")
    nft = NftId(token_id=token, serial_number=7)

    # serialNumber -> serial_number
    with pytest.warns(FutureWarning) as record_serial:
        got = nft.serialNumber
    assert got == 7
    assert "serialNumber" in str(record_serial[0].message)

    # tokenId -> token_id
    with pytest.warns(FutureWarning) as record_tokenid:
        got = nft.tokenId
    assert got is token
    assert "tokenId" in str(record_tokenid[0].message)


def test_tokeninfo_deprecated_alias_access():
    token = TokenId.from_string("0.0.456")
    info = TokenInfo(token_id=token, total_supply=1000, is_deleted=True)

    # totalSupply -> total_supply
    with pytest.warns(FutureWarning) as record_supply:
        got = info.totalSupply
    assert got == 1000
    assert "totalSupply" in str(record_supply[0].message)

    # isDeleted -> is_deleted
    with pytest.warns(FutureWarning) as record_delete:
        got = info.isDeleted
    assert got is True
    assert "isDeleted" in str(record_delete[0].message)


def test_transactionreceipt_deprecated_alias_access():
    proto = MagicMock()
    proto.status = "OK"
    proto.HasField.return_value = False
    proto.serialNumbers = [1, 2, 3]

    tr = TransactionReceipt(receipt_proto=proto)

    # tokenId -> token_id
    with pytest.warns(FutureWarning) as record_token:
        got = tr.tokenId
    assert got is None
    assert "tokenId" in str(record_token[0].message)

    # topicId -> topic_id
    with pytest.warns(FutureWarning) as record_topic:
        got = tr.topicId
    assert got is None
    assert "topicId" in str(record_topic[0].message)

    # accountId -> account_id
    with pytest.warns(FutureWarning) as record_acc:
        acc = tr.accountId
    assert acc is None
    assert "accountId" in str(record_acc[0].message)

    # fileId -> file_id
    with pytest.warns(FutureWarning) as record_file:
        fileid = tr.fileId
    assert fileid is None
    assert "fileId" in str(record_file[0].message)

class DummyProto:
    """Stand‑in for proto_TokenInfo; uses real TokenID/AccountID so ._from_proto accepts them."""

    def __init__(self):
        self.name = "Foo"
        self.symbol = "F"
        self.decimals = 2
        self.totalSupply = 1_000
        self.deleted = False
        self.memo = "test"
        self.tokenType = TokenType.FUNGIBLE_COMMON.value
        self.maxSupply = 10_000
        self.ledger_id = b"\x00"
        self.metadata = b"\x01"

        # real protobuf messages for tokenId and treasury
        self.tokenId = TokenID(shardNum=0, realmNum=0, tokenNum=42)
        self.treasury = AccountID(shardNum=0, realmNum=0, accountNum=99)

        # empty key protos
        self.adminKey = Key()
        self.kycKey = Key()
        self.freezeKey = Key()
        self.wipeKey = Key()
        self.supplyKey = Key()
        self.metadata_key = Key()
        self.fee_schedule_key = Key()
        self.pause_key = Key()

        # statuses
        self.defaultFreezeStatus = TokenFreezeStatus.FREEZE_NOT_APPLICABLE.value
        self.defaultKycStatus = TokenKycStatus.KYC_NOT_APPLICABLE.value
        self.pause_status = TokenPauseStatus.PAUSE_NOT_APPLICABLE.value
        self.supplyType = SupplyType.FINITE.value

        # skip these branches
        self.autoRenewAccount = None
        self.autoRenewPeriod = None
        self.expiry = None


def test_camelcase_init_and_snake_field_assignment():
    tid = TokenId.from_string("0.0.123")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", FutureWarning)
        ti = TokenInfo(tokenId=tid, totalSupply=500, isDeleted=True)
        assert any("tokenId" in str(wi.message) for wi in w)
        assert any("totalSupply" in str(wi.message) for wi in w)
    assert ti.token_id == tid
    assert ti.total_supply == 500
    assert ti.is_deleted is True

def test_legacy_attribute_get_and_set_warns():
    ti = TokenInfo()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", FutureWarning)
        ti.adminKey = "AKey"
        assert any("adminKey=" in str(wi.message) for wi in w)
    assert ti.admin_key == "AKey"

    ti.default_freeze_status = TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", FutureWarning)
        val = ti.defaultFreezeStatus
        assert any("defaultFreezeStatus" in str(wi.message) for wi in w)
    assert isinstance(val, TokenFreezeStatus)

def test_setter_aliases_work_and_mutate_correct_field():
    ti = TokenInfo()
    ti.set_freezeKey(TokenFreezeStatus.FREEZE_NOT_APPLICABLE)
    assert ti.freeze_key == TokenFreezeStatus.FREEZE_NOT_APPLICABLE
    ti.set_defaultKycStatus(TokenKycStatus.KYC_NOT_APPLICABLE)
    assert ti.default_kyc_status == TokenKycStatus.KYC_NOT_APPLICABLE
    ti.set_pauseStatus(TokenPauseStatus.PAUSE_NOT_APPLICABLE)
    assert ti.pause_status == TokenPauseStatus.PAUSE_NOT_APPLICABLE
    ti.set_supplyType(SupplyType.INFINITE)
    assert ti.supply_type == SupplyType.INFINITE

def test_from_proto_and_to_string_contains_expected():
    proto = DummyProto()
    ti = TokenInfo._from_proto(proto)
    # core fields
    assert ti.name == "Foo"
    assert ti.symbol == "F"
    # repr uses snake_case
    s = str(ti)
    assert "token_id=" in s
    assert "name='Foo'" in s
    assert "total_supply=1000" in s

@pytest.mark.parametrize("field,value", [
    ("decimals", 8),
    ("memo", "hello"),
])
def test_snake_case_assignment_and_retrieval(field, value):
    ti = TokenInfo()
    setattr(ti, field, value)
    assert getattr(ti, field) == value