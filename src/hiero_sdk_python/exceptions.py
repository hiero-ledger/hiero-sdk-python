from __future__ import annotations

from typing import TYPE_CHECKING

from hiero_sdk_python.response_code import ResponseCode


if TYPE_CHECKING:
    from hiero_sdk_python import TransactionId, TransactionReceipt
    from hiero_sdk_python.hbar import Hbar


class PrecheckError(Exception):
    """
    Exception thrown when a transaction fails its precheck validation.

    This occurs before the transaction reaches consensus.

    Attributes:
        status (ResponseCode): The precheck status code.
        transaction_id (TransactionId): The ID of the transaction that failed.
        message (str): The message of the error. If not provided, a default message is generated.
    """

    def __init__(
        self,
        status: ResponseCode | int,
        transaction_id: TransactionId | None = None,
        message: str | None = None,
    ) -> None:
        self.status = ResponseCode(status)
        self.transaction_id = transaction_id

        # Build a default message if none provided
        if message is None:
            status_name = self.status.name
            message = f"Transaction failed precheck with status: {status_name} ({int(self.status)})"
            if transaction_id:
                message += f", transaction ID: {transaction_id}"

        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"PrecheckError(status={self.status}, transaction_id={self.transaction_id})"


class MaxAttemptsError(Exception):
    """
    Exception raised when the maximum number of attempts for a request has been reached.

    Attributes:
        message (str): The error message explaining why the maximum attempts were reached
        node_id (str): The ID of the node that was being contacted when the max attempts were reached
        last_error (BaseException): The last error that occurred during the final attempt
    """

    def __init__(self, message: str, node_id: str, last_error: BaseException | None = None) -> None:
        self.node_id = node_id
        self.last_error = last_error

        # Build a comprehensive error message
        error_message = message
        if last_error is not None:
            error_message += f"; last error: {str(last_error)}"

        self.message = error_message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"MaxAttemptsError(message='{self.message}', node_id='{self.node_id}')"


class ReceiptStatusError(Exception):
    """
    Exception raised when a transaction receipt contains an error status.

    Attributes:
        status (ResponseCode): The error status code from the receipt
        transaction_id (TransactionId): The ID of the transaction that failed (Optional)
        transaction_receipt (TransactionReceipt): The receipt containing the error status
        message (str): The error message describing the failure
    """

    def __init__(
        self,
        status: ResponseCode | int,
        transaction_id: TransactionId | None,
        transaction_receipt: TransactionReceipt,
        message: str | None = None,
    ) -> None:
        self.status = ResponseCode(status)
        self.transaction_id = transaction_id
        self.transaction_receipt = transaction_receipt

        # Build a default message if none provided
        if message is None:
            status_name = self.status.name
            if transaction_id:
                message = f"Receipt for transaction {transaction_id} contained error status: {status_name} ({int(self.status)})"
            else:
                message = f"Receipt contained error status: {status_name} ({int(self.status)})"

        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"ReceiptStatusError(status={self.status}, transaction_id={self.transaction_id})"


class MaxQueryPaymentExceededError(ValueError):
    """
    Exception raised when a query's actual network cost exceeds the configured maximum payment.

    This is raised during query execution when the SDK fetches the real cost from the
    network and finds it is higher than the allowed ceiling set by
    ``Query.set_max_query_payment()`` or ``Client.set_default_max_query_payment()``.

    Because this inherits from ``ValueError``, existing code that catches ``ValueError``
    continues to work without modification.

    Attributes:
        query_cost (Hbar): The actual cost the network quoted for the query.
        max_query_payment (Hbar): The maximum the caller was willing to pay.
        message (str): Human-readable description of the violation.

    Example::

        from hiero_sdk_python import MaxQueryPaymentExceededError

        try:
            result = query.execute(client)
        except MaxQueryPaymentExceededError as e:
            print(f"Query costs {e.query_cost} but limit is {e.max_query_payment}")
    """

    def __init__(self, query_cost: Hbar, max_query_payment: Hbar) -> None:
        self.query_cost = query_cost
        self.max_query_payment = max_query_payment
        message = (
            f"Query cost {query_cost.to_hbars():.8f} ℏ "
            f"exceeds the maximum query payment of {max_query_payment.to_hbars():.8f} ℏ"
        )
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return (
            f"MaxQueryPaymentExceededError("
            f"query_cost={self.query_cost!r}, "
            f"max_query_payment={self.max_query_payment!r})"
        )
