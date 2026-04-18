from __future__ import annotations

import sys
import warnings

import atheris
from cryptography.exceptions import UnsupportedAlgorithm


with atheris.instrument_imports():
    from hiero_sdk_python import PrivateKey, PublicKey


EXPECTED_EXCEPTIONS = (TypeError, UnsupportedAlgorithm, ValueError)
BYTE_PARSERS = (PrivateKey.from_bytes, PublicKey.from_bytes)
STRING_PARSERS = (PrivateKey.from_string, PublicKey.from_string)


def _try_parse(parser, value: bytes | str) -> None:
    try:
        parser(value)
    except EXPECTED_EXCEPTIONS:
        return


def TestOneInput(data: bytes) -> None:
    provider = atheris.FuzzedDataProvider(data)
    raw_bytes = provider.ConsumeBytes(512)
    raw_text = provider.ConsumeUnicodeNoSurrogates(1024)
    hex_text = raw_bytes.hex()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)

        for parser in BYTE_PARSERS:
            _try_parse(parser, raw_bytes)

        for candidate in (raw_text, hex_text, f"0x{hex_text}"):
            for parser in STRING_PARSERS:
                _try_parse(parser, candidate)


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
