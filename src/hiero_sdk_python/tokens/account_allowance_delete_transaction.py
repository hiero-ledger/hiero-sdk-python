"""
AccountAllowanceDeleteTransaction class for deleting account allowances.
"""

from typing import List, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.crypto_delete_allowance_pb2 import (
    CryptoDeleteAllowanceTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_nft_allowance import TokenNftAllowance
from hiero_sdk_python.transaction.transaction import Transaction

DEFAULT_TRANSACTION_FEE = Hbar(1).to_tinybars()


class AccountAllowanceDeleteTransaction(Transaction):
    """
    Represents an account allowance delete transaction on the network.

    This transaction deletes one or more non-fungible approved allowances from an owner's account.
    This operation will remove the allowances granted to one or more specific non-fungible token
    serial numbers. Each owner account listed as wiping an allowance must sign the transaction.

    HBAR and fungible token allowances can be removed by setting the amount to zero in
    AccountAllowanceApproveTransaction.
    """

    def __init__(
        self,
        nft_wipe: Optional[List[TokenNftAllowance]] = None,
    ) -> None:
        """
        Initializes a new AccountAllowanceDeleteTransaction instance.

        Args:
            nft_wipe (Optional[List[TokenNftAllowance]]): Initial NFT allowances to delete.
        """
        super().__init__()
        self.nft_wipe: List[TokenNftAllowance] = list(nft_wipe) if nft_wipe is not None else []
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def delete_all_token_nft_allowances(
        self,
        nft_id: NftId,
        owner_account_id: AccountId,
    ) -> "AccountAllowanceDeleteTransaction":
        """
        Deletes non-fungible token allowance/allowances to remove.

        Args:
            nft_id (NftId): The ID of the NFT to remove allowance for.
            owner_account_id (AccountId): The account that owns the NFT.

        Returns:
            AccountAllowanceDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()

        # Check if there's already a wipe entry for this token and owner
        for wipe_entry in self.nft_wipe:
            if (
                wipe_entry.token_id == nft_id.token_id
                and wipe_entry.owner_account_id == owner_account_id
            ):
                # Add the serial number if it's not already present
                if nft_id.serial_number not in wipe_entry.serial_numbers:
                    wipe_entry.serial_numbers.append(nft_id.serial_number)
                return self

        # Create a new wipe entry
        self.nft_wipe.append(
            TokenNftAllowance(
                token_id=nft_id.token_id,
                owner_account_id=owner_account_id,
                serial_numbers=[nft_id.serial_number],
                approved_for_all=False,
            )
        )
        return self

    def _build_proto_body(self) -> CryptoDeleteAllowanceTransactionBody:
        """
        Builds the protobuf body for the account allowance delete transaction.

        Returns:
            CryptoDeleteAllowanceTransactionBody: The protobuf body for this transaction.
        """
        body = CryptoDeleteAllowanceTransactionBody(
            nftAllowances=[allowance._to_wipe_proto() for allowance in self.nft_wipe],
        )

        return body

    def build_transaction_body(self):
        """
        Builds the transaction body for this account allowance delete transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        crypto_delete_allowance_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.cryptoDeleteAllowance.CopyFrom(crypto_delete_allowance_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this account allowance delete transaction.

        Returns:
            SchedulableTransactionBody: The scheduled transaction body.
        """
        crypto_delete_allowance_body = self._build_proto_body()
        scheduled_body = SchedulableTransactionBody()
        scheduled_body.cryptoDeleteAllowance.CopyFrom(crypto_delete_allowance_body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the account allowance delete transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to delete allowances.
        """
        return _Method(transaction_func=channel.crypto.deleteAllowances, query_func=None)
