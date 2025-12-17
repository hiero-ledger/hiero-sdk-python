from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.tokens.token_airdrop_pending_record import PendingAirdropRecord
import pytest
from collections import defaultdict
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.transaction.transaction_record import TransactionRecord
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import (
    transaction_record_pb2,
    transaction_receipt_pb2,
)
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId

pytestmark = pytest.mark.unit


@pytest.fixture
def transaction_record(transaction_id):
    """Create a mock transaction record."""
    receipt = TransactionReceipt(
        receipt_proto=transaction_receipt_pb2.TransactionReceipt(
            status=ResponseCode.SUCCESS
        ),
        transaction_id=transaction_id
    )
    
    return TransactionRecord(
        transaction_id=transaction_id,
        transaction_hash=b'\x01\x02\x03\x04' * 12,
        transaction_memo="Test transaction memo",
        transaction_fee=100000,
        receipt=receipt,
        token_transfers=defaultdict(lambda: defaultdict(int)),
        nft_transfers=defaultdict(list[TokenNftTransfer]),
        transfers=defaultdict(int),
        new_pending_airdrops=[],
        prng_number=100,
        prng_bytes=None,
    )

@pytest.fixture
def proto_transaction_record(transaction_id):
    """Create a mock transaction record protobuf."""
    proto = transaction_record_pb2.TransactionRecord(
        transactionHash=b'\x01\x02\x03\x04' * 12,
        memo="Test transaction memo",
        transactionFee=100000,
        receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        transactionID=transaction_id._to_proto(),
        prng_number=100,
    )
    return proto

def test_transaction_record_initialization(transaction_record, transaction_id):
    """Test the initialization of the TransactionRecord class"""
    assert transaction_record.transaction_id == transaction_id
    assert transaction_record.transaction_hash == b'\x01\x02\x03\x04' * 12
    assert transaction_record.transaction_memo == "Test transaction memo"
    assert transaction_record.transaction_fee == 100000
    assert isinstance(transaction_record.receipt, TransactionReceipt)
    assert transaction_record.receipt.status == ResponseCode.SUCCESS
    assert transaction_record.prng_number == 100
    assert transaction_record.prng_bytes is None


def test_transaction_record_default_initialization():
    """Test the default initialization of the TransactionRecord class"""
    record = TransactionRecord()
    assert record.transaction_id is None
    assert record.transaction_hash is None
    assert record.transaction_memo is None
    assert record.transaction_fee is None
    assert record.receipt is None
    assert record.token_transfers == defaultdict(lambda: defaultdict(int))
    assert record.nft_transfers == defaultdict(list[TokenNftTransfer])
    assert record.transfers == defaultdict(int)
    assert record.new_pending_airdrops == []
    assert record.prng_number is None
    assert record.prng_bytes is None

def test_from_proto(proto_transaction_record, transaction_id):
    """Test the from_proto method of the TransactionRecord class"""
    record = TransactionRecord._from_proto(proto_transaction_record, transaction_id)

    assert record.transaction_id == transaction_id
    assert record.transaction_hash == b'\x01\x02\x03\x04' * 12
    assert record.transaction_memo == "Test transaction memo"
    assert record.transaction_fee == 100000
    assert isinstance(record.receipt, TransactionReceipt)
    assert record.receipt.status == ResponseCode.SUCCESS
    assert record.prng_number == 100
    assert record.prng_bytes == b""

def test_from_proto_with_transfers(transaction_id):
    """Test from_proto with HBAR transfers"""
    proto = transaction_record_pb2.TransactionRecord()
    transfer = proto.transferList.accountAmounts.add()
    transfer.accountID.CopyFrom(AccountId(0, 0, 200)._to_proto())
    transfer.amount = 1000

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.transfers[AccountId(0, 0, 200)] == 1000

def test_from_proto_with_token_transfers(transaction_id):
    """Test from_proto with token transfers"""
    proto = transaction_record_pb2.TransactionRecord()
    token_list = proto.tokenTransferLists.add()
    token_list.token.CopyFrom(TokenId(0, 0, 300)._to_proto())
    
    transfer = token_list.transfers.add()
    transfer.accountID.CopyFrom(AccountId(0, 0, 200)._to_proto())
    transfer.amount = 500

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.token_transfers[TokenId(0, 0, 300)][AccountId(0, 0, 200)] == 500

def test_from_proto_with_nft_transfers(transaction_id):
    """Test from_proto with NFT transfers"""
    proto = transaction_record_pb2.TransactionRecord()
    token_list = proto.tokenTransferLists.add()
    token_list.token.CopyFrom(TokenId(0, 0, 300)._to_proto())
    
    nft = token_list.nftTransfers.add()
    nft.senderAccountID.CopyFrom(AccountId(0, 0, 100)._to_proto())
    nft.receiverAccountID.CopyFrom(AccountId(0, 0, 200)._to_proto())
    nft.serialNumber = 1
    nft.is_approval = False

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert len(record.nft_transfers[TokenId(0, 0, 300)]) == 1
    transfer = record.nft_transfers[TokenId(0, 0, 300)][0]
    assert transfer.sender_id == AccountId(0, 0, 100)
    assert transfer.receiver_id == AccountId(0, 0, 200)
    assert transfer.serial_number == 1
    assert transfer.is_approved == False

