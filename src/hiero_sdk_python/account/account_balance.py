"""
AccountBalance class.
"""

from typing import Dict

from hiero_sdk_python.hapi.services.crypto_get_account_balance_pb2 import (
    CryptoGetAccountBalanceResponse,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.token_id import TokenId


class AccountBalance:
    """
    Represents the balance of an account, including hbars and tokens.

    Attributes:
        hbars (Hbar): The balance in hbars.
        token_balances (dict): A dictionary mapping TokenId to token balances.
    """

    def __init__(self, hbars: Hbar, token_balances: Dict[TokenId, int] = None) -> None:
        """
        Initializes the AccountBalance with the given hbar balance and token balances.

        Args:
            hbars (Hbar): The balance in hbars.
            token_balances (dict, optional): A dictionary mapping TokenId to token balances.
        """
        self.hbars = hbars
        self.token_balances = token_balances or {}

    @classmethod
    def _from_proto(cls, proto: CryptoGetAccountBalanceResponse) -> "AccountBalance":
        """
        Creates an AccountBalance instance from a protobuf response.

        Args:
            proto: The protobuf CryptoGetAccountBalanceResponse.

        Returns:
            AccountBalance: The account balance instance.
        """
        hbars: Hbar = Hbar.from_tinybars(tinybars=proto.balance)

        token_balances: Dict[TokenId, int] = {}
        if proto.tokenBalances:
            for token_balance in proto.tokenBalances:
                token_id: TokenId = TokenId._from_proto(token_balance.tokenId)
                balance: int = token_balance.balance
                token_balances[token_id] = balance

        return cls(hbars=hbars, token_balances=token_balances)
