"""SignableNodeTransactionBodyBytes class."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.transaction.transaction_id import TransactionId


@dataclass(frozen=True)
class SignableNodeTransactionBodyBytes:
    """
    The exact body bytes a node expects to be signed, for one transaction ID and one node.

    A frozen transaction holds one body per transaction ID (chunk) and node. Signing
    signable_transaction_body_bytes externally, e.g. in an HSM, yields a signature
    that is valid for that node only.

    Attributes:
        node_account_id (AccountId): The node the body is addressed to.
        transaction_id (TransactionId): The transaction ID in the body.
        signable_transaction_body_bytes (bytes): The serialized TransactionBody to sign.
    """

    node_account_id: AccountId
    transaction_id: TransactionId
    signable_transaction_body_bytes: bytes
