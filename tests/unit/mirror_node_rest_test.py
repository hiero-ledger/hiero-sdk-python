from __future__ import annotations

import base64
import re

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.query._mirror_node_rest import to_account_id_param


pytestmark = pytest.mark.unit

EVM_HEX = "1234567890abcdef1234567890abcdef12345678"


def test_to_account_id_param_plain_account_id():
    """A plain shard.realm.num account ID is sent unchanged."""
    account_id = AccountId(0, 0, 1234)

    assert to_account_id_param(account_id) == "0.0.1234"


def test_to_account_id_param_evm_address_object():
    """An EvmAddress object is sent as 0x-prefixed lowercase hex."""
    account_id = AccountId(0, 0, 0, evm_address=EvmAddress.from_string("0x" + EVM_HEX))

    result = to_account_id_param(account_id)

    assert result == "0x" + EVM_HEX
    assert re.fullmatch(r"0x[0-9a-f]{40}", result)


def test_to_account_id_param_evm_address_raw_bytes():
    """An EVM address held as raw 20 bytes is sent as 0x-prefixed hex."""
    raw = bytes.fromhex(EVM_HEX)
    account_id = AccountId(0, 0, 0, evm_address=EvmAddress.from_bytes(raw))
    account_id.evm_address = raw  # exercise the raw-bytes branch directly

    result = to_account_id_param(account_id)

    assert result == "0x" + raw.hex()


def test_to_account_id_param_public_key_alias():
    """A public key alias is sent as unpadded base32 of its protobuf key bytes."""
    alias_key = PrivateKey.generate_ed25519().public_key()
    account_id = AccountId(0, 0, 0, alias_key=alias_key)

    result = to_account_id_param(account_id)

    expected_bytes = alias_key.to_proto_key().SerializeToString()
    expected = base64.b32encode(expected_bytes).decode("ascii").rstrip("=")

    assert result == expected
    assert "=" not in result
