import pytest
from datetime import timezone

from hiero_sdk_python.account.account_info import AccountInfo
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.staking_info import StakingInfo
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_relationship import TokenRelationship
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hapi.services.crypto_get_info_pb2 import CryptoGetInfoResponse
from hiero_sdk_python.hapi.services.basic_types_pb2 import StakingInfo as StakingInfoProto
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp as TimestampProto

pytestmark = pytest.mark.unit


@pytest.fixture
def account_info():
    return AccountInfo(
        account_id=AccountId(0, 0, 100),
        contract_account_id="0.0.100",
        is_deleted=False,
        proxy_received=Hbar.from_tinybars(1000),
        key=PrivateKey.generate_ed25519().public_key(),
        balance=Hbar.from_tinybars(5000000),
        receiver_signature_required=True,
        expiration_time=Timestamp(1625097600, 0),
        auto_renew_period=Duration(7776000),  # 90 days
        token_relationships=[],
        account_memo="Test account memo",
        owned_nfts=5,
    )


@pytest.fixture
def proto_account_info():
    public_key = PrivateKey.generate_ed25519().public_key()
    staking_info_proto = StakingInfoProto(
        decline_reward=True,
        pending_reward=500,
        staked_to_me=1000,
    )
    staking_info_proto.staked_account_id.CopyFrom(AccountId(0, 0, 200)._to_proto())
    staking_info_proto.stake_period_start.CopyFrom(TimestampProto(seconds=1625097600, nanos=0))
    proto = CryptoGetInfoResponse.AccountInfo(
        accountID=AccountId(0, 0, 100)._to_proto(),
        contractAccountID="0.0.100",
        deleted=False,
        proxyReceived=1000,
        key=public_key._to_proto(),
        balance=5000000,
        receiverSigRequired=True,
        expirationTime=Timestamp(1625097600, 0)._to_protobuf(),
        autoRenewPeriod=Duration(7776000)._to_proto(),
        tokenRelationships=[],
        memo="Test account memo",
        ownedNfts=5,
    )
    proto.staking_info.CopyFrom(staking_info_proto)
    return proto


def test_account_info_initialization(account_info):
    """Test the initialization of the AccountInfo class"""
    assert account_info.account_id == AccountId(0, 0, 100)
    assert account_info.contract_account_id == "0.0.100"
    assert account_info.is_deleted is False
    assert account_info.proxy_received.to_tinybars() == 1000
    assert account_info.key is not None
    assert account_info.balance.to_tinybars() == 5000000
    assert account_info.receiver_signature_required is True
    assert account_info.expiration_time == Timestamp(1625097600, 0)
    assert account_info.auto_renew_period == Duration(7776000)
    assert account_info.token_relationships == []
    assert account_info.account_memo == "Test account memo"
    assert account_info.owned_nfts == 5


def test_account_info_default_initialization():
    """Test the default initialization of the AccountInfo class"""
    account_info = AccountInfo()
    assert account_info.account_id is None
    assert account_info.contract_account_id is None
    assert account_info.is_deleted is None
    assert account_info.proxy_received is None
    assert account_info.key is None
    assert account_info.balance is None
    assert account_info.receiver_signature_required is None
    assert account_info.expiration_time is None
    assert account_info.auto_renew_period is None
    assert account_info.token_relationships == []
    assert account_info.account_memo is None
    assert account_info.owned_nfts is None


