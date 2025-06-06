from hiero_sdk_python.response_code import ResponseCode

class PrecheckError(Exception):
    """
    Exception thrown when a transaction fails its precheck validation.
    
    This occurs before the transaction reaches consensus.
    
    Attributes:
        status (ResponseCode): The precheck status code.
        transaction_id (TransactionId): The ID of the transaction that failed.
        message (str): The message of the error. If not provided, a default message is generated.
    """
    def __init__(self, status, transaction_id=None, message=None):
        self.status = status
        self.transaction_id = transaction_id
        
        # Build a default message if none provided
        if message is None:
            status_name = ResponseCode(status).name
            message = f"Transaction failed precheck with status: {status_name} ({status})"
            if transaction_id:
                message += f", transaction ID: {transaction_id}"
        
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
    
    def __repr__(self):
        return f"PrecheckError(status={self.status}, transaction_id={self.transaction_id})"
    
    
class MaxAttemptsError(Exception):
    """
    Exception raised when the maximum number of attempts for a request has been reached.
    
    Attributes:
        message (str): The error message explaining why the maximum attempts were reached
        node_id (str): The ID of the node that was being contacted when the max attempts were reached
        last_error (Exception): The last error that occurred during the final attempt
    """
    
    def __init__(self, message, node_id, last_error=None):
        self.node_id = node_id
        self.last_error = last_error
        
        # Build a comprehensive error message
        error_message = message
        if last_error is not None:
            error_message += f"; last error: {str(last_error)}"
            
        self.message = error_message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
    
    def __repr__(self):
        return f"MaxAttemptsError(message='{self.message}', node_id='{self.node_id}')"
    
class ReceiptStatusError(Exception):
    """
    Exception raised when a transaction receipt contains an error status.
    
    Attributes:
        status (ResponseCode): The error status code from the receipt
        transaction_id (TransactionId): The ID of the transaction that failed
        transaction_receipt (TransactionReceipt): The receipt containing the error status
        message (str): The error message describing the failure
    """
    
    def __init__(self, status, transaction_id, transaction_receipt, message=None):
        self.status = status
        self.transaction_id = transaction_id
        self.transaction_receipt = transaction_receipt
        
        # Build a default message if none provided
        if message is None:
            status_name = ResponseCode(status).name
            message = f"Receipt for transaction {transaction_id} contained error status: {status_name} ({status})"
            
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
    
    def __repr__(self):
        return f"ReceiptStatusError(status={self.status}, transaction_id={self.transaction_id})"
