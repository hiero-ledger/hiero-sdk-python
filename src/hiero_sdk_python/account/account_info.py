from dataclasses import dataclass
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_relationship import TokenRelationship
from hiero_sdk_python.hapi.services.crypto_get_info_pb2 import CryptoGetInfoResponse

@dataclass
class AccountInfo:
    """
    Contains information about an account.

    Attributes:
        account_id (AccountId): The ID of this account.
        contract_account_id (str): The contract account ID.
        is_deleted (bool): Whether the account has been deleted.
        proxy_received (Hbar): The total number of tinybars proxy staked to this account.
        key (PublicKey): The key for this account.
        balance (Hbar): The current balance of account in hbar.
        receiver_signature_required (bool): If true, this account's key must sign any transaction depositing into this account.
        expiration_time (Timestamp): The timestamp at which this account is set to expire.
        auto_renew_period (Duration): The duration for which this account will automatically renew.
        token_relationships (list[TokenRelationship]): List of token relationships associated with this account.
        account_memo (str): The memo associated with this account.
        owned_nfts (int): The number of NFTs owned by this account.
    """
    account_id : AccountId = None
    contract_account_id : str = None
    is_deleted : bool = None
    proxy_received : Hbar = None
    key : PublicKey = None
    balance : Hbar = None
    receiver_signature_required : bool = None
    expiration_time : Timestamp = None
    auto_renew_period : Duration = None
    token_relationships : list[TokenRelationship] = None
    account_memo : str = None
    owned_nfts : int = None
    
    @classmethod
    def _from_proto(cls, proto: CryptoGetInfoResponse.AccountInfo) -> 'AccountInfo':
        if proto is None:
            raise ValueError("Account info proto is None")

        token_relationships = []
        if proto.tokenRelationships:
            for relationship in proto.tokenRelationships:
                token_relationships.append(TokenRelationship._from_proto(relationship))

        return cls(
            account_id=AccountId._from_proto(proto.accountID) if proto.accountID else None,
            contract_account_id=proto.contractAccountID,
            is_deleted=proto.deleted,
            proxy_received=Hbar.from_tinybars(proto.proxyReceived),
            key=PublicKey._from_proto(proto.key) if proto.key else None,
            balance=Hbar.from_tinybars(proto.balance),
            receiver_signature_required=proto.receiverSigRequired,
            expiration_time=Timestamp._from_protobuf(proto.expirationTime) if proto.expirationTime else None,
            auto_renew_period=Duration._from_proto(proto.autoRenewPeriod) if proto.autoRenewPeriod else None,
            token_relationships=token_relationships,
            account_memo=proto.memo,
            owned_nfts=proto.ownedNfts
        )
        
    def _to_proto(self) -> CryptoGetInfoResponse.AccountInfo:
        token_relationships_proto = []
        if self.token_relationships:
            for relationship in self.token_relationships:
                token_relationships_proto.append(relationship._to_proto())

        return CryptoGetInfoResponse.AccountInfo(
            accountID=self.account_id._to_proto() if self.account_id else None,
            contractAccountID=self.contract_account_id,
            deleted=self.is_deleted,
            proxyReceived=self.proxy_received.to_tinybars() if self.proxy_received else None,
            key=self.key._to_proto() if self.key else None,
            balance=self.balance.to_tinybars() if self.balance else None,
            receiverSigRequired=self.receiver_signature_required,
            expirationTime=self.expiration_time._to_protobuf() if self.expiration_time else None,
            autoRenewPeriod=self.auto_renew_period._to_proto() if self.auto_renew_period else None,
            tokenRelationships=token_relationships_proto,
            memo=self.account_memo,
            ownedNfts=self.owned_nfts
        )