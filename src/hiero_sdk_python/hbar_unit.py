from decimal import Decimal
from enum import Enum

class HbarUnit(Enum):
    TINYBAR = ('tℏ', 1)
    MICROBAR = ('μℏ', 10**2)
    MILLIBAR = ('mℏ', 10**5)
    HBAR = ('ℏ', 10**8)
    KILOBAR = ('kℏ', 10**11)
    MEGABAR = ('Mℏ', 10**14)
    GIGABAR = ('Gℏ', 10**17)

    def __init__(self, symbol: str, tinybar: int):
        self._symbol = symbol
        self._tinybar = tinybar

    @classmethod
    def from_string(cls, symbol: str):
        for unit in cls:
            if unit._symbol == symbol:
                return unit
            
        raise ValueError(f"Invalid Hbar unit symbol: {symbol}")
