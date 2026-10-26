from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hiero_sdk_python.tokens.token_id import TokenId


@dataclass(frozen=True)
class MirrorNodeTokenBalance:
    """
    Represents an account's balance for a single token, as reported by a Mirror Node REST API.

    For fungible tokens, the balance is expressed in the token's smallest denomination.
    For non-fungible tokens (NFTs), it represents the number of NFTs held.

    Attributes:
      token_id: The ID of the token.
      balance: The balance held, in the token's smallest denomination or as an NFT count.
      decimals: The number of decimal places for the token. This is 0 for an NFT and when the
        Mirror Node reports null.
      associated: False only when the account has no relationship with the token (the Mirror Node
        returned an empty tokens array); True otherwise.
    """

    token_id: TokenId
    balance: int
    decimals: int
    associated: bool = True

    def __post_init__(self) -> None:
        """Validate the token balance fields."""
        if not isinstance(self.token_id, TokenId):
            raise TypeError("token_id must be an instance of TokenId")

        if isinstance(self.balance, bool) or not isinstance(self.balance, int):
            raise TypeError("balance must be an integer")

        if isinstance(self.decimals, bool) or not isinstance(self.decimals, int):
            raise TypeError("decimals must be an integer")

        if not isinstance(self.associated, bool):
            raise TypeError("associated must be a bool")

    @staticmethod
    def _from_json(root: dict[str, Any], requested_token_id: TokenId) -> MirrorNodeTokenBalance:
        """
        Create a token balance from a Mirror Node REST API response.

        The response is expected to contain the tokens array returned
        by GET /api/v1/accounts/{id}/tokens.

        An empty array means the account has no relationship with the requested token, and
        the result has balance 0, decimals 0 and associated False. A missing or null tokens
        array is malformed, not "not associated", and raises ValueError.

        Args:
          root: The JSON response containing token relationships.
          requested_token_id: The ID of the token whose balance was requested.

        Returns:
          A MirrorNodeTokenBalance representing the token balance or the absence of a token relationship.

        Raises:
          TypeError: If the response, a token relationship, or a balance/decimals value has an unexpected type.
          ValueError: If the tokens array is missing or null, or the token ID is invalid.
        """
        if not isinstance(root, dict):
            raise TypeError("Mirror Node returned a malformed response: root must be a dictionary")

        if not isinstance(requested_token_id, TokenId):
            raise TypeError("requested_token_id must be of type TokenId")

        tokens = root.get("tokens")

        if tokens is None:
            raise ValueError("Mirror Node returned a malformed response: missing tokens array")

        if not isinstance(tokens, list):
            raise TypeError("Mirror Node returned a malformed response: tokens must be a list")

        if not tokens:
            return MirrorNodeTokenBalance(requested_token_id, 0, 0, associated=False)

        relationship = tokens[0]
        if not isinstance(relationship, dict):
            raise TypeError("Mirror Node returned a malformed response: token relationship must be a dictionary")

        token_id = requested_token_id
        if relationship.get("token_id") is not None:
            token_id = TokenId.from_string(relationship.get("token_id"))

        balance = relationship.get("balance")
        decimals = relationship.get("decimals")

        return MirrorNodeTokenBalance(
            token_id,
            0 if balance is None else balance,
            0 if decimals is None else decimals,
        )
