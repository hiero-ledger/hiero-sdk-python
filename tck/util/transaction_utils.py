"""Shared utility for executing transactions and validating their receipts."""

from __future__ import annotations

from hiero_sdk_python import Client, Transaction, TransactionReceipt


def execute_validated(transaction: Transaction, client: Client) -> TransactionReceipt:
    """Execute a transaction and return its receipt, validated as SUCCESS.

    The returned receipt always has SUCCESS status. Any other status raises
    ReceiptStatusError, which the handle_sdk_errors decorator maps to a
    JSON-RPC -32001 error.
    """
    response = transaction.execute(client, wait_for_receipt=False)
    return response.get_receipt(client, validate_status=True)
