# examples/tokens/token_association.py
"""
Simple examples demonstrating the TokenAssociation class.

TokenAssociation is an immutable value object that represents a link between
a token and an account. It most commonly appears in:

- TransactionRecord.automatic_token_associations
  (automatic associations created by the network during transfers, airdrops, etc.)
"""

from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_association import TokenAssociation

def main():
    print("TokenAssociation Examples")
    print("=========================")

    # 1. Creating a TokenAssociation instance
    assoc = TokenAssociation(
        token_id=TokenId.from_string("0.0.1234"),
        account_id=AccountId.from_string("0.0.5678")
    )
    print("\n1. Created association:")
    print(f"   {assoc}")
    # → TokenAssociation(token_id=0.0.1234, account_id=0.0.5678)

    # 2. Immutability (frozen dataclass)
    print("\n2. Trying to modify (should fail):")
    try:
        assoc.token_id = TokenId.from_string("0.0.9999")
    except Exception as e:
        print(f"   → {type(e).__name__}: {e}")
        # → FrozenInstanceError: cannot assign to field 'token_id'

    # 3. Protobuf round-trip (used during serialization/deserialization)
    print("\n3. Protobuf round-trip:")
    proto = assoc._to_proto()
    restored = TokenAssociation._from_proto(proto)
    print(f"   Original == Restored: {restored == assoc}")
    print(f"   Restored: {restored}")
    # → True + same string representation

    # 4. Typical real-world usage pattern
    print("\n4. Typical usage when reading a transaction record:")
    print("   # Assuming you have a TransactionRecord from the network")
    print("   # for assoc in record.automatic_token_associations:")
    print("   #     print(f'Auto-associated {assoc.token_id} to {assoc.account_id}')")

if __name__ == "__main__":
    main()
    