def test_from_proto(proto_account_info):
    """Test the from_proto method of the AccountInfo class"""
    account_info = AccountInfo._from_proto(proto_account_info)

    assert account_info.account_id == AccountId(0, 0, 100)
    assert account_info.contract_account_id == "0.0.100"
    assert account_info.is_deleted is False
    assert account_info.proxy_received.to_tinybars() == 1000
    assert account_info.key is not None
    assert account_info.balance.to_tinybars() == 5000000
    assert account_info.receiver_signature_required is True
    assert account_info.expiration_time == Timestamp(1625097600, 0)
    assert account_info.auto_renew_period == Duration(7776000)
    assert account_info.token_relationships == []
    assert account_info.account_memo == "Test account memo"
    assert account_info.owned_nfts == 5
    assert account_info.staking_info is not None
    assert account_info.staking_info.decline_staking_reward is True
    assert account_info.staking_info.pending_reward.to_tinybars() == 500
    assert account_info.staking_info.staked_to_me.to_tinybars() == 1000
    assert account_info.staking_info.staked_account_id == AccountId(0, 0, 200)
    assert account_info.staking_info.stake_period_start is not None
    assert account_info.staking_info.stake_period_start.tzinfo == timezone.utc


def test_from_proto_with_token_relationships():
    """Test the from_proto method of the AccountInfo class with token relationships"""
    # Create a minimal proto without a key to avoid the key parsing issue
    public_key = PrivateKey.generate_ed25519().public_key()
    proto = CryptoGetInfoResponse.AccountInfo(
        accountID=AccountId(0, 0, 100)._to_proto(),
        key=public_key._to_proto(),
        balance=5000000,
        tokenRelationships=[],
    )

    account_info = AccountInfo._from_proto(proto)
    assert account_info.account_id == AccountId(0, 0, 100)
    assert account_info.balance.to_tinybars() == 5000000
    assert account_info.token_relationships == []


def test_from_proto_none_raises_error():
    """Test the from_proto method of the AccountInfo class with a None proto"""
    with pytest.raises(ValueError, match="Account info proto is None"):
        AccountInfo._from_proto(None)


def test_to_proto(account_info):
    """Test the to_proto method of the AccountInfo class"""
    from datetime import datetime, timezone as tz
    account_info.staking_info = StakingInfo(
        pending_reward=Hbar.from_tinybars(500),
        staked_to_me=Hbar.from_tinybars(1000),
        stake_period_start=datetime.fromtimestamp(1625097600, tz=tz.utc),
        staked_account_id=AccountId(0, 0, 200),
        decline_staking_reward=True,
    )
    proto = account_info._to_proto()

    assert proto.accountID == AccountId(0, 0, 100)._to_proto()
    assert proto.contractAccountID == "0.0.100"
    assert proto.deleted is False
    assert proto.proxyReceived == 1000
    assert proto.key is not None
    assert proto.balance == 5000000
    assert proto.receiverSigRequired is True
    assert proto.expirationTime == Timestamp(1625097600, 0)._to_protobuf()
    assert proto.autoRenewPeriod == Duration(7776000)._to_proto()
    assert proto.tokenRelationships == []
    assert proto.memo == "Test account memo"
    assert proto.ownedNfts == 5
    assert proto.HasField('staking_info')
    assert proto.staking_info.decline_reward is True
    assert proto.staking_info.pending_reward == 500
    assert proto.staking_info.staked_to_me == 1000
    assert proto.staking_info.HasField('staked_account_id')
    assert proto.staking_info.staked_account_id == AccountId(0, 0, 200)._to_proto()


def test_to_proto_with_none_values():
    """Test the to_proto method of the AccountInfo class with none values"""
    account_info = AccountInfo()
    proto = account_info._to_proto()

    # Protobuf has default values, so we check the proto structure exists
    assert hasattr(proto, "accountID")
    assert proto.contractAccountID == ""  # Empty string is default for protobuf
    assert proto.deleted is False  # False is default for protobuf bool
    assert proto.proxyReceived == 0  # 0 is default for protobuf int when None is passed
    assert hasattr(proto, "key")
    assert proto.balance == 0  # 0 is default for protobuf int when None is passed
    assert proto.receiverSigRequired is False  # False is default for protobuf bool
    assert hasattr(proto, "expirationTime")
    assert hasattr(proto, "autoRenewPeriod")
    assert proto.tokenRelationships == []
    assert proto.memo == ""  # Empty string is default for protobuf
    assert proto.ownedNfts == 0  # 0 is default for protobuf int


