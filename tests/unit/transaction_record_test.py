"""Unit tests for the TransactionRecord class functionality."""

from collections import defaultdict

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import (
    transaction_receipt_pb2,
    transaction_record_pb2,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.assessed_custom_fee import AssessedCustomFee
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.tokens.token_airdrop_pending_record import PendingAirdropRecord
from hiero_sdk_python.tokens.token_association import TokenAssociation
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.transaction.transaction_id import TransactionId  # noqa: F401
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_record import TransactionRecord

pytestmark = pytest.mark.unit


@pytest.fixture
def transaction_record(transaction_id):
    """Create a mock transaction record."""
    receipt = TransactionReceipt(
        receipt_proto=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        transaction_id=transaction_id,
    )


    ts = Timestamp(seconds=1234567890, nanos=500000000)
    sched = ScheduleId(0, 0, 9999)

    return TransactionRecord(
        transaction_id=transaction_id,
        transaction_hash=b"\x01\x02\x03\x04" * 12,
        transaction_memo="Test transaction memo",
        transaction_fee=100000,
        receipt=receipt,
        token_transfers=defaultdict(lambda: defaultdict(int)),
        nft_transfers=defaultdict(list[TokenNftTransfer]),
        transfers=defaultdict(int),
        new_pending_airdrops=[],
        prng_number=100,
        prng_bytes=None,
        children=[],
        consensus_timestamp=ts,
        schedule_ref=sched,
        assessed_custom_fees=[
            AssessedCustomFee(
                amount=500000000,
                fee_collector_account_id=AccountId(shard=0, realm=0, num=98)
            )
        ],
        automatic_token_associations=[
            TokenAssociation(
                token_id=TokenId(shard=0, realm=0, num=5678),
                account_id=AccountId(shard=0, realm=0, num=1234)
            )
        ],
        parent_consensus_timestamp=ts,
        alias=b'\x12\x34\x56\x78',
        ethereum_hash=b'\xab' * 32,
        paid_staking_rewards=[
            (AccountId(shard=0, realm=0, num=456), 1000000)
        ],
        evm_address=b'\x12' * 20,
        contract_create_result=ContractFunctionResult(
            contract_id=ContractId(shard=0, realm=0, contract=789),
            contract_call_result=b"Mock result"
        ),
    )


@pytest.fixture
def proto_transaction_record(transaction_id):
    """Create a mock transaction record protobuf."""
    return transaction_record_pb2.TransactionRecord(
        transactionHash=b'\x01\x02\x03\x04' * 12,
        memo="Test transaction memo",
        transactionFee=100000,
        receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        transactionID=transaction_id._to_proto(),
        prng_number=100,
    )


def test_transaction_record_initialization(transaction_record, transaction_id):
    """Test the initialization of the TransactionRecord class."""
    assert transaction_record.transaction_id == transaction_id
    assert transaction_record.transaction_hash == b"\x01\x02\x03\x04" * 12
    assert transaction_record.transaction_memo == "Test transaction memo"
    assert transaction_record.transaction_fee == 100000
    assert isinstance(transaction_record.receipt, TransactionReceipt)
    assert transaction_record.receipt.status == ResponseCode.SUCCESS
    assert transaction_record.prng_number == 100
    assert transaction_record.prng_bytes is None
    assert transaction_record.children == []


def test_transaction_record_default_initialization():
    """Test the default initialization of the TransactionRecord class."""
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
    assert hasattr(record, "duplicates"), "TransactionRecord should have duplicates attribute"
    assert isinstance(record.duplicates, list)
    assert len(record.duplicates) == 0
    assert record.duplicates == []
    assert record.children == []


    assert record.consensus_timestamp is None
    assert record.schedule_ref is None
    assert record.assessed_custom_fees == []
    assert record.automatic_token_associations == []
    assert record.parent_consensus_timestamp is None
    assert record.alias is None
    assert record.ethereum_hash is None
    assert record.paid_staking_rewards == []
    assert record.evm_address is None
    assert record.contract_create_result is None

def test_from_proto(proto_transaction_record, transaction_id):
    """Test the from_proto method of the TransactionRecord class."""
    record = TransactionRecord._from_proto(proto_transaction_record, transaction_id)

    assert record.transaction_id == transaction_id
    assert record.transaction_hash == b"\x01\x02\x03\x04" * 12
    assert record.transaction_memo == "Test transaction memo"
    assert record.transaction_fee == 100000
    assert isinstance(record.receipt, TransactionReceipt)
    assert record.receipt.status == ResponseCode.SUCCESS
    assert record.prng_number == 100
    assert record.prng_bytes is None

    assert record.consensus_timestamp is None
    assert record.schedule_ref is None
    assert record.assessed_custom_fees == []
    assert record.automatic_token_associations == []
    assert record.parent_consensus_timestamp is None
    assert record.alias is None
    assert record.ethereum_hash is None
    assert record.paid_staking_rewards == []
    assert record.evm_address is None
    assert record.contract_create_result is None


def test_from_proto_with_transfers(transaction_id):
    """Test from_proto with HBAR transfers."""
    proto = transaction_record_pb2.TransactionRecord()
    transfer = proto.transferList.accountAmounts.add()
    transfer.accountID.CopyFrom(AccountId(0, 0, 200)._to_proto())
    transfer.amount = 1000

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.transfers[AccountId(0, 0, 200)] == 1000


def test_from_proto_with_token_transfers(transaction_id):
    """Test from_proto with token transfers."""
    proto = transaction_record_pb2.TransactionRecord()
    token_list = proto.tokenTransferLists.add()
    token_list.token.CopyFrom(TokenId(0, 0, 300)._to_proto())

    transfer = token_list.transfers.add()
    transfer.accountID.CopyFrom(AccountId(0, 0, 200)._to_proto())
    transfer.amount = 500

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.token_transfers[TokenId(0, 0, 300)][AccountId(0, 0, 200)] == 500


def test_from_proto_with_nft_transfers(transaction_id):
    """Test from_proto with NFT transfers."""
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
    assert transfer.is_approved is False


def test_from_proto_with_new_pending_airdrops(transaction_id):
    """Test from_proto with Pending Airdrops."""
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
    """Test from_proto with prng_number set."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.prng_number = 42

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.prng_number == 42
    assert record.prng_bytes is None


def test_from_proto_with_prng_bytes(transaction_id):
    """Test from_proto with prng_bytes set."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.prng_bytes = b"123"

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.prng_bytes == b"123"
    assert record.prng_number is None

def test_from_proto_with_consensus_timestamp(transaction_id):
    """Test parsing consensus_timestamp from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.consensusTimestamp.seconds = 1234567890
    proto.consensusTimestamp.nanos = 500000000

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.consensus_timestamp is not None
    assert record.consensus_timestamp.seconds == 1234567890
    assert record.consensus_timestamp.nanos == 500000000


def test_from_proto_with_schedule_ref(transaction_id):
    """Test parsing schedule_ref from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.scheduleRef.shardNum = 0
    proto.scheduleRef.realmNum = 0
    proto.scheduleRef.scheduleNum = 9999

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.schedule_ref is not None
    assert record.schedule_ref.shard == 0
    assert record.schedule_ref.realm == 0
    assert record.schedule_ref.schedule == 9999


def test_from_proto_with_assessed_custom_fees(transaction_id):
    """Test parsing assessed_custom_fees from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    fee = proto.assessed_custom_fees.add()
    fee.amount = 500000000
    fee.fee_collector_account_id.shardNum = 0
    fee.fee_collector_account_id.realmNum = 0
    fee.fee_collector_account_id.accountNum = 98

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert len(record.assessed_custom_fees) == 1
    f = record.assessed_custom_fees[0]
    assert isinstance(f, AssessedCustomFee)
    assert f.amount == 500000000
    assert f.fee_collector_account_id.num == 98


def test_from_proto_with_automatic_token_associations(transaction_id):
    """Test parsing automatic_token_associations from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    assoc = proto.automatic_token_associations.add()
    assoc.token_id.shardNum = 0
    assoc.token_id.realmNum = 0
    assoc.token_id.tokenNum = 5678
    assoc.account_id.shardNum = 0
    assoc.account_id.realmNum = 0
    assoc.account_id.accountNum = 1234

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert len(record.automatic_token_associations) == 1
    a = record.automatic_token_associations[0]
    assert isinstance(a, TokenAssociation)
    assert a.token_id.num == 5678
    assert a.account_id.num == 1234


def test_from_proto_with_parent_consensus_timestamp(transaction_id):
    """Test parsing parent_consensus_timestamp from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.parent_consensus_timestamp.seconds = 9876543210
    proto.parent_consensus_timestamp.nanos = 0

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.parent_consensus_timestamp is not None
    assert record.parent_consensus_timestamp.seconds == 9876543210


def test_from_proto_with_alias(transaction_id):
    """Test parsing alias bytes from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.alias = b'\x12\x34\x56\x78'

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.alias == b'\x12\x34\x56\x78'


def test_from_proto_with_ethereum_hash(transaction_id):
    """Test parsing ethereum_hash from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.ethereum_hash = b'\xab' * 32

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.ethereum_hash == b'\xab' * 32


def test_from_proto_with_paid_staking_rewards(transaction_id):
    """Test parsing paid_staking_rewards from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    reward = proto.paid_staking_rewards.add()
    reward.accountID.shardNum = 0
    reward.accountID.realmNum = 0
    reward.accountID.accountNum = 456
    reward.amount = 1000000

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert len(record.paid_staking_rewards) == 1
    account, amount = record.paid_staking_rewards[0]
    assert account.num == 456
    assert amount == 1000000


def test_from_proto_with_evm_address(transaction_id):
    """Test parsing evm_address from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.evm_address = b'\x12' * 20

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.evm_address == b'\x12' * 20


def test_from_proto_with_contract_create_result(transaction_id):
    """Test parsing contract_create_result from proto."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.contractCreateResult.contractID.shardNum = 0
    proto.contractCreateResult.contractID.realmNum = 0
    proto.contractCreateResult.contractID.contractNum = 789
    proto.contractCreateResult.contractCallResult = b"Created!"

    record = TransactionRecord._from_proto(proto, transaction_id)
    assert record.contract_create_result is not None
    assert record.contract_create_result.contract_id.contract == 789
    assert record.contract_create_result.contract_call_result == b"Created!"

def test_to_proto(transaction_record, transaction_id):
    """Test the to_proto method of the TransactionRecord class."""
    proto = transaction_record._to_proto()

    assert proto.transactionHash == b"\x01\x02\x03\x04" * 12
    assert proto.memo == "Test transaction memo"
    assert proto.transactionFee == 100000
    assert proto.receipt.status == ResponseCode.SUCCESS
    assert proto.transactionID == transaction_id._to_proto()
    assert proto.prng_number == 100
    assert proto.prng_bytes == b""


def test_proto_conversion(transaction_record):
    """Test converting TransactionRecord to proto and back preserves data."""
    proto = transaction_record._to_proto()
    converted = TransactionRecord._from_proto(proto, transaction_record.transaction_id)

    assert converted.transaction_id == transaction_record.transaction_id
    assert converted.transaction_hash == transaction_record.transaction_hash
    assert converted.transaction_memo == transaction_record.transaction_memo
    assert converted.transaction_fee == transaction_record.transaction_fee
    assert converted.receipt.status == transaction_record.receipt.status
    assert converted.prng_number == transaction_record.prng_number
    assert converted.prng_bytes is None


def test_proto_conversion_with_transfers(transaction_id):
    """Test proto conversion preserves transfer data."""
    record = TransactionRecord()
    record.transfers = defaultdict(int)
    record.transfers[AccountId(0, 0, 100)] = -1000
    record.transfers[AccountId(0, 0, 200)] = 1000

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, transaction_id)

    assert converted.transfers[AccountId(0, 0, 100)] == -1000
    assert converted.transfers[AccountId(0, 0, 200)] == 1000


