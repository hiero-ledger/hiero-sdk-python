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

import datetime
import pytest
from unittest.mock import MagicMock, patch

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
    TokenKeys,
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    transaction_pb2,
    transaction_pb2,
    transaction_contents_pb2,
    timestamp_pb2,
)
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

pytestmark = pytest.mark.unit

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

# This test uses fixture mock_account_ids as parameter
def test_build_transaction_body_without_key(mock_account_ids):
    """Test building a token creation transaction body without an admin, supply or freeze key."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_memo("Token Memo")
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    transaction_body = token_tx.build_transaction_body()

    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000
    assert transaction_body.tokenCreation.memo == "Token Memo"
    assert transaction_body.tokenCreation.autoRenewPeriod == Duration(7890000)._to_proto() # Default value of 90days.
    assert not transaction_body.tokenCreation.HasField('expiry') # By default, this is set to "now + AUTO_RENEW_PERIOD" (90 days).
    # Ensure keys are not set
    assert not transaction_body.tokenCreation.HasField("adminKey")
    assert not transaction_body.tokenCreation.HasField("supplyKey")
    assert not transaction_body.tokenCreation.HasField("freezeKey")
    assert not transaction_body.tokenCreation.HasField("wipeKey")
    assert not transaction_body.tokenCreation.HasField("metadata_key")
    assert not transaction_body.tokenCreation.HasField("pause_key")
    assert not transaction_body.tokenCreation.HasField("fee_schedule_key")

# This test uses fixture mock_account_ids as parameter
def test_build_transaction_body(mock_account_ids):
    """Test building a token creation transaction body with valid values and admin, supply and freeze keys."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    # Generate real private keys for all key types
    private_key_admin = PrivateKey.generate_ed25519()
    private_key_supply = PrivateKey.generate_ed25519()
    private_key_freeze = PrivateKey.generate_ed25519()
    private_key_wipe = PrivateKey.generate_ed25519()
    private_key_metadata = PrivateKey.generate_ed25519()
    private_key_kyc = PrivateKey.generate_ed25519()
    private_key_fee_schedule = PrivateKey.generate_ed25519()

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
    token_tx.set_wipe_key(private_key_wipe)
    token_tx.set_metadata_key(private_key_metadata)
    token_tx.set_kyc_key(private_key_kyc)
    token_tx.set_fee_schedule_key(private_key_fee_schedule)
    token_tx.node_account_id = node_account_id

    transaction_body = token_tx.build_transaction_body()

    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000

    assert transaction_body.tokenCreation.adminKey == private_key_admin.public_key()._to_proto()
    assert transaction_body.tokenCreation.supplyKey == private_key_supply.public_key()._to_proto()
    assert transaction_body.tokenCreation.freezeKey == private_key_freeze.public_key()._to_proto()
    assert transaction_body.tokenCreation.wipeKey == private_key_wipe.public_key()._to_proto()
    assert transaction_body.tokenCreation.metadata_key == private_key_metadata.public_key()._to_proto()
    assert transaction_body.tokenCreation.kycKey == private_key_kyc.public_key()._to_proto()
    assert transaction_body.tokenCreation.fee_schedule_key == private_key_fee_schedule.public_key()._to_proto()

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

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token creation transaction that has multiple keys."""
    treasury_account, _, _, _, _ = mock_account_ids

    # Mock keys
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b"admin_signature"
    private_key_admin.public_key().to_bytes_raw.return_value = b"admin_public_key"
    private_key_admin.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"admin_public_key")

    private_key_supply = MagicMock()
    private_key_supply.sign.return_value = b"supply_signature"
    private_key_supply.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"supply_public_key")

    private_key_freeze = MagicMock()
    private_key_freeze.sign.return_value = b"freeze_signature"
    private_key_freeze.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"freeze_public_key")

    private_key_wipe = MagicMock()
    private_key_wipe.sign.return_value = b"wipe_signature"
    private_key_wipe.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"wipe_public_key")

    private_key_metadata = MagicMock()
    private_key_metadata.sign.return_value = b"metadata_signature"
    private_key_metadata.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"metadata_public_key")

    private_key_pause = MagicMock()
    private_key_pause.sign.return_value = b"pause_signature"
    private_key_pause.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"pause_public_key")

    private_key_kyc = MagicMock()
    private_key_kyc.sign.return_value = b"kyc_signature"
    private_key_kyc.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"kyc_public_key")

    private_key_fee_schedule = MagicMock()
    private_key_fee_schedule.sign.return_value = b"fee_schedule_signature"
    private_key_fee_schedule.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"fee_schedule_public_key")

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_admin_key(private_key_admin)
    token_tx.set_supply_key(private_key_supply)
    token_tx.set_freeze_key(private_key_freeze)
    token_tx.set_wipe_key(private_key_wipe)
    token_tx.set_metadata_key(private_key_metadata)
    token_tx.set_pause_key(private_key_pause)
    token_tx.set_kyc_key(private_key_kyc)
    token_tx.set_fee_schedule_key(private_key_fee_schedule)
    
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    
    token_tx.freeze_with(mock_client)

    # Sign with both sign keys
    token_tx.sign(private_key) # Necessary
    token_tx.sign(private_key_admin) # Since admin key exists
    
    node_id = mock_client.network.current_node._account_id
    body_bytes = token_tx._transaction_body_bytes[node_id]

    # Expect 2 sigPairs
    assert len(token_tx._signature_map[body_bytes].sigPair) == 2

    sig_pair = token_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"

    sig_pair_admin = token_tx._signature_map[body_bytes].sigPair[1]
    assert sig_pair_admin.pubKeyPrefix == b"admin_public_key"
    assert sig_pair_admin.ed25519 == b"admin_signature"

    # Confirm that neither sigPair belongs to supply, freeze, wipe or metadata keys:
    for sig_pair in token_tx._signature_map[body_bytes].sigPair:
        assert sig_pair.pubKeyPrefix not in (
            b"supply_public_key",
            b"freeze_public_key", 
            b"wipe_public_key", 
            b"metadata_public_key",
            b"pause_public_key",
            b"fee_schedule_public_key"
        )

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_to_proto_without_keys(mock_account_ids, mock_client):
    """Test protobuf conversion when keys are not set."""
    treasury_account, _, _, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_memo("Token Memo")
    token_tx.transaction_id = generate_transaction_id(treasury_account)

    # Mock treasury/operator key
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    token_tx.freeze_with(mock_client)

    # Sign with treasury key
    token_tx.sign(private_key)

    # Parse the TransactionBody starting with the outer wrapper
    proto_tx = token_tx._to_proto()
    assert len(proto_tx.signedTransactionBytes) > 0

    outer_tx = transaction_pb2.Transaction.FromString(proto_tx.SerializeToString())
    assert len(outer_tx.signedTransactionBytes) > 0

    signed_tx = transaction_contents_pb2.SignedTransaction.FromString(
        outer_tx.signedTransactionBytes
    )
    assert len(signed_tx.bodyBytes) > 0

    transaction_body = transaction_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

    # Verify the transaction built was correctly serialized to and from proto.
    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000
    assert transaction_body.tokenCreation.memo == "Token Memo"
    # Default Values
    assert transaction_body.tokenCreation.autoRenewPeriod == Duration(7890000)._to_proto()
    assert not  transaction_body.tokenCreation.HasField('expiry')

    assert not transaction_body.tokenCreation.HasField("adminKey")

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_to_proto_with_keys(mock_account_ids, mock_client):
    """Test converting the token creation transaction to protobuf format after signing."""
    treasury_account, _, _, _, _ = mock_account_ids

    # Generate real private keys for all key types
    private_key = PrivateKey.generate_ed25519()
    private_key_admin = PrivateKey.generate_ed25519()
    private_key_supply = PrivateKey.generate_ed25519()
    private_key_freeze = PrivateKey.generate_ed25519()
    private_key_wipe = PrivateKey.generate_ed25519()
    private_key_metadata = PrivateKey.generate_ed25519()
    private_key_kyc = PrivateKey.generate_ed25519()
    private_key_fee_schedule = PrivateKey.generate_ed25519()

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
    token_tx.set_wipe_key(private_key_wipe)
    token_tx.set_metadata_key(private_key_metadata)
    token_tx.set_kyc_key(private_key_kyc)
    token_tx.set_fee_schedule_key(private_key_fee_schedule)
    token_tx.transaction_id = generate_transaction_id(treasury_account)

    token_tx.freeze_with(mock_client)

    # Sign with required sign keys
    token_tx.sign(private_key)
    token_tx.sign(private_key_admin)

    # Convert to protobuf
    proto_tx = token_tx._to_proto()
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
    tx_body = transaction_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

    # Confirm fields set in the token creation portion of the TransactionBody
    assert tx_body.tokenCreation.name == "MyToken"
    assert tx_body.tokenCreation.adminKey == private_key_admin.public_key()._to_proto()
    assert tx_body.tokenCreation.supplyKey == private_key_supply.public_key()._to_proto()
    assert tx_body.tokenCreation.freezeKey == private_key_freeze.public_key()._to_proto()
    assert tx_body.tokenCreation.wipeKey == private_key_wipe.public_key()._to_proto()
    assert tx_body.tokenCreation.metadata_key == private_key_metadata.public_key()._to_proto()
    assert tx_body.tokenCreation.kycKey == private_key_kyc.public_key()._to_proto()
    assert tx_body.tokenCreation.fee_schedule_key == private_key_fee_schedule.public_key()._to_proto()

# This test uses fixture mock_account_ids as parameter
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

# This test uses fixture mock_account_ids as parameter
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
    
    # Set the transaction body bytes to avoid calling build_transaction_body
    token_tx._transaction_body_bytes = b"mock_body_bytes"
    
    # Mock the client and its operator_private_key
    token_tx.client = MagicMock()
    mock_public_key = MagicMock()
    mock_public_key.to_bytes_raw.return_value = b"mock_public_key"
    
    token_tx.client.operator_private_key = MagicMock()
    token_tx.client.operator_private_key.sign.return_value = b"mock_signature"
    token_tx.client.operator_private_key.public_key.return_value = mock_public_key
    
    # Skip the actual sign method by mocking is_signed_by to return True
    token_tx.is_signed_by = MagicMock(return_value=True)

    with patch.object(token_tx, "_execute") as mock_execute:
        # Create a PrecheckError with INVALID_SIGNATURE status
        precheck_error = PrecheckError(ResponseCode.INVALID_SIGNATURE, token_tx.transaction_id)
        # Make _execute raise this error when called
        mock_execute.side_effect = precheck_error
        
        # The expected message pattern should match the PrecheckError message format
        expected_pattern = r"Transaction failed precheck with status: INVALID_SIGNATURE \(7\)"

        with pytest.raises(PrecheckError, match=expected_pattern):
            # Attempt to execute - this should raise the mocked PrecheckError
            token_tx.execute(token_tx.client)

        # Verify _execute was called with client
        mock_execute.assert_called_once_with(token_tx.client)

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_overwrite_defaults(mock_account_ids, mock_client):
    """
    Demonstrates that defaults in TokenCreateTransaction can be overwritten
    by calling set_* methods, and the final protobuf reflects the updated values.
    """
    treasury_account, _, _, _, _ = mock_account_ids

    # Create a new TokenCreateTransaction with all default params
    token_tx = TokenCreateTransaction()

    # Assert the internal defaults.
    assert token_tx._token_params.token_name == "" #Empty String
    assert token_tx._token_params.token_symbol == "" #Empty String
    assert token_tx._token_params.treasury_account_id == AccountId(0, 0, 1)
    assert token_tx._token_params.decimals == 0
    assert token_tx._token_params.initial_supply == 0
    assert token_tx._token_params.token_type == TokenType.FUNGIBLE_COMMON
    assert token_tx._token_params.auto_renew_account_id is None
    assert token_tx._token_params.auto_renew_period == Duration(7890000)
    assert token_tx._token_params.expiration_time is None

    # 3. Overwrite the defaults using set_* methods
    token_tx.set_token_name("MyUpdatedToken")
    token_tx.set_token_symbol("UPD")
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_decimals(5)
    token_tx.set_initial_supply(10000)
    token_tx.set_auto_renew_period(Duration(2592000))
    token_tx.set_auto_renew_account_id(AccountId(0, 0, 2))

    # Set transaction/node IDs so can sign
    token_tx.transaction_id = generate_transaction_id(treasury_account)

    token_tx.freeze_with(mock_client)

    # Mock a private key and sign the transaction
    private_key = MagicMock()
    private_key.sign.return_value = b"test_signature"
    private_key.public_key().to_bytes_raw.return_value = b"test_public_key"
    token_tx.sign(private_key)

    # Convert to protobuf transaction
    proto_tx = token_tx._to_proto()
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
    tx_body = transaction_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

    # Check that updated values made it into tokenCreation
    assert tx_body.tokenCreation.name == "MyUpdatedToken"
    assert tx_body.tokenCreation.symbol == "UPD"
    assert tx_body.tokenCreation.decimals == 5
    assert tx_body.tokenCreation.initialSupply == 10000
    assert tx_body.tokenCreation.autoRenewPeriod == Duration(2592000)._to_proto()
    assert tx_body.tokenCreation.autoRenewAccount == AccountId(0, 0, 2)._to_proto()

    # Confirm no adminKey was set
    assert not tx_body.tokenCreation.HasField("adminKey")

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_transaction_freeze_prevents_modification(mock_account_ids, mock_client):
    """
    Test that after freeze() is called, attempts to modify TokenCreateTransaction
    parameters raise an exception indicating immutability.
    """
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    transaction = TokenCreateTransaction()

    # Set some initial parameters
    transaction.set_token_name("TestName")
    transaction.set_token_symbol("TEST")
    transaction.set_initial_supply(1000)
    transaction.set_decimals(2)
    transaction.set_treasury_account_id(treasury_account)

    transaction.node_account_id = node_account_id
    transaction.transaction_id = generate_transaction_id(treasury_account)
    
    # Freeze the transaction
    transaction.freeze_with(mock_client)

    # Attempt to overwrite after freeze - expect exceptions
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_token_name("NewName")

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_token_name("NEW")

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_initial_supply(5000)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_decimals(8)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_token_type(TokenType.NON_FUNGIBLE_UNIQUE) # Should have defaulted to this

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_expiration_time(Duration(2592000))

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_auto_renew_period(Duration(2592000))
    
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transaction.set_auto_renew_account_id(AccountId(0, 0, 2))
    
    

    # Confirm that values remain unchanged after freeze attempt
    assert transaction._token_params.token_name == "TestName"
    assert transaction._token_params.token_symbol == "TEST"    
    assert transaction._token_params.initial_supply == 1000
    assert transaction._token_params.decimals == 2
    assert transaction._token_params.treasury_account_id == treasury_account
    assert transaction._token_params.token_type == TokenType.FUNGIBLE_COMMON
    assert transaction._token_params.auto_renew_period == Duration(7890000)
    # On freezeWith(client) it will auto assign from transaction Id
    assert transaction._token_params.auto_renew_account_id == treasury_account
    assert transaction._token_params.expiration_time is None


# This test uses fixture mock_account_ids as parameter
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
    token_tx.set_memo("NFT Memo")

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
    assert transaction_body.tokenCreation.memo == "NFT Memo"
    assert transaction_body.tokenCreation.autoRenewPeriod == Duration(7890000)._to_proto() # Default value of 90days.
    assert not transaction_body.tokenCreation.HasField('expiry') # By default, this is set to "now + AUTO_RENEW_PERIOD" (90 days).

    # No keys are set
    assert not transaction_body.tokenCreation.HasField("adminKey")
    assert not transaction_body.tokenCreation.HasField("supplyKey")
    assert not transaction_body.tokenCreation.HasField("freezeKey")
    assert not transaction_body.tokenCreation.HasField("wipeKey")
    assert not transaction_body.tokenCreation.HasField("metadata_key")
    assert not transaction_body.tokenCreation.HasField("kycKey")
    assert not transaction_body.tokenCreation.HasField("fee_schedule_key")

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_build_and_sign_nft_transaction_to_proto(mock_account_ids, mock_client):
    """
    Test building, signing, and protobuf serialization of 
    a valid Non-Fungible Unique token creation transaction.
    """
    treasury_account, _, _, _, _ = mock_account_ids

    # Mock keys
    private_key_private = MagicMock()
    private_key_private.sign.return_value = b"private_signature"
    private_key_private.public_key().to_bytes_raw.return_value = b"private_public_key"

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b"admin_signature"
    private_key_admin.public_key().to_bytes_raw.return_value = b"admin_public_key"
    private_key_admin.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"admin_public_key")

    private_key_supply = MagicMock()
    private_key_supply.sign.return_value = b"supply_signature"
    private_key_supply.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"supply_public_key")

    private_key_freeze = MagicMock()
    private_key_freeze.sign.return_value = b"freeze_signature"
    private_key_freeze.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"freeze_public_key")

    private_key_wipe = MagicMock()
    private_key_wipe.sign.return_value = b"wipe_signature"
    private_key_wipe.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"wipe_public_key")

    private_key_metadata = MagicMock()
    private_key_metadata.sign.return_value = b"metadata_signature"
    private_key_metadata.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"metadata_public_key")

    private_key_pause = MagicMock()
    private_key_pause.sign.return_value = b"pause_signature"
    private_key_pause.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"pause_public_key")

    private_key_kyc = MagicMock()
    private_key_kyc.sign.return_value = b"kyc_signature"
    private_key_kyc.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"kyc_public_key")

    private_key_fee_schedule = MagicMock()
    private_key_fee_schedule.sign.return_value = b"fee_schedule_signature"
    private_key_fee_schedule.public_key()._to_proto.return_value = basic_types_pb2.Key(ed25519=b"fee_schedule_public_key")

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
    token_tx.set_wipe_key(private_key_wipe)
    token_tx.set_metadata_key(private_key_metadata)
    token_tx.set_pause_key(private_key_pause)
    token_tx.set_kyc_key(private_key_kyc)
    token_tx.set_fee_schedule_key(private_key_fee_schedule)
    token_tx.transaction_id = generate_transaction_id(treasury_account)

    token_tx.freeze_with(mock_client)

    # Sign the transaction
    token_tx.sign(private_key_private)
    token_tx.sign(private_key_admin)

    # Convert to protobuf (outer Transaction)
    proto_tx = token_tx._to_proto()
    assert len(proto_tx.signedTransactionBytes) > 0

    # Parse the outer Transaction
    outer_tx = transaction_pb2.Transaction.FromString(proto_tx.SerializeToString())
    assert len(outer_tx.signedTransactionBytes) > 0

    # Parse the inner SignedTransaction
    signed_tx = transaction_contents_pb2.SignedTransaction.FromString(outer_tx.signedTransactionBytes)
    assert len(signed_tx.bodyBytes) > 0

    # Finally parse the TransactionBody
    tx_body = transaction_pb2.TransactionBody.FromString(signed_tx.bodyBytes)

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
    assert tx_body.tokenCreation.wipeKey.ed25519 == b"wipe_public_key"
    assert tx_body.tokenCreation.metadata_key.ed25519 == b"metadata_public_key"
    assert tx_body.tokenCreation.pause_key.ed25519  == b"pause_public_key"
    assert tx_body.tokenCreation.kycKey.ed25519 == b"kyc_public_key"
    assert tx_body.tokenCreation.fee_schedule_key.ed25519 == b"fee_schedule_public_key"

@pytest.mark.parametrize(
    "token_type, supply_type, max_supply, initial_supply, expected_error",
    [
        #
        # FUNGIBLE + INFINITE
        #
        # 1) Infinite supply requires max_supply=0 => VALID
        (TokenType.FUNGIBLE_COMMON, SupplyType.INFINITE, 0, 1, None),
        # 2) Infinite supply but max_supply != 0 => ERROR
        (TokenType.FUNGIBLE_COMMON, SupplyType.INFINITE, 100, 100,
         "Setting a max supply field requires setting a finite supply type"),
        #
        # FUNGIBLE + FINITE
        #
        # 3) Finite supply but max_supply=0 => ERROR
        (TokenType.FUNGIBLE_COMMON, SupplyType.FINITE, 0, 100,
         "A finite supply token requires max_supply greater than zero 0"),
        # 4) Finite supply, max_supply>0 but initial_supply > max_supply => ERROR
        (TokenType.FUNGIBLE_COMMON, SupplyType.FINITE, 500, 600,
         "Initial supply cannot exceed the defined max supply for a finite token"),
        # 5) Finite supply, max_supply>0, initial_supply <= max_supply => VALID
        (TokenType.FUNGIBLE_COMMON, SupplyType.FINITE, 5000, 100, None),

        #
        # NON-FUNGIBLE + INFINITE
        #
        # 6) NFT + infinite supply => must have max_supply=0 => VALID
        (TokenType.NON_FUNGIBLE_UNIQUE, SupplyType.INFINITE, 0, 0, None),
        # 7) NFT + infinite supply + nonzero max_supply => ERROR
        (TokenType.NON_FUNGIBLE_UNIQUE, SupplyType.INFINITE, 200, 0,
         "Setting a max supply field requires setting a finite supply type"),
        #
        # NON-FUNGIBLE + FINITE
        #
        # 8) NFT, finite supply but max_supply=0 => ERROR
        (TokenType.NON_FUNGIBLE_UNIQUE, SupplyType.FINITE, 0, 0,
        "A finite supply token requires max_supply greater than zero 0"),

        # 9) NFT, finite supply, no initial supply, max_supply>0 => VALID
        (TokenType.NON_FUNGIBLE_UNIQUE, SupplyType.FINITE, 100, 0, None),
    ]
)
def test_supply_type_and_max_supply_validation(
    mock_account_ids,
    token_type,
    supply_type,
    max_supply,
    initial_supply,
    expected_error
):
    """ 
    Verifies the combination of token_type, supply_type, max_supply, and initial_supply 
    either passes validation or raises the correct ValueError
    """
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    # Prepare the token params
    params = TokenParams(
        token_name="MaxSupplyToken",
        token_symbol="MSUP",
        treasury_account_id=treasury_account,
        decimals=0 if token_type == TokenType.NON_FUNGIBLE_UNIQUE else 2,
        initial_supply=initial_supply,
        token_type=token_type,
        supply_type=supply_type,
        max_supply=max_supply,
        freeze_default=False
    )

    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            TokenCreateTransaction(params).build_transaction_body()
    else:
        tx = TokenCreateTransaction(params)
        tx.operator_account_id = treasury_account
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()

        assert body.tokenCreation.tokenType == token_type.value
        assert body.tokenCreation.supplyType == supply_type.value
        assert body.tokenCreation.maxSupply == max_supply
        assert body.tokenCreation.initialSupply == initial_supply

def test_build_scheduled_body_fungible_token(mock_account_ids, private_key):
    """Test building a scheduled transaction body for fungible token creation."""
    treasury_account, _, _, _, _ = mock_account_ids
    
    # Prepare token parameters for a fungible token
    params = TokenParams(
        token_name="TestToken",
        token_symbol="TTK",
        treasury_account_id=treasury_account,
        decimals=2,
        initial_supply=1000,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.INFINITE,
    )
    
    # Prepare token keys
    keys = TokenKeys(
        admin_key=private_key,
        supply_key=private_key
    )
    
    # Create the transaction
    token_tx = TokenCreateTransaction(params, keys)

    schedulable_body = token_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenCreation")
    assert schedulable_body.tokenCreation.name == "TestToken"
    assert schedulable_body.tokenCreation.symbol == "TTK"
    assert schedulable_body.tokenCreation.treasury == treasury_account._to_proto()
    assert schedulable_body.tokenCreation.decimals == 2
    assert schedulable_body.tokenCreation.initialSupply == 1000
    assert schedulable_body.tokenCreation.tokenType == TokenType.FUNGIBLE_COMMON.value
    assert schedulable_body.tokenCreation.supplyType == SupplyType.INFINITE.value
    assert schedulable_body.tokenCreation.adminKey.HasField("ed25519")
    assert schedulable_body.tokenCreation.supplyKey.HasField("ed25519")
    
def test_build_scheduled_body_nft(mock_account_ids, private_key):
    """Test building a scheduled transaction body for NFT token creation."""
    treasury_account, _, _, _, _ = mock_account_ids
    
    # Prepare token parameters for an NFT
    params = TokenParams(
        token_name="TestNFT",
        token_symbol="TNFT",
        treasury_account_id=treasury_account,
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
        supply_type=SupplyType.FINITE,
        max_supply=1000,
    )
    
    # Prepare token keys
    keys = TokenKeys(
        admin_key=private_key,
        supply_key=private_key,
        wipe_key=private_key
    )
    
    # Create the transaction
    token_tx = TokenCreateTransaction(params, keys)
    
    schedulable_body = token_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenCreation")
    assert schedulable_body.tokenCreation.name == "TestNFT"
    assert schedulable_body.tokenCreation.symbol == "TNFT"
    assert schedulable_body.tokenCreation.treasury == treasury_account._to_proto()
    assert schedulable_body.tokenCreation.tokenType == TokenType.NON_FUNGIBLE_UNIQUE.value
    assert schedulable_body.tokenCreation.supplyType == SupplyType.FINITE.value
    assert schedulable_body.tokenCreation.maxSupply == 1000
    assert schedulable_body.tokenCreation.adminKey.HasField("ed25519")
    assert schedulable_body.tokenCreation.supplyKey.HasField("ed25519")
    assert schedulable_body.tokenCreation.wipeKey.HasField("ed25519")

def test_token_create_with_expiration_time_overrides_auto_renew(mock_account_ids):
    """Test set_expiration_time set the autoRenewPeriod to None"""
    treasury_account, _, node_account_id, *_ = mock_account_ids
    expiration_time = Timestamp.from_date(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    )

    params = TokenParams(
        token_name="ExpToken",
        token_symbol="EXP",
        treasury_account_id=treasury_account,
        initial_supply=1
    )
    tx = TokenCreateTransaction(params)
    
    assert tx._token_params.auto_renew_period == Duration(seconds=7890000)
    assert tx._token_params.expiration_time is None
    
    tx.set_expiration_time(expiration_time);
    tx.transaction_id = generate_transaction_id(treasury_account)
    tx.node_account_id = node_account_id    
    body = tx.build_transaction_body()

    assert body.tokenCreation.expiry.seconds == expiration_time.seconds
    assert not body.tokenCreation.HasField("autoRenewPeriod") 

def test_auto_renew_account_assignment_during_freeze_with_client(mock_account_ids, mock_client):
    """Test autoRenewPeriod and autoRenewAccount assignment behavior when freezing with a client."""
    treasury_account, auto_renew_account_id, *_ = mock_account_ids

    # Auto renewAccountId must not be set if autoRenewPeriod is None
    tx = TokenCreateTransaction(
        TokenParams(
            token_name="FreezeClientToken",
            token_symbol="FCT",
            treasury_account_id=treasury_account,
            initial_supply=1,
            auto_renew_period=None
        )
    )
    frozen_tx = tx.freeze_with(mock_client)
    body = frozen_tx.build_transaction_body()

    assert not body.tokenCreation.HasField("autoRenewPeriod") 
    assert not body.tokenCreation.HasField('autoRenewAccount')

    # If autoRenewAccountId is set then freezeWith(client) will not assing value to it
    tx1 = TokenCreateTransaction(
        TokenParams(
            token_name="FreezeClientToken",
            token_symbol="FCT",
            treasury_account_id=treasury_account,
            initial_supply=1
        )
    )
    tx1.set_auto_renew_account_id(auto_renew_account_id)
    frozen_tx1 = tx1.freeze_with(mock_client)
    body1 = frozen_tx1.build_transaction_body()

    assert body1.tokenCreation.autoRenewPeriod == Duration(7890000)._to_proto() # Default around 90 days
    assert body1.tokenCreation.autoRenewAccount == auto_renew_account_id._to_proto()

    # If Trasnaction Id not generated. Then use client operator_account
    tx2 = TokenCreateTransaction(
        TokenParams(
            token_name="FreezeClientToken",
            token_symbol="FCT",
            treasury_account_id=treasury_account,
            initial_supply=1,
        )
    )
    frozen_tx2 = tx2.freeze_with(mock_client)

    body2 = frozen_tx2.build_transaction_body();

    assert body2.tokenCreation.autoRenewPeriod == Duration(7890000)._to_proto() # Default around 90 days
    assert body2.tokenCreation.autoRenewAccount == mock_client.operator_account_id._to_proto()

    # If Transaction Id generated. Then use transaction_id account
    tx3 = TokenCreateTransaction(
        TokenParams(
            token_name="FreezeClientToken",
            token_symbol="FCT",
            treasury_account_id=treasury_account,
            initial_supply=1,
        )
    );
    tx3.transaction_id = generate_transaction_id(treasury_account)
    frozen_tx3 = tx3.freeze_with(mock_client)

    body3 = frozen_tx3.build_transaction_body()
    
    assert body3.tokenCreation.autoRenewPeriod == Duration(7890000)._to_proto() # Default around 90 days
    assert body3.tokenCreation.autoRenewAccount == treasury_account._to_proto()
