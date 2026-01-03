"""
uv run examples/account/account_info.py
"""

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_relationship import TokenRelationship
from hiero_sdk_python.account.account_info import AccountInfo


def create_mock_account_id() -> AccountId:
    """Create a mock AccountId."""
    return AccountId.from_string("0.0.1234")


def create_mock_public_key() -> PublicKey:
    """Generate a random ED25519 public key for demonstration."""
    private_key_demo = PrivateKey.generate_ecdsa()
    public_key_demo = private_key_demo.public_key()
    return public_key_demo


def create_mock_balance() -> Hbar:
    """Return a mock account balance."""
    return Hbar(100)


def create_mock_expiration_time() -> Timestamp:
    """Return a sample expiration timestamp (arbitrary future date)."""
    return Timestamp(seconds=1736539200, nanos=100)


def create_mock_auto_renew_period() -> Duration:
    """Return a 90-day auto-renew period."""
    return Duration(seconds=7776000)


def create_mock_token_relationship() -> TokenRelationship:
    """Create a sample token relationship with a mock token."""
    token_id = TokenId.from_string("0.0.9999")
    return TokenRelationship(token_id=token_id, balance=50)


def build_mock_account_info() -> AccountInfo:
    """Construct a complete AccountInfo instance manually (no network calls)."""
    info = AccountInfo()
    info.account_id = create_mock_account_id()
    info.key = create_mock_public_key()
    info.balance = create_mock_balance()
    info.expiration_time = create_mock_expiration_time()
    info.auto_renew_period = create_mock_auto_renew_period()
    info.token_relationships = [create_mock_token_relationship()]
    info.account_memo = "Mock Account for Example"
    return info


def print_account_info(info: AccountInfo) -> None:
    """Pretty-print key AccountInfo fields."""
    print("📜 AccountInfo String Representation:")
    print(info)


def main():
    """Run the AccountInfo example."""
    info = build_mock_account_info()
    print_account_info(info)


if __name__ == "__main__":
    main()
