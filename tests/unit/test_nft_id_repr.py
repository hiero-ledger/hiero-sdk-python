import pytest

from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services import basic_types_pb2

pytestmark = pytest.mark.unit


def test_nft_id_repr():
    token_id = TokenId(0, 0, 123)
    nft_id = NftId(token_id, 5)
    assert repr(nft_id) == "NftId(token_id = 0.0.123, serial_number = 5)"