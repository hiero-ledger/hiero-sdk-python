import pytest

from hedera_sdk_python.tokens.nft_id import NftId
from hedera_sdk_python.tokens.token_id import TokenId
from hedera_sdk_python.hapi.services import basic_types_pb2


def test_nft_id():
    #return true
    nftid_constructor_tokenid = TokenId(shard=0, realm=1, num=2)
    nftid_constructor_test = NftId(token_id=nftid_constructor_tokenid, serial_number=1234)

    assert nftid_constructor_test.is_valid() is True
    assert str(nftid_constructor_test) == "0.1.2/1234"
    assert repr(nftid_constructor_test) == "NftId(0.1.2/1234)"
    assert nftid_constructor_test.to_proto().__eq__(
        basic_types_pb2.NftID(
            token_ID=basic_types_pb2.TokenID(shardNum=0, realmNum=1, tokenNum=2),
            serial_number=1234)
    )
    assert NftId.from_proto(
        nft_id_proto=basic_types_pb2.NftID(
            token_ID=basic_types_pb2.TokenID(shardNum=0, realmNum=1, tokenNum=2),
            serial_number=1234
        )
    ).__eq__(nftid_constructor_test)

    #return false
    #NOTE: this looks super scummy, will check to see if
    # nesting errors of the same value in a with... works
    with pytest.raises(TypeError):
        nftid_failed_constructor_tokenid1 = TokenId(shard=0, realm=1, num="A")
    with pytest.raises(TypeError):
        nftid_failed_constructor_tokenid = TokenId(shard=0, realm="b", num=1)
    with pytest.raises(TypeError):
        nftid_failed_constructor_tokenid = TokenId(shard='c', realm=1, num=1)
    with pytest.raises(TypeError):
        nftid_failed_constructor = NftId(token_id=None, serial_number=1234)
    with pytest.raises(TypeError):
        nftid_failed_constructor = NftId(token_id=1234, serial_number=1234)
    with pytest.raises(TypeError):
        nftid_failed_constructor = NftId(token_id=TokenId(shard=0, realm=1, num=0), serial_number="asdfasdfasdf")
    with pytest.raises(ValueError):
        nftid_failed_constructor = NftId(token_id=TokenId(shard=0, realm=1, num=0), serial_number=-1234)

    with pytest.raises(TypeError):
        nftid_changed_constructor = NftId(token_id=TokenId(shard=1, realm=2, num=3), serial_number=1234)
        nftid_changed_constructor.tokenId = None
        nftid_changed_constructor.is_valid()

    with pytest.raises(TypeError):
        nftid_changed_constructor = NftId(token_id=TokenId(shard=1, realm=2, num=3), serial_number=1234)
        nftid_changed_constructor.tokenId = "None lol"
        nftid_changed_constructor.is_valid()

    with pytest.raises(TypeError):
        nftid_changed_constructor = NftId(token_id=TokenId(shard=1, realm=2, num=3), serial_number=1234)
        nftid_changed_constructor.serialNumber = "asdfasdf"
        nftid_changed_constructor.is_valid()

    with pytest.raises(ValueError):
        nftid_changed_constructor = NftId(token_id=TokenId(shard=1, realm=2, num=3), serial_number=1234)
        nftid_changed_constructor.serialNumber = -1234
        nftid_changed_constructor.is_valid()

    nftid_toproto_invalid = NftId(token_id=TokenId(shard=0, realm=1, num=0), serial_number=1234)
    with pytest.raises(TypeError):
        nftid_toproto_invalid.tokenId = None
        nftid_toproto_invalid.to_proto()

    nftid_toproto_invalid = NftId(token_id=TokenId(shard=0, realm=1, num=0), serial_number=1234)
    with pytest.raises(TypeError):
        nftid_toproto_invalid.tokenId = "None"
        nftid_toproto_invalid.to_proto()

    nftid_toproto_invalid = NftId(token_id=TokenId(shard=0, realm=1, num=0), serial_number=1234)
    with pytest.raises(ValueError):
        nftid_toproto_invalid.serialNumber = -2134
        nftid_toproto_invalid.to_proto()

    #don't need to test protobuf cause its final and type checked
    with pytest.raises(ValueError):
        NftId.from_string("")

    with pytest.raises(TypeError):
        NftId.from_string(None)

    with pytest.raises(TypeError):
        NftId.from_string(134)

    fail_str = "0.0.0.0/19"
    with pytest.raises(ValueError):
        NftId.from_string(fail_str)

    fail_str = "0.0.a/19"
    with pytest.raises(ValueError):
        NftId.from_string(fail_str)

    fail_str = "0.a.3/19"
    with pytest.raises(ValueError):
        NftId.from_string(fail_str)

    fail_str = "a.3.3/19"
    with pytest.raises(ValueError):
        NftId.from_string(fail_str)