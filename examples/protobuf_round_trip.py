"""
Worked Example: Hedera Protobuf Round Trip

This script demonstrates constructing, serializing, and deserializing
Hedera protobuf messages without connecting to the network. It shows:
- Building a CryptoGetInfoQuery with an AccountID
- Wrapping queries in Hedera's Query envelope
- Serializing and parsing protobuf messages
- Extracting data from parsed responses

This example accompanies the ProtoBuff Training documentation.
"""
from hiero_sdk_python.hapi.services import (
    query_pb2,
    crypto_get_info_pb2,
    basic_types_pb2,
    response_pb2,
)


def build_crypto_get_info_query(account_num: int) -> query_pb2.Query:
    crypto_info = crypto_get_info_pb2.CryptoGetInfoQuery()

    account_id = basic_types_pb2.AccountID(
        shardNum=0,
        realmNum=0,
        accountNum=account_num,
    )

    crypto_info.accountID.CopyFrom(account_id)

    query = query_pb2.Query()
    query.cryptoGetInfo.CopyFrom(crypto_info)

    return query


def serialize_and_parse_query(query: query_pb2.Query) -> query_pb2.Query:
    serialized = query.SerializeToString()

    parsed = query_pb2.Query()
    parsed.ParseFromString(serialized)

    return parsed


def mock_crypto_get_info_response(account_num: int) -> response_pb2.Response:
    response = response_pb2.Response()
    crypto_resp = response.cryptoGetInfo

    crypto_resp.header.nodeTransactionPrecheckCode = 0

    crypto_resp.accountInfo.accountID.CopyFrom(
        basic_types_pb2.AccountID(
            shardNum=0,
            realmNum=0,
            accountNum=account_num,
        )
    )

    crypto_resp.accountInfo.balance = 100_000
    crypto_resp.accountInfo.deleted = False

    return response


def serialize_and_parse_response(
    response: response_pb2.Response,
) -> response_pb2.Response:
    serialized = response.SerializeToString()

    parsed = response_pb2.Response()
    parsed.ParseFromString(serialized)

    return parsed


def main():
    query = build_crypto_get_info_query(account_num=1234)
    parsed_query = serialize_and_parse_query(query)

    print("Parsed Query:")
    print(parsed_query)

    response = mock_crypto_get_info_response(account_num=1234)
    parsed_response = serialize_and_parse_response(response)

    print("\nParsed Response:")
    print(parsed_response)

    account_info = parsed_response.cryptoGetInfo.accountInfo

    print("\nExtracted Account Info:")
    print("Account ID:", account_info.accountID.accountNum)
    print("Balance:", account_info.balance)
    print("Deleted:", account_info.deleted)


if __name__ == "__main__":
    main()
