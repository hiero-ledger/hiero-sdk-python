from __future__ import annotations

from typing import TYPE_CHECKING

from hiero_sdk_python.response_code import ResponseCode


if TYPE_CHECKING:
    from hiero_sdk_python import TransactionId, TransactionReceipt


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

    def __init__(self, message: str, node_id: str | None = None, last_error: BaseException | None = None) -> None:
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
        return f"MaxAttemptsError(message='{self.message}', node_id={self.node_id!r})"


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


class MirrorNodeError(RuntimeError):
    """
    Exception raised when the mirror node REST API answers with an error status.

    The mirror node puts the reason for a failure in ``_status.messages[]``.
    For a contract call that reverts, this is the only place the revert
    reason appears, so the messages are kept on the exception and included
    in its text.

    Attributes:
        status_code (int): The HTTP status code returned by the mirror node.
        messages (list[str]): The ``_status.messages[]`` entries, each formatted as
            ``"<message>: <detail>"`` (or just ``"<message>"`` when there is no detail).
        data (list[str]): The ``data`` field of each ``_status.messages[]`` entry that
            has one, for example the ABI-encoded revert reason.
        message (str): The full error message.
    """

    def __init__(
        self,
        status_code: int,
        messages: list[str] | None = None,
        data: list[str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.messages = list(messages or [])
        self.data = list(data or [])

        message = f"Mirror node returned HTTP {status_code}"
        if self.messages:
            message += ": " + "; ".join(self.messages)

        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"MirrorNodeError(status_code={self.status_code}, messages={self.messages!r})"