def test_proto_conversion_with_token_transfers(transaction_id):
    """Test proto conversion preserves token transfer data."""
    record = TransactionRecord()
    token_id = TokenId(0, 0, 300)
    record.token_transfers = defaultdict(lambda: defaultdict(int))
    record.token_transfers[token_id][AccountId(0, 0, 100)] = -500
    record.token_transfers[token_id][AccountId(0, 0, 200)] = 500

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, transaction_id)

    assert converted.token_transfers[token_id][AccountId(0, 0, 100)] == -500
    assert converted.token_transfers[token_id][AccountId(0, 0, 200)] == 500


def test_proto_conversion_with_nft_transfers(transaction_id):
    """Test proto conversion preserves NFT transfer data."""
    record = TransactionRecord()
    token_id = TokenId(0, 0, 300)
    nft_transfer = TokenNftTransfer(
        token_id=token_id,
        sender_id=AccountId(0, 0, 100),
        receiver_id=AccountId(0, 0, 200),
        serial_number=1,
        is_approved=False,
    )
    record.nft_transfers = defaultdict(list[TokenNftTransfer])
    record.nft_transfers[token_id].append(nft_transfer)

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, transaction_id)

    assert len(converted.nft_transfers[token_id]) == 1
    transfer = converted.nft_transfers[token_id][0]
    assert transfer.sender_id == AccountId(0, 0, 100)
    assert transfer.receiver_id == AccountId(0, 0, 200)
    assert transfer.serial_number == 1
    assert not transfer.is_approved


