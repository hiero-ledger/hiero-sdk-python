"""
Private helpers shared by the mirror node REST queries.
"""

from __future__ import annotations

import base64

from hiero_sdk_python.account.account_id import AccountId


def to_account_id_param(account_id: AccountId) -> str:
    """
    Convert an AccountId to the format expected by the mirror node.

    Plain account IDs are sent as shard.realm.num.

    EVM addresses are sent as 0x-prefixed hexadecimal.

    Public-key aliases are sent as unpadded Base32 encoded protobuf
    key bytes.
    """
    # EVM address
    evm_address = account_id.evm_address

    if evm_address is not None:
        if isinstance(evm_address, bytes):
            return "0x" + evm_address.hex()

        return "0x" + str(evm_address)

    # Public key alias
    alias_key = account_id.alias_key

    if alias_key is not None:
        # The exact conversion here depends on the Python SDK's
        # PublicKey/Key protobuf implementation.
        #
        # This corresponds to:
        #
        # BaseEncoding.base32()
        #     .omitPadding()
        #     .encode(accountId.aliasKey.toProtoKey().toByteArray());

        protobuf_key = alias_key.to_proto_key()
        key_bytes = protobuf_key.SerializeToString()

        return base64.b32encode(key_bytes).decode("ascii").rstrip("=")

    # Standard shard.realm.num account ID
    return str(account_id)
