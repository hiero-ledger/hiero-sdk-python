from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hiero_sdk_python.tokens.token_id import TokenId


@dataclass
class MirrorNodeTokenBalance:
    """
    Represents an account's balance for a single token, as reported by a Mirror Node REST API.

    For fungible tokens, the balance is expressed in the token's smallest denomination.
    For non-fungible tokens (NFTs), it represents the number of NFTs held.

    Attributes:
      token_id: The ID of the token.
      balance: The balance held, in the token's smallest denomination or as an NFT count.
      decimals: The number of decimal places for the token, or None if the Mirror Node does not report it.
      associated: Whether the account has a relationship with the token.
    """

    token_id: TokenId
    balance: int
    decimals: int | None
    associated: bool

    def __post_init__(self) -> None:
        """Validate the token balance fields."""
        if not isinstance(self.token_id, TokenId):
            raise TypeError("token_id must be an instance of TokenId")

        if isinstance(self.balance, bool) or not isinstance(self.balance, int):
            raise TypeError("balance must be an integer")

        if self.decimals is not None and (isinstance(self.decimals, bool) or not isinstance(self.decimals, int)):
            raise TypeError("decimals must be an integer or None")

        if not isinstance(self.associated, bool):
            raise TypeError("associated must be a boolean")

    @staticmethod
    def _from_json(root: dict[str, Any], requested_token_id: TokenId) -> MirrorNodeTokenBalance:
        """
        Create a token balance from a Mirror Node REST API response.

        The response is expected to contain the tokens array returned
        by GET /api/v1/accounts/{id}/tokens.

        If the array is missing, null, or empty, the account is treated as
        not associated with the requested token.

        Args:
          root: The JSON response containing token relationships.
          requested_token_id: The ID of the token whose balance was requested.

        Returns:
          A MirrorNodeTokenBalance representing the token balance or the absence of a token relationship.

        Raises:
          TypeError: If the response or a token relationship has an unexpected type.
          ValueError: If the response contains invalid token data.
        """
        if not isinstance(root, dict):
            raise TypeError("Mirror Node returned a malformed response: root must be a dictionary")

        if not isinstance(requested_token_id, TokenId):
            raise TypeError("requested_token_id must be of type TokenId")

        tokens = root.get("tokens")

        if tokens is None or tokens == []:
            return MirrorNodeTokenBalance(requested_token_id, 0, None, False)

        if not isinstance(tokens, list):
            raise TypeError("Mirror Node returned a malformed response: tokens must be a list")

        relationship = tokens[0]
        if not isinstance(relationship, dict):
            raise TypeError("Mirror Node returned a malformed response: token relationship must be a dictionary")

        token_id = requested_token_id
        if relationship.get("token_id") is not None:
            token_id = TokenId.from_string(relationship.get("token_id"))

        balance_value = relationship.get("balance")
        balance = 0 if balance_value is None else balance_value

        decimals = relationship.get("decimals")
        associated = relationship.get("automatic_association", False)

        return MirrorNodeTokenBalance(token_id, balance, decimals, associated)