def test_proto_conversion_with_new_pending_airdrops(transaction_id):
    """Test proto conversion preserves PendingAirdropsRecord."""
    sender = AccountId(0,0,100)
    receiver = AccountId(0,0,200)
    token_id = TokenId(0,0,1)
    amount = 10

    record = TransactionRecord()
    record.new_pending_airdrops = []
    record.new_pending_airdrops.append(PendingAirdropRecord(PendingAirdropId(sender, receiver, token_id), amount))

    proto = record._to_proto()
    converted = TransactionRecord._from_proto(proto, transaction_id)

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
    repr_default = repr(record_default)
    assert "duplicates_count=0" in repr_default
    assert "transaction_id='None'" in repr_default
    assert "receipt_status='None'" in repr_default
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
        "prng_bytes=None, "
        "duplicates_count=0, "
        "children_count=0, "
        "consensus_timestamp=None, "
        "schedule_ref=None, "
        "assessed_custom_fees=[], "
        "automatic_token_associations=[], "
        "parent_consensus_timestamp=None, "
        "alias=None, "
        "ethereum_hash=None, "
        "paid_staking_rewards=[], "
        "evm_address=None, "
        "contract_create_result=None)"
    )
    assert repr(record_default) == expected_repr_default

    # Test with receipt only
    receipt = TransactionReceipt(
        receipt_proto=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        transaction_id=transaction_id,
    )
    record_with_receipt = TransactionRecord(transaction_id=transaction_id, receipt=receipt)
    repr_receipt = repr(record_with_receipt)
    assert "duplicates_count=0" in repr_receipt
    assert f"transaction_id='{transaction_id}'" in repr_receipt
    assert "receipt_status='SUCCESS'" in repr_receipt
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
        f"prng_bytes=None, "
        f"duplicates_count=0, "
        f"children_count=0, "
        f"consensus_timestamp=None, "
        f"schedule_ref=None, "
        f"assessed_custom_fees=[], "
        f"automatic_token_associations=[], "
        f"parent_consensus_timestamp=None, "
        f"alias=None, "
        f"ethereum_hash=None, "
        f"paid_staking_rewards=[], "
        f"evm_address=None, "
        f"contract_create_result=None)"
    )
    assert repr(record_with_receipt) == expected_repr_with_receipt

    # Test with all parameters set
    ts = Timestamp(1234567890, 0)
    sched = ScheduleId(0, 0, 9999)
    record_full = TransactionRecord(
        transaction_id=transaction_id,
        transaction_hash=b"\x01\x02\x03\x04",
        transaction_memo="Test memo",
        transaction_fee=100000,
        receipt=receipt,
        consensus_timestamp=ts,
        schedule_ref=sched,
        assessed_custom_fees=[AssessedCustomFee(
            amount=500000000,
            fee_collector_account_id=AccountId(0, 0, 98)
        )],
        automatic_token_associations=[TokenAssociation(token_id=TokenId(0, 0, 5678), account_id=AccountId(0, 0, 1234))],
        parent_consensus_timestamp=ts,
        alias=b'\x12\x34',
        ethereum_hash=b'\xab' * 32,
        paid_staking_rewards=[(AccountId(0, 0, 456), 1000000)],
        evm_address=b'\x12' * 20,
        contract_create_result=ContractFunctionResult(contract_id=ContractId(0, 0, 789)),
    )
    
    repr_full = repr(record_full)
    assert f"transaction_id='{transaction_id}'" in repr_full
    assert "transaction_hash=b'\\x01\\x02\\x03\\x04'" in repr_full
    assert "transaction_memo='Test memo'" in repr_full
    assert "transaction_fee=100000" in repr_full
    assert "receipt_status='SUCCESS'" in repr_full
    assert "consensus_timestamp=" in repr_full
    assert f"schedule_ref={sched}" in repr_full
    assert "assessed_custom_fees=" in repr_full
    assert "automatic_token_associations=" in repr_full
    assert "parent_consensus_timestamp=" in repr_full
    assert "alias=b'\\x124'" in repr_full
    assert "ethereum_hash=" in repr_full
    assert "paid_staking_rewards=" in repr_full
    assert "evm_address=" in repr_full
    assert "contract_create_result=" in repr_full
    assert "duplicates_count=0" in repr_full
    assert "children_count=0" in repr_full

    # Test with transfers
    record_with_transfers = TransactionRecord(transaction_id=transaction_id, receipt=receipt)
    record_with_transfers.transfers[AccountId(0, 0, 100)] = -1000
    record_with_transfers.transfers[AccountId(0, 0, 200)] = 1000
    repr_transfers = repr(record_with_transfers)
    assert "duplicates_count=0" in repr_transfers
    assert (
        "transfers={AccountId(shard=0, realm=0, num=100): -1000, AccountId(shard=0, realm=0, num=200): 1000}"
        in repr_transfers
    )

    expected_repr_with_transfers = (
        f"TransactionRecord(transaction_id='{transaction_id}', "
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
        f"prng_bytes=None, "
        f"duplicates_count=0, "
        f"children_count=0)"
    )
    assert "transfers={AccountId(shard=0, realm=0, num=100): -1000, AccountId(shard=0, realm=0, num=200): 1000}" in repr_transfers
    
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
                                  f"prng_bytes=None, "
                                  f"duplicates_count=0, "
                                  f"children_count=0, "
                                  f"consensus_timestamp=None, "
                                  f"schedule_ref=None, "
                                  f"assessed_custom_fees=[], "
                                  f"automatic_token_associations=[], "
                                  f"parent_consensus_timestamp=None, "
                                  f"alias=None, "
                                  f"ethereum_hash=None, "
                                  f"paid_staking_rewards=[], "
                                  f"evm_address=None, "
                                  f"contract_create_result=None)")
    assert repr(record_with_transfers) == expected_repr_with_transfers


