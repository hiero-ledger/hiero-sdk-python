import re
from decimal import Decimal
from typing import Union

from hiero_sdk_python.hbar_unit import HbarUnit

FROM_STRING_PATTERN = re.compile(r"^((?:\+|\-)?\d+(?:\.\d+)?)(\ (tℏ|μℏ|mℏ|ℏ|kℏ|Mℏ|Gℏ))?$")

class Hbar:
    """
    Represents the network utility token. For historical purposes this is referred to as an hbar in the SDK because
    that is the native currency of the Hedera network, but for other Hiero networks, it represents the network utility
    token, whatever its designation may be.
    """

    def __init__(
            self,
            amount: Union[int, float, Decimal],
            in_tinybars: bool=False,
            unit: HbarUnit=HbarUnit.HBAR
        ) -> None:
        """
        Create an Hbar instance with the given amount designated either in hbars or tinybars.

        Args:
            amount: The numeric amount of hbar or tinybar.
            in_tinybars: If True, treat the amount as tinybars directly.
            unit: The unit of the provided amount (default: HBAR).
        """
        if in_tinybars or unit is HbarUnit.TINYBAR:
            self._amount_in_tinybar = int(amount)
            return

        if isinstance(amount, (float, int)):
            amount = Decimal(str(amount))
        elif not isinstance(amount, Decimal):
            raise TypeError("Amount must be of type int, float, or Decimal")

        tinybar = amount * Decimal(unit._tinybar)

        if tinybar % 1 != 0:
            raise ValueError(
                "Amount and Unit combination results in a fractional value for tinybar. "
                "Ensure tinybar value is a whole number."
            )

        self._amount_in_tinybar = int(tinybar)

    def to(self, unit: HbarUnit):
        """Convert the Hbar value to the specified unit."""
        return self._amount_in_tinybar / unit._tinybar

    def to_tinybars(self):
        """Returns the amount of hbars in tinybars."""
        return self._amount_in_tinybar

    def to_hbars(self):
        """Returns the amount of hbars."""
        return self.to(HbarUnit.HBAR)
    
    def negated(self) -> "Hbar":
        return Hbar.from_tinybars(-self._amount_in_tinybar)

    @classmethod
    def from_tinybars(cls, tinybars: int) -> "Hbar":
        """Creates an hbar instance from the given amount in tinybars."""
        return cls(tinybars, in_tinybars=True)

    @classmethod
    def from_string(cls, amount: str, unit: HbarUnit = HbarUnit.HBAR) -> "Hbar":
        """
        Creates an Hbar instance from a string like "10 ℏ" or "5000 tℏ".
        
        Args:
            amount: The string to parse (e.g., "1.5 ℏ", "1000 tℏ", or just "10").
            unit: The default unit to use if the string does not include one (default: HBAR).
            
        Returns:
            Hbar: A new Hbar instance.
        """
        match = FROM_STRING_PATTERN.match(amount)
        if not match:
            raise ValueError(f"Invalid Hbar format: '{amount}'")

        parts = amount.split(' ')
        amount = Decimal(parts[0])
        unit = HbarUnit.from_string(parts[1]) if len(parts) == 2 else unit
        
        return cls(amount, unit=unit)

    @classmethod
    def from_amount(cls, amount: Union[int, float, Decimal], unit: HbarUnit) -> "Hbar":
        """Create an Hbar instance from the given amount and unit."""
        return cls(amount, unit=unit)

    def __str__(self) -> str:
        return f"{self.to_hbars():.8f} ℏ"

    def __repr__(self) -> str:
        return f"Hbar({self.to_hbars():.8f})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(object, Hbar):
            return NotImplemented
        return self._amount_in_tinybar == other._amount_in_tinybar
    
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self.value_in_tinybar < other.value_in_tinybar
    
    def __le__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self.value_in_tinybar <= other.value_in_tinybar
    
    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self.value_in_tinybar > other.value_in_tinybar
    
    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Hbar):
            return NotImplemented
        return self.value_in_tinybar >= other.value_in_tinybar
    
    def __hash__(self) -> int:
        return hash(self._amount_in_tinybar)

Hbar.ZERO = Hbar(0, in_tinybars=True)
Hbar.MAX = Hbar(50_000_000_000)
Hbar.MIN = Hbar(-50_000_000_000)
