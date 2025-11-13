from enum import Enum

class HbarUnit(Enum):
    """
    Represents the various denominations of the HBAR (or network utility token).
    """
    # 1 tinybar = base unit
    TINYBAR = ('tℏ', 1)

    # 1 microbar = 100 tinybars
    MICROBAR = ('μℏ', 10**2)
    
    # 1 millibar = 100,000 tinybars
    MILLIBAR = ('mℏ', 10**5)
    
    # 1 hbar = 100,000,000 tinybars
    HBAR = ('ℏ', 10**8)

    # 1 kilobar = 100,000,000,000 tinybars
    KILOBAR = ('kℏ', 10**11)
    
    # 1 megabar = 100,000,000,000,000 tinybars
    MEGABAR = ('Mℏ', 10**14)
    
    # 1 gigabar = 100,000,000,000,000,000 tinybars
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
