import pytest

from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services.token_claim_airdrop_pb2 import ( # pylint: disable=no-name-in-module
    TokenClaimAirdropTransactionBody,
)
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_airdrop_claim import TokenClaimAirdropTransaction
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId

pytestmark = pytest.mark.unit

def _make_fungible_pending(sender: AccountId, receiver: AccountId, num: int) -> PendingAirdropId:
    return PendingAirdropId(sender, receiver, TokenId(0, 0, num), None)

def _make_nft_pending(sender: AccountId, receiver: AccountId, num: int, serial: int) -> PendingAirdropId:
    return PendingAirdropId(sender, receiver, None, NftId(TokenId(0, 0, num), serial))

def test_add_pending_airdrop_id():
    """Test adding one pending fungible airdrop id using chaining method"""
    sender = AccountId(0, 0, 1001)
    receiver = AccountId(0, 0, 1002)

    pending_airdrop_fungible_1 = _make_fungible_pending(sender, receiver, 1000)

    tx_claim = TokenClaimAirdropTransaction()
    chained = tx_claim.add_pending_airdrop_id(pending_airdrop_fungible_1)
    assert chained is tx_claim  # chaining should return same instance

    ids = tx_claim.get_pending_airdrop_ids()
    assert isinstance(ids, list)
    assert len(ids) == 1
    assert ids[0] == pending_airdrop_fungible_1

def test_add_pending_airdrop_id_nft():
    """Test adding one pending NFT airdrop id using chaining method"""
    sender = AccountId(0, 0, 2001)
    receiver = AccountId(0, 0, 2002)

    pending_airdrop_nft_1 = _make_nft_pending(sender, receiver, 2000, 1)

    tx_claim = TokenClaimAirdropTransaction()
    chained = tx_claim.add_pending_airdrop_id(pending_airdrop_nft_1)
    assert chained is tx_claim  # chaining should return same instance

    ids = tx_claim.get_pending_airdrop_ids()
    assert isinstance(ids, list)
    assert len(ids) == 1
    assert ids[0] == pending_airdrop_nft_1

def test_add_pending_airdrop_ids_mixed_fungible_and_nft():
    """Claim one fungible and one NFT pending airdrop in a single transaction."""
    sender = AccountId(0, 0, 3001)
    receiver = AccountId(0, 0, 3002)

    fungible = _make_fungible_pending(sender, receiver, 3000)   # token num=3000
    nft = _make_nft_pending(sender, receiver, 4000, 1)          # token num=4000, serial=1

    tx_claim = TokenClaimAirdropTransaction()
    tx_claim.add_pending_airdrop_id(fungible).add_pending_airdrop_id(nft)

    ids = tx_claim.get_pending_airdrop_ids()
    assert isinstance(ids, list)
    assert len(ids) == 2

    # Order should be preserved: [fungible, nft]
    assert ids[0] == fungible
    assert ids[1] == nft

def test_add_pending_airdrop_ids_multiple_mixed_dynamic():
    """Test adding several fungible + NFT pending airdrop IDs built dynamically."""
    sender = AccountId(0, 0, 6201)
    receiver = AccountId(0, 0, 6202)

    pending_ids = []
    # Add fungible IDs
    for token_num in (6200, 6201):
        pending_ids.append(PendingAirdropId(sender, receiver, TokenId(0, 0, token_num), None))
    # Add NFT IDs
    for serial in (1, 2):
        pending_ids.append(PendingAirdropId(sender, receiver, None, NftId(TokenId(0, 0, 7200), serial)))

    tx_claim = TokenClaimAirdropTransaction()
    tx_claim.add_pending_airdrop_ids(pending_ids)

    ids = tx_claim.get_pending_airdrop_ids()
    assert ids == pending_ids

def test_cannot_exceed_max_airdrops():
    """ Tests that 10 airdrops is fine but anything more not"""
    sender = AccountId(0, 0, 8001)
    receiver = AccountId(0, 0, 8002)
    tx = TokenClaimAirdropTransaction()

    items = [PendingAirdropId(sender, receiver, TokenId(0, 0, 8000 + i), None)
             for i in range(tx.MAX_IDS)]
    tx.add_pending_airdrop_ids(items)
    assert len(tx.get_pending_airdrop_ids()) == tx.MAX_IDS

    with pytest.raises(ValueError):
        tx.add_pending_airdrop_id(PendingAirdropId(sender, receiver, TokenId(0, 0, 9999), None)) #This would be 11

