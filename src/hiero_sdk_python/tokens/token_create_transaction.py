from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_create_pb2, basic_types_pb2
from hiero_sdk_python.response_code import ResponseCode
from cryptography.hazmat.primitives import serialization

class TokenCreateTransaction(Transaction):
    """
    Represents a token creation transaction on the Hedera network.

    This transaction creates a new token with specified properties, such as
    name, symbol, decimals, initial supply, and treasury account.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token creation transaction.
    """

    def __init__(self, token_name=None, token_symbol=None, decimals=None, initial_supply=None, 
                 treasury_account_id=None, admin_key=None, supply_key=None, freeze_key=None):
        """
        Initializes a new TokenCreateTransaction instance with optional keyword arguments.

        Args:
            token_name (str, optional): The name of the token.
            token_symbol (str, optional): The symbol of the token.
            decimals (int, optional): The number of decimals for the token.
            initial_supply (int, optional): The initial supply of the token.
            treasury_account_id (AccountId, optional): The treasury account ID.
            admin_key (PrivateKey, optional): The admin key for the token.
            supply_key (PrivateKey, optional): The supply key for the token.

            freeze_key (PrivateKey, optional): The freeze key for the token.
        """
        super().__init__()
        self.token_name = token_name
        self.token_symbol = token_symbol
        self.decimals = decimals
        self.initial_supply = initial_supply
        self.treasury_account_id = treasury_account_id
        self.admin_key = admin_key
        self.supply_key = supply_key
        self.freeze_key = freeze_key

        self._default_transaction_fee = 3_000_000_000

    def set_token_name(self, name):
        self._require_not_frozen()
        self.token_name = name
        return self

    def set_token_symbol(self, symbol):
        self._require_not_frozen()
        self.token_symbol = symbol
        return self

    def set_decimals(self, decimals):
        self._require_not_frozen()
        self.decimals = decimals
        return self

    def set_initial_supply(self, initial_supply):
        self._require_not_frozen()
        self.initial_supply = initial_supply
        return self

    def set_treasury_account_id(self, account_id):
        self._require_not_frozen()
        self.treasury_account_id = account_id
        return self

    def set_admin_key(self, admin_key): 
        self._require_not_frozen()
        self.admin_key = admin_key
        return self
    
    def set_supply_key(self, supply_key): 
        self._require_not_frozen()
        self.supply_key = supply_key
        return self
    
    def set_freeze_key(self, freeze_key): 
        self._require_not_frozen()
        self.freeze_key = freeze_key
        return self
    
    
    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the token creation details.

        Raises:
            ValueError: If required fields are missing.
        """
        if not all([
            self.token_name,
            self.token_symbol,
            self.decimals is not None,
            self.initial_supply is not None,
            self.treasury_account_id
        ]):
            raise ValueError("Missing required fields")

        admin_key_proto = None
        if self.admin_key:
            admin_public_key_bytes = self.admin_key.public_key().to_bytes_raw()
            admin_key_proto = basic_types_pb2.Key(ed25519=admin_public_key_bytes)

        supply_key_proto = None
        if self.supply_key:
            supply_public_key_bytes = self.supply_key.public_key().to_bytes_raw()
            supply_key_proto = basic_types_pb2.Key(ed25519=supply_public_key_bytes)

        freeze_key_proto = None
        if self.freeze_key:
            freeze_public_key_bytes = self.freeze_key.public_key().to_bytes_raw()
            freeze_key_proto = basic_types_pb2.Key(ed25519=freeze_public_key_bytes)

        token_create_body = token_create_pb2.TokenCreateTransactionBody(
            name=self.token_name,
            symbol=self.token_symbol,
            decimals=self.decimals,
            initialSupply=self.initial_supply,
            treasury=self.treasury_account_id.to_proto(),
            adminKey=admin_key_proto,
            supplyKey=supply_key_proto,
            freezeKey=freeze_key_proto

        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenCreation.CopyFrom(token_create_body)

        return transaction_body

    def _execute_transaction(self, client, transaction_proto):
        """
        Executes the token creation transaction using the provided client.

        Args:
            client (Client): The client instance to use for execution.
            transaction_proto (Transaction): The protobuf Transaction message.

        Returns:
            TransactionReceipt: The receipt from the network after transaction execution.

        Raises:
            Exception: If the transaction submission fails or receives an error response.
        """
        response = client.token_stub.createToken(transaction_proto)

        if response.nodeTransactionPrecheckCode != ResponseCode.OK:
            error_code = response.nodeTransactionPrecheckCode
            error_message = ResponseCode.get_name(error_code)
            raise Exception(f"Error during transaction submission: {error_code} ({error_message})")

        receipt = self.get_receipt(client)
        return receipt
