"""
uv run examples/account/account_id.py
python examples/account/account_id.py

This example demonstrates various ways to use the AccountId class:
1. Creating a standard AccountId
2. Parsing AccountId from a string
3. Comparing AccountId instances
4. Creating an AccountId with a public key alias
"""

from hiero_sdk_python import AccountId, PrivateKey


def create_standard_account_id():
    """
    Demonstrates creating a standard AccountId with shard, realm, and num.

    The standard format is: shard.realm.num (e.g., 0.0.123)
    """
    print("\n=== Example 1: Creating a Standard AccountId ===")

    # create an AccountId with default shard and realm (0.0) and account number 123
    account_id = AccountId(shard=0, realm=0, num=123)

    print(f"Created AccountId: {account_id}")
    print(f"  Shard: {account_id.shard}")
    print(f"  Realm: {account_id.realm}")
    print(f"  Account Number: {account_id.num}")
    print(f"  String representation: {str(account_id)}")

    return account_id


def parse_account_id_from_string():
    """
    Demonstrates parsing an AccountId from a string.

    The string format should be: 'shard.realm.num'
    """
    print("\n=== Example 2: Parsing AccountId from String ===")

    # Parse AccountId from a string
    account_id_str = "0.0.456789"
    account_id = AccountId.from_string(account_id_str)

    print(f"Parsed AccountId from string: '{account_id_str}'")
    print(f"  Shard: {account_id.shard}")
    print(f"  Realm: {account_id.realm}")
    print(f"  Account Number: {account_id.num}")
    print(f"  String representation: {str(account_id)}")

    return account_id


def compare_account_ids():
    """
    Demonstrates comparing AccountId instances for equality.

    Two AccountIds are equal if they have the same shard, realm, num, and alias_key.
    """
    print("\n=== Example 3: Comparing AccountId Instances ===")

    # Create two identical AccountIds
    account_id1 = AccountId(shard=0, realm=0, num=100)
    account_id2 = AccountId(shard=0, realm=0, num=100)

    # Create a different AccountId
    account_id3 = AccountId(shard=0, realm=0, num=200)

    print(f"AccountId 1: {account_id1}")
    print(f"AccountId 2: {account_id2}")
    print(f"AccountId 3: {account_id3}")

    print(f"\nAre AccountId 1 and 2 equal? {account_id1 == account_id2}")
    print(f"Are AccountId 1 and 3 equal? {account_id1 == account_id3}")

    # Demonstrate hash equality (useful for sets and dictionaries)
    print(f"\nHash of AccountId 1: {hash(account_id1)}")
    print(f"Hash of AccountId 2: {hash(account_id2)}")
    print(f"Hash of AccountId 3: {hash(account_id3)}")
    print(
        f"Are hashes of AccountId 1 and 2 equal? {hash(account_id1) == hash(account_id2)}"
    )


def create_account_id_with_alias():
    """
    Demonstrates creating an AccountId with a public key alias.

    An alias is a public key (ED25519 or ECDSA) that can be used instead of
    an account number to identify an account.
    """
    print("\n=== Example 4: Creating AccountId with Public Key Alias ===")

    # Generate a new private key and get its public key
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()

    # Create an AccountId with a public key alias
    account_id_with_alias = AccountId(shard=0, realm=0, num=0, alias_key=public_key)

    print(f"Created AccountId with alias: {account_id_with_alias}")
    print(f"  Shard: {account_id_with_alias.shard}")
    print(f"  Realm: {account_id_with_alias.realm}")
    print(f"  Alias Key: {account_id_with_alias.alias_key.to_string()}")
    print(f"  String representation: {str(account_id_with_alias)}")
    print(f"  Repr representation: {repr(account_id_with_alias)}")

    return account_id_with_alias


def main():
    """
    Main function that runs all AccountId examples.
    """
    print("=" * 60)
    print("AccountId Examples")
    print("=" * 60)

    # ex 1: Create a standard AccountId
    create_standard_account_id()

    # ex 2: Parse AccountId from string
    parse_account_id_from_string()

    # ex 3: Compare AccountId instances
    compare_account_ids()

    # ex 4: Create AccountId with public key alias
    create_account_id_with_alias()

    print("\n" + "=" * 60)
    print("All AccountId examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