def test_proto_conversion(account_info):
    """Test converting AccountInfo to proto and back preserves data"""
    proto = account_info._to_proto()
    converted_account_info = AccountInfo._from_proto(proto)

    assert converted_account_info.account_id == account_info.account_id
    assert (
        converted_account_info.contract_account_id == account_info.contract_account_id
    )
    assert converted_account_info.is_deleted == account_info.is_deleted
    assert (
        converted_account_info.proxy_received.to_tinybars()
        == account_info.proxy_received.to_tinybars()
    )
    assert (
        converted_account_info.balance.to_tinybars()
        == account_info.balance.to_tinybars()
    )
    assert (
        converted_account_info.receiver_signature_required
        == account_info.receiver_signature_required
    )
    assert converted_account_info.expiration_time == account_info.expiration_time
    assert converted_account_info.auto_renew_period == account_info.auto_renew_period
    assert (
        converted_account_info.token_relationships == account_info.token_relationships
    )
    assert converted_account_info.account_memo == account_info.account_memo
    assert converted_account_info.owned_nfts == account_info.owned_nfts
    assert converted_account_info.staking_info == account_info.staking_info


def test_proto_conversion_with_staking_info():
    """Test converting AccountInfo with staking_info to proto and back preserves data"""
    from datetime import datetime, timezone as tz
    original = AccountInfo(
        account_id=AccountId(0, 0, 100),
        balance=Hbar.from_tinybars(5000000),
        key=PrivateKey.generate_ed25519().public_key(),
        staking_info=StakingInfo(
            pending_reward=Hbar.from_tinybars(300),
            staked_to_me=Hbar.from_tinybars(700),
            stake_period_start=datetime.fromtimestamp(1625097600, tz=tz.utc),
            staked_account_id=AccountId(0, 0, 200),
            decline_staking_reward=True,
        ),
    )
    proto = original._to_proto()
    restored = AccountInfo._from_proto(proto)

    assert restored.staking_info is not None
    assert restored.staking_info.decline_staking_reward is True
    assert restored.staking_info.pending_reward.to_tinybars() == 300
    assert restored.staking_info.staked_to_me.to_tinybars() == 700
    assert restored.staking_info.staked_account_id == AccountId(0, 0, 200)
    assert restored.staking_info.stake_period_start is not None


def test_str_and_repr(account_info):
    """Test the __str__ and __repr__ methods"""
    info_str = str(account_info)
    info_repr = repr(account_info)

    # __str__ checks (User-friendly output)
    assert "Account ID: 0.0.100" in info_str
    assert "Contract Account ID: 0.0.100" in info_str
    assert "Balance: 0.05000000 ℏ" in info_str
    assert "Memo: Test account memo" in info_str

    # __repr__ checks (Debug output)
    assert info_repr.startswith("AccountInfo(")
    assert "account_id=AccountId(shard=0, realm=0, num=100" in info_repr
    assert "contract_account_id='0.0.100'" in info_repr
    assert "account_memo='Test account memo'" in info_repr


# ---------------------------------------------------------------------------
# StakingInfo (account.staking_info) unit tests
# ---------------------------------------------------------------------------

