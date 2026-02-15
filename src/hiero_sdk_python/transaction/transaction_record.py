"""
This module implements the TransactionRecord class which represents a complete record
of a transaction executed on the Hiero network. It serves as a comprehensive data
structure that captures all aspects of a transaction's execution and its effects.

The module provides functionality to:
- Store and access detailed transaction metadata (ID, hash, memo, fees)
- Track various types of asset transfers:
  * HBAR cryptocurrency transfers between accounts
  * Fungible token transfers with amounts
  * Non-fungible token (NFT) transfers with serial numbers
- Handle smart contract execution results
- Process airdrop records for token distributions
- Manage pseudo-random number generation (PRNG) outputs
- Convert between Hiero's internal representation and protobuf messages

"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.hapi.services import transaction_record_pb2
from hiero_sdk_python.tokens.token_airdrop_pending_record import PendingAirdropRecord
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.tokens.assessed_custom_fee import AssessedCustomFee
from hiero_sdk_python.tokens.token_association import TokenAssociation

@dataclass
class TransactionRecord:
    """
    Represents a record of a completed transaction on the Hiero network.

    This class captures comprehensive information about a transaction's execution,
    including metadata, HBAR and token transfers, contract results, staking rewards,
    custom fees, pending airdrops, PRNG outputs, and scheduling information.

    Attributes:
        transaction_id: The unique identifier of the transaction.
        transaction_hash: The raw SHA-384 hash of the signed transaction bytes.
        transaction_memo: Optional text memo attached to the transaction.
        transaction_fee: Total network fee charged (in tinybars).
        receipt: Summary of transaction outcome (status, account & file IDs created, etc.).
        call_result: Result of a ContractCall transaction (if applicable).
        contract_create_result: Result of a ContractCreate transaction (if applicable).
        token_transfers: Fungible token movements (token → account → amount).
        nft_transfers: Non-fungible token (NFT) movements (token → list of serial transfers).
        transfers: HBAR / account balance changes (account → net amount in tinybars).
        new_pending_airdrops: Newly created pending airdrop records from this transaction.
        prng_number: 32-bit pseudo-random number (if PRNG service was used).
        prng_bytes: Variable-length pseudo-random bytes (if PRNG service was used).
        consensus_timestamp: When the transaction reached consensus (network-assigned).
        parent_consensus_timestamp: For child transactions — parent's consensus time.
        schedule_ref: Schedule ID if this transaction was executed via Schedule.
        assessed_custom_fees: Custom fees assessed and deducted during this transaction.
        automatic_token_associations: Token associations automatically created.
        alias: EVM-style alias bytes (usually for account creation via ECDSA key).
        ethereum_hash: 32-byte hash used in Ethereum-compatible transaction format.
        evm_address: 20-byte EVM-compatible address (if created or referenced).
        paid_staking_rewards: List of (account, amount) staking reward payments made.
        duplicates: Other transaction records considered duplicates (when queried with include_duplicates).
    """
    transaction_id: Optional[TransactionId] = None
    transaction_hash: Optional[bytes] = None
    transaction_memo: Optional[str] = None
    transaction_fee: Optional[int] = None
    receipt: Optional[TransactionReceipt] = None
    call_result: Optional[ContractFunctionResult] = None
    token_transfers: defaultdict[TokenId, defaultdict[AccountId, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    nft_transfers: defaultdict[TokenId, list[TokenNftTransfer]] = field(default_factory=lambda: defaultdict(list))
    transfers: defaultdict[AccountId, int] = field(default_factory=lambda: defaultdict(int))
    new_pending_airdrops: list[PendingAirdropRecord] = field(default_factory=list)
    prng_number: Optional[int] = None
    prng_bytes: Optional[bytes] = None
    consensus_timestamp: Optional[Timestamp] = None
    parent_consensus_timestamp: Optional[Timestamp] = None
    schedule_ref: Optional[ScheduleId] = None
    assessed_custom_fees: list[AssessedCustomFee] = field(default_factory=list)
    automatic_token_associations: list[TokenAssociation] = field(default_factory=list)
    alias: Optional[bytes] = None
    ethereum_hash: Optional[bytes] = None
    evm_address: Optional[bytes] = None
    paid_staking_rewards: defaultdict[AccountId, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    contract_create_result: Optional[ContractFunctionResult] = None
    duplicates: list['TransactionRecord'] = field(default_factory=list)

    def __repr__(self) -> str:
        """Returns a human-readable string representation of the TransactionRecord."""
        status = None
        if self.receipt:
            try:
                from hiero_sdk_python.response_code import ResponseCode
                status = ResponseCode(self.receipt.status).name
            except (ValueError, AttributeError):
                status = self.receipt.status

        parts = [
            f"transaction_id='{self.transaction_id}'",
            f"transaction_hash={self.transaction_hash!r}",
            f"transaction_memo={self.transaction_memo!r}",
            f"transaction_fee={self.transaction_fee}",
            f"receipt_status='{status}'",
        ]

        # Core transfers (full dict repr - usually small)
        parts.append(f"transfers={dict(self.transfers)}")
        parts.append(f"token_transfers={dict(self.token_transfers)}")
        parts.append(f"nft_transfers={ {k: len(v) for k, v in self.nft_transfers.items()} }")  # count for NFTs is fine

        parts.append(f"new_pending_airdrops={self.new_pending_airdrops!r}")

        # Contract & PRNG
        parts.append(f"call_result={self.call_result}")
        parts.append(f"contract_create_result={self.contract_create_result}")
        parts.append(f"prng_number={self.prng_number}")
        parts.append(f"prng_bytes={self.prng_bytes!r}")

        # Timestamps & schedule
        parts.append(f"consensus_timestamp={self.consensus_timestamp}")
        parts.append(f"parent_consensus_timestamp={self.parent_consensus_timestamp}")
        parts.append(f"schedule_ref={self.schedule_ref}")

        # Complex repeated fields with preview
        if self.assessed_custom_fees:
            preview = ", ".join(str(f) for f in self.assessed_custom_fees[:2])
            extra = f", ... ({len(self.assessed_custom_fees)-2} more)" if len(self.assessed_custom_fees) > 2 else ""
            parts.append(f"assessed_custom_fees=[{preview}{extra}]")
        else:
            parts.append("assessed_custom_fees=[]")

        if self.automatic_token_associations:
            preview = ", ".join(str(a) for a in self.automatic_token_associations[:2])
            extra = f", ... ({len(self.automatic_token_associations)-2} more)" if len(self.automatic_token_associations) > 2 else ""
            parts.append(f"automatic_token_associations=[{preview}{extra}]")
        else:
            parts.append("automatic_token_associations=[]")

        if self.paid_staking_rewards:
            preview = ", ".join(f"({a}, {amt})" for a, amt in self.paid_staking_rewards[:2])
            extra = f", ... ({len(self.paid_staking_rewards)-2} more)" if len(self.paid_staking_rewards) > 2 else ""
            parts.append(f"paid_staking_rewards=[{preview}{extra}]")
        else:
            parts.append("paid_staking_rewards=[]")

        parts.append(f"alias={self.alias!r}")
        parts.append(f"ethereum_hash={self.ethereum_hash!r}")
        parts.append(f"evm_address={self.evm_address!r}")
        parts.append(f"duplicates_count={len(self.duplicates)}")

        return f"TransactionRecord({', '.join(parts)})"
        
    @classmethod
    def _from_proto(
        cls,
        proto: transaction_record_pb2.TransactionRecord,
        transaction_id: Optional[TransactionId] = None,
        duplicates: Optional[list['TransactionRecord']] = None,
    ) -> 'TransactionRecord':
        """Creates a TransactionRecord instance from a protobuf transaction record.

        This method performs complex data aggregation from the protobuf message,
        including:
        - Basic transaction metadata (hash, memo, fees)
        - Token transfers (both fungible and non-fungible)
        - Account balance transfers
        - Contract execution results
        - Airdrop records
        - PRNG (pseudo-random number generation) results
        The method maps all nested transfer data from the raw protobuf message into
        the structured format used by the TransactionRecord class & organizing them

        into appropriate defaultdict collections for efficient access.

        Args:
            proto: The raw protobuf transaction record containing all transaction data.
            transaction_id: The transaction ID to associate with this record (required).
            duplicates: Optional list of duplicate transaction records to attach.
                        Defaults to an empty list.

        Returns:
            TransactionRecord: A new instance containing all processed and structured data.
        """
        tx_id = cls._resolve_transaction_id(proto, transaction_id)
        duplicates = duplicates or []

        token_transfers, nft_transfers = cls._parse_token_transfers(proto)
        transfers = cls._parse_hbar_transfers(proto)
        new_pending_airdrops = cls._parse_pending_airdrops(proto)
        call_result = cls._parse_contract_call_result(proto)

        consensus_timestamp = (
            Timestamp._from_protobuf(proto.consensusTimestamp)
            if proto.HasField("consensusTimestamp")
            else None
        )

        parent_consensus_timestamp = (
            Timestamp._from_protobuf(proto.parent_consensus_timestamp)
            if proto.HasField("parent_consensus_timestamp")
            else None
        )

        schedule_ref = (
            ScheduleId._from_proto(proto.scheduleRef)
            if proto.HasField("scheduleRef")
            else None
        )

        assessed_custom_fees = [
            AssessedCustomFee._from_proto(fee)
            for fee in proto.assessed_custom_fees
        ]

        automatic_token_associations = [
            TokenAssociation._from_proto(assoc)
            for assoc in proto.automatic_token_associations
        ]

        alias = proto.alias or None
        ethereum_hash = proto.ethereum_hash or None
        evm_address = proto.evm_address or None
        
        paid_staking_rewards = [
            (
                AccountId._from_proto(r.accountID),
                r.amount
            )
            for r in proto.paid_staking_rewards
        ]

        contract_create_result = (
            ContractFunctionResult._from_proto(proto.contractCreateResult)
            if proto.HasField("contractCreateResult")
            else None
        )

        return cls(
            transaction_id=tx_id,
            transaction_hash=proto.transactionHash,
            transaction_memo=proto.memo,
            transaction_fee=proto.transactionFee,
            receipt=TransactionReceipt._from_proto(proto.receipt, tx_id),
            token_transfers=token_transfers,
            nft_transfers=nft_transfers,
            transfers=transfers,
            new_pending_airdrops=new_pending_airdrops,
            call_result=call_result,
            prng_number=proto.prng_number,
            prng_bytes=proto.prng_bytes,

            consensus_timestamp=consensus_timestamp,
            parent_consensus_timestamp=parent_consensus_timestamp,
            schedule_ref=schedule_ref,
            assessed_custom_fees=assessed_custom_fees,
            automatic_token_associations=automatic_token_associations,
            alias=alias,
            ethereum_hash=ethereum_hash,
            evm_address=evm_address,
            paid_staking_rewards=paid_staking_rewards,
            contract_create_result=contract_create_result,
            
            duplicates=duplicates,
        )

    @staticmethod
    def _resolve_transaction_id(
        proto: transaction_record_pb2.TransactionRecord,
        transaction_id: Optional[TransactionId],
    ) -> TransactionId:
        """Resolves the transaction ID from proto or raises error if not available."""
        if proto.HasField("transactionID"):
            return TransactionId._from_proto(proto.transactionID)
    
        if transaction_id is not None:
            return transaction_id
    
        raise ValueError("transaction_id is required when proto.transactionID is not present")

    @staticmethod
    def _parse_token_transfers(
        proto: transaction_record_pb2.TransactionRecord,
    ) -> tuple[dict, dict]:
        """Parses fungible and non-fungible token transfers from proto."""
        token_transfers = defaultdict(lambda: defaultdict(int))
        nft_transfers = defaultdict(list)

        for ttl in proto.tokenTransferLists:
            token_id = TokenId._from_proto(ttl.token)

            # Fungible token transfers
            for transfer in ttl.transfers:
                account_id = AccountId._from_proto(transfer.accountID)
                token_transfers[token_id][account_id] = transfer.amount

            # Non-fungible (NFT) transfers
            nft_transfers[token_id].extend(
                TokenNftTransfer._from_proto(ttl)
            )

        return token_transfers, nft_transfers

    @staticmethod
    def _parse_hbar_transfers(
        proto: transaction_record_pb2.TransactionRecord,
    ) -> dict:
        """Parses HBAR transfers from proto."""
        transfers = defaultdict(int)
        for transfer in proto.transferList.accountAmounts:
            account_id = AccountId._from_proto(transfer.accountID)
            transfers[account_id] += transfer.amount
        return transfers

    @staticmethod
    def _parse_pending_airdrops(
        proto: transaction_record_pb2.TransactionRecord,
    ) -> list:
        """Parses pending airdrop records from proto."""
        return [
            PendingAirdropRecord._from_proto(pending)
            for pending in proto.new_pending_airdrops
        ]

    @staticmethod
    def _parse_contract_call_result(
        proto: transaction_record_pb2.TransactionRecord,
    ) -> Optional[ContractFunctionResult]:
        """Parses contract call result from proto if present."""
        if proto.HasField("contractCallResult"):
            return ContractFunctionResult._from_proto(proto.contractCallResult)
        return None

    def _to_proto(self) -> transaction_record_pb2.TransactionRecord:
        """Converts the TransactionRecord instance to its protobuf representation.

        Note: The 'duplicates' field is intentionally **not** serialized.
        Duplicate records are only present in query responses and are never
        included when sending TransactionRecord messages to the network.
        
        This method serializes all components of the transaction record into a protobuf message,
        including:
        - Basic transaction metadata (hash, memo, fees)
        - Token transfers (both fungible and non-fungible)
        - Account balance transfers
        - Contract execution results
        - Airdrop records
        - PRNG (pseudo-random number generation) results

        The method performs a deep conversion of all nested objects (token transfers,
        NFT transfers, account transfers, and pending airdrops) to their respective
        protobuf representations.

        Returns:
            transaction_record_pb2.TransactionRecord: A protobuf message containing
            all the transaction record data in a format suitable for network transmission
            or storage.
        """
        # Defensive guard for protobuf oneof
        if self.call_result is not None and self.contract_create_result is not None:
            raise ValueError(
                "call_result and contract_create_result are mutually exclusive "
                "(protobuf oneof) — only one may be set at a time"
            )

        record_proto = transaction_record_pb2.TransactionRecord(
            transactionHash=self.transaction_hash,
            memo=self.transaction_memo,
            transactionFee=self.transaction_fee,
            receipt=self.receipt._to_proto() if self.receipt else None,
            contractCallResult=(
                self.call_result._to_proto() if self.call_result else None
            ),
            prng_number=self.prng_number,
            prng_bytes=self.prng_bytes,
        )
        
        if self.contract_create_result is not None:
            record_proto.contractCreateResult.CopyFrom(self.contract_create_result._to_proto())
        
        if self.transaction_id is not None:
            record_proto.transactionID.CopyFrom(self.transaction_id._to_proto())

        for token_id, account_transfers in self.token_transfers.items():
            token_transfer_list = record_proto.tokenTransferLists.add()
            token_transfer_list.token.CopyFrom(token_id._to_proto())
            for account_id, amount in account_transfers.items():
                transfer = token_transfer_list.transfers.add()
                transfer.accountID.CopyFrom(account_id._to_proto())
                transfer.amount = amount

        for token_id, nft_transfers in self.nft_transfers.items():
            token_transfer_list = record_proto.tokenTransferLists.add()
            token_transfer_list.token.CopyFrom(token_id._to_proto())
            for nft_transfer in nft_transfers:
                token_transfer_list.nftTransfers.append(nft_transfer._to_proto())

        for account_id, amount in self.transfers.items():
            transfer = record_proto.transferList.accountAmounts.add()
            transfer.accountID.CopyFrom(account_id._to_proto())
            transfer.amount = amount

        for pending_airdrop in self.new_pending_airdrops:
            record_proto.new_pending_airdrops.add().CopyFrom(pending_airdrop._to_proto())
        
        if self.consensus_timestamp is not None:
            record_proto.consensusTimestamp.CopyFrom(self.consensus_timestamp._to_protobuf())

        if self.parent_consensus_timestamp is not None:
            record_proto.parent_consensus_timestamp.CopyFrom(self.parent_consensus_timestamp._to_protobuf())

        if self.schedule_ref is not None:
            record_proto.scheduleRef.CopyFrom(self.schedule_ref._to_proto())

        if self.assessed_custom_fees:
            record_proto.assessed_custom_fees.extend(
                fee._to_proto() for fee in self.assessed_custom_fees
            )

        if self.automatic_token_associations:
            for assoc in self.automatic_token_associations:
                record_proto.automatic_token_associations.append(assoc._to_proto())

        if self.alias is not None:
            record_proto.alias = self.alias

        if self.ethereum_hash is not None:
            record_proto.ethereum_hash = self.ethereum_hash

        if self.evm_address is not None:
            record_proto.evm_address = self.evm_address

        for account_id, amount in self.paid_staking_rewards:
            r = record_proto.paid_staking_rewards.add()
            r.accountID.CopyFrom(account_id._to_proto())
            r.amount = amount

        return record_proto
    