from __future__ import annotations

import sys
import warnings

import atheris


with atheris.instrument_imports():
    from hiero_sdk_python import AccountId, TokenId
    from hiero_sdk_python.contract.contract_id import ContractId


EXPECTED_EXCEPTIONS = (TypeError, UnicodeDecodeError, ValueError)
PARSERS = (AccountId.from_string, TokenId.from_string, ContractId.from_string)


def _try_parse(parser, candidate: str) -> None:
    try:
        parser(candidate)
    except EXPECTED_EXCEPTIONS:
        return


def _consume_text(provider: atheris.FuzzedDataProvider) -> str:
    return provider.ConsumeUnicodeNoSurrogates(256)


def _candidate_inputs(provider: atheris.FuzzedDataProvider) -> list[str]:
    text = _consume_text(provider)
    shard = provider.ConsumeIntInRange(-10, 10)
    realm = provider.ConsumeIntInRange(-10, 10)
    number = provider.ConsumeIntInRange(-(2**31), 2**31 - 1)
    hex_text = provider.ConsumeBytes(48).hex()

    return [
        text,
        f"{shard}.{realm}.{number}",
        f"{shard}.{realm}.{hex_text}",
        f"0x{hex_text}",
    ]


def TestOneInput(data: bytes) -> None:
    provider = atheris.FuzzedDataProvider(data)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        for candidate in _candidate_inputs(provider):
            for parser in PARSERS:
                _try_parse(parser, candidate)


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
