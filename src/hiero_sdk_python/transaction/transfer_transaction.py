from collections import defaultdict
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import crypto_transfer_pb2, basic_types_pb2
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TransferTransaction(Transaction):
    """
    Represents a transaction to transfer HBAR or tokens between accounts.
    """

    def __init__(self, hbar_transfers=None, token_transfers=None):
        """
        Initializes a new TransferTransaction instance.

        Args:
            hbar_transfers (dict[AccountId, int], optional): Initial HBAR transfers.
            token_transfers (dict[TokenId, dict[AccountId, int]], optional): Initial token transfers.
        """
        super().__init__()
        self.hbar_transfers = defaultdict(int)
        self.token_transfers = defaultdict(lambda: defaultdict(int))
        self._default_transaction_fee = 100_000_000

        if hbar_transfers:
            for account_id, amount in hbar_transfers.items():
                self.add_hbar_transfer(account_id, amount)

        if token_transfers:
            for token_id, account_transfers in token_transfers.items():
                for account_id, amount in account_transfers.items():
                    self.add_token_transfer(token_id, account_id, amount)

    def add_hbar_transfer(self, account_id: AccountId, amount: int) -> "TransferTransaction":
        """
        Adds a HBAR transfer to the transaction.
        """
        self._require_not_frozen()
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if not isinstance(amount, int) or amount == 0:
            raise ValueError("Amount must be a non-zero integer.")

        self.hbar_transfers[account_id] += amount
        return self

    def add_token_transfer(self, token_id: TokenId, account_id: AccountId, amount: int) -> "TransferTransaction":
        """
        Adds a token transfer to the transaction.
        """
        self._require_not_frozen()
        if not isinstance(token_id, TokenId):
            raise TypeError("token_id must be a TokenId instance.")
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId instance.")
        if not isinstance(amount, int) or amount == 0:
            raise ValueError("Amount must be a non-zero integer.")

        self.token_transfers[token_id][account_id] += amount
        return self

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for a transfer transaction.
        """
        crypto_transfer_tx_body = crypto_transfer_pb2.CryptoTransferTransactionBody()

        # HBAR
        if self.hbar_transfers:
            transfer_list = basic_types_pb2.TransferList()
            for account_id, amount in self.hbar_transfers.items():
                transfer_list.accountAmounts.append(
                    basic_types_pb2.AccountAmount(
                        accountID=account_id.to_proto(),
                        amount=amount,
                    )
                )
            crypto_transfer_tx_body.transfers.CopyFrom(transfer_list)

        # Tokens
        for token_id, transfers in self.token_transfers.items():
            token_transfer_list = basic_types_pb2.TokenTransferList(
                token=token_id.to_proto()
            )
            for account_id, amount in transfers.items():
                token_transfer_list.transfers.append(
                    basic_types_pb2.AccountAmount(
                        accountID=account_id.to_proto(),
                        amount=amount,
                    )
                )
            crypto_transfer_tx_body.tokenTransfers.append(token_transfer_list)

        transaction_body = self.build_base_transaction_body()
        transaction_body.cryptoTransfer.CopyFrom(crypto_transfer_tx_body)

        return transaction_body

    def get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.crypto.cryptoTransfer,
            query_func=None
        )