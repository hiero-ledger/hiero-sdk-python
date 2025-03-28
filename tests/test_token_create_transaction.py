"""
Test cases for the TokenCreateTransaction class in the Hiero Python SDK.

This file contains unit tests for creating tokens, signing transactions,
and validating various parameters and behaviors for both fungible and non-fungible tokens.

Coverage includes:
- Building transaction bodies with and without keys
- Missing/invalid fields
- Signing and converting to protobuf
- Freeze logic checks
- Transaction execution error handling
"""

import re
import pytest
from unittest.mock import MagicMock, patch

# Hiero SDK imports
from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
    TokenKeys,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    transaction_pb2,
    transaction_body_pb2,
    transaction_contents_pb2,
    timestamp_pb2,
)
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId

def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time
    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)

    tx_id = TransactionId(
        valid_start=tx_timestamp,
        account_id=account_id_proto
    )
    return tx_id

########### Basic Tests for Building Transactions ###########

def test_build_transaction_body_without_key(mock_account_ids):
    """Test building a token creation transaction body without an admin, supply or freeze key."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    transaction_body = token_tx.build_transaction_body()

    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000
    # Ensure keys are not set
    assert not transaction_body.tokenCreation.HasField("adminKey")
    assert not transaction_body.tokenCreation.HasField("supplyKey")
    assert not transaction_body.tokenCreation.HasField("freezeKey")


def test_build_transaction_body(mock_account_ids):
    """Test building a token creation transaction body with valid values and admin, supply and freeze keys."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    # Mock admin key
    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b"admin_signature"
    private_key_admin.public_key().to_bytes_raw.return_value = b"admin_public_key"

    # Mock supply key
    private_key_supply = MagicMock()
    private_key_supply.sign.return_value = b"supply_signature"
    private_key_supply.public_key().to_bytes_raw.return_value = b"supply_public_key"

    # Mock freeze key
    private_key_freeze = MagicMock()
    private_key_freeze.sign.return_value = b"freeze_signature"
    private_key_freeze.public_key().to_bytes_raw.return_value = b"freeze_public_key"

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.transaction_id = generate_transaction_id(treasury_account)

    # Assign keys
    token_tx.set_admin_key(private_key_admin)
    token_tx.set_supply_key(private_key_supply)
    token_tx.set_freeze_key(private_key_freeze)

    token_tx.node_account_id = node_account_id

    transaction_body = token_tx.build_transaction_body()

    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000

    assert transaction_body.tokenCreation.adminKey.ed25519 == b"admin_public_key"
    assert transaction_body.tokenCreation.supplyKey.ed25519 == b"supply_public_key"
    assert transaction_body.tokenCreation.freezeKey.ed25519 == b"freeze_public_key"


