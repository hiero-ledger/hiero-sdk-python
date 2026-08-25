"""

Example: Token Id.

uv run examples/tokens/token_id.py
python examples/tokens/token_id.py
"""

from hiero_sdk_python import Client, Network
from hiero_sdk_python.tokens.token_id import TokenId


def create_token_id() -> TokenId:
    """Create a TokenId manually."""
    token_id = TokenId(shard=0, realm=0, num=1234)

    print(f"  Shard: {token_id.shard}")
    print(f"  Realm: {token_id.realm}")
    print(f"  Num: {token_id.num}")
    print(f"  TokenId: {token_id}")

    return token_id


def parse_token_id() -> TokenId:
    """Parse a TokenId from string representation."""
    token_id_str = "0.0.1234"
    token_id = TokenId.from_string(token_id_str)
    manually_constructed_token_id = TokenId(shard=0, realm=0, num=1234)

    print(f"  Shard: {token_id.shard}")
    print(f"  Realm: {token_id.realm}")
    print(f"  Num: {token_id.num}")
    print(f"  Parsed TokenId equals manually constructed TokenId: {manually_constructed_token_id == token_id}")

    return token_id


def parse_bad_token_id() -> None:
    """Parse an invalid token and handle resulting error."""
    try:
        TokenId.from_string("not-a-token-id")
    except ValueError as e:
        print(f"  Error: {e}")


def convert_to_proto_and_back(token_id: TokenId) -> TokenId:
    """Convert a TokenId to protobuf and back."""
    # Leading underscore marks _to_proto and _from_proto as internal methods that users normally never call
    # This example shows how the SDK communicates with the network
    proto = token_id._to_proto()
    token_id = TokenId._from_proto(proto)

    print(f"  Shard: {token_id.shard}")
    print(f"  Realm: {token_id.realm}")
    print(f"  Num: {token_id.num}")

    return token_id


def show_with_checksum(client: Client, token_id: TokenId) -> None:
    """Display TokenId with checksum."""
    # Checksum is network-specific so a Client is required
    # Checksum generated for testnet will not validate on mainnet
    token_id_with_checksum = token_id.to_string_with_checksum(client)

    print(f"  TokenId with checksum: {token_id_with_checksum}")


def main() -> None:
    """Demonstrate TokenId functionality."""
    token_id = TokenId(shard=0, realm=0, num=1234)
    network = Network("testnet")
    client = Client(network)

    # Create a TokenId
    create_token_id()

    # Parse a TokenId from string representation
    parse_token_id()

    # Parse an invalid token and handle error
    parse_bad_token_id()

    # Convert a TokenId to protobuf and back
    convert_to_proto_and_back(token_id)

    # Display TokenId with checksum
    show_with_checksum(client, token_id)


if __name__ == "__main__":
    main()