def test_add_batch_overflow_is_atomic():
    sender_account = AccountId(0, 0, 9001)
    receiver_account = AccountId(0, 0, 9002)
    transaction_claim = TokenClaimAirdropTransaction()

    # Fill to exactly MAX_IDS - 1
    initial_ids = [
        PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9000 + i), None)
        for i in range(transaction_claim.MAX_IDS - 1)
    ]
    transaction_claim.add_pending_airdrop_ids(initial_ids)

    overflow_batch = [
        PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9990), None),
        PendingAirdropId(sender_account, receiver_account, None, NftId(TokenId(0, 0, 9991), 1)),
    ]

    before_ids = transaction_claim.get_pending_airdrop_ids()
    with pytest.raises(ValueError):
        transaction_claim.add_pending_airdrop_ids(overflow_batch)
    after_ids = transaction_claim.get_pending_airdrop_ids()

    assert after_ids == before_ids

def test_min_ids_enforced_on_build_hits_validation():
    """ Tests that at least one airdrop is required to claim"""
    transaction_claim = TokenClaimAirdropTransaction()
    transaction_claim.transaction_id = TransactionId(AccountId(0, 0, 9999), timestamp_pb2.Timestamp(seconds=1))
    transaction_claim.node_account_id = AccountId(0, 0, 3)

    with pytest.raises(ValueError):
        transaction_claim.build_transaction_body()

def test_rejects_duplicate_fungible():
    sender = AccountId(0, 0, 8101)
    receiver = AccountId(0, 0, 8102)

    f1 = PendingAirdropId(sender, receiver, TokenId(0, 0, 8100), None)
    f2 = PendingAirdropId(sender, receiver, TokenId(0, 0, 8100), None)  # duplicate

    tx = TokenClaimAirdropTransaction().add_pending_airdrop_id(f1)

    with pytest.raises(ValueError):
        tx.add_pending_airdrop_ids([f2])

    # List should remain unchanged because it should deduplicate
    ids = tx.get_pending_airdrop_ids()
    assert ids == [f1]

def test_rejects_duplicate_nft():
    sender = AccountId(0, 0, 8201)
    receiver = AccountId(0, 0, 8202)

    n1 = PendingAirdropId(sender, receiver, None, NftId(TokenId(0, 0, 8200), 1))
    n2 = PendingAirdropId(sender, receiver, None, NftId(TokenId(0, 0, 8200), 1))  # duplicate

    tx = TokenClaimAirdropTransaction().add_pending_airdrop_id(n1)

    with pytest.raises(ValueError):
        tx.add_pending_airdrop_ids([n2])

    # List should remain unchanged because it should deduplicate
    ids = tx.get_pending_airdrop_ids()
    assert ids == [n1]

def test_build_transaction_body_populates_proto():
    sender = AccountId(0, 0, 8401)
    receiver = AccountId(0, 0, 8402)

    fungible_airdrop = PendingAirdropId(sender, receiver, TokenId(0, 0, 8400), None)
    nft_airdrop = PendingAirdropId(sender, receiver, None, NftId(TokenId(0, 0, 8405), 3))

    tx_claim = TokenClaimAirdropTransaction().add_pending_airdrop_ids(
        [fungible_airdrop, nft_airdrop]
    )

    # Satisfy base preconditions: set transaction_id and node_account_id
    tx_claim.transaction_id = TransactionId(
        sender, timestamp_pb2.Timestamp(seconds=1, nanos=0)
    )
    tx_claim.node_account_id = AccountId(0, 0, 3)  # dummy node account

    body: transaction_pb2.TransactionBody = tx_claim.build_transaction_body()

    claim = body.tokenClaimAirdrop
    assert isinstance(claim, TokenClaimAirdropTransactionBody)
    assert len(claim.pending_airdrops) == 2

    expected = [a._to_proto().SerializeToString() for a in [fungible_airdrop, nft_airdrop]]
    actual = [a.SerializeToString() for a in claim.pending_airdrops]
    assert actual == expected

def test_from_proto_round_trip():
    sender_account = AccountId(0, 0, 9041)
    receiver_account = AccountId(0, 0, 9042)
    original_ids = [
        PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9040), None),
        PendingAirdropId(sender_account, receiver_account, None, NftId(TokenId(0, 0, 9045), 7)),
    ]
    proto_body = TokenClaimAirdropTransactionBody(pending_airdrops=[i._to_proto() for i in original_ids])

    rebuilt = TokenClaimAirdropTransaction._from_proto(proto_body)  # pylint: disable=protected-access
    assert rebuilt.get_pending_airdrop_ids() == original_ids

