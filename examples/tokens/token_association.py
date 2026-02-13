# examples/tokens/token_association.py
"""
Simple demonstration of TokenAssociation objects.

Shows local usage and simulates how you would inspect automatic associations
from a real transaction record.

Real TokenAssociation instances come from TransactionRecord.automatic_token_associations
after network-triggered auto-associations (e.g. transfers with available slots).
They are informational only — use TokenAssociateTransaction to create associations.
"""

from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_association import TokenAssociation


class MockTransactionRecord:
    """Fake record for demo purposes — mimics what get_record() returns."""
    def __init__(self, associations):
        self.automatic_token_associations = associations


def main():
    print("TokenAssociation Simple Demo + Mock Inspection")
    print("==============================================")
    print("All examples are local — no network calls are made.\n")

    # 1. Local example
    assoc = TokenAssociation(
        token_id=TokenId.from_string("0.0.56789"),
        account_id=AccountId.from_string("0.0.98765")
    )
    print("1. Example TokenAssociation (local):")
    print(f"   {assoc}\n")

    # 2. Immutability demo
    print("2. Trying to modify (should fail):")
    try:
        assoc.token_id = TokenId.from_string("0.0.11111")
    except Exception as e:
        print(f"   → {type(e).__name__}: {e}\n")

    # 3. Protobuf round-trip
    print("3. Protobuf round-trip:")
    proto = assoc._to_proto()
    restored = TokenAssociation._from_proto(proto)
    print(f"   Original == Restored: {restored == assoc}\n")

    # 4–5. Simulate real-world inspection using mock record
    print("4–5. Simulating real usage: Inspecting automatic associations")
    print("   (In real code this comes from record = response.get_record(client))\n")

    # Mock some associations (as if a transfer just happened)
    mock_assocs = [
        TokenAssociation(
            token_id=TokenId.from_string("0.0.56789"),
            account_id=AccountId.from_string("0.0.98765")
        ),
        # Could add more if multiple tokens were transferred
    ]

    mock_record = MockTransactionRecord(mock_assocs)

    # ------------------------------------------------------------
    # 5. Inspect automatic associations (exact reviewer-suggested code)
    # ------------------------------------------------------------
    if not mock_record.automatic_token_associations:
        print("No automatic associations found.")
    else:
        print("Automatic associations created:")
        for assoc in mock_record.automatic_token_associations:
            print(f" Type: {type(assoc).__name__}")
            print(f" Token {assoc.token_id} → Account {assoc.account_id}")

    print("\nDemo complete.")


if __name__ == "__main__":
    main()