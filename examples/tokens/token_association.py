"""
Simple demonstration of TokenAssociation objects.

These objects commonly appear in TransactionRecord.automatic_token_associations
after the network automatically creates token associations during transfers.
They are read-only and informational only.
"""
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_association import TokenAssociation


def main():
    print("TokenAssociation Demo")
    print("====================\n")

    # 1. Creating a TokenAssociation
    assoc = TokenAssociation(
        token_id=TokenId.from_string("0.0.56789"),
        account_id=AccountId.from_string("0.0.98765")
    )

    print("1. Created TokenAssociation:")
    print(f"   Token:   {assoc.token_id}")
    print(f"   Account: {assoc.account_id}\n")

    # 2. Immutability demo
    print("2. Trying to modify (should fail):")
    try:
        assoc.token_id = TokenId.from_string("0.0.11111")
    except Exception as e:
        print(f"   → {type(e).__name__}: {e}\n")

    # 3. Protobuf round-trip
    print("3. Protobuf round-trip test:")
    proto = assoc._to_proto()
    restored = TokenAssociation._from_proto(proto)
    print(f"   Original == Restored: {restored == assoc}\n")

    print("Demo complete.")


if __name__ == "__main__":
    main()
    