def test_from_proto_with_new_pending_airdrops(transaction_id):
    """Test from_proto with Pending Airdrops"""
    sender = AccountId(0,0,100)
    receiver = AccountId(0,0,200)
    token_id = TokenId(0,0,1)
    amount = 10

    proto = transaction_record_pb2.TransactionRecord()
    pending_airdrop_id = PendingAirdropId(sender, receiver, token_id)
    proto.new_pending_airdrops.add().CopyFrom(PendingAirdropRecord(pending_airdrop_id, amount)._to_proto())
    
    record = TransactionRecord._from_proto(proto, transaction_id)
    assert len(record.new_pending_airdrops) == 1
    new_pending_airdrops = record.new_pending_airdrops[0]
    assert new_pending_airdrops.pending_airdrop_id.sender_id == sender
    assert new_pending_airdrops.pending_airdrop_id.receiver_id == receiver
    assert new_pending_airdrops.pending_airdrop_id.token_id == token_id
    assert new_pending_airdrops.amount == amount


def test_from_proto_with_prng_number(transaction_id):
    """Test from_proto with prng_number set"""
    proto = transaction_record_pb2.TransactionRecord()
    proto.prng_number = 42

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.prng_number == 42
    assert record.prng_bytes == b""


def test_from_proto_with_prng_bytes(transaction_id):
    """Test from_proto with prng_bytes set"""
    proto = transaction_record_pb2.TransactionRecord()
    proto.prng_bytes = b"123"

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.prng_bytes == b"123"
    assert record.prng_number == 0


def test_to_proto(transaction_record, transaction_id):
    """Test the to_proto method of the TransactionRecord class"""
    proto = transaction_record._to_proto()

    assert proto.transactionHash == b'\x01\x02\x03\x04' * 12
    assert proto.memo == "Test transaction memo"
    assert proto.transactionFee == 100000
    assert proto.receipt.status == ResponseCode.SUCCESS
    assert proto.transactionID == transaction_id._to_proto()
    assert proto.prng_number == 100
    assert proto.prng_bytes == b""

def test_proto_conversion(transaction_record):
    """Test converting TransactionRecord to proto and back preserves data"""
    proto = transaction_record._to_proto()
    converted = TransactionRecord._from_proto(proto, transaction_record.transaction_id)

    assert converted.transaction_id == transaction_record.transaction_id
    assert converted.transaction_hash == transaction_record.transaction_hash
    assert converted.transaction_memo == transaction_record.transaction_memo
    assert converted.transaction_fee == transaction_record.transaction_fee
    assert converted.receipt.status == transaction_record.receipt.status
    assert converted.prng_number == transaction_record.prng_number
    assert converted.prng_bytes == b""

def test_proto_conversion_with_transfers():
    """Test proto conversion preserves transfer data"""
    record = TransactionRecord()
    record.transfers = defaultdict(int)
    record.transfers[AccountId(0, 0, 100)] = -1000
    record.transfers[AccountId(0, 0, 200)] = 1000

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, None)

    assert converted.transfers[AccountId(0, 0, 100)] == -1000
    assert converted.transfers[AccountId(0, 0, 200)] == 1000

def test_proto_conversion_with_token_transfers():
    """Test proto conversion preserves token transfer data"""
    record = TransactionRecord()
    token_id = TokenId(0, 0, 300)
    record.token_transfers = defaultdict(lambda: defaultdict(int))
    record.token_transfers[token_id][AccountId(0, 0, 100)] = -500
    record.token_transfers[token_id][AccountId(0, 0, 200)] = 500

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, None)

    assert converted.token_transfers[token_id][AccountId(0, 0, 100)] == -500
    assert converted.token_transfers[token_id][AccountId(0, 0, 200)] == 500

def test_proto_conversion_with_nft_transfers():
    """Test proto conversion preserves NFT transfer data"""
    record = TransactionRecord()
    token_id = TokenId(0, 0, 300)
    nft_transfer = TokenNftTransfer(
        token_id=token_id,
        sender_id=AccountId(0, 0, 100),
        receiver_id=AccountId(0, 0, 200),
        serial_number=1,
        is_approved=False
    )
    record.nft_transfers = defaultdict(list[TokenNftTransfer])
    record.nft_transfers[token_id].append(nft_transfer)

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, None)

    assert len(converted.nft_transfers[token_id]) == 1
    transfer = converted.nft_transfers[token_id][0]
    assert transfer.sender_id == AccountId(0, 0, 100)
    assert transfer.receiver_id == AccountId(0, 0, 200)
    assert transfer.serial_number == 1
    assert transfer.is_approved == False