def test_proto_conversion_with_call_result(transaction_id):
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
    converted = TransactionRecord._from_proto(proto, transaction_id)

    assert converted.call_result.contract_id == record.call_result.contract_id
    assert converted.call_result.contract_call_result == record.call_result.contract_call_result
    assert converted.call_result.error_message == record.call_result.error_message
    assert converted.call_result.bloom == record.call_result.bloom
    assert converted.call_result.gas_used == record.call_result.gas_used
    assert converted.call_result.gas_available == record.call_result.gas_available
    assert converted.call_result.amount == record.call_result.amount


def test_from_proto_accepts_and_stores_duplicates(transaction_id):
    """Test that _from_proto correctly stores provided duplicate records."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.memo = "Main"

    dup1 = TransactionRecord(transaction_id=transaction_id, transaction_memo="dup1")
    dup2 = TransactionRecord(transaction_id=transaction_id, transaction_memo="dup2")

    record = TransactionRecord._from_proto(proto, transaction_id, duplicates=[dup1, dup2])

    assert len(record.duplicates) == 2, "Should store exactly two duplicates"
    assert record.duplicates[0].transaction_memo == "dup1", "First duplicate memo mismatch"
    assert record.duplicates[1].transaction_memo == "dup2", "Second duplicate memo mismatch"


def test_from_proto_without_duplicates_param_backward_compat(transaction_id):
    """Test _from_proto works without duplicates parameter (backward compatibility)."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.memo = "Test"

    record = TransactionRecord._from_proto(proto, transaction_id)

    assert record.duplicates == [], "Duplicates should default to empty list when omitted"
    assert record.transaction_memo == "Test"


