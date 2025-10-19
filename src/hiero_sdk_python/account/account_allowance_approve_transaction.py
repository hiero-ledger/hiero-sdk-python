"""
AccountAllowanceApproveTransaction class for approving account allowances.
"""

from typing import List, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    CryptoApproveAllowanceTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.hbar_allowance import HbarAllowance
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_allowance import TokenAllowance
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_allowance import TokenNftAllowance
from hiero_sdk_python.transaction.transaction import Transaction

DEFAULT_TRANSACTION_FEE = Hbar(1).to_tinybars()


class AccountAllowanceApproveTransaction(Transaction):
    """
    Represents an account allowance approve transaction on the network.

    This transaction creates one or more HBAR/token approved allowances relative to the owner
    account specified in the allowances of the transaction. Each allowance grants a spender
    the right to transfer a pre-determined amount of the owner's HBAR/token to any other
    account of the spender's choice.

    If the owner is not specified in any allowance, the payer of the transaction is considered
    to be the owner for that particular allowance. Setting the amount to zero in HbarAllowance
    or TokenAllowance will remove the respective allowance for the spender.

    NOTE:
    - If account 0.0.X pays for this transaction and owner is not specified in the allowance,
      then at consensus each spender account will have new allowances to spend HBAR or tokens from 0.0.X.
    """

    def __init__(
        self,
        hbar_allowances: Optional[List[HbarAllowance]] = None,
        token_allowances: Optional[List[TokenAllowance]] = None,
        nft_allowances: Optional[List[TokenNftAllowance]] = None,
    ) -> None:
        """
        Initializes a new AccountAllowanceApproveTransaction instance.

        Args:
            hbar_allowances (Optional[List[HbarAllowance]]): Initial HBAR allowances.
            token_allowances (Optional[List[TokenAllowance]]): Initial token allowances.
            nft_allowances (Optional[List[TokenNftAllowance]]): Initial NFT allowances.
        """
        super().__init__()
        self.hbar_allowances: List[HbarAllowance] = (
            list(hbar_allowances) if hbar_allowances is not None else []
        )
        self.token_allowances: List[TokenAllowance] = (
            list(token_allowances) if token_allowances is not None else []
        )
        self.nft_allowances: List[TokenNftAllowance] = (
            list(nft_allowances) if nft_allowances is not None else []
        )
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def approve_hbar_allowance(
        self,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
        amount: Hbar,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Approves allowance of HBAR transfers for a spender.

        Args:
            owner_account_id (AccountId): The account that owns the HBAR.
            spender_account_id (AccountId): The account permitted to transfer the HBAR.
            amount (Hbar): The amount of HBAR allowed for transfer.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.hbar_allowances.append(
            HbarAllowance(
                owner_account_id=owner_account_id,
                spender_account_id=spender_account_id,
                amount=amount.to_tinybars() if amount is not None else 0,
            )
        )
        return self

    def approve_token_allowance(
        self,
        token_id: TokenId,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
        amount: int,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Approves allowance of fungible token transfers for a spender.

        Args:
            token_id (TokenId): The ID of the fungible token.
            owner_account_id (AccountId): The account that owns the tokens.
            spender_account_id (AccountId): The account permitted to transfer the tokens.
            amount (int): The amount of tokens allowed for transfer.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.token_allowances.append(
            TokenAllowance(
                token_id=token_id,
                owner_account_id=owner_account_id,
                spender_account_id=spender_account_id,
                amount=amount if amount is not None else 0,
            )
        )
        return self

    def _approve_token_nft_approval(
        self,
        nft_id: NftId,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
        delegating_spender: AccountId,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Internal method to approve allowance of non-fungible token transfers for a spender.

        Args:
            nft_id (NftId): The ID of the NFT.
            owner_account_id (AccountId): The account that owns the NFT.
            spender_account_id (AccountId): The account permitted to transfer the NFT.
            delegating_spender (AccountId): The account that can delegate the NFT transfer.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        self._require_not_frozen()

        # Check if there's already an allowance for this token and spender
        for allowance in self.nft_allowances:
            if (
                allowance.token_id == nft_id.token_id
                and allowance.spender_account_id == spender_account_id
            ):
                # Add the serial number if it's not already present
                if nft_id.serial_number not in allowance.serial_numbers:
                    allowance.serial_numbers.append(nft_id.serial_number)
                return self

        # Create a new allowance
        self.nft_allowances.append(
            TokenNftAllowance(
                token_id=nft_id.token_id,
                owner_account_id=owner_account_id,
                spender_account_id=spender_account_id,
                serial_numbers=[nft_id.serial_number],
                approved_for_all=False,
                delegating_spender=delegating_spender,
            )
        )
        return self

    def approve_token_nft_allowance(
        self,
        nft_id: NftId,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Approves allowance of non-fungible token transfers for a spender.

        Args:
            nft_id (NftId): The ID of the NFT.
            owner_account_id (AccountId): The account that owns the NFT.
            spender_account_id (AccountId): The account permitted to transfer the NFT.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        return self._approve_token_nft_approval(nft_id, owner_account_id, spender_account_id, None)

    def approve_token_nft_allowance_with_delegating_spender(
        self,
        nft_id: NftId,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
        delegating_spender: AccountId,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Approves allowance of non-fungible token transfers for a spender.

        Args:
            nft_id (NftId): The ID of the NFT.
            owner_account_id (AccountId): The account that owns the NFT.
            spender_account_id (AccountId): The account permitted to transfer the NFT.
            delegating_spender (AccountId): The account that can delegate the NFT transfer.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        return self._approve_token_nft_approval(
            nft_id, owner_account_id, spender_account_id, delegating_spender
        )

    def _approve_token_nft_allowance_all_serials(
        self,
        token_id: TokenId,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Internal method to approve allowance of non-fungible token transfers for a spender.

        Args:
            token_id (TokenId): The ID of the NFT token type.
            owner_account_id (AccountId): The account that owns the NFTs.
            spender_account_id (AccountId): The account permitted to transfer the NFTs.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        self._require_not_frozen()

        # Check if there's already an allowance for this token and spender
        for allowance in self.nft_allowances:
            if (
                allowance.token_id == token_id
                and allowance.spender_account_id == spender_account_id
            ):
                allowance.serial_numbers = []
                allowance.approved_for_all = True
                return self

        # Create a new allowance
        self.nft_allowances.append(
            TokenNftAllowance(
                token_id=token_id,
                owner_account_id=owner_account_id,
                spender_account_id=spender_account_id,
                serial_numbers=[],
                approved_for_all=True,
            )
        )
        return self

    def approve_token_nft_allowance_all_serials(
        self,
        token_id: TokenId,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Approves allowance of non-fungible token transfers for a spender.
        Spender has access to all of the owner's NFT units of type tokenId (currently
        owned and any in the future).

        Args:
            token_id (TokenId): The ID of the NFT token type.
            owner_account_id (AccountId): The account that owns the NFTs.
            spender_account_id (AccountId): The account permitted to transfer the NFTs.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        return self._approve_token_nft_allowance_all_serials(
            token_id, owner_account_id, spender_account_id
        )

    def delete_token_nft_allowance_all_serials(
        self,
        token_id: TokenId,
        owner_account_id: AccountId,
        spender_account_id: AccountId,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Revokes an allowance that permits a spender to transfer all of the owner's
        non-fungible tokens (NFTs) of a specific type (tokenId).
        This action applies to both the NFTs currently owned by the owner and any
        future NFTs of the same type.

        Args:
            token_id (TokenId): The ID of the NFT token type.
            owner_account_id (AccountId): The account that owns the NFTs.
            spender_account_id (AccountId): The account to revoke the allowance from.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        self._require_not_frozen()

        for allowance in self.nft_allowances:
            if (
                allowance.token_id == token_id
                and allowance.spender_account_id == spender_account_id
            ):
                allowance.serial_numbers = []
                allowance.approved_for_all = True
                return self

        self.nft_allowances.append(
            TokenNftAllowance(
                token_id=token_id,
                owner_account_id=owner_account_id,
                spender_account_id=spender_account_id,
                serial_numbers=[],
                approved_for_all=False,
            )
        )
        return self

    def add_all_token_nft_approval(
        self,
        token_id: TokenId,
        spender_account_id: AccountId,
    ) -> "AccountAllowanceApproveTransaction":
        """
        Approve allowance of non-fungible token transfers for a spender.
        Spender has access to all of the owner's NFT units of type tokenId (currently
        owned and any in the future).

        Args:
            token_id (TokenId): The ID of the NFT token type.
            spender_account_id (AccountId): The account to grant the allowance to.

        Returns:
            AccountAllowanceApproveTransaction: This transaction instance.
        """
        return self._approve_token_nft_allowance_all_serials(
            token_id=token_id,
            owner_account_id=None,
            spender_account_id=spender_account_id,
        )

    def _build_proto_body(self) -> CryptoApproveAllowanceTransactionBody:
        """
        Builds the protobuf body for the account allowance approve transaction.

        Returns:
            CryptoApproveAllowanceTransactionBody: The protobuf body for this transaction.
        """
        body = CryptoApproveAllowanceTransactionBody(
            cryptoAllowances=[allowance._to_proto() for allowance in self.hbar_allowances],
            tokenAllowances=[allowance._to_proto() for allowance in self.token_allowances],
            nftAllowances=[allowance._to_proto() for allowance in self.nft_allowances],
        )

        return body

    def build_transaction_body(self):
        """
        Builds the transaction body for this account allowance approve transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        crypto_approve_allowance_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.cryptoApproveAllowance.CopyFrom(crypto_approve_allowance_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this account allowance approve transaction.

        Returns:
            SchedulableTransactionBody: The scheduled transaction body.
        """
        crypto_approve_allowance_body = self._build_proto_body()
        scheduled_body = SchedulableTransactionBody()
        scheduled_body.cryptoApproveAllowance.CopyFrom(crypto_approve_allowance_body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the account allowance approve transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to approve allowances.
        """
        return _Method(transaction_func=channel.crypto.approveAllowances, query_func=None)
