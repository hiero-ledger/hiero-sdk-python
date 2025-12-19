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

    def __str__(self) -> str:
        """
        Returns a human-friendly string representation of the account balance.
        
        Returns:
            str: A string showing HBAR balance and token balances.
        """
        lines = [f"HBAR Balance: {self.hbars} hbars"]
        if self.token_balances:
            lines.append("Token Balances:")
            for token_id, balance in self.token_balances.items():
                lines.append(f" - Token ID {token_id}: {balance} units")
        return "\n".join(lines)

    def __repr__(self) -> str:
        """
        Returns a developer-friendly string representation of the account balance.
        
        Returns:
            str: A string representation that shows the key attributes.
        """
        token_balances_repr = (
            f"{{{', '.join(f'{token_id!r}: {balance}' for token_id, balance in self.token_balances.items())}}}"
            if self.token_balances
            else "{}"
        )
        return f"AccountBalance(hbars={self.hbars!r}, token_balances={token_balances_repr})"


def getBalance(id):
    return None
