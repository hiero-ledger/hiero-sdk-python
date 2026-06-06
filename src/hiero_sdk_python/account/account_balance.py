"""AccountBalance class."""

from __future__ import annotations

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
        token_decimals (dict, optional): A dictionary mapping TokenId to token deimals.
    """

    def __init__(
        self, hbars: Hbar, token_balances: dict[TokenId, int] = None, token_decimals: dict[TokenId, int] = None
    ) -> None:
        """
        Initializes the AccountBalance with the given hbar balance and token balances.

        Args:
            hbars (Hbar): The balance in hbars.
            token_balances (dict, optional): A dictionary mapping TokenId to token balances.
            token_decimals (dict, optional): A dictionary mapping TokenId to token deimals.
        """
        self.hbars = hbars
        self.token_balances = token_balances or {}
        self.token_decimals = token_decimals or {}

    @classmethod
    def _from_proto(cls, proto: CryptoGetAccountBalanceResponse) -> AccountBalance:
        """
        Creates an AccountBalance instance from a protobuf response.

        Args:
            proto: The protobuf CryptoGetAccountBalanceResponse.

        Returns:
            AccountBalance: The account balance instance.
        """
        hbars: Hbar = Hbar.from_tinybars(tinybars=proto.balance)

        token_balances: dict[TokenId, int] = {}
        token_decimals: dict[TokenId, int] = {}

        if proto.tokenBalances:
            for token_balance in proto.tokenBalances:
                token_id: TokenId = TokenId._from_proto(token_balance.tokenId)
                balance: int = token_balance.balance
                decimal: int = token_balance.decimals

                token_balances[token_id] = balance
                token_decimals[token_id] = decimal

        return cls(hbars=hbars, token_balances=token_balances, token_decimals=token_decimals)

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

        if self.token_decimals:
            lines.append("Token Decimals:")
            for token_id, decimal in self.token_decimals.items():
                lines.append(f" - Token ID {token_id}: {decimal} decimals")

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
        token_decimals_repr = (
            f"{{{', '.join(f'{token_id!r}: {decimals}' for token_id, decimals in self.token_decimals.items())}}}"
            if self.token_decimals
            else "{}"
        )
        return f"AccountBalance(hbars={self.hbars!r}, token_balances={token_balances_repr}) token_decimals={token_decimals_repr})"
