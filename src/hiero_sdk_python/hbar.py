"""
hiero_sdk_python.hbar.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines the Hbar, a value object for representing, converting,
and validating amounts of the network utility token (HBAR).
"""

import math
import re
import warnings
from decimal import Decimal
from typing import ClassVar, Union

from hiero_sdk_python.hbar_unit import HbarUnit

FROM_STRING_PATTERN = re.compile(r"^((?:\+|\-)?\d+(?:\.\d+)?)(\ (tℏ|μℏ|mℏ|ℏ|kℏ|Mℏ|Gℏ))?$")

class Hbar:
    """
    Represents the network utility token.
    For historical purposes this is referred to as an hbar in the SDK because that is the 
    native currency of the Hedera network, but for other Hiero networks, it represents
    the network utility token, whatever its designation may be.
    """

    ZERO: ClassVar["Hbar"]
    MAX: ClassVar["Hbar"]
    MIN: ClassVar["Hbar"]

    def __init__(
            self,
            amount: Union[int, float, Decimal],
            unit: HbarUnit=HbarUnit.HBAR
        ) -> None:
        """
        Create an Hbar instance with the given amount designated either in hbars or tinybars.

        Args:
            amount: The numeric amount of hbar or tinybar.
            unit: Unit of the provided amount.
        """
        if isinstance(amount, bool) or not isinstance(amount, (int, float, Decimal)):
            raise TypeError("Amount must be of type int, float, or Decimal")

        if isinstance(amount, float) and not math.isfinite(amount):
            raise ValueError("Hbar amount must be finite")

        if  unit == HbarUnit.TINYBAR:
            if not isinstance(amount, int):
                raise ValueError("Fractional tinybar value not allowed")
            self._amount_in_tinybar = int(amount)
            return

        if isinstance(amount, (float, int)):
            amount = Decimal(str(amount))

        tinybar = amount * Decimal(unit.tinybar)
        if tinybar % 1 != 0:
            raise ValueError("Fractional tinybar value not allowed")

        self._amount_in_tinybar = int(tinybar)

    def to(self, unit: HbarUnit) -> float:
        """Return the amount of hbar value to the specified unit."""
        return self._amount_in_tinybar / unit.tinybar

    def to_tinybars(self) -> int:
        """Return the amount of hbars in tinybars."""
        return int(self.to(HbarUnit.TINYBAR))

    def to_hbars(self) -> float:
        """
        Return the amount of hbars as a floating-point number.
        """
        return self.to(HbarUnit.HBAR)

    def negated(self) -> "Hbar":
        """
        Return a new Hbar representing the negated value.

        Returns:
            Hbar: The negated hbar amount.
        """
        return Hbar.from_tinybars(-self._amount_in_tinybar)

    @classmethod
    def of(cls, amount: Union[int, float, Decimal], unit: HbarUnit) -> "Hbar":
        """
        Create an Hbar instance from a given amount and unit.

        Args:
            amount (Union[int, float, Decimal]): The amount to represent.
            unit (HbarUnit): The unit of the given amount.
        
        Returns:
            Hbar: A new Hbar instance.
        """
        return cls(amount, unit=unit)

    @classmethod
    def from_tinybars(cls, tinybars: int) -> "Hbar":
        """
        Create an Hbar instance from the given amount in tinybars.

        Args:
            tinybars (int): The number of tinybars.

        Returns:
            Hbar: A new Hbar instance.
        """
        if isinstance(tinybars, bool) or not isinstance(tinybars, int):
            raise TypeError("tinybars must be an int.")
        return cls(tinybars, unit=HbarUnit.TINYBAR)
    
    @classmethod
    def from_microbars(cls, amount: Union[int, float, Decimal]) -> "Hbar":
        """
        Create an Hbar object representing the specified amount of microbars.
        Example: Hbar.from_microbars(100) -> 100 μℏ
        """
        return cls(amount, unit=HbarUnit.MICROBAR)

    @classmethod
    def from_millibars(cls, amount: Union[int, float, Decimal]) -> "Hbar":
        """
        Create an Hbar object representing the specified amount of millibars.
        Example: Hbar.from_millibars(500) -> 500 mℏ
        """
        return cls(amount, unit=HbarUnit.MILLIBAR)

    @classmethod
    def from_hbars(cls, amount: Union[int, float, Decimal]) -> "Hbar":
        """
        Create an Hbar object representing the specified amount of hbars.
        Example: Hbar.from_hbars(10) -> 10 ℏ
        """
        return cls(amount, unit=HbarUnit.HBAR)

    @classmethod
    def from_kilobars(cls, amount: Union[int, float, Decimal]) -> "Hbar":
        """
        Create an Hbar object representing the specified amount of kilobars.
        Example: Hbar.from_kilobars(1) -> 1 kℏ
        """
        return cls(amount, unit=HbarUnit.KILOBAR)

    @classmethod
    def from_megabars(cls, amount: Union[int, float, Decimal]) -> "Hbar":
        """
        Create an Hbar object representing the specified amount of megabars.
        Example: Hbar.from_megabars(1) -> 1 Mℏ
        """
        return cls(amount, unit=HbarUnit.MEGABAR)

    @classmethod
    def from_gigabars(cls, amount: Union[int, float, Decimal]) -> "Hbar":
        """
        Create an Hbar object representing the specified amount of gigabars.
        Example: Hbar.from_gigabars(1) -> 1 Gℏ
        """
        return cls(amount, unit=HbarUnit.GIGABAR)

    @classmethod
    def from_string(cls, amount: str, unit: HbarUnit = HbarUnit.HBAR) -> "Hbar":
        """
        Create an Hbar instance from a string like "10 ℏ", "5000 tℏ", "-0.25 Mℏ", or "10".
        
        Args:
            amount (str): The string to parse (e.g., "1.5 ℏ", "1000 tℏ", or just "10").
            unit (HbarUnit): The unit to use if the string does not include one (default: HBAR).
            
        Returns:
            Hbar: A new Hbar instance.
        """
        match = FROM_STRING_PATTERN.match(amount)

        if not match:
            raise ValueError(f"Invalid Hbar format: '{amount}'")

        parts = amount.split(' ')
        value = Decimal(parts[0])
        unit = HbarUnit.from_string(parts[1]) if len(parts) == 2 else unit
        return cls(value, unit=unit)

    def __str__(self) -> str:
        return f"{self.to_hbars():.8f} ℏ"

    def __repr__(self) -> str:
        return f"Hbar({self.to_hbars():.8f})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self._amount_in_tinybar == other._amount_in_tinybar

    def __hash__(self) -> int:
        return hash(self._amount_in_tinybar)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self._amount_in_tinybar < other._amount_in_tinybar

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self._amount_in_tinybar <= other._amount_in_tinybar

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self._amount_in_tinybar > other._amount_in_tinybar

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self._amount_in_tinybar >= other._amount_in_tinybar


Hbar.ZERO = Hbar(0)
Hbar.MAX = Hbar(50_000_000_000)
Hbar.MIN = Hbar(-50_000_000_000)