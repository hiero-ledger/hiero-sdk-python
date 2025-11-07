from enum import Enum

class HbarUnit(Enum):
    """
    Represents the various denominations of the HBAR (or network utility token).
    """
    TINYBAR = ('tℏ', 1)
    MICROBAR = ('μℏ', 10**2)
    MILLIBAR = ('mℏ', 10**5)
    HBAR = ('ℏ', 10**8)
    KILOBAR = ('kℏ', 10**11)
    MEGABAR = ('Mℏ', 10**14)
    GIGABAR = ('Gℏ', 10**17)

    def __init__(self, symbol: str, tinybar: int):
        self.symbol = symbol
        self.tinybar = tinybar

    @classmethod
    def from_string(cls, symbol: str) -> "HbarUnit":
        """
        Convert a unit symbol string into the corresponding `HbarUnit`.

        Args:
            symbol (str): The string symbol (e.g., "ℏ", "tℏ", "Mℏ").

        Returns:
            HbarUnit: The corresponding enumeration member.
        """
        for unit in cls:
            if unit.symbol == symbol:
                return unit

        raise ValueError(f"Invalid Hbar unit symbol: {symbol}")
