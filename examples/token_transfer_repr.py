"""
Example demonstrating the __repr__ method of TokenTransfer class.

This example shows how to use the __repr__ method for debugging and 
object representation purposes.

Usage:
    uv run examples/token_transfer_repr.py
    python examples/token_transfer_repr.py
"""

from hiero_sdk_python import TokenId, AccountId
from hiero_sdk_python.tokens.token_transfer import TokenTransfer


def demonstrate_repr():
    """
    Demonstrates the difference between __str__ and __repr__ methods
    for the TokenTransfer class.
    """
    print("=" * 70)
    print("TokenTransfer __repr__ Method Demonstration")
    print("=" * 70)

    # Create sample TokenTransfer instances
    token_id = TokenId(shard=0, realm=0, num=12345)
    account_id = AccountId(shard=0, realm=0, num=67890)

    # Example 1: Basic TokenTransfer
    print("\n1. Basic TokenTransfer:")
    print("-" * 70)
    transfer1 = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=100,
        expected_decimals=None,
        is_approved=False
    )

    print(f"str(transfer1):  {str(transfer1)}")
    print(f"repr(transfer1): {repr(transfer1)}")

    # Example 2: TokenTransfer with expected_decimals
    print("\n2. TokenTransfer with expected_decimals:")
    print("-" * 70)
    transfer2 = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=1000,
        expected_decimals=2,
        is_approved=False
    )

    print(f"str(transfer2):  {str(transfer2)}")
    print(f"repr(transfer2): {repr(transfer2)}")

    # Example 3: Approved TokenTransfer
    print("\n3. Approved TokenTransfer:")
    print("-" * 70)
    transfer3 = TokenTransfer(
        token_id=token_id,
        account_id=account_id,
        amount=500,
        expected_decimals=2,
        is_approved=True
    )

    print(f"str(transfer3):  {str(transfer3)}")
    print(f"repr(transfer3): {repr(transfer3)}")

    # Example 4: Using repr() in debugging scenarios
    print("\n4. Debugging with repr():")
    print("-" * 70)
    transfers = [transfer1, transfer2, transfer3]
    print("List of transfers using repr():")
    for i, transfer in enumerate(transfers, 1):
        print(f"  Transfer {i}: {repr(transfer)}")

    # Example 5: Demonstrating repr() in collections
    print("\n5. TokenTransfer in dictionary (uses repr()):")
    print("-" * 70)
    transfer_dict = {
        "transfer_1": transfer1,
        "transfer_2": transfer2,
        "transfer_3": transfer3
    }
    print(f"Dictionary: {transfer_dict}")

    print("\n" + "=" * 70)
    print("Key Differences:")
    print("=" * 70)
    print("• __str__():  Human-readable representation (for end users)")
    print("• __repr__(): Unambiguous representation (for developers/debugging)")
    print("• repr() uses !r format specifier to show quoted strings")
    print("• repr() output can ideally be used to recreate the object")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_repr()
