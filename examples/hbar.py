from hiero_sdk_python import HbarUnit, Hbar


def run_example():
     # --- Basic Hbar creation examples ---
    print("=== Creating Hbar amounts ===")
    hbar_hbar = Hbar.of(50, HbarUnit.HBAR)
    hbar_tinybar = Hbar.of(50, HbarUnit.TINYBAR)
    hbar_millibar = Hbar.of(1_000, HbarUnit.MILLIBAR)

    print(f"50 HBAR = {hbar_hbar.to_tinybars()} tinybars")
    print(f"50 tinybars = {hbar_tinybar.to(HbarUnit.HBAR)} HBAR")
    print(f"1,000 millibars = {hbar_millibar.to(HbarUnit.HBAR)} HBAR")

    # --- Unit conversions ---
    print("\n=== Unit conversions ===")
    hbar_value = Hbar(2.5)

    print(f"{hbar_value} in tinybars: {hbar_value.to_tinybars()}")
    print(f"{hbar_value} in kilobars: {hbar_value.to(HbarUnit.KILOBAR)}")

    # --- Using predefined constants ---
    print("\n=== Predefined Hbar constants ===")
    
    print(f"Hbar.ZERO       = {Hbar.ZERO}")
    print(f"Hbar.MAX        = {Hbar.MAX}")
    print(f"Hbar.MIN        = {Hbar.MIN}")


if __name__ == "__main__":
    run_example()