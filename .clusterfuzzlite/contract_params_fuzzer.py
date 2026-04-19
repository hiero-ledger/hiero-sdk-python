"""Atheris fuzz target: ContractFunctionParameters ABI encoding."""

from __future__ import annotations

import sys

import atheris


with atheris.instrument_imports():
    from hiero_sdk_python import ContractFunctionParameters


def TestOneInput(data: bytes) -> None:
    """Feed arbitrary bytes into ContractFunctionParameters encoding paths."""
    fdp = atheris.FuzzedDataProvider(data)
    choice = fdp.ConsumeIntInRange(0, 7)

    try:
        params = ContractFunctionParameters()

        if choice == 0:
            params.add_bool(fdp.ConsumeBool())
        elif choice == 1:
            # add_address expects a 20-byte hex string or bytes
            params.add_address(fdp.ConsumeBytes(20).hex())
        elif choice == 2:
            params.add_string(fdp.ConsumeUnicodeNoSurrogates(256))
        elif choice == 3:
            params.add_bytes(fdp.ConsumeBytes(256))
        elif choice == 4:
            params.add_bytes32(fdp.ConsumeBytes(32))
        elif choice == 5:
            count = fdp.ConsumeIntInRange(0, 8)
            params.add_bool_array([fdp.ConsumeBool() for _ in range(count)])
        elif choice == 6:
            count = fdp.ConsumeIntInRange(0, 8)
            params.add_string_array([fdp.ConsumeUnicodeNoSurrogates(64) for _ in range(count)])
        else:
            count = fdp.ConsumeIntInRange(0, 8)
            params.add_bytes_array([fdp.ConsumeBytes(32) for _ in range(count)])

        params.to_bytes()

    except Exception:
        pass


atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