def test_proto_conversion_with_new_pending_airdrops():
    """Test proto conversion preserves PendingAirdropsRecord"""
    sender = AccountId(0,0,100)
    receiver = AccountId(0,0,200)
    token_id = TokenId(0,0,1)
    amount = 10

    record = TransactionRecord()
    record.new_pending_airdrops = []
    record.new_pending_airdrops.append(PendingAirdropRecord(PendingAirdropId(sender, receiver, token_id),amount))

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, None)

    assert len(converted.new_pending_airdrops) == 1
    new_pending_airdrops = converted.new_pending_airdrops[0]
    assert new_pending_airdrops.pending_airdrop_id.sender_id == sender
    assert new_pending_airdrops.pending_airdrop_id.receiver_id == receiver
    assert new_pending_airdrops.pending_airdrop_id.token_id == token_id
    assert new_pending_airdrops.amount == amount

def test_repr_method(transaction_id):
    """Test the __repr__ method of TransactionRecord."""
    # Test with default values
    record_default = TransactionRecord()
    expected_repr_default = (
        "TransactionRecord(transaction_id='None', "
        "transaction_hash=None, "
        "transaction_memo='None', "
        "transaction_fee=None, "
        "receipt_status='None', "
        "token_transfers={}, "
        "nft_transfers={}, "
        "transfers={}, "
        "new_pending_airdrops=[], "
        "call_result=None, "
        "prng_number=None, "
        "prng_bytes=None)"
    )
    assert repr(record_default) == expected_repr_default
    
    # Test with receipt only
    receipt = TransactionReceipt(
        receipt_proto=transaction_receipt_pb2.TransactionReceipt(
            status=ResponseCode.SUCCESS
        ),
        transaction_id=transaction_id,
    )
    record_with_receipt = TransactionRecord(
        transaction_id=transaction_id, receipt=receipt
    )
    expected_repr_with_receipt = (
        f"TransactionRecord(transaction_id='{transaction_id}', "
        f"transaction_hash=None, "
        f"transaction_memo='None', "
        f"transaction_fee=None, "
        f"receipt_status='SUCCESS', "
        f"token_transfers={{}}, "
        f"nft_transfers={{}}, "
        f"transfers={{}}, "
        f"new_pending_airdrops={[]}, "
        f"call_result=None, "
        f"prng_number=None, "
        f"prng_bytes=None)"
    )
    assert repr(record_with_receipt) == expected_repr_with_receipt

    # Test with all parameters set
    record_full = TransactionRecord(
        transaction_id=transaction_id,
        transaction_hash=b'\x01\x02\x03\x04',
        transaction_memo="Test memo",
        transaction_fee=100000,
        receipt=receipt,
    )
    expected_repr_full = (f"TransactionRecord(transaction_id='{transaction_id}', "
                         f"transaction_hash=b'\\x01\\x02\\x03\\x04', "
                         f"transaction_memo='Test memo', "
                         f"transaction_fee=100000, "
                         f"receipt_status='SUCCESS', "
                         f"token_transfers={{}}, "
                         f"nft_transfers={{}}, "
                         f"transfers={{}}, "
                         f"new_pending_airdrops={[]}, "
                         f"call_result=None, "
                         f"prng_number=None, "
                         f"prng_bytes=None)")
    assert repr(record_full) == expected_repr_full

    # Test with transfers
    record_with_transfers = TransactionRecord(
        transaction_id=transaction_id, receipt=receipt
    )
    record_with_transfers.transfers[AccountId(0, 0, 100)] = -1000
    record_with_transfers.transfers[AccountId(0, 0, 200)] = 1000
    
    expected_repr_with_transfers = (f"TransactionRecord(transaction_id='{transaction_id}', "
                                  f"transaction_hash=None, "
                                  f"transaction_memo='None', "
                                  f"transaction_fee=None, "
                                  f"receipt_status='SUCCESS', "
                                  f"token_transfers={{}}, "
                                  f"nft_transfers={{}}, "
                                  f"transfers={{AccountId(shard=0, realm=0, num=100): -1000, AccountId(shard=0, realm=0, num=200): 1000}}, "
                                  f"new_pending_airdrops={[]}, "
                                  f"call_result=None, "
                                  f"prng_number=None, "
                                  f"prng_bytes=None)")
    assert repr(record_with_transfers) == expected_repr_with_transfers


def test_proto_conversion_with_call_result():
    """Test the call_result property of TransactionRecord."""
    record = TransactionRecord()

    record.call_result = ContractFunctionResult(
        contract_id=ContractId(0, 0, 100),
        contract_call_result=b"Hello, world!",
        error_message="No errors",
        bloom=bytes.fromhex("ffff"),
        gas_used=100000,
        gas_available=1000000,
        amount=50,
    )

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, None)

    assert converted.call_result.contract_id == record.call_result.contract_id
    assert converted.call_result.contract_call_result == record.call_result.contract_call_result
    assert converted.call_result.error_message == record.call_result.error_message
    assert converted.call_result.bloom == record.call_result.bloom
    assert converted.call_result.gas_used == record.call_result.gas_used
    assert converted.call_result.gas_available == record.call_result.gas_available
    assert converted.call_result.amount == record.call_result.amount
