import pytest

from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services import basic_types_pb2

pytestmark = pytest.mark.unit
def test_nft_id():
    #return true
    nftid_constructor_tokenid = TokenId(shard=0, realm=1, num=2)
    nftid_constructor_test = NftId(tokenId=nftid_constructor_tokenid, serialNumber=1234)

    assert str(nftid_constructor_test) == "0.1.2/1234"
    assert repr(nftid_constructor_test) == "NftId(tokenId=TokenId(shard=0, realm=1, num=2), serialNumber=1234)"
    assert nftid_constructor_test._to_proto().__eq__(
        basic_types_pb2.NftID(
            token_ID=basic_types_pb2.TokenID(shardNum=0, realmNum=1, tokenNum=2),
            serial_number=1234)
    )
    assert NftId._from_proto(
        nft_id_proto=basic_types_pb2.NftID(
            token_ID=basic_types_pb2.TokenID(shardNum=0, realmNum=1, tokenNum=2),
            serial_number=1234
        )
    ).__eq__(nftid_constructor_test)

    #return false
    with pytest.raises(TypeError):
        nftid_failed_constructor_tokenid1 = TokenId(shard=0, realm=1, num="A")
    with pytest.raises(TypeError):
        nftid_failed_constructor_tokenid = TokenId(shard=0, realm="b", num=1)
    with pytest.raises(TypeError):
        nftid_failed_constructor_tokenid = TokenId(shard='c', realm=1, num=1)
    with pytest.raises(TypeError):
        nftid_failed_constructor = NftId(tokenId=None, serialNumber=1234)
    with pytest.raises(TypeError):
        nftid_failed_constructor = NftId(tokenId=1234, serialNumber=1234)
    with pytest.raises(TypeError):
        nftid_failed_constructor = NftId(tokenId=TokenId(shard=0, realm=1, num=0), serialNumber="asdfasdfasdf")
    with pytest.raises(ValueError):
        nftid_failed_constructor = NftId(tokenId=TokenId(shard=0, realm=1, num=0), serialNumber=-1234)

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