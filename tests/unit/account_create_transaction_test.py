import time
import pytest
from unittest.mock import patch
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.hapi.services import basic_types_pb2, response_pb2
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (
    TransactionResponse as TransactionResponseProto,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import (
    TransactionReceipt as TransactionReceiptProto,
)
from hiero_sdk_python.hapi.services import (
    transaction_get_receipt_pb2,
    response_header_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(
        seconds=timestamp_seconds, nanos=timestamp_nanos
    )

    tx_id = TransactionId(valid_start=tx_timestamp, account_id=account_id_proto)
    return tx_id


# This test uses fixture mock_account_ids as parameter
def test_account_create_transaction_build(mock_account_ids):
    """Test building an account create transaction body with valid parameters."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()

    account_tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_public_key)
        .set_initial_balance(100000000)
        .set_account_memo("Test account")
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    expected_public_key_bytes = new_public_key.to_bytes_raw()

    assert transaction_body.cryptoCreateAccount.key.ed25519 == expected_public_key_bytes
    assert transaction_body.cryptoCreateAccount.initialBalance == 100000000
    assert transaction_body.cryptoCreateAccount.memo == "Test account"


# This test uses fixture mock_account_ids as parameter
def test_account_create_transaction_build_scheduled_body(mock_account_ids):
    """Test building a schedulable account create transaction body."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()

    account_tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_public_key)
        .set_initial_balance(200000000)
        .set_account_memo("Schedulable account")
        .set_receiver_signature_required(True)
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id

    # Build the scheduled transaction body
    schedulable_body = account_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with account create type
    assert schedulable_body.HasField("cryptoCreateAccount")

    # Verify fields in the schedulable body
    expected_public_key_bytes = new_public_key.to_bytes_raw()
    assert schedulable_body.cryptoCreateAccount.key.ed25519 == expected_public_key_bytes
    assert schedulable_body.cryptoCreateAccount.initialBalance == 200000000
    assert schedulable_body.cryptoCreateAccount.memo == "Schedulable account"
    assert schedulable_body.cryptoCreateAccount.receiverSigRequired == True


# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_account_create_transaction_sign(mock_account_ids, mock_client):
    """Test signing the account create transaction."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()
    operator_private_key = PrivateKey.generate()

    account_tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_public_key)
        .set_initial_balance(100000000)
        .set_account_memo("Test account")
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id
    account_tx.freeze_with(mock_client)

    # Add first signiture
    account_tx.sign(mock_client.operator_private_key)
    body_bytes = account_tx._transaction_body_bytes[node_account_id]

    assert (
        body_bytes in account_tx._signature_map
    ), "Body bytes should be a key in the signature map dictionary"
    assert (
        len(account_tx._signature_map[body_bytes].sigPair) == 1
    ), "Transaction should have exactly one signature"

    # Add second signiture
    account_tx.sign(operator_private_key)
    body_bytes = account_tx._transaction_body_bytes[node_account_id]

    assert (
        body_bytes in account_tx._signature_map
    ), "Body bytes should be a key in the signature map dictionary"
    assert (
        len(account_tx._signature_map[body_bytes].sigPair) == 2
    ), "Transaction should have exactly two signatures"


def test_account_create_transaction():
    """Integration test for AccountCreateTransaction with retry and response handling."""
    # Create test transaction responses
    busy_response = TransactionResponseProto()
    busy_response.nodeTransactionPrecheckCode = ResponseCode.BUSY

    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for a successful account creation
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS,
        accountID=basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234),
    )

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto,
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    # Use the context manager to set up and tear down the mock environment
    with mock_hedera_servers(response_sequences) as client, patch("time.sleep"):

        # Create the transaction
        new_key = PrivateKey.generate()
        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(new_key.public_key())
            .set_initial_balance(100000000)  # 1 HBAR
        )

        # Execute the transaction and get receipt
        receipt = transaction.execute(client)

        # Verify the results
        assert (
            receipt.status == ResponseCode.SUCCESS
        ), "Transaction should have succeeded"
        assert (
            receipt.account_id.num == 1234
        ), "Should have created account with ID 1234"


def test_sign_account_create_without_freezing_raises_error(mock_account_ids):
    """Test that signing a transaction without freezing it first raises an error."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()

    account_tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_public_key)
        .set_initial_balance(100000000)
        .set_account_memo("Test account")
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id

    with pytest.raises(Exception, match="Transaction is not frozen"):
        account_tx.sign(new_private_key)


