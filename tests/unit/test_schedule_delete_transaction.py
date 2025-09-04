"""
Test cases for the ScheduleDeleteTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import (
    TransactionReceipt as TransactionReceiptProto,
)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (
    TransactionResponse as TransactionResponseProto,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_delete_transaction import (
    ScheduleDeleteTransaction,
)
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def delete_params():
    """Fixture for schedule delete parameters."""
    return {
        "schedule_id": ScheduleId(0, 0, 123),
    }


def test_constructor_with_parameters(delete_params):
    """Test creating a schedule delete transaction with constructor parameters."""
    delete_tx = ScheduleDeleteTransaction(schedule_id=delete_params["schedule_id"])

    assert delete_tx.schedule_id == delete_params["schedule_id"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    delete_tx = ScheduleDeleteTransaction()

    assert delete_tx.schedule_id is None
    assert delete_tx._default_transaction_fee == 500000000  # 5 hbar in tinybars


def test_build_transaction_body_with_valid_parameters(mock_account_ids, delete_params):
    """Test building a schedule delete transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    delete_tx = ScheduleDeleteTransaction(schedule_id=delete_params["schedule_id"])

    # Set operator and node account IDs needed for building transaction body
    delete_tx.operator_account_id = operator_id
    delete_tx.node_account_id = node_account_id

    transaction_body = delete_tx.build_transaction_body()

    assert (
        transaction_body.scheduleDelete.scheduleID
        == delete_params["schedule_id"]._to_proto()
    )


def test_build_transaction_body_missing_schedule_id():
    """Test that build_transaction_body raises ValueError when schedule_id is missing."""
    delete_tx = ScheduleDeleteTransaction()

    with pytest.raises(ValueError, match="Missing required ScheduleID"):
        delete_tx.build_transaction_body()


def test_set_schedule_id(delete_params):
    """Test setting schedule_id using the setter method."""
    delete_tx = ScheduleDeleteTransaction()

    result = delete_tx.set_schedule_id(delete_params["schedule_id"])

    assert delete_tx.schedule_id == delete_params["schedule_id"]
    assert result is delete_tx  # Should return self for method chaining


def test_method_chaining_with_setter(delete_params):
    """Test that setter method supports method chaining."""
    delete_tx = ScheduleDeleteTransaction()

    result = delete_tx.set_schedule_id(delete_params["schedule_id"])

    assert result is delete_tx
    assert delete_tx.schedule_id == delete_params["schedule_id"]


def test_set_methods_require_not_frozen(mock_client, delete_params):
    """Test that setter methods raise exception when transaction is frozen."""
    delete_tx = ScheduleDeleteTransaction(schedule_id=delete_params["schedule_id"])
    delete_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        delete_tx.set_schedule_id(delete_params["schedule_id"])


def test_sign_transaction(mock_client, delete_params):
    """Test signing the schedule delete transaction with a private key."""
    delete_tx = ScheduleDeleteTransaction(schedule_id=delete_params["schedule_id"])

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    delete_tx.freeze_with(mock_client)
    delete_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = delete_tx._transaction_body_bytes[node_id]

    assert len(delete_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = delete_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, delete_params):
    """Test converting the schedule delete transaction to protobuf format after signing."""
    delete_tx = ScheduleDeleteTransaction(schedule_id=delete_params["schedule_id"])

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    delete_tx.freeze_with(mock_client)
    delete_tx.sign(private_key)
    proto = delete_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    delete_tx = ScheduleDeleteTransaction()

    mock_channel = MagicMock()
    mock_schedule_stub = MagicMock()
    mock_channel.schedule = mock_schedule_stub

    method = delete_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_schedule_stub.deleteSchedule


def test_parameter_validation_types(delete_params):
    """Test that parameters accept the correct types."""
    delete_tx = ScheduleDeleteTransaction()

    # Test with valid type
    delete_tx.set_schedule_id(delete_params["schedule_id"])
    assert isinstance(delete_tx.schedule_id, ScheduleId)


def test_parameter_validation_none_values():
    """Test that parameters can be set to None."""
    delete_tx = ScheduleDeleteTransaction(schedule_id=ScheduleId(0, 0, 123))

    # schedule_id can be set to None
    delete_tx.set_schedule_id(None)
    assert delete_tx.schedule_id is None


def test_constructor_parameter_combinations():
    """Test various constructor parameter combinations."""
    schedule_id = ScheduleId(0, 0, 123)

    # Test with schedule_id
    delete_tx = ScheduleDeleteTransaction(schedule_id=schedule_id)
    assert delete_tx.schedule_id == schedule_id

    # Test with no parameters
    delete_tx = ScheduleDeleteTransaction()
    assert delete_tx.schedule_id is None


def test_build_scheduled_body_raises_exception():
    """Test that build_scheduled_body raises ValueError."""
    delete_tx = ScheduleDeleteTransaction()

    with pytest.raises(ValueError, match="Cannot schedule a ScheduleDeleteTransaction"):
        delete_tx.build_scheduled_body()


def test_build_proto_body_with_valid_schedule_id(delete_params):
    """Test building protobuf body with valid schedule_id."""
    delete_tx = ScheduleDeleteTransaction(schedule_id=delete_params["schedule_id"])

    proto_body = delete_tx._build_proto_body()

    assert proto_body.scheduleID == delete_params["schedule_id"]._to_proto()


def test_build_proto_body_missing_schedule_id():
    """Test that _build_proto_body raises ValueError when schedule_id is missing."""
    delete_tx = ScheduleDeleteTransaction()

    with pytest.raises(ValueError, match="Missing required ScheduleID"):
        delete_tx._build_proto_body()


def test_default_transaction_fee():
    """Test that the default transaction fee is set correctly."""
    delete_tx = ScheduleDeleteTransaction()

    assert delete_tx._default_transaction_fee == 500000000  # 5 hbar in tinybars


def test_schedule_delete_transaction_can_execute():
    """Test that a schedule delete transaction can be executed successfully."""
    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for successful schedule deletion
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS,
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

    with mock_hedera_servers(response_sequences) as client:
        schedule_id = ScheduleId(0, 0, 123)

        transaction = ScheduleDeleteTransaction().set_schedule_id(schedule_id)

        receipt = transaction.execute(client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), "Transaction should have succeeded"
