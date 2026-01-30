from examples.worked_example import (
    build_crypto_get_info_query,
    serialize_and_parse_query,
    mock_crypto_get_info_response,
    serialize_and_parse_response,
)
 

def test_query_round_trip():
    query = build_crypto_get_info_query(account_num=1234)
    parsed = serialize_and_parse_query(query)

    assert parsed.cryptoGetInfo.accountID.accountNum == 1234


def test_response_round_trip():
    response = mock_crypto_get_info_response(account_num=1234)
    parsed = serialize_and_parse_response(response)

    info = parsed.cryptoGetInfo.accountInfo

    assert info.accountID.accountNum == 1234
    assert info.balance == 100_000
    assert info.deleted is False
