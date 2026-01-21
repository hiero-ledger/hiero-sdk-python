import re
import struct
import requests

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

ID_REGEX = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([a-z]{5}))?$")

MULTIPLIER = 1000003
P3 = 26**3
P5 = 26**5

def parse_from_string(address: str):
    """
    Parse an address string of the form: <shard>.<realm>.<num>[-<checksum>]
    Examples:
        "0.0.123"
        "0.0.123-abcde"

    Returns:
        An instance of cls with shard, realm, num, and optional checksum.
    """
    match = ID_REGEX.match(address)
    if not match:
        raise ValueError("Invalid format for entity ID")

    shard, realm, num, checksum = match.groups()

    return shard, realm, num, checksum

def generate_checksum(ledger_id: bytes, address: str) -> str:
    """
    Compute the 5-character checksum for a Hiero entity ID string (HIP-15).
    
    Args:
        ledger_id: The ledger identifier as raw bytes (e.g., b"\x00" for mainnet).
        address: A string of the form "shard.realm.num" (e.g., "0.0.123").
    
    Returns:
        A 5-letter checksum string (e.g., "kfmza").
    """
    # Convert "0.0.123" into a digit list with '.' as 10
    d = []
    for ch in address:
        if ch == '.':
            d.append(10)
        else:
            d.append(int(ch))

    # Initialize running sums
    sd0 = 0  # sum of digits at even indices mod 11
    sd1 = 0  # sum of digits at odd indices mod 11
    sd = 0   # weight sum of all position mod P3

    for i in range(len(d)):
        sd = (sd * 31 + d[i]) % P3
        if i % 2 == 0:
            sd0 = (sd0 + d[i]) % 11
        else:
            sd1 = (sd1 + d[i]) % 11

    # Compute hash of ledger ID bytes (padded with six zeros)
    sh = 0
    h = list(ledger_id or b"")
    h += [0] * 6

    for i in range(len(h)):
        sh = (sh * 31 + h[i]) % P5

    cp = ((((len(address) % 5) * 11 + sd0) * 11 + sd1) * P3 + sd + sh) % P5
    cp = (cp * MULTIPLIER) % P5

    letter = []

    for _ in range(5):
        letter.append(chr(ord('a') + (cp % 26)))
        cp //= 26

    return "".join(reversed(letter))

def validate_checksum(shard: int, realm: int, num: int, checksum: str | None, client: "Client") -> None:
    """
    Validate a Hiero entity ID checksum against the current client's ledger.

    Args:
        shard: Shard number of the entity ID.
        realm: Realm number of the entity ID.
        num: Entity number (account, token, topic, etc.).
        checksum: The 5-letter checksum string to validate.
        client: The Hiero client, which holds the target ledger_id.

    Raises:
        ValueError: If the ledger ID is missing or if the checksum is invalid.
    """
    # If no checksum present then return.
    if checksum is None:
        return

    ledger_id = client.network.ledger_id
    if not ledger_id:
        raise ValueError("Missing ledger ID in client")

    address = format_to_string(shard, realm, num)
    expected_checksum = generate_checksum(ledger_id, address)

    if expected_checksum != checksum:
        raise ValueError(f"Checksum mismatch for {address}")

def format_to_string(shard: int, realm: int, num: int) -> str:
    """
    Convert an entity ID into its standard string representation.
    """
    return f"{shard}.{realm}.{num}"

def format_to_string_with_checksum(shard: int, realm: int, num: int, client: "Client") -> str:
    """
    Convert an entity ID into its string representation with checksum.
    """
    ledger_id = client.network.ledger_id
    if not ledger_id:
        raise ValueError("Missing ledger ID in client")

    base_str = format_to_string(shard, realm, num)
    return f"{base_str}-{generate_checksum(ledger_id, format_to_string(shard, realm, num))}"

def perform_query_to_mirror_node(url: str, timeout: float=10) -> Dict[str, Any]:
    """Perform a GET request to the Hedera Mirror Node REST API."""
    if not isinstance(url, str) or not url:
        raise ValueError("url must be a non-empty string")

    try:
        response: requests.Response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        return response.json()
    
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        raise RuntimeError(f"Mirror node request failed for {url}: {e}") from e

    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Mirror node request timed out for {url}") from e

    except requests.RequestException as e:
        raise RuntimeError(f"Unexpected error while querying mirror node: {url}") from e
    
def to_solidity_address(shard: int, realm: int, num: int) -> str:
    """Convert entity ID components to a 20-byte Solidity-style address (long-zero format)."""
    # Check shard fits in 32-bit range
    if shard.bit_length() > 31:
        raise ValueError(f"shard out of 32-bit range {shard}")

    # Pack into 20 bytes: shard(4 bytes), realm(8 bytes), num(8 bytes) (big-endian)
    raw = struct.pack(">iqq", shard, realm, num)

    return raw.hex()
