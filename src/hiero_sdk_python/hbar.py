class Hbar:
    """ Represents the network utility token. For historical purposes this is referred to as an hbar in the SDK because
    that is the native currency of the Hedera network, but for other Hiero networks, it represents the network utility
    token, whatever its designation may be. """

    """ There are 100 million tinybars in one hbar. """
    TINYBAR_TO_HBAR = 100_000_000

    def __init__(self, amount: int, in_tinybars: bool=False):
        """ Create an hbar instance with the given amount designated either in hbars or tinybars. """
        if in_tinybars:
            self._amount_in_tinybar = int(amount)
        else:
            self._amount_in_tinybar = int(amount * self.TINYBAR_TO_HBAR)

    def to_tinybars(self):
        """ Returns the amount of hbars in tinybars. """
        return self._amount_in_tinybar

    def to_hbars(self):
        """ Returns the amount of hbars. """
        return self._amount_in_tinybar / self.TINYBAR_TO_HBAR

    @classmethod
    def from_tinybars(cls, tinybars: int):
        """ Creates an hbar instance from the given amount in tinybars. """
        return cls(tinybars, in_tinybars=True)

    def __str__(self):
        return f"{self.to_hbars():.8f} ℏ"

    def __repr__(self):
        return f"Hbar({self.to_hbars():.8f})"