class TestStakingInfo:
    """Unit tests for the account.staking_info.StakingInfo wrapper."""

    def test_from_proto_none_raises(self):
        """_from_proto(None) should raise ValueError."""
        with pytest.raises(ValueError, match="Staking info proto is None"):
            StakingInfo._from_proto(None)

    def test_from_proto_staked_node_id(self):
        """_from_proto should populate staked_node_id from the oneof field."""
        from hiero_sdk_python.hapi.services.basic_types_pb2 import StakingInfo as StakingInfoProto
        proto = StakingInfoProto(decline_reward=False, pending_reward=0, staked_to_me=0)
        proto.staked_node_id = 5
        si = StakingInfo._from_proto(proto)
        assert si.staked_node_id == 5
        assert si.staked_account_id is None

    def test_to_proto_staked_node_id(self):
        """_to_proto should set staked_node_id on the proto."""
        si = StakingInfo(staked_node_id=7, decline_staking_reward=False)
        proto = si._to_proto()
        assert proto.staked_node_id == 7
        assert not proto.HasField("staked_account_id")

    def test_to_proto_oneof_raises(self):
        """_to_proto should raise ValueError if both staked fields are set."""
        si = StakingInfo(
            staked_account_id=AccountId(0, 0, 1),
            staked_node_id=2,
        )
        with pytest.raises(ValueError, match="mutually exclusive"):
            si._to_proto()

    def test_to_proto_all_fields(self):
        """_to_proto should serialize all optional fields correctly."""
        from datetime import datetime, timezone as tz
        si = StakingInfo(
            pending_reward=Hbar.from_tinybars(100),
            staked_to_me=Hbar.from_tinybars(200),
            stake_period_start=datetime.fromtimestamp(1625097600, tz=tz.utc),
            staked_account_id=AccountId(0, 0, 50),
            decline_staking_reward=True,
        )
        proto = si._to_proto()
        assert proto.pending_reward == 100
        assert proto.staked_to_me == 200
        assert proto.decline_reward is True
        assert proto.HasField("stake_period_start")
        assert proto.stake_period_start.seconds == 1625097600
        assert proto.HasField("staked_account_id")

    def test_to_proto_none_fields(self):
        """_to_proto with all-None fields should return empty proto."""
        si = StakingInfo()
        proto = si._to_proto()
        assert proto.pending_reward == 0
        assert proto.staked_to_me == 0
        assert proto.decline_reward is False

    def test_str_contains_set_fields(self):
        """__str__ should include only set fields."""
        si = StakingInfo(staked_node_id=3, decline_staking_reward=True)
        s = str(si)
        assert "Staked Node ID: 3" in s
        assert "Decline Staking Reward: True" in s
        assert "Pending Reward" not in s

    def test_str_with_account_id(self):
        """__str__ should include staked_account_id when set."""
        si = StakingInfo(staked_account_id=AccountId(0, 0, 99))
        s = str(si)
        assert "Staked Account ID" in s

    def test_repr(self):
        """__repr__ should include all field names."""
        si = StakingInfo(staked_node_id=1)
        r = repr(si)
        assert r.startswith("StakingInfo(")
        assert "staked_node_id=1" in r
        assert "pending_reward=" in r
        assert "decline_staking_reward=" in r


# ---------------------------------------------------------------------------
# Deprecated flat property tests on AccountInfo
# ---------------------------------------------------------------------------

class TestDeprecatedProperties:
    """Ensure the deprecated flat staking properties still work with warnings."""

    def _make_info(self):
        si = StakingInfo(
            staked_account_id=AccountId(0, 0, 10),
            staked_node_id=None,
            decline_staking_reward=True,
        )
        return AccountInfo(staking_info=si)

    def test_staked_account_id_deprecated(self):
        import warnings
        info = self._make_info()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            val = info.staked_account_id
        assert val == AccountId(0, 0, 10)
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "staked_account_id" in str(w[0].message)

    def test_staked_node_id_deprecated(self):
        import warnings
        info = self._make_info()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            val = info.staked_node_id
        assert val is None
        assert issubclass(w[0].category, DeprecationWarning)

    def test_decline_staking_reward_deprecated(self):
        import warnings
        info = self._make_info()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            val = info.decline_staking_reward
        assert val is True
        assert issubclass(w[0].category, DeprecationWarning)

    def test_deprecated_properties_return_none_without_staking_info(self):
        import warnings
        info = AccountInfo()
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            assert info.staked_account_id is None
            assert info.staked_node_id is None
            assert info.decline_staking_reward is None