@pytest.mark.parametrize(
    "token_name, token_symbol, decimals, initial_supply, token_type, expected_error",
    [
        # ------------------ Fungible Invalid Cases ------------------ #
        ("", "SYMB", 2, 100, TokenType.FUNGIBLE_COMMON, "Token name is required"),
        ("1"*101, "SYMB", 2, 100, TokenType.FUNGIBLE_COMMON,
            "Token name must be between 1 and 100 bytes"),
        ("\x00", "SYMB", 2, 100, TokenType.FUNGIBLE_COMMON,
            "Token name must not contain the Unicode NUL"),

        ("MyToken", "", 2, 100, TokenType.FUNGIBLE_COMMON, "Token symbol is required"),
        ("MyToken", "1"*101, 2, 100, TokenType.FUNGIBLE_COMMON,
            "Token symbol must be between 1 and 100 bytes"),
        ("MyToken", "\x00", 2, 100, TokenType.FUNGIBLE_COMMON,
            "Token symbol must not contain the Unicode NUL"),

        ("MyToken", "SYMB", -2, 100, TokenType.FUNGIBLE_COMMON,
            "Decimals must be a non-negative integer"),
        ("MyToken", "SYMB", 2, -100, TokenType.FUNGIBLE_COMMON,
            "Initial supply must be a non-negative integer"),
        ("MyToken", "SYMB", 2, 0, TokenType.FUNGIBLE_COMMON,
            "A Fungible Token requires an initial supply greater than zero"),
        ("MyToken", "SYMB", 2, 2**64, TokenType.FUNGIBLE_COMMON,
            "Initial supply cannot exceed"),

        # Valid fungible
        ("MyToken", "SYMB", 2, 100, TokenType.FUNGIBLE_COMMON, None),

        # ------------------ Non-Fungible Invalid Cases ------------------ #
        ("", "SYMB", 0, 0,  TokenType.NON_FUNGIBLE_UNIQUE, "Token name is required"),
        ("1"*101, "SYMB", 0, 0, TokenType.NON_FUNGIBLE_UNIQUE,
            "Token name must be between 1 and 100 bytes"),
        ("\x00", "SYMB", 0, 0, TokenType.NON_FUNGIBLE_UNIQUE,
            "Token name must not contain the Unicode NUL character"),

        ("MyNFTToken", "", 0, 0, TokenType.NON_FUNGIBLE_UNIQUE, "Token symbol is required"),
        ("MyNFTToken", "1"*101, 0, 0, TokenType.NON_FUNGIBLE_UNIQUE,
            "Token symbol must be between 1 and 100 bytes"),
        ("MyNFTToken", "\x00", 0, 0, TokenType.NON_FUNGIBLE_UNIQUE,
            "Token symbol must not contain the Unicode NUL character"),

        ("MyNFTToken", "SYMB", -2, 0, TokenType.NON_FUNGIBLE_UNIQUE,
            "Decimals must be a non-negative integer"),
        ("MyNFTToken", "SYMB", 2, 0, TokenType.NON_FUNGIBLE_UNIQUE,
            "A Non-fungible Unique Token must have zero decimals"),
        ("MyNFTToken", "SYMB", 0, 100, TokenType.NON_FUNGIBLE_UNIQUE,
            "A Non-fungible Unique Token requires an initial supply of zero"),

        # Valid non-fungible
        ("MyNFTToken", "SYMB", 0, 0, TokenType.NON_FUNGIBLE_UNIQUE, None),
    ],
)
def test_token_creation_validation(
    mock_account_ids,
    token_name,
    token_symbol,
    decimals,
    initial_supply,
    token_type,
    expected_error,
):
    """
    A single test covering both fungible and non-fungible tokens. It verifies:
      - Required fields
      - Byte-length constraints
      - NUL characters
      - Decimals & initialSupply rules specific to token_type
    """
    treasury_account, _, node_account_id, *_ = mock_account_ids

    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            # Create the TokenParams (no error yet, because validation is deferred)
            params = TokenParams(
                token_name=token_name,
                token_symbol=token_symbol,
                decimals=decimals,
                initial_supply=initial_supply,
                treasury_account_id=treasury_account,
                token_type=token_type,
            )
            # Building triggers validation
            tx = TokenCreateTransaction(params)
            tx.build_transaction_body() 
    else:
        # Valid scenario; no error expected
        params = TokenParams(
            token_name=token_name,
            token_symbol=token_symbol,
            decimals=decimals,
            initial_supply=initial_supply,
            treasury_account_id=treasury_account,
            token_type=token_type,
        )
        tx = TokenCreateTransaction(params)
        tx.operator_account_id = treasury_account
        tx.node_account_id = node_account_id

        body = tx.build_transaction_body()

        # Basic checks to confirm the fields are set properly
        assert body.tokenCreation.name == token_name
        assert body.tokenCreation.symbol == token_symbol
        assert body.tokenCreation.decimals == decimals
        assert body.tokenCreation.initialSupply == initial_supply


########### Tests for Signing and Protobuf Conversion ###########

def test_sign_transaction(mock_account_ids):
    """Test signing the token creation transaction that has multiple keys."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    # Mock keys
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b"admin_signature"
    private_key_admin.public_key().to_bytes_raw.return_value = b"admin_public_key"

    private_key_supply = MagicMock()
    private_key_supply.sign.return_value = b"supply_signature"
    private_key_supply.public_key().to_bytes_raw.return_value = b"supply_public_key"

    private_key_freeze = MagicMock()
    private_key_freeze.sign.return_value = b"freeze_signature"
    private_key_freeze.public_key().to_bytes_raw.return_value = b"freeze_public_key"

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_admin_key(private_key_admin)
    token_tx.set_supply_key(private_key_supply)
    token_tx.set_freeze_key(private_key_freeze)

    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    # Sign with both sign keys
    token_tx.sign(private_key) # Necessary
    token_tx.sign(private_key_admin) # Since admin key exists

    # Expect 2 sigPairs
    assert len(token_tx.signature_map.sigPair) == 2

    sig_pair = token_tx.signature_map.sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"

    sig_pair_admin = token_tx.signature_map.sigPair[1]
    assert sig_pair_admin.pubKeyPrefix == b"admin_public_key"
    assert sig_pair_admin.ed25519 == b"admin_signature"

    # Confirm that neither sigPair belongs to supply_key or freeze_key:
    for sig_pair in token_tx.signature_map.sigPair:
        assert sig_pair.pubKeyPrefix not in (b"supply_public_key", b"freeze_public_key")

def test_to_proto_without_keys(mock_account_ids):
    """Test protobuf conversion when keys are not set."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    # Mock treasury/operator key
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    # Sign with treasury key
    token_tx.sign(private_key)

    # Parse the TransactionBody starting with the outer wrapper
    proto_tx = token_tx.to_proto()
    assert len(proto_tx.signedTransactionBytes) > 0

    outer_tx = transaction_pb2.Transaction.FromString(proto_tx.SerializeToString())
    assert len(outer_tx.signedTransactionBytes) > 0

    signed_tx = transaction_contents_pb2.SignedTransaction.FromString(
        outer_tx.signedTransactionBytes
    )
    assert len(signed_tx.bodyBytes) > 0

    transaction_body = transaction_body_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

    # Verify the transaction built was correctly serialized to and from proto.
    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000

    assert not transaction_body.tokenCreation.HasField("adminKey")


