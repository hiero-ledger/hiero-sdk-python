from __future__ import annotations

import sys

import atheris
from eth_abi.exceptions import EncodingError, ParseError


with atheris.instrument_imports():
    from hiero_sdk_python import ContractFunctionParameters


EXPECTED_EXCEPTIONS = (EncodingError, OverflowError, ParseError, TypeError, ValueError)


def _consume_function_name(provider: atheris.FuzzedDataProvider) -> str | None:
    if provider.ConsumeBool():
        return None

    return provider.ConsumeUnicodeNoSurrogates(64)


def _add_parameter(provider: atheris.FuzzedDataProvider, params: ContractFunctionParameters) -> None:
    choice = provider.ConsumeIntInRange(0, 7)

    if choice == 0:
        params.add_bool(provider.ConsumeBool())
    elif choice == 1:
        params.add_address(provider.ConsumeBytes(20))
    elif choice == 2:
        params.add_address(provider.ConsumeBytes(20).hex())
    elif choice == 3:
        params.add_string(provider.ConsumeUnicodeNoSurrogates(256))
    elif choice == 4:
        params.add_bytes(provider.ConsumeBytes(256))
    elif choice == 5:
        params.add_bytes32(provider.ConsumeBytes(64))
    elif choice == 6:
        size = provider.ConsumeIntInRange(1, 32) * 8
        getattr(params, f"add_int{size}")(provider.ConsumeInt(256))
    else:
        size = provider.ConsumeIntInRange(1, 32) * 8
        getattr(params, f"add_uint{size}")(provider.ConsumeInt(256))


def TestOneInput(data: bytes) -> None:
    provider = atheris.FuzzedDataProvider(data)
    params = ContractFunctionParameters(_consume_function_name(provider))

    for _ in range(provider.ConsumeIntInRange(0, 8)):
        _add_parameter(provider, params)

    try:
        params.to_bytes()
    except EXPECTED_EXCEPTIONS:
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
