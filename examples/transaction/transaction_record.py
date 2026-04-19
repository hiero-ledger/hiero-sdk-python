"""
Simple example: Exploring TransactionRecord fields.

This example creates a mock TransactionRecord with sample data and prints all fields
in a readable format.

No network or client needed — just run the file!

Run:
    python examples/transaction/transaction_record.py
"""

from collections import defaultdict

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import transaction_receipt_pb2
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.assessed_custom_fee import AssessedCustomFee
from hiero_sdk_python.tokens.token_association import TokenAssociation
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_record import TransactionRecord


def create_mock_record():
    """Create a mock TransactionRecord with sample values for all fields."""
    # Basic setup
    tx_id = TransactionId.from_string("0.0.1234@1698765432.000000000")

    receipt_proto = transaction_receipt_pb2.TransactionReceipt()
    receipt_proto.status = ResponseCode.SUCCESS.value

    receipt = TransactionReceipt(receipt_proto=receipt_proto, transaction_id=tx_id)

    ts = Timestamp(seconds=1698765432, nanos=123456789)
    sched = ScheduleId(0, 0, 9999)

    record = TransactionRecord(
        transaction_id=tx_id,
        transaction_hash=b"\x01\x02\x03\x04" * 12,
        transaction_memo="Hello from example!",
        transaction_fee=50000,
        receipt=receipt,
        token_transfers=defaultdict(lambda: defaultdict(int)),
        nft_transfers=defaultdict(list),
        transfers=defaultdict(int),
        new_pending_airdrops=[],
        prng_number=42,
        prng_bytes=None,  # mutually exclusive with prng_number
        duplicates=[],
        children=[],
        consensus_timestamp=ts,
        schedule_ref=sched,
        assessed_custom_fees=[
            AssessedCustomFee(
                amount=1000000,
                fee_collector_account_id=AccountId(shard=0, realm=0, num=98),
                effective_payer_account_ids=[AccountId(shard=0, realm=0, num=100)],
            )
        ],
        automatic_token_associations=[
            TokenAssociation(
                token_id=TokenId(shard=0, realm=0, num=5678), account_id=AccountId(shard=0, realm=0, num=1234)
            )
        ],
        parent_consensus_timestamp=ts,
        alias=b"\x12\x34\x56\x78\x9a\xbc",
        ethereum_hash=b"\xab" * 32,
        paid_staking_rewards=[
            (AccountId(shard=0, realm=0, num=456), 500000),
            (AccountId(shard=0, realm=0, num=789), 250000),
        ],
        evm_address=b"\xef" * 20,
        contract_create_result=ContractFunctionResult(
            contract_id=ContractId(shard=0, realm=0, contract=1000),
            contract_call_result=b"Contract created successfully!",
        ),
    )

    record.transfers[AccountId(shard=0, realm=0, num=100)] = -10000
    record.transfers[AccountId(shard=0, realm=0, num=200)] = 10000

    return record


def _print_basic_fields(record):
    print("Basic:")
    print(f"  Transaction ID: {record.transaction_id}")
    print(f"  Memo: {record.transaction_memo}")
    print(f"  Fee: {record.transaction_fee} tinybars")
    print(f"  Hash: {record.transaction_hash.hex() if record.transaction_hash else 'None'}")
    if record.receipt:
        try:
            status = ResponseCode(record.receipt.status).name
        except ValueError:
            status = str(record.receipt.status)
    else:
        status = "None"
    print(f"  Receipt Status: {status}")
    print(f"  PRNG Number: {record.prng_number}")
    print(f"  PRNG Bytes (hex): {record.prng_bytes.hex() if record.prng_bytes else 'None'}")


def _print_transfer_fields(record):
    print(f"  HBAR Transfers: {dict(record.transfers) if record.transfers else 'None'}")
    print(f"  Token Transfers: {dict(record.token_transfers) if record.token_transfers else 'None'}")
    print(
        f"  NFT Transfers: { {k: len(v) for k, v in record.nft_transfers.items()} if record.nft_transfers else 'None' }"
    )
    print(f"  Pending Airdrops: {len(record.new_pending_airdrops)}")


def _print_new_fields(record):
    print(f"  Consensus Timestamp: {record.consensus_timestamp}")
    print(f"  Parent Consensus Timestamp: {record.parent_consensus_timestamp}")
    print(f"  Schedule Ref: {record.schedule_ref}")
    print(f"  Assessed Custom Fees ({len(record.assessed_custom_fees)}):")
    for fee in record.assessed_custom_fees:
        token = fee.token_id if fee.token_id else "HBAR"
        payers = (
            ", ".join(str(p) for p in fee.effective_payer_account_ids) if fee.effective_payer_account_ids else "N/A"
        )
        print(f"    - {fee.amount} {token} → Collector: {fee.fee_collector_account_id}, Payers: {payers}")
    print(f"  Automatic Token Associations ({len(record.automatic_token_associations)}):")
    for assoc in record.automatic_token_associations:
        print(f"    - Token {assoc.token_id} → Account {assoc.account_id}")
    print(f"  Alias (hex): {record.alias.hex() if record.alias else 'None'}")
    print(f"  Ethereum Hash (hex): {record.ethereum_hash.hex() if record.ethereum_hash else 'None'}")
    print(f"  Paid Staking Rewards ({len(record.paid_staking_rewards)}):")
    for account, amount in record.paid_staking_rewards:
        print(f"    - {account}: {amount} tinybars")
    print(f"  EVM Address (hex): {record.evm_address.hex() if record.evm_address else 'None'}")
    if record.contract_create_result:
        print(f"  Contract Create Result: {record.contract_create_result.contract_id}")
        print(
            f"    Result bytes (first 32): {record.contract_create_result.contract_call_result[:32].hex() if record.contract_create_result.contract_call_result else 'None'}..."
        )
    else:
        print("  Contract Create Result: None")


def print_all_fields(record):
    """Print all fields of TransactionRecord in a simple, readable way."""
    print("=== TransactionRecord Example ===")
    _print_basic_fields(record)
    _print_transfer_fields(record)
    _print_new_fields(record)


def main():
    """Run the TransactionRecord example."""
    print("Creating mock TransactionRecord...\n")
    record = create_mock_record()
    print_all_fields(record)


if __name__ == "__main__":
    main()