def test_get_pending_airdrop_ids_returns_copy():
    sender_account = AccountId(0, 0, 9021)
    receiver_account = AccountId(0, 0, 9022)
    airdrop_id = PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9020), None)

    transaction_claim = TokenClaimAirdropTransaction().add_pending_airdrop_id(airdrop_id)
    snapshot = transaction_claim.get_pending_airdrop_ids()
    snapshot.append(PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9999), None))

    assert transaction_claim.get_pending_airdrop_ids() == [airdrop_id]  # unchanged

def test_order_preserved_across_batched_adds():
    sender_account = AccountId(0, 0, 9031)
    receiver_account = AccountId(0, 0, 9032)

    id_a = PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9030), None)
    id_b = PendingAirdropId(sender_account, receiver_account, None, NftId(TokenId(0, 0, 9035), 1))
    id_c = PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9031), None)
    id_d = PendingAirdropId(sender_account, receiver_account, None, NftId(TokenId(0, 0, 9035), 2))

    transaction_claim = TokenClaimAirdropTransaction()
    transaction_claim.add_pending_airdrop_ids([id_a, id_b]).add_pending_airdrop_ids([id_c]).add_pending_airdrop_ids([id_d])

    assert transaction_claim.get_pending_airdrop_ids() == [id_a, id_b, id_c, id_d]

def test_add_empty_list_is_noop():
    sender_account = AccountId(0, 0, 9071)
    receiver_account = AccountId(0, 0, 9072)
    first_id = PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9070), None)

    transaction_claim = TokenClaimAirdropTransaction().add_pending_airdrop_id(first_id)
    transaction_claim.add_pending_airdrop_ids([])

    assert transaction_claim.get_pending_airdrop_ids() == [first_id]

def test_from_proto_rejects_too_many():
    sender_account = AccountId(0, 0, 9051)
    receiver_account = AccountId(0, 0, 9052)
    too_many = [PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9050 + i), None)
                for i in range(TokenClaimAirdropTransaction.MAX_IDS + 1)]
    body = TokenClaimAirdropTransactionBody(pending_airdrops=[x._to_proto() for x in too_many])

    with pytest.raises(ValueError):
        TokenClaimAirdropTransaction._from_proto(body)  # pylint: disable=protected-access

def test_from_proto_rejects_duplicates():
    sender_account = AccountId(0, 0, 9061)
    receiver_account = AccountId(0, 0, 9062)
    duplicate = PendingAirdropId(sender_account, receiver_account, TokenId(0, 0, 9060), None)
    body = TokenClaimAirdropTransactionBody(pending_airdrops=[duplicate._to_proto(), duplicate._to_proto()])

    with pytest.raises(ValueError):
        TokenClaimAirdropTransaction._from_proto(body)  # pylint: disable=protected-access

def test_reject_pending_airdrop_with_both_token_and_nft():
    """A PendingAirdropId must not have both token_id and nft_id at the same time"""
    sender = AccountId(0, 0, 9111)
    receiver = AccountId(0, 0, 9112)

    token_id = TokenId(0, 0, 5001)
    nft_id = NftId(TokenId(0, 0, 5002), 1)

    # Expect ValueError because both token_id and nft_id are provided
    with pytest.raises(ValueError, match="Exactly one of 'token_id' or 'nft_id' must be required."):
        PendingAirdropId(sender, receiver, token_id, nft_id)

def test_from_proto_with_invalid_pending_airdrop():
    """_from_proto should raise if proto contains a PendingAirdropId with neither token_id nor nft_id"""
    sender = AccountId(0, 0, 9111)
    receiver = AccountId(0, 0, 9112)

    # Build an invalid PendingAirdropId (both token_id and nft_id are None)
    with pytest.raises(ValueError):
        PendingAirdropId(sender, receiver, token_id=None, nft_id=None)

def test_str_and_repr():
    sender = AccountId(0, 0, 1)
    receiver = AccountId(0, 0, 2)
    tx = TokenClaimAirdropTransaction()
    assert str(tx) == "No pending airdrops in this transaction."
    tx.add_pending_airdrop_id(PendingAirdropId(sender, receiver, TokenId(0,0,10), None))
    assert "Pending Airdrops to claim:" in str(tx)
    assert repr(tx).startswith("TokenClaimAirdropTransaction(")