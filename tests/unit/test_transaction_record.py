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
        transfers=defaultdict(int)
    )

@pytest.fixture
def proto_transaction_record(transaction_id):
    """Create a mock transaction record protobuf."""
    proto = transaction_record_pb2.TransactionRecord(
        transactionHash=b'\x01\x02\x03\x04' * 12,
        memo="Test transaction memo",
        transactionFee=100000,
        receipt=transaction_receipt_pb2.TransactionReceipt(
            status=ResponseCode.SUCCESS
        ),
        transactionID=transaction_id._to_proto()
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

def test_from_proto(proto_transaction_record, transaction_id):
    """Test the from_proto method of the TransactionRecord class"""
    record = TransactionRecord._from_proto(proto_transaction_record, transaction_id)

    assert record.transaction_id == transaction_id
    assert record.transaction_hash == b'\x01\x02\x03\x04' * 12
    assert record.transaction_memo == "Test transaction memo"
    assert record.transaction_fee == 100000
    assert isinstance(record.receipt, TransactionReceipt)
    assert record.receipt.status == ResponseCode.SUCCESS

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

def test_to_proto(transaction_record, transaction_id):
    """Test the to_proto method of the TransactionRecord class"""
    proto = transaction_record._to_proto()

    assert proto.transactionHash == b'\x01\x02\x03\x04' * 12
    assert proto.memo == "Test transaction memo"
    assert proto.transactionFee == 100000
    assert proto.receipt.status == ResponseCode.SUCCESS
    assert proto.transactionID == transaction_id._to_proto()

def test_proto_conversion(transaction_record):
    """Test converting TransactionRecord to proto and back preserves data"""
    proto = transaction_record._to_proto()
    converted = TransactionRecord._from_proto(proto, transaction_record.transaction_id)

    assert converted.transaction_id == transaction_record.transaction_id
    assert converted.transaction_hash == transaction_record.transaction_hash
    assert converted.transaction_memo == transaction_record.transaction_memo
    assert converted.transaction_fee == transaction_record.transaction_fee
    assert converted.receipt.status == transaction_record.receipt.status

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

def test_repr_method(transaction_id):
    """Test the __repr__ method of TransactionRecord."""
    # Test with default values
    record_default = TransactionRecord()
    expected_repr_default = ("TransactionRecord(transaction_id='None', "
                           "transaction_hash=None, "
                           "transaction_memo='None', "
                           "transaction_fee=None, "
                           "receipt_status='None', "
                           "token_transfers={}, "
                           "nft_transfers={}, "
                           "transfers={})")
    assert repr(record_default) == expected_repr_default
    
    # Test with receipt only
    receipt = TransactionReceipt(
        receipt_proto=transaction_receipt_pb2.TransactionReceipt(
            status=ResponseCode.SUCCESS
        ),
        transaction_id=transaction_id
    )
    record_with_receipt = TransactionRecord(transaction_id=transaction_id, receipt=receipt)
    expected_repr_with_receipt = (f"TransactionRecord(transaction_id='{transaction_id}', "
                                f"transaction_hash=None, "
                                f"transaction_memo='None', "
                                f"transaction_fee=None, "
                                f"receipt_status='SUCCESS', "
                                f"token_transfers={{}}, "
                                f"nft_transfers={{}}, "
                                f"transfers={{}})")
    assert repr(record_with_receipt) == expected_repr_with_receipt
    
    # Test with all parameters set
    record_full = TransactionRecord(
        transaction_id=transaction_id,
        transaction_hash=b'\x01\x02\x03\x04',
        transaction_memo="Test memo",
        transaction_fee=100000,
        receipt=receipt
    )
    expected_repr_full = (f"TransactionRecord(transaction_id='{transaction_id}', "
                         f"transaction_hash=b'\\x01\\x02\\x03\\x04', "
                         f"transaction_memo='Test memo', "
                         f"transaction_fee=100000, "
                         f"receipt_status='SUCCESS', "
                         f"token_transfers={{}}, "
                         f"nft_transfers={{}}, "
                         f"transfers={{}})")
    assert repr(record_full) == expected_repr_full
    
    # Test with transfers
    record_with_transfers = TransactionRecord(
        transaction_id=transaction_id,
        receipt=receipt
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
                                  f"transfers={{AccountId(shard=0, realm=0, num=100): -1000, AccountId(shard=0, realm=0, num=200): 1000}})")
    assert repr(record_with_transfers) == expected_repr_with_transfers
