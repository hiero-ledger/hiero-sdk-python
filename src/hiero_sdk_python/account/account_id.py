"""
AccountId class.
"""

import re
from typing import TYPE_CHECKING, Optional, Union

from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    validate_checksum,
    format_to_string_with_checksum,
    perform_query_to_mirror_node,
    to_solidity_address
)

if TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

ALIAS_REGEX = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.((?:[0-9a-fA-F][0-9a-fA-F])+)$")

class AccountId:
    """
    Represents an account ID on the network.

    An account ID consists of three components: shard, realm, and num.
    These components uniquely identify an account in the network.

    The standard format is `<shardNum>.<realmNum>.<accountNum>`, e.g., `0.0.10`.

    In addition to the account number, the account component can also be an alias:
    - An alias can be either a public key (ED25519 or ECDSA) or an EVM address (20 bytes)
    - The alias format is `<shardNum>.<realmNum>.<alias>`, where `alias` is the public key or evm address
    """

    def __init__(
        self,
        shard: int = 0,
        realm: int = 0,
        num: int = 0,
        alias_key: Optional[PublicKey] = None,
        evm_address: Optional[EvmAddress] = None
    ) -> None:
        """
        Initialize a new AccountId instance.
        Args:
            shard (int): The shard number of the account.
            realm (int): The realm number of the account.
            num (int): The account number.
            alias_key (PublicKey): The public key of the account.
            evm_address (EvmAddress): The public evm_address of the account.
        """
        self.shard = shard
        self.realm = realm
        self.num = num
        self.alias_key = alias_key
        self.evm_address = evm_address
        self.__checksum: str | None = None

    @classmethod
    def from_string(cls, account_id_str: str) -> "AccountId":
        """
        Creates an AccountId instance from a string.
        Supported formats:
        - shard.realm.num
        - shard.realm.num-checksum
        - shard.realm.<hex-alias>
        - 0x-prefixed or raw 20-byte hex EVM address
        
        Args:
            account_id_str (str): Account ID string
        
        Returns:
            AccountId: An instance of AccountId
        
        Raises:
            ValueError: If the string format is invalid
        """
        if account_id_str is None or not isinstance(account_id_str, str):
            raise TypeError(f"account_id_str must be a string, got {type(account_id_str).__name__}.")
        
        if cls._is_evm_address(account_id_str):
            # Detect EVM address input (raw 20-byte hex or 0x-prefixed).
            # EVM addresses do not encode shard or realm information, so both
            # values default to 0. The numeric account ID can later be resolved
            # via the mirror node using populate_account_num().
            return cls.from_evm_address(account_id_str, 0, 0)

        try:
            shard, realm, num, checksum = parse_from_string(account_id_str)

            account_id: AccountId = cls(
                shard=int(shard),
                realm=int(realm),
                num=int(num)
            )
            account_id.__checksum = checksum

            return account_id
        except Exception as e:
            alias_match = ALIAS_REGEX.match(account_id_str)
            
            if alias_match:
                shard, realm, alias = alias_match.groups()
                alias_bytes = bytes.fromhex(alias)
                
                is_evm_address = len(alias_bytes) == 20

                # num is set to 0 because the numeric account ID is unknown at creation time.
                # It can later be populated via the mirror node using populate_account_num().
                return cls(
                    shard=int(shard),
                    realm=int(realm),
                    num=0,
                    alias_key=PublicKey.from_bytes(alias_bytes) if not is_evm_address else None,
                    evm_address=EvmAddress.from_bytes(alias_bytes) if is_evm_address else None
                )

            raise ValueError(
                f"Invalid account ID string '{account_id_str}'."
                "Supported formats: "
                "'shard.realm.num', "
                "'shard.realm.num-checksum', "
                "'shard.realm.<hex-alias>', "
                "or a 20-byte EVM address."
            ) from e

    @classmethod
    def from_evm_address(cls, evm_address: Union[str, EvmAddress], shard: int, realm: int) -> "AccountId":
        """
        Create an AccountId from an EVM address.
        In case shard and realm are unknown, they should be set to zero
        
        Args:
            evm_address (Union[str, EvmAddress]): EVM address string or object
            shard (int): Shard number
            realm (int): Realm number
            
        Returns:
            AccountId: An instance of AccountId
        """
        if evm_address is None:
            raise ValueError("evm_address must not be None")

        if isinstance(evm_address, str):
            try:
                evm_address = EvmAddress.from_string(evm_address)
            except Exception as e:
                raise ValueError(f"Invalid EVM address string: {evm_address}") from e
    
        elif not isinstance(evm_address, EvmAddress):
            raise TypeError(
                f"evm_address must be a str or EvmAddress, got {type(evm_address).__name__}"
            )

        return cls(
            shard=shard,
            realm=realm,
            num=0, # numeric account ID unknown at creation time
            alias_key=None,
            evm_address=evm_address
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "AccountId":
        """
        Deserialize an AccountId from protobuf-encoded bytes.
        
        Args:
           data (bytes): Protobuf bytes

        Returns:
            AccountId: An instance of AccountId
        """
        return cls._from_proto(basic_types_pb2.AccountID.FromString(data))

    @classmethod
    def _from_proto(cls, account_id_proto: basic_types_pb2.AccountID) -> "AccountId":
        """
        Creates an AccountId instance from a protobuf AccountID object.

        Args:
            account_id_proto (AccountID): The protobuf AccountID object.

        Returns:
            AccountId: An instance of AccountId.
        """
        result = cls(
            shard=account_id_proto.shardNum,
            realm=account_id_proto.realmNum,
            num=account_id_proto.accountNum,
        )
        if account_id_proto.alias:
            alias = account_id_proto.alias 
            if len(alias) == 20:
                result.evm_address = EvmAddress.from_bytes(alias)
            else:
                alias = alias[2:] # remove 2 bytes, i.e prefix
                result.alias_key = PublicKey.from_bytes(alias)

        return result

    def _to_proto(self) -> basic_types_pb2.AccountID:
        """
        Converts the AccountId instance to a protobuf AccountID object.

        Returns:
            AccountID: The protobuf AccountID object.
        """
        account_id_proto = basic_types_pb2.AccountID(
            shardNum=self.shard,
            realmNum=self.realm,
            accountNum=self.num,
        )

        if self.alias_key:
            key = self.alias_key._to_proto().SerializeToString()
            account_id_proto.alias = key
        elif self.evm_address:
            account_id_proto.alias = self.evm_address.address_bytes

        return account_id_proto

    @property
    def checksum(self) -> str | None:
        """Checksum of the accountId"""
        return self.__checksum

    def validate_checksum(self, client: "Client") -> None:
        """Validate the checksum for the accountId"""
        if self.alias_key is not None or self.evm_address is not None:
            raise ValueError("Cannot calculate checksum with an account ID that has a aliasKey or evmAddress")

        validate_checksum(
            self.shard,
            self.realm,
            self.num,
            self.__checksum,
            client,
        )
    
    @staticmethod
    def _is_evm_address(value: str) -> bool:
        """Check if the given string value is an evm_address"""
        if value.startswith("0x"):
            value = value[2:]

        if len(value) != 40:
            return False

        try:
            bytes.fromhex(value)
        except ValueError:
            return False

        return True


    def __str__(self) -> str:
        """
        Returns the string representation of the AccountId in 'shard.realm.num' format.
        """
        if self.alias_key:
            return f"{self.shard}.{self.realm}.{self.alias_key.to_string()}"
        if self.evm_address:
            return f"{self.shard}.{self.realm}.{self.evm_address.to_string()}"
        return f"{self.shard}.{self.realm}.{self.num}"

    def to_string_with_checksum(self, client: "Client") -> str:
        """
        Returns the string representation of the AccountId with checksum 
        in 'shard.realm.num-checksum' format.
        """
        if self.alias_key is not None or self.evm_address is not None:
            raise ValueError("Cannot calculate checksum with an account ID that has a aliasKey or evmAddress")

        return format_to_string_with_checksum(
            self.shard,
            self.realm,
            self.num,
            client
        )

    def populate_account_num(self, client: "Client") -> "AccountId":
        """
        Populate the numeric account ID using the Mirror Node.
        Intended for AccountIds created from EVM addresses.
        """
        if not self.evm_address:
            raise ValueError("Account evm_address is required before populating num")

        url = f"{client.network.get_mirror_rest_url()}/accounts/{self.evm_address.to_string()}"

        try:
            data = perform_query_to_mirror_node(url)

            account_id = data.get("account")
            if not account_id:
                raise ValueError(f"Mirror node response missing 'account': {data}")
        
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to populate account number from mirror node for evm_address "
                f"{self.evm_address.to_string()}"
            ) from e    
        
        try:
            self.num = int(account_id.split(".")[-1])
            return self
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid account format received: {account_id}")

    def populate_evm_address(self, client: "Client") -> "AccountId":
        """Populate the EVM address using the Mirror Node."""
        if self.num is None or self.num == 0:
            raise ValueError("Account number is required before populating evm_address")

        url = f"{client.network.get_mirror_rest_url()}/accounts/{self.num}"
        try:
            data = perform_query_to_mirror_node(url)

            evm_addr = data.get("evm_address")
            if not evm_addr:
                raise ValueError(f"Mirror node response missing 'evm_address': {data}")
        
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to populate evm_address from mirror node for account {self.num}"
            ) from e

        self.evm_address = EvmAddress.from_string(evm_addr)
        return self

    def to_evm_address(self) -> str:
        """Return the EVM-compatible address for this account. Using account num"""
        if self.evm_address:
            return self.evm_address.to_string()

        return to_solidity_address(self.shard,self.realm,self.num)

    def to_bytes(self) -> bytes:
        """Serialize this AccountId to protobuf bytes."""
        return self._to_proto().SerializeToString()
    
    def __repr__(self) -> str:
        """
        Returns the repr representation of the AccountId.
        """
        if self.alias_key:
            return (
                f"AccountId(shard={self.shard}, realm={self.realm}, "
                f"alias_key={self.alias_key.to_string_raw()})"
            )
        if self.evm_address:
            return (
                f"AccountId(shard={self.shard}, realm={self.realm}, "
                f"evm_address={self.evm_address.to_string()})"
            )
        return f"AccountId(shard={self.shard}, realm={self.realm}, num={self.num})"

    def __eq__(self, other: object) -> bool:
        """
        Checks equality between two AccountId instances.
        Args:
            other (object): The object to compare with.
        Returns:
            bool: True if both instances are equal, False otherwise.
        """
        if not isinstance(other, AccountId):
            return False
        return (self.shard, self.realm, self.num, self.alias_key, self.evm_address) == (
            other.shard,
            other.realm,
            other.num,
            other.alias_key,
            other.evm_address
        )

    def __hash__(self) -> int:
        """Returns a hash value for the AccountId instance."""
        return hash((self.shard, self.realm, self.num))