def test_from_proto_with_empty_duplicates_list(transaction_id):
    """Test _from_proto with explicit empty duplicates list."""
    proto = transaction_record_pb2.TransactionRecord()

    record = TransactionRecord._from_proto(proto, transaction_id, duplicates=[])

    assert len(record.duplicates) == 0, "Empty duplicates list should remain empty"


def test_from_proto_with_duplicates_none(transaction_id):
    """Test explicit duplicates=None uses the fallback to empty list."""
    proto = transaction_record_pb2.TransactionRecord()
    proto.memo = "With None duplicates"

    record = TransactionRecord._from_proto(proto, transaction_id, duplicates=None)

    assert record.duplicates == [], "duplicates=None should resolve to empty list"
    assert record.transaction_memo == "With None duplicates"


def test_from_proto_with_duplicates_instances(transaction_id):
    """Test that provided duplicate instances are stored by reference."""
    proto = transaction_record_pb2.TransactionRecord()

    dup = TransactionRecord(transaction_id=transaction_id, transaction_memo="example dup")

    record = TransactionRecord._from_proto(proto, transaction_id, duplicates=[dup])

    assert record.duplicates[0] is dup, "Should store the exact duplicate instance by reference"


def test_to_proto_does_not_serialize_duplicates(transaction_id):
    """Test that _to_proto excludes duplicates, preserving the query-only invariant."""
    dup = TransactionRecord(transaction_id=transaction_id, transaction_memo="dup")
    record = TransactionRecord(
        transaction_id=transaction_id,
        transaction_memo="primary",
        duplicates=[dup],
    )
    assert len(record.duplicates) == 1, "Pre-condition: duplicates exist"

    proto = record._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)

    assert round_tripped.duplicates == [], "Duplicates must not survive round-trip through proto"
    assert round_tripped.transaction_memo == "primary"


