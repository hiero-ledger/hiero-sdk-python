import pytest
from unittest.mock import MagicMock

from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_info import TokenInfo
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.tokens.token_id import TokenId

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