@pytest.fixture
def mock_account_ids():
    """Fixture to provide mock account IDs for testing."""
    operator_account_id = AccountId(0, 0, 1001)
    node_account_id = AccountId(0, 0, 3)
    return operator_account_id, node_account_id


def test_set_max_automatic_token_associations_validation():
    """Test validation for max_automatic_token_associations."""
    tx = AccountCreateTransaction()

    # Test good value: -1 for unlimited
    tx.set_max_automatic_token_associations(-1)
    assert tx.max_automatic_token_associations == -1

    # Test good value: 0 for default
    tx.set_max_automatic_token_associations(0)
    assert tx.max_automatic_token_associations == 0

    # Test good value: 100
    tx.set_max_automatic_token_associations(100)
    assert tx.max_automatic_token_associations == 100

    # Test bad value: -2
    with pytest.raises(ValueError) as e:
        tx.set_max_automatic_token_associations(-2)

    # Check for the new error message
    assert "must be -1 (unlimited) or a non-negative integer" in str(e.value)


def test_account_create_build_with_max_auto_assoc(mock_account_ids):
    """Test building transaction with max_automatic_token_associations."""
    operator_id, node_account_id = mock_account_ids
    new_public_key = PrivateKey.generate().public_key()

    account_tx = (
        AccountCreateTransaction()
        .set_key_without_alias(new_public_key)
        .set_max_automatic_token_associations(-1)  # Test the new value
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id

    body = account_tx.build_transaction_body()

    # Verify the value is correctly set in the protobuf body
    assert body.cryptoCreateAccount.max_automatic_token_associations == -1


def test_create_account_transaction_without_alias(mock_account_ids):
    """Test Create account transaction using set_key_without_alias method"""
    operator_id, node_id = mock_account_ids
    public_key = PrivateKey.generate().public_key()
    tx = AccountCreateTransaction().set_key_without_alias(public_key)

    assert tx.key == public_key
    assert tx.alias is None

    tx.operator_account_id = operator_id
    tx.node_account_id = node_id
    tx_body = tx.build_transaction_body()

    assert tx_body.cryptoCreateAccount.key == public_key._to_proto()
    assert tx_body.cryptoCreateAccount.alias == b""


def test_create_account_transaction_set_key_with_alias(mock_account_ids):
    """Test Create account transaction using set_key_with_alias method"""
    operator_id, node_id = mock_account_ids
    public_key = PrivateKey.generate_ecdsa().public_key()

    tx = AccountCreateTransaction().set_key_with_alias(public_key)

    assert tx.key == public_key
    assert tx.alias == public_key.to_evm_address()

    tx.operator_account_id = operator_id
    tx.node_account_id = node_id
    tx_body = tx.build_transaction_body()

    assert tx_body.cryptoCreateAccount.key == public_key._to_proto()
    assert (
        tx_body.cryptoCreateAccount.alias == public_key.to_evm_address().address_bytes
    )


def test_create_account_transaction_set_key_with_seperate_key_for_alias(
    mock_account_ids,
):
    """Test Create account transaction using set_key_with_alias method with seprate key"""
    operator_id, node_id = mock_account_ids
    public_key = PrivateKey.generate().public_key()
    alias_key = PrivateKey.generate_ecdsa().public_key()

    tx = AccountCreateTransaction().set_key_with_alias(public_key, alias_key)

    assert tx.key == public_key
    assert tx.alias == alias_key.to_evm_address()

    tx.operator_account_id = operator_id
    tx.node_account_id = node_id
    tx_body = tx.build_transaction_body()

    assert tx_body.cryptoCreateAccount.key == public_key._to_proto()
    assert tx_body.cryptoCreateAccount.alias == alias_key.to_evm_address().address_bytes


def test_create_account_transaction_set_key_with_alias_non_ecdsa_key():
    """Test Create account transaction using set_key_with_alias method"""
    public_key = PrivateKey.generate().public_key()

    with pytest.raises(ValueError):
        (AccountCreateTransaction().set_key_with_alias(public_key))

    # With seperate key for deriving alias
    alias_key = PrivateKey.generate().public_key()
    with pytest.raises(ValueError):
        (AccountCreateTransaction().set_key_with_alias(public_key, alias_key))


def test_create_account_transaction_with_set_alias(mock_account_ids):
    """Test account creation transaction using a valid EvmAddress object."""
    operator_id, node_id = mock_account_ids
    public_key = PrivateKey.generate().public_key()
    evm_address = PrivateKey.generate_ecdsa().public_key().to_evm_address()

    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(public_key)
        .set_alias(evm_address)
    )

    assert tx.key == public_key
    assert tx.alias == evm_address

    tx.operator_account_id = operator_id
    tx.node_account_id = node_id
    tx_body = tx.build_transaction_body()

    assert tx_body.cryptoCreateAccount.key == public_key._to_proto()
    assert tx_body.cryptoCreateAccount.alias == evm_address.address_bytes


