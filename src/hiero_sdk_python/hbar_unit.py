from decimal import Decimal
from enum import Enum

class HbarUnit(Enum):
    TINYBAR = ('tℏ', Decimal(1))
    MICROBAR = ('μℏ', Decimal(10**2))
    MILLIBAR = ('mℏ', Decimal(10**5))
    HBAR = ('ℏ', Decimal(10**8))
    KILOBAR = ('kℏ', Decimal(10**11))
    MEGABAR = ('Mℏ', Decimal(10**14))
    GIGABAR = ('Gℏ', Decimal(10**17))

    def __init__(self, symbol: str, tinybar: Decimal):
        self._symbol = symbol
        self._tinybar = tinybar

    @classmethod
    def from_string(cls, symbol: str):
        for unit in cls:
            if unit.symbol == symbol:
                return unit
            
        raise ValueError(f"Invalid Hbar unit symbol: {symbol}")
