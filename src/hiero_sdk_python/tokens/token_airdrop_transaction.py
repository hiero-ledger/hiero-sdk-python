from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.abstract_token_transfer_transaction import AbstractTokenTransferTransaction
from hiero_sdk_python.hapi.services import token_airdrop_pb2

class TokenAirdropTransaction(AbstractTokenTransferTransaction):
    """
    Represents a token airdrop transaction on the Hedera network.

    The TokenAirdropTransaction allows users to transfer tokens to multiple accounts,
    handling both fungible tokens and NFTs.
    """
    def __init__(self, token_transfers: list[TokenTransfer]=None, nft_transfers: list[TokenNftTransfer]=None):
        """
        Initializes a new TokenAirdropTransaction instance.

        Args:
            token_transfers (list[TokenTransfer], optional): Initial list of fungible token transfers.
            nft_transfers (list[TokenNftTransfer], optional): Initial list of NFT transfers.
        """
        super().__init__()
        if token_transfers:
            self.token_transfers = token_transfers
        if nft_transfers:
            self.nft_transfers = nft_transfers

    def add_token_transfer(self, token_id: TokenId, account_id: AccountId, amount: int) -> 'TokenAirdropTransaction':
        """
        Adds a tranfer to token_transfers list 
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.

        Returns:
            TokenAirdropTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self.token_transfers.append(TokenTransfer(token_id, account_id, amount))
        return self
    
    def add_token_transfer_with_decimals(self, token_id: TokenId, account_id: AccountId, amount: int, decimals: int) -> 'TokenAirdropTransaction':
        """
        Adds a tranfer with expected_decimals to token_transfers list
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.
            decimals (int): The number specifying the amount in the smallest denomination.

        Returns:
            TokenAirdropTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self.token_transfers.append(TokenTransfer(token_id, account_id, amount, expected_decimals=decimals))
        return self
    
    def add_approved_token_transfer(self, token_id: TokenId, account_id: AccountId, amount: int) -> 'TokenAirdropTransaction':
        """
        Adds a tranfer with approve allowance to token_transfers list 
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.

        Returns:
            TokenAirdropTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self.token_transfers.append(TokenTransfer(token_id, account_id, amount, is_approved=True))
        return self
    
    def add_approved_token_transfer_with_decimals(self, token_id: TokenId, account_id: AccountId, amount: int, decimals: int) -> 'TokenAirdropTransaction':
        """
        Adds a tranfer with expected_decimals and approve allowance to token_transfers list
        Args:
            token_id (TokenId): The ID of the token being transferred.
            account_id (AccountId): The accountId of sender/receiver.
            amount (int): The amount of the fungible token to transfer.
            decimals (int): The number specifying the amount in the smallest denomination.

        Returns:
            TokenAirdropTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self.token_transfers.append(TokenTransfer(token_id, account_id, amount, expected_decimals=decimals, is_approved=True))
        return self
        
    def add_nft_transfer(self, nft_id: NftId, sender: AccountId, receiver: AccountId):
        """
        Adds a transfer to the nft_transfers

        Args:
            nft_id (NftId): The ID of the NFT being transferred.
            sender (AccountId): The sender's account ID.
            receiver (AccountId): The receiver's account ID.

        Returns:
            TokenAirdropTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self.nft_transfers.append(TokenNftTransfer(nft_id.tokenId, sender, receiver, nft_id.serialNumber))
        return self
    
    def add_approved_nft_transfer(self, nft_id: NftId, sender: AccountId, receiver: AccountId):
        """
        Adds a transfer to the nft_transfers with approved allowance

        Args:
            nft_id (NftId): The ID of the NFT being transferred.
            sender (AccountId): The sender's account ID.
            receiver (AccountId): The receiver's account ID.

        Returns:
            TokenAirdropTransaction: The current instance of the transaction for chaining.
        """
        self._require_not_frozen()
        self.nft_transfers.append(TokenNftTransfer(nft_id.tokenId, sender, receiver, nft_id.serialNumber, True))
        return self
    
    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token airdrop.
        """
        token_transfer_list = self.build_token_transfer_list()
        token_airdrop_body = token_airdrop_pb2.TokenAirdropTransactionBody()

        for transfer in token_transfer_list:
            token_airdrop_body.token_transfers.append(transfer._to_proto())

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenAirdrop.CopyFrom(token_airdrop_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.token.associateTokens,
            query_func=None
        )        