def test_repr_includes_duplicates_count(transaction_id):
    """Test that __repr__ shows correct duplicates_count."""
    record = TransactionRecord(transaction_id=transaction_id)
    assert "duplicates_count=0" in repr(record), "Default duplicates_count should be 0"

    dup = TransactionRecord(transaction_id=transaction_id)
    record.duplicates = [dup, dup]

    assert "duplicates_count=2" in repr(record), "duplicates_count should reflect list length"



def test_from_proto_raises_when_no_transaction_id_available():
    """Verify error is raised when neither transaction_id param nor proto.transactionID is present."""
    proto = transaction_record_pb2.TransactionRecord()

    # Force-clear the field (works in protobuf 3 & 4)
    
    proto.ClearField("transactionID")

    assert not proto.HasField("transactionID"), "Field should be absent after ClearField"

    with pytest.raises(ValueError, match=r"transaction_id is required when proto\.transactionID is not present"):
        TransactionRecord._from_proto(proto, transaction_id=None)


def test_transaction_record_children_not_shared_between_instances():
    """Children not shared between two different instances."""
    r1 = TransactionRecord()
    r2 = TransactionRecord()

    r1.children.append(TransactionRecord())

    assert len(r1.children) == 1
    assert len(r2.children) == 0

def test_round_trip_consensus_timestamp(transaction_id):
    """Test consensus timestamp survives protobuf round-trip."""
    ts = Timestamp(1234567890, 500000000)
    original = TransactionRecord(consensus_timestamp=ts)
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.consensus_timestamp == ts


