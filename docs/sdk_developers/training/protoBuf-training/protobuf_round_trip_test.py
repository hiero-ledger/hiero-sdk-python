from examples.protobuf_round_trip import (
    build_crypto_get_info_query,
    serialize_and_parse_query,
    mock_crypto_get_info_response,
    serialize_and_parse_response,
)
 

def test_query_round_trip():
    query = build_crypto_get_info_query(account_num=1234)
    parsed = serialize_and_parse_query(query)

    assert parsed.cryptoGetInfo.accountID.accountNum == 1234, (
        f"Expected accountNum 1234, got {parsed.cryptoGetInfo.accountID.accountNum}"
    )


def test_response_round_trip():
    response = mock_crypto_get_info_response(account_num=1234)
    parsed = serialize_and_parse_response(response)

    info = parsed.cryptoGetInfo.accountInfo

    assert info.accountID.accountNum == 1234, (
        f"Expected accountNum 1234, got {info.accountID.accountNum}"
    )
    assert info.balance == 100_000, f"Expected balance 100000, got {info.balance}"
    assert info.deleted is False, f"Expected deleted=False, got {info.deleted}"

def test_query_round_trip_account_num_zero():
    query = build_crypto_get_info_query(account_num=0)
    parsed = serialize_and_parse_query(query)

    assert parsed.cryptoGetInfo.accountID.accountNum == 0

def test_response_round_trip_account_num_zero():
    response = mock_crypto_get_info_response(account_num=0)
    parsed = serialize_and_parse_response(response)

    info = parsed.cryptoGetInfo.accountInfo
    assert info.accountID.accountNum == 0

def test_query_round_trip_large_account_num():
    large_account_num = 2**31 - 1  # or any suitably large int

    query = build_crypto_get_info_query(account_num=large_account_num)
    parsed = serialize_and_parse_query(query)

    assert parsed.cryptoGetInfo.accountID.accountNum == large_account_num

def test_response_round_trip_large_account_num():
    large_account_num = 2**31 - 1

    response = mock_crypto_get_info_response(account_num=large_account_num)
    parsed = serialize_and_parse_response(response)

    info = parsed.cryptoGetInfo.accountInfo
    assert info.accountID.accountNum == large_account_num
