from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.token_revoke_kyc_pb2 import TokenRevokeKycTransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


def test_build_transaction_body(mock_account_ids):
    """Test building a token revoke KYC transaction body with valid values."""
    account_id, _, node_account_id, token_id, _ = mock_account_ids

    revoke_kyc_tx = TokenRevokeKycTransaction().set_token_id(token_id).set_account_id(account_id)

    # Set operator and node account IDs needed for building transaction body
    revoke_kyc_tx.operator_account_id = account_id
    revoke_kyc_tx.set_node_account_ids([node_account_id])

    transaction_body = revoke_kyc_tx.build_transaction_body()

    assert transaction_body.tokenRevokeKyc.token == token_id._to_proto()
    assert transaction_body.tokenRevokeKyc.account == account_id._to_proto()


def test_build_transaction_body_allows_missing_ids(mock_account_ids):
    """Allow missing IDs so validation is performed by the network, per the TCK spec."""
    account_id, _, _, token_id, _ = mock_account_ids

    # Missing token ID: build must succeed, with the token field left unset.
    revoke_kyc_tx = TokenRevokeKycTransaction(account_id=account_id)
    body = revoke_kyc_tx._build_proto_body()
    assert not body.HasField("token")
    assert body.account == account_id._to_proto()

    # Missing account ID: build must succeed, with the account field left unset.
    revoke_kyc_tx = TokenRevokeKycTransaction(token_id=token_id)
    body = revoke_kyc_tx._build_proto_body()
    assert body.token == token_id._to_proto()
    assert not body.HasField("account")


def test_constructor_with_parameters(mock_account_ids):
    """Test creating a token revoke KYC transaction with constructor parameters."""
    account_id, _, _, token_id, _ = mock_account_ids

    revoke_kyc_tx = TokenRevokeKycTransaction(token_id=token_id, account_id=account_id)

    assert revoke_kyc_tx.token_id == token_id
    assert revoke_kyc_tx.account_id == account_id


def test_set_methods(mock_account_ids):
    """Test the set methods of TokenRevokeKycTransaction."""
    account_id, _, _, token_id, _ = mock_account_ids

    revoke_kyc_tx = TokenRevokeKycTransaction()

    # Test method chaining
    tx_after_set = revoke_kyc_tx.set_token_id(token_id)
    assert tx_after_set is revoke_kyc_tx
    assert revoke_kyc_tx.token_id == token_id

    tx_after_set = revoke_kyc_tx.set_account_id(account_id)
    assert tx_after_set is revoke_kyc_tx
    assert revoke_kyc_tx.account_id == account_id


def test_set_methods_require_not_frozen(mock_account_ids, mock_client):
    """Test that set methods raise exception when transaction is frozen."""
    account_id, _, _, token_id, _ = mock_account_ids

    revoke_kyc_tx = TokenRevokeKycTransaction(token_id=token_id, account_id=account_id)
    revoke_kyc_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        revoke_kyc_tx.set_token_id(token_id)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        revoke_kyc_tx.set_account_id(account_id)


def test_revoke_kyc_transaction_can_execute(mock_account_ids):
    """Test that a revoke KYC transaction can be executed successfully."""
    account_id, _, _, token_id, _ = mock_account_ids

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for a successful token revoke KYC
    mock_receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=mock_receipt_proto,
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        transaction = TokenRevokeKycTransaction().set_token_id(token_id).set_account_id(account_id)

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"


