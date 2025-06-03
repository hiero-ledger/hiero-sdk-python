from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hbar import Hbar

class AccountBalance:
    """
    Represents the balance of an account, including hbars and tokens.

    Attributes:
        hbars (Hbar): The balance in hbars.
        token_balances (dict): A dictionary mapping TokenId to token balances.
    """

    def __init__(self, hbars, token_balances=None):
        """
        Initializes the AccountBalance with the given hbar balance and token balances.

        Args:
            hbars (Hbar): The balance in hbars.
            token_balances (dict, optional): A dictionary mapping TokenId to token balances.
        """
        self.hbars = hbars
        self.token_balances = token_balances or {}

    @classmethod
    def _from_proto(cls, proto):
        """
        Creates an AccountBalance instance from a protobuf response.

        Args:
            proto: The protobuf CryptoGetAccountBalanceResponse.

        Returns:
            AccountBalance: The account balance instance.
        """
        hbars = Hbar.from_tinybars(proto.balance)

        token_balances = {}
        if proto.tokenBalances:
            for token_balance in proto.tokenBalances:
                token_id = TokenId._from_proto(token_balance.tokenId)
                balance = token_balance.balance
                token_balances[token_id] = balance

        return cls(hbars=hbars, token_balances=token_balances)