@pytest.mark.parametrize("with_prefix", [False, True])
def test_create_account_transaction_with_set_alias_from_string(
    mock_account_ids, with_prefix
):
    """Test account creation transaction using alias from string (with and without '0x' prefix)."""
    operator_id, node_id = mock_account_ids
    public_key = PrivateKey.generate().public_key()
    evm_address = PrivateKey.generate_ecdsa().public_key().to_evm_address()

    evm_string = evm_address.to_string()
    alias_str = "0x" + evm_string if with_prefix else evm_string

    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(public_key)
        .set_alias(alias_str)
    )

    assert tx.key == public_key
    assert tx.alias == evm_address

    tx.operator_account_id = operator_id
    tx.node_account_id = node_id
    tx_body = tx.build_transaction_body()

    assert tx_body.cryptoCreateAccount.key == public_key._to_proto()
    assert tx_body.cryptoCreateAccount.alias == evm_address.address_bytes


@pytest.mark.parametrize(
    "invalid_str",
    [
        "",
        "0x",
        "12345",
        "0x12345",
        "0x" + "g" * 40,
        "0x" + "a" * 39,
        "0x" + "a" * 41,
    ],
)
def test_create_account_transaction_with_set_alias_from_invalid_string(invalid_str):
    """Test invalid alias strings raise ValueError."""
    public_key = PrivateKey.generate().public_key()
    tx = AccountCreateTransaction().set_key_without_alias(public_key)

    with pytest.raises(ValueError):
        tx.set_alias(invalid_str)


def test_create_account_transaction_with_set_alias_from_invalid_type():
    """Test alias with invalid type raises TypeError."""
    public_key = PrivateKey.generate().public_key()
    tx = AccountCreateTransaction().set_key_without_alias(public_key)

    with pytest.raises(TypeError):
        tx.set_alias(1234)


# This test uses fixture mock_account_ids as parameter
def test_account_create_transaction_build_with_private_key(mock_account_ids):
    """AccountCreateTransaction should accept also PrivateKey and serialize the PublicKey in the proto."""
    operator_id, node_account_id = mock_account_ids

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()

    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(private_key)
        .set_initial_balance(100000000)
        .set_account_memo("Account with private key")
    )

    tx.transaction_id = generate_transaction_id(operator_id)
    tx.node_account_id = node_account_id

    body = tx.build_transaction_body()

    # In the proto  we should have the public key not the private one
    assert body.cryptoCreateAccount.key.ed25519 == public_key.to_bytes_raw()
    assert body.cryptoCreateAccount.initialBalance == 100000000
    assert body.cryptoCreateAccount.memo == "Account with private key"