def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token revoke KYC transaction."""
    account_id, _, _, token_id, _ = mock_account_ids

    revoke_kyc_tx = TokenRevokeKycTransaction().set_token_id(token_id).set_account_id(account_id)

    schedulable_body = revoke_kyc_tx.build_scheduled_body()

    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenRevokeKyc")
    assert schedulable_body.tokenRevokeKyc.token == token_id._to_proto()
    assert schedulable_body.tokenRevokeKyc.account == account_id._to_proto()


def test_revoke_kyc_transaction_from_proto(mock_account_ids):
    """Test that a revoke KYC transaction can be created from a protobuf object."""
    account_id, _, _, token_id, _ = mock_account_ids

    # Create protobuf object
    proto = TokenRevokeKycTransactionBody(token=token_id._to_proto(), account=account_id._to_proto())

    # Deserialize the protobuf object
    from_proto = TokenRevokeKycTransaction()._from_proto(proto)

    # Verify deserialized transaction matches original data
    assert from_proto.token_id == token_id
    assert from_proto.account_id == account_id

    # Deserialize empty protobuf
    from_proto = TokenRevokeKycTransaction()._from_proto(TokenRevokeKycTransactionBody())

    # Verify empty protobuf deserializes to empty/default values
    assert from_proto.token_id == TokenId(0, 0, 0)
    assert from_proto.account_id == AccountId()


def _round_trip(tx, signer=None):
    tx.set_transaction_id(TransactionId.from_string("0.0.123@1800000000.123456789"))
    tx.set_node_account_ids([AccountId(0, 0, 3)])
    tx.set_transaction_memo("Deserialization regression")
    tx.set_transaction_valid_duration(90)
    tx.transaction_fee = 123_456_789
    tx.freeze()

    if signer is not None:
        tx.sign(signer)

    original_bytes = tx.to_bytes()
    restored = Transaction.from_bytes(original_bytes)

    assert type(restored) is type(tx)
    assert restored.to_bytes() == original_bytes
    assert restored.transaction_id == tx.transaction_id
    assert restored.memo == "Deserialization regression"
    assert restored.transaction_valid_duration == 90
    assert restored.transaction_fee == 123_456_789

    return restored


@pytest.mark.parametrize("signed", [False, True], ids=["unsigned", "signed"])
def test_from_bytes_restores_all_fields(signed, private_key):
    """Restore populated IDs while retaining signatures and frozen state."""
    token_id = TokenId(1, 2, 345)
    account_id = AccountId(4, 5, 678)

    tx = TokenRevokeKycTransaction(token_id=token_id, account_id=account_id)
    restored = _round_trip(tx, signer=private_key if signed else None)

    assert restored.token_id == token_id
    assert restored.account_id == account_id

    if signed:
        assert restored.is_signed_by(private_key.public_key())

    with pytest.raises(Exception, match="immutable"):
        restored.set_token_id(TokenId(0, 0, 999))


@pytest.mark.parametrize(
    "token_id", [None, TokenId(0, 0, 0), TokenId(1, 2, 345)], ids=["absent-token", "zero-token", "nonzero-token"]
)
@pytest.mark.parametrize(
    "account_id", [None, AccountId(), AccountId(4, 5, 678)], ids=["absent-account", "zero-account", "nonzero-account"]
)
def test_from_bytes_preserves_token_and_account_presence(token_id, account_id):
    """Distinguish absent IDs from explicitly present zero-valued IDs."""
    tx = TokenRevokeKycTransaction(token_id=token_id, account_id=account_id)

    restored = _round_trip(tx)

    assert restored.token_id == token_id
    assert restored.account_id == account_id


@pytest.mark.parametrize("alias_kind", ["key", "evm"])
def test_from_bytes_preserves_account_alias(private_key, alias_kind):
    """Preserve public-key and EVM-address account aliases."""
    if alias_kind == "key":
        account_id = AccountId(4, 5, alias_key=private_key.public_key())
    else:
        account_id = AccountId(4, 5, evm_address=EvmAddress.from_bytes(bytes.fromhex("12" * 20)))

    tx = TokenRevokeKycTransaction(token_id=TokenId(1, 2, 345), account_id=account_id)

    restored = _round_trip(tx)

    assert restored.account_id == account_id


def test_from_protobuf_without_specific_body():
    """Retain common fields when the transaction-specific body is absent."""
    body = transaction_pb2.TransactionBody(memo="Common fields only")

    restored = TokenRevokeKycTransaction._from_protobuf(body)

    assert type(restored) is TokenRevokeKycTransaction
    assert restored.memo == "Common fields only"
    assert restored.token_id is None
    assert restored.account_id is None


def test_from_bytes_rejects_invalid_present_token_id():
    """Propagate validation errors for a present but invalid token ID."""
    body = transaction_pb2.TransactionBody()
    body.tokenFreeze.token.tokenNum = -1

    transaction_bytes = transaction_pb2.Transaction(bodyBytes=body.SerializeToString()).SerializeToString()

    with pytest.raises(ValueError, match="Num must be >= 0"):
        Transaction.from_bytes(transaction_bytes)