def test_round_trip_schedule_ref(transaction_id):
    """Test schedule reference survives protobuf round-trip."""
    sched = ScheduleId(0, 0, 9999)
    original = TransactionRecord(schedule_ref=sched)
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.schedule_ref == sched


def test_round_trip_assessed_custom_fees(transaction_id):
    """Test custom fees survive protobuf round-trip."""
    fee = AssessedCustomFee(
        amount=500000000,
        fee_collector_account_id=AccountId(0, 0, 98)
    )
    original = TransactionRecord(assessed_custom_fees=[fee])
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert len(round_tripped.assessed_custom_fees) == 1
    assert round_tripped.assessed_custom_fees[0].amount == 500000000


def test_round_trip_automatic_token_associations(transaction_id):
    """Test token associations survive protobuf round-trip."""
    assoc = TokenAssociation(
        token_id=TokenId(0, 0, 5678),
        account_id=AccountId(0, 0, 1234)
    )
    original = TransactionRecord(automatic_token_associations=[assoc])
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert len(round_tripped.automatic_token_associations) == 1
    assert round_tripped.automatic_token_associations[0].token_id.num == 5678


def test_round_trip_parent_consensus_timestamp(transaction_id):
    """Test parent timestamp survives protobuf round-trip."""
    ts = Timestamp(9876543210, 0)
    original = TransactionRecord(parent_consensus_timestamp=ts)
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.parent_consensus_timestamp == ts


def test_round_trip_alias(transaction_id):
    """Test alias bytes survive protobuf round-trip."""
    original = TransactionRecord(alias=b'\x12\x34')
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.alias == b'\x12\x34'


def test_round_trip_ethereum_hash(transaction_id):
    """Test ethereum hash survives protobuf round-trip."""
    original = TransactionRecord(ethereum_hash=b'\xab' * 32)
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.ethereum_hash == b'\xab' * 32


def test_round_trip_paid_staking_rewards(transaction_id):
    """Test staking rewards survive protobuf round-trip."""
    rewards = [(AccountId(0, 0, 456), 1000000)]
    original = TransactionRecord(paid_staking_rewards=rewards)
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.paid_staking_rewards == rewards


def test_round_trip_evm_address(transaction_id):
    """Test EVM address survives protobuf round-trip."""
    original = TransactionRecord(evm_address=b'\x12' * 20)
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.evm_address == b'\x12' * 20


def test_round_trip_contract_create_result(transaction_id):
    """Test contract creation result survives round-trip."""
    result = ContractFunctionResult(
        contract_id=ContractId(0, 0, 789),
        contract_call_result=b"Created!"
    )
    original = TransactionRecord(contract_create_result=result)
    proto = original._to_proto()
    round_tripped = TransactionRecord._from_proto(proto, transaction_id)
    assert round_tripped.contract_create_result.contract_id == result.contract_id
    assert round_tripped.contract_create_result.contract_call_result == b"Created!"

def test_to_proto_raises_when_both_call_and_create_result_set(transaction_id):
    """Setting both call_result and contract_create_result must raise (protobuf oneof)."""
    record = TransactionRecord(
        transaction_id=transaction_id,
        call_result=ContractFunctionResult(
            contract_id=ContractId(0, 0, 100),
        ),
        contract_create_result=ContractFunctionResult(
            contract_id=ContractId(0, 0, 200),
        ),
    )

    with pytest.raises(ValueError, match="mutually exclusive"):
        record._to_proto()

def test_to_proto_raises_when_both_prng_fields_set(transaction_id):
    """Setting both prng_number and prng_bytes must raise (entropy oneof)."""
    record = TransactionRecord(
        transaction_id=transaction_id,
        prng_number=1,
        prng_bytes=b"\x01",
    )

    with pytest.raises(ValueError, match="mutually exclusive"):
        record._to_proto()
        