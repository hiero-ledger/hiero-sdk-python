"""
PrngTransaction class.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.util_prng_pb2 import UtilPrngTransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


class PrngTransaction(Transaction):
    """
    A transaction that requests a pseudo-random number.

    This transaction can be used to request a pseudo-random number.
    You can specify the range of the pseudo-random number.
    
    If no range is specified, the transaction will return
    a 48 byte unsigned pseudo-random number.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a prng transaction.
    """

    def __init__(self, range: Optional[int] = None):
        """
        Initializes a new PrngTransaction instance.

        Args:
            range (Optional[int]): The range of the pseudo-random number.
        """
        super().__init__()
        self.range: Optional[int] = range

    def set_range(self, range: Optional[int]) -> "PrngTransaction":
        """
        Sets the range for the transaction.

        Args:
            range (Optional[int]): The range of the pseudo-random number.
        """
        self._require_not_frozen()
        self.range = range
        return self

    def _build_proto_body(self):
        """
        Builds the protobuf body for the prng transaction.

        Returns:
            UtilPrngTransactionBody: The protobuf body for the prng transaction.
        
        Raises:
            ValueError: If the range is negative.
        """
        if self.range is not None and self.range < 0:
            raise ValueError("Range can't be negative.")
            
        return UtilPrngTransactionBody(range=self.range)

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for prng transaction.

        Returns:
            TransactionBody: The protobuf transaction body containing the
                prng details.
        
        Raises:
            ValueError: If the range is negative.
        """
        prng_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.util_prng.CopyFrom(prng_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the prng transaction.

        Implements the abstract method from Transaction to provide the specific
        gRPC method for executing a prng transaction.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the transaction function
        """
        return _Method(transaction_func=channel.util.prng, query_func=None)