def test_to_proto_with_keys(mock_account_ids):
    """Test converting the token creation transaction to protobuf format after signing."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    # Mock keys
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b"admin_signature"
    private_key_admin.public_key().to_bytes_raw.return_value = b"admin_public_key"

    private_key_supply = MagicMock()
    private_key_supply.sign.return_value = b"supply_signature"
    private_key_supply.public_key().to_bytes_raw.return_value = b"supply_public_key"

    private_key_freeze = MagicMock()
    private_key_freeze.sign.return_value = b"freeze_signature"
    private_key_freeze.public_key().to_bytes_raw.return_value = b"freeze_public_key"

    # Build the transaction
    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_admin_key(private_key_admin)
    token_tx.set_supply_key(private_key_supply)
    token_tx.set_freeze_key(private_key_freeze)

    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    # Sign with required sign keys
    token_tx.sign(private_key) 
    token_tx.sign(private_key_admin)

    # Convert to protobuf
    proto_tx = token_tx.to_proto()
    assert len(proto_tx.signedTransactionBytes) > 0

    # 1) Parse the outer Transaction
    outer_tx = transaction_pb2.Transaction.FromString(proto_tx.SerializeToString())
    assert len(outer_tx.signedTransactionBytes) > 0

    # 2) Parse the inner SignedTransaction
    signed_tx = transaction_contents_pb2.SignedTransaction.FromString(
        outer_tx.signedTransactionBytes
    )
    assert len(signed_tx.bodyBytes) > 0

    # 3) Finally parse the TransactionBody
    tx_body = transaction_body_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

    # Confirm fields set in the token creation portion of the TransactionBody
    assert tx_body.tokenCreation.name == "MyToken"
    assert tx_body.tokenCreation.adminKey.ed25519 == b"admin_public_key"
    assert tx_body.tokenCreation.supplyKey.ed25519 == b"supply_public_key"
    assert tx_body.tokenCreation.freezeKey.ed25519 == b"freeze_public_key"

def test_freeze_status_without_freeze_key(mock_account_ids):
    """
    Ensure a token is permanently frozen if freeze_default is True but no freeze key is provided.
    """
    treasury_account, *_ = mock_account_ids

    # Build NFT token params with freeze_default=True, but no freeze_key
    params = TokenParams(
        token_name="MyNFTToken",
        token_symbol="MTKNFT",
        decimals=0,
        initial_supply=0,
        treasury_account_id=treasury_account,
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
        freeze_default=True,
    )

    # Attempt to create the transaction
    with pytest.raises(ValueError, match="Token is permanently frozen"):
        TokenCreateTransaction(params, keys=TokenKeys()).build_transaction_body()

def test_transaction_execution_failure(mock_account_ids):
    """
    Ensure an exception is raised when transaction execution fails
    (e.g., precheck code is INVALID_SIGNATURE).
    """
    treasury_account, _, node_account_id, *_ = mock_account_ids

    token_tx = TokenCreateTransaction(
        TokenParams(
            token_name="MyToken",
            token_symbol="MTK",
            decimals=2,
            initial_supply=1000,
            treasury_account_id=treasury_account,
            token_type=TokenType.FUNGIBLE_COMMON,
        )
    )
    token_tx.node_account_id = node_account_id
    token_tx.transaction_id = generate_transaction_id(treasury_account)

    # Mock the client
    token_tx.client = MagicMock()

    with patch.object(token_tx.client.token_stub, "createToken") as mock_create_token:
        # Simulate an INVALID_SIGNATURE
        mock_create_token.return_value.nodeTransactionPrecheckCode = ResponseCode.INVALID_SIGNATURE
        expected_message = "Error during transaction submission: 7 (INVALID_SIGNATURE)"

        with pytest.raises(Exception, match=re.escape(expected_message)):
            # Attempt to execute
            token_tx._execute_transaction(token_tx.client, "mock_proto")

        mock_create_token.assert_called_once_with("mock_proto")

def test_overwrite_defaults(mock_account_ids):
    """
    Demonstrates that defaults in TokenCreateTransaction can be overwritten
    by calling set_* methods, and the final protobuf reflects the updated values.
    """
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    # Create a new TokenCreateTransaction with all default params
    token_tx = TokenCreateTransaction()

    # Assert the internal defaults.
    assert token_tx._token_params.token_name == "" #Empty String
    assert token_tx._token_params.token_symbol == "" #Empty String
    assert token_tx._token_params.treasury_account_id == AccountId(0, 0, 1)
    assert token_tx._token_params.decimals == 0
    assert token_tx._token_params.initial_supply == 0
    assert token_tx._token_params.token_type == TokenType.FUNGIBLE_COMMON

    # 3. Overwrite the defaults using set_* methods
    token_tx.set_token_name("MyUpdatedToken")
    token_tx.set_token_symbol("UPD")
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_decimals(5)
    token_tx.set_initial_supply(10000)

    # Set transaction/node IDs so can sign
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    # Mock a private key and sign the transaction
    private_key = MagicMock()
    private_key.sign.return_value = b"test_signature"
    private_key.public_key().to_bytes_raw.return_value = b"test_public_key"
    token_tx.sign(private_key)

    # Convert to protobuf transaction
    proto_tx = token_tx.to_proto()
    assert len(proto_tx.signedTransactionBytes) > 0, "Expected non-empty signedTransactionBytes"

    # # Deserialize the protobuf to verify the fields that actually got serialized
    # Parse the outer Transaction: the wrapper with just signedTransactionBytes
    # message Transaction {
    # bytes signedTransactionBytes = 5}
    outer_tx = transaction_pb2.Transaction.FromString(proto_tx.SerializeToString())
    assert len(outer_tx.signedTransactionBytes) > 0

    # Parse the inner SignedTransaction: Inside signedTransactionBytes is another message called SignedTransaction
    # message SignedTransaction {
    # bytes bodyBytes = 1;
    # SignatureMap sigMap = 2}
    signed_tx = transaction_contents_pb2.SignedTransaction.FromString(outer_tx.signedTransactionBytes)
    assert len(signed_tx.bodyBytes) > 0

    # Parse the TransactionBody from SignedTransaction.bodyBytes
    # bodyBytes: A byte array containing a serialized `TransactionBody`.
    tx_body = transaction_body_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

    # Check that updated values made it into tokenCreation
    assert tx_body.tokenCreation.name == "MyUpdatedToken"
    assert tx_body.tokenCreation.symbol == "UPD"
    assert tx_body.tokenCreation.decimals == 5
    assert tx_body.tokenCreation.initialSupply == 10000

    # Confirm no adminKey was set
    assert not tx_body.tokenCreation.HasField("adminKey")

def test_transaction_freeze_prevents_modification(mock_account_ids):
    """
    Test that after freeze() is called, attempts to modify TokenCreateTransaction
    parameters raise an exception indicating immutability.
    """
    treasury_account_id, _, _, _, _ = mock_account_ids

    transaction = TokenCreateTransaction()

    # Set some initial parameters
    transaction.set_token_name("TestName")
    transaction.set_token_symbol("TEST")
    transaction.set_initial_supply(1000)
    transaction.set_decimals(2)
    transaction.set_treasury_account_id(treasury_account_id)

    # Freeze the transaction
    transaction.freeze()

    # Attempt to overwrite after freeze - expect exceptions
    with pytest.raises(ValueError, match="Transaction is frozen and cannot be modified."):
        transaction.set_token_name("NewName")

    with pytest.raises(ValueError, match="Transaction is frozen and cannot be modified."):
        transaction.set_token_name("NEW")

    with pytest.raises(ValueError, match="Transaction is frozen and cannot be modified."):
        transaction.set_initial_supply(5000)

    with pytest.raises(ValueError, match="Transaction is frozen and cannot be modified."):
        transaction.set_decimals(8)

    with pytest.raises(ValueError, match="Transaction is frozen and cannot be modified."):
        transaction.set_token_type(TokenType.NON_FUNGIBLE_UNIQUE) # Should have defaulted to this

    # Confirm that values remain unchanged after freeze attempt
    assert transaction._token_params.token_name == "TestName"
    assert transaction._token_params.token_symbol == "TEST"    
    assert transaction._token_params.initial_supply == 1000
    assert transaction._token_params.decimals == 2
    assert transaction._token_params.treasury_account_id == treasury_account_id
    assert transaction._token_params.token_type == TokenType.FUNGIBLE_COMMON


def test_build_transaction_body_non_fungible(mock_account_ids):
    """
    Test building a token creation transaction body for a Non-Fungible Unique token
    with no admin, supply, or freeze key.
    """
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyNFT")
    token_tx.set_token_symbol("NFT")
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
    token_tx.set_decimals(0)         # NFTs must have 0 decimals
    token_tx.set_initial_supply(0)   # NFTs must have 0 initial supply

    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    # Build the transaction body
    transaction_body = token_tx.build_transaction_body()

    # Check NFT-specific fields
    assert transaction_body.tokenCreation.name == "MyNFT"
    assert transaction_body.tokenCreation.symbol == "NFT"
    assert transaction_body.tokenCreation.tokenType == TokenType.NON_FUNGIBLE_UNIQUE.value
    assert transaction_body.tokenCreation.decimals == 0
    assert transaction_body.tokenCreation.initialSupply == 0

    # No keys are set
    assert not transaction_body.tokenCreation.HasField("adminKey")
    assert not transaction_body.tokenCreation.HasField("supplyKey")
    assert not transaction_body.tokenCreation.HasField("freezeKey")

def test_build_and_sign_nft_transaction_to_proto(mock_account_ids):
    """
    Test building, signing, and protobuf serialization of 
    a valid Non-Fungible Unique token creation transaction.
    """
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    # Mock keys
    private_key_private = MagicMock()
    private_key_private.sign.return_value = b"private_signature"
    private_key_private.public_key().to_bytes_raw.return_value = b"private_public_key"

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b"admin_signature"
    private_key_admin.public_key().to_bytes_raw.return_value = b"admin_public_key"

    private_key_supply = MagicMock()
    private_key_supply.sign.return_value = b"supply_signature"
    private_key_supply.public_key().to_bytes_raw.return_value = b"supply_public_key"

    private_key_freeze = MagicMock()
    private_key_freeze.sign.return_value = b"freeze_signature"
    private_key_freeze.public_key().to_bytes_raw.return_value = b"freeze_public_key"

    # Build the transaction
    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyNFTToken")
    token_tx.set_token_symbol("NFT1")
    token_tx.set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
    token_tx.set_decimals(0)
    token_tx.set_initial_supply(0)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_admin_key(private_key_admin)
    token_tx.set_supply_key(private_key_supply)
    token_tx.set_freeze_key(private_key_freeze)

    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    # Sign the transaction
    token_tx.sign(private_key_private)
    token_tx.sign(private_key_admin)

    # Convert to protobuf (outer Transaction)
    proto_tx = token_tx.to_proto()
    assert len(proto_tx.signedTransactionBytes) > 0

    # Parse the outer Transaction
    outer_tx = transaction_pb2.Transaction.FromString(proto_tx.SerializeToString())
    assert len(outer_tx.signedTransactionBytes) > 0

    # Parse the inner SignedTransaction
    signed_tx = transaction_contents_pb2.SignedTransaction.FromString(outer_tx.signedTransactionBytes)
    assert len(signed_tx.bodyBytes) > 0

    # Finally parse the TransactionBody
    tx_body = transaction_body_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

    # Verify the NFT-specific fields
    assert tx_body.tokenCreation.name == "MyNFTToken"
    assert tx_body.tokenCreation.symbol == "NFT1"
    assert tx_body.tokenCreation.tokenType == TokenType.NON_FUNGIBLE_UNIQUE.value
    assert tx_body.tokenCreation.decimals == 0
    assert tx_body.tokenCreation.initialSupply == 0

    # Verify the keys are set in the final protobuf
    assert tx_body.tokenCreation.adminKey.ed25519 == b"admin_public_key"
    assert tx_body.tokenCreation.supplyKey.ed25519 == b"supply_public_key"
    assert tx_body.tokenCreation.freezeKey.ed25519 == b"freeze_public_key"