# This test uses fixture mock_account_ids as parameter
def test_create_account_transaction_set_key_with_alias_private_keys(mock_account_ids):
    """set_key_with_alias should work also with PrivateKey ECDSA (account key + alias key)."""
    operator_id, node_id = mock_account_ids

    # Account key(ECDSA)
    account_private_key = PrivateKey.generate_ecdsa()
    account_public_key = account_private_key.public_key()

    # Alias key (ECDSA)
    alias_private_key = PrivateKey.generate_ecdsa()
    alias_public_key = alias_private_key.public_key()
    expected_evm_address = alias_public_key.to_evm_address()

    tx = AccountCreateTransaction().set_key_with_alias(
        account_private_key, alias_private_key
    )

    assert tx.key == account_private_key
    assert tx.alias == expected_evm_address

    tx.operator_account_id = operator_id
    tx.node_account_id = node_id
    tx_body = tx.build_transaction_body()

    # In the proto we should have account public key
    assert tx_body.cryptoCreateAccount.key == account_public_key._to_proto()
    # Alias should be the address bytes from the key for the alias
    assert tx_body.cryptoCreateAccount.alias == expected_evm_address.address_bytes


# This test uses fixture mock_account_ids as parameter
def test_create_account_transaction_set_key_with_alias_private_key_without_ecdsa_key(
    mock_account_ids,
):
    """set_key_with_alias should work also without ecdsa_key."""
    operator_id, node_id = mock_account_ids

    # Account key(ECDSA)
    account_private_key = PrivateKey.generate_ecdsa()
    account_public_key = account_private_key.public_key()

    expected_evm_address = account_public_key.to_evm_address()

    tx = AccountCreateTransaction().set_key_with_alias(account_private_key)

    assert tx.key == account_private_key
    assert tx.alias == expected_evm_address

    tx.operator_account_id = operator_id
    tx.node_account_id = node_id
    tx_body = tx.build_transaction_body()

    # In the proto we should have account public key
    assert tx_body.cryptoCreateAccount.key == account_public_key._to_proto()
    # Alias should be the address bytes from the key for the alias
    assert tx_body.cryptoCreateAccount.alias == expected_evm_address.address_bytes


def test_set_key_without_alias_then_with_alias_overrides_alias():
    """set_key_with_alias should ovveride set_key_without_alias"""
    # Account key(ECDSA)
    account_private_key = PrivateKey.generate_ecdsa()
    account_public_key = account_private_key.public_key()

    # Alias key (ECDSA)
    alias_private_key = PrivateKey.generate_ecdsa()
    alias_public_key = alias_private_key.public_key()
    expected_evm_address = alias_public_key.to_evm_address()

    tx = AccountCreateTransaction().set_key_without_alias(account_private_key)

    assert tx.alias is None

    tx.set_key_with_alias(account_private_key, alias_private_key)

    assert tx.alias == expected_evm_address


def test_set_key_with_alias_then_without_alias_overrides_alias():
    """set_key_without_alias should ovveride set_key_with_alias"""
    # Account key(ECDSA)
    account_private_key = PrivateKey.generate_ecdsa()
    account_public_key = account_private_key.public_key()

    # Alias key (ECDSA)
    alias_private_key = PrivateKey.generate_ecdsa()
    alias_public_key = alias_private_key.public_key()
    expected_evm_address = alias_public_key.to_evm_address()

    tx = AccountCreateTransaction().set_key_with_alias(
        account_private_key, alias_private_key
    )

    assert tx.alias == expected_evm_address

    tx.set_key_without_alias(account_private_key)

    assert tx.alias is None
