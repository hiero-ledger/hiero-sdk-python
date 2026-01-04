"""
uv run examples/hbar.py
python examples/hbar.py
"""

from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hbar_unit import HbarUnit


def demonstrate_factory_methods():
    """
    Demonstrates creating Hbar values using the convenient factory methods.
    """
    print("\n=== Creating Hbar Using Factory Methods ===")

    # Creates an Hbar object representing 1 Gigabar (1,000,000,000 ℏ)
    h_giga = Hbar.from_gigabars(1)

    # Creates an Hbar object representing 500 Millibars (0.5 ℏ)
    h_milli = Hbar.from_millibars(500)

    # Creates an Hbar object representing 10.5 Hbars (10.5 ℏ)
    h_standard = Hbar.from_hbars(10.5)

    print(f"Hbar.from_gigabars(1): {h_giga}")
    print(f"Hbar.from_millibars(500): {h_milli}")
    print(f"Hbar.from_hbars(10.5): {h_standard}")


def create_hbar_using_constructor():
    """
    Demonstrates creating Hbar values using the constructor.

    The constructor accepts:
      - amount (int, float, or Decimal)
      - optional unit, Unit of the provided amount.
    """
    print("\n=== Creating Hbar Using Constructor ===")

    # Treated as 10 ℏ
    h1 = Hbar(10)
    # Treated as -3 ℏ
    h2 = Hbar(-3)
    # Treated as 0.1 ℏ
    h3 = Hbar(0.1)
    # Treated as 500 tinybars
    h4 = Hbar(500, unit=HbarUnit.TINYBAR)

    print(f"Hbar(10): {h1}")
    print(f"Hbar(-3): {h2}")
    print(f"Hbar(0.1): {h3}")
    print(f"Hbar(500, unit=HbarUnit.TINYBAR): {h4}")


def create_hbar_using_of():
    """
    Demonstrates creating Hbar using the of() method with explicit units.
    """
    print("\n=== Creating Hbar Using of() Method ===")

    # Treated as 5 ℏ
    h_hbar = Hbar.of(5, HbarUnit.HBAR)
    # Treated as 1 kℏ
    h_kilo = Hbar.of(1, HbarUnit.KILOBAR)
    # Treated as 500 mℏ
    h_milli = Hbar.of(500, HbarUnit.MILLIBAR)

    print(f"Hbar.of(5, HBAR): {h_hbar}")
    print(f"Hbar.of(1, KILOBAR): {h_kilo}")
    print(f"Hbar.of(500, MILLIBAR): {h_milli}")


def create_hbar_from_tinybars():
    """
    Demonstrates using from_tinybars() to create Hbar values directly.
    """
    print("\n=== Creating from Tinybars ===")

    # Treated as tinyhbars
    h1 = Hbar.from_tinybars(1000)
    h2 = Hbar.from_tinybars(50_000_000)
    h3 = Hbar.from_tinybars(-999)

    print(f"Hbar.from_tinybars(1000): {h1}")
    print(f"Hbar.from_tinybars(50_000_000): {h2}")
    print(f"Hbar.from_tinybars(-999): {h3}")


def parse_hbar_from_string():
    """
    Demonstrates parsing Hbar from strings.

    The method accepts:
      - amount string such as '10', '-10', '1.25 Mℏ', or '-1.25 Mℏ'.
      - optional unit (HbarUnit). If the amount string includes a unit symbol
        (e.g., ℏ, kℏ, Mℏ), that symbol determines the unit. Otherwise, the provided
        unit parameter is used. Defaults to HBAR if not specified.
    """
    print("\n=== Parsing Hbar from String ===")

    h1 = Hbar.from_string("10 ℏ")
    h2 = Hbar.from_string("50")  # Default consider as Hbar
    h3 = Hbar.from_string("1.25 Mℏ")
    h4 = Hbar.from_string("-3.5 kℏ")

    print(f"from_string('10 ℏ'): {h1}")
    print(f"from_string('50'): {h2}")
    print(f"from_string('1.25 Mℏ'): {h3}")
    print(f"from_string('-3.5 kℏ'): {h4}")


def demonstrate_conversion_methods():
    """
    Demonstrates usage of to(), to_tinybars(), and to_hbars().
    """
    print("\n=== Converting Hbar Values ===")

    h = Hbar(10)  # 10 ℏ

    print(f"Hbar = {h}")
    print("Hbar in tinybars:", h.to_tinybars())
    print("Hbar in hbars:", h.to_hbars())
    print("Hbar in kilobars:", h.to(HbarUnit.KILOBAR))
    print("Hbar in microbars:", h.to(HbarUnit.MICROBAR))


def demonstrate_negation():
    """
    Demonstrates use of negated() method.
    """
    print("\n=== Negating Hbar Values ===")

    h = Hbar(15)
    neg = h.negated()
    dbl_neg = neg.negated()

    print(f"Original: {h}")
    print(f"Negated: {neg}")
    print(f"Negated twice: {dbl_neg}")


def demonstrate_constants():
    """
    Demonstrates using ZERO, MAX, and MIN constants.
    """
    print("\n=== Using Constants ===")

    # A constant value of zero hbars
    zero_hbar = Hbar.ZERO
    # A constant value of the maximum number of hbars (50_000_000_000 hbars)
    max_hbar = Hbar.MAX
    # A constant value of the minimum number of hbars (-50_000_000_000 hbars)
    min_hbar = Hbar.MIN

    print(f"Hbar.ZERO: {zero_hbar}")
    print(f"Hbar.MAX: {max_hbar}")
    print(f"Hbar.MIN: {min_hbar}")


def run_example():
    create_hbar_using_constructor()
    create_hbar_using_of()
    create_hbar_from_tinybars()
    parse_hbar_from_string()
    demonstrate_conversion_methods()
    demonstrate_negation()
    demonstrate_constants()
    demonstrate_factory_methods()


if __name__ == "__main__":
    run_example()
