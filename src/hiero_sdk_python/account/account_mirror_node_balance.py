from __future__ import annotations

from typing import Any

from hiero_sdk_python.hbar import Hbar


class MirrorNodeAccountBalance:
    """
    The HBAR balance of an account as reported by the mirror node REST API.

    Returned by MirrorNodeAccountBalanceQuery. Token balances are not included.
    """

    def __init__(self, hbars: Hbar) -> None:
        """
        Initialize a mirror node account balance.

        Args:
            hbars: The HBAR balance of the account.
        """
        if not isinstance(hbars, Hbar):
            raise ValueError("hbars must be an instance of Hbar")

        self.hbars = hbars

    @staticmethod
    def _from_json(root: dict[str, Any]) -> MirrorNodeAccountBalance | None:
        """
        Create a balance from a mirror node REST JSON payload.

        The mirror node reports an account it does not know with an empty
        `balances` array rather than a 404. In that case, None is returned.

        An account that exists but holds no HBAR is represented by a
        populated entry with `"balance": 0` and is parsed normally.

        Args:
            root: The JSON object returned by GET /api/v1/balances.

        Returns:
            A MirrorNodeAccountBalance, or None if the mirror node knows
            no such account.

        Raises:
            ValueError: If the payload is not a well-formed balances response.
        """
        if not isinstance(root, dict):
            raise TypeError("Mirror Node returned a malformed response: root is not an object")

        if root.get("balances") is None:
            raise ValueError("Mirror Node returned a malformed response: no `balances` array")

        balances = root["balances"]

        if not isinstance(balances, list):
            raise ValueError("Mirror Node returned a malformed response: `balances` is not an array")

        if len(balances) == 0:
            return None

        balance = balances[0]

        if not isinstance(balance, dict):
            raise ValueError("Mirror Node returned a malformed response: balances entry is not an object")

        if balance.get("balance") is None:
            raise ValueError("Mirror Node returned a malformed response: balances entry has no `balance` field")

        return MirrorNodeAccountBalance(Hbar.from_tinybars(int(balance["balance"])))

    @property
    def hbars(self) -> Hbar:
        """
        Returns:
            The HBAR balance of the account.
        """
        return self.hbars

    def __str__(self) -> str:
        return f"MirrorNodeAccountBalance{{hbars={self.hbars}}}"
