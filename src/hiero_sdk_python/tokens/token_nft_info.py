"""
hiero_sdk_python.transaction.token_nft_info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenNftInfo, a class representing Non-Fungible Token details (ID, owner,
creation time, metadata, spender) on the Hedera network, with protobuf conversion.
"""
from typing import Optional
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.hapi.services import timestamp_pb2, token_get_nft_info_pb2

class TokenNftInfo:
    """
    Represents information about a Non-Fungible Token (NFT) on the Hedera network.
    
    This class encapsulates details about an NFT including its unique identifier,
    owner account, creation time, associated metadata, and any account with spending privileges.
    """

    def __init__(
        self,
        nft_id: Optional[NftId] = None,
        account_id: Optional[AccountId] = None,
        creation_time: Optional[int] = None,
        metadata: Optional[bytes] = None,
        spender_id: Optional[AccountId] = None
    ) -> None:
        """
        Initialize a TokenNftInfo instance.
        
        Args:
            nft_id (NftId, optional): The unique identifier of the NFT.
            account_id (AccountId, optional): The account ID of the NFT owner.
            creation_time (int, optional): The timestamp when the NFT was created (in seconds).
            metadata (bytes, optional): The metadata associated with the NFT.
            spender_id (AccountId, optional): The account ID with spending privileges for this NFT.
        """
        self.nft_id: Optional[NftId] = nft_id
        self.account_id: Optional[AccountId] = account_id
        self.creation_time: Optional[int] = creation_time
        self.metadata: Optional[bytes] = metadata
        self.spender_id: Optional[AccountId] = spender_id

    @classmethod
    def _from_proto(cls, proto: token_get_nft_info_pb2.TokenNftInfo) -> "TokenNftInfo":
        """
        Create a TokenNftInfo instance from a protobuf message.
        
        Args:
            proto (token_get_nft_info_pb2.TokenNftInfo): 
            The protobuf message containing NFT information.
            
        Returns:
            TokenNftInfo: A new instance populated with data from the protobuf message.
        """
        return cls(
            nft_id=NftId._from_proto(proto.nftID),
            account_id=AccountId._from_proto(proto.accountID),
            creation_time=proto.creationTime.seconds,
            metadata=proto.metadata,
            spender_id=AccountId._from_proto(proto.spender_id)
        )

    def _to_proto(self) -> token_get_nft_info_pb2.TokenNftInfo:
        """
        Convert this TokenNftInfo instance to a protobuf message.
        
        Returns:
            token_get_nft_info_pb2.TokenNftInfo: 
            The protobuf representation of this NFT information.
        """
        return token_get_nft_info_pb2.TokenNftInfo(
            nftID=self.nft_id._to_proto(),
            accountID=self.account_id._to_proto(),
            creationTime=timestamp_pb2.Timestamp(seconds=self.creation_time),
            metadata=self.metadata,
            spender_id=self.spender_id._to_proto()
        )

    def __str__(self) -> str:
        """
        Get a string representation of this TokenNftInfo instance.
        
        Returns:
            str: A string representation including all fields of this NFT information.
        """
        return (f"TokenNftInfo(nft_id={self.nft_id}, "
                f"account_id={self.account_id}, "
                f"creation_time={self.creation_time}, "
                f"metadata={self.metadata!r}, "
                f"spender_id={self.spender_id})")
