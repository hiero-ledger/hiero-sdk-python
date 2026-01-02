"""
Unit tests for the dataclass_strings utility module.

Tests the DataclassStringMixin and auto_str_repr decorator for automatic
__str__ and __repr__ generation in dataclasses.
"""

import pytest
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from hiero_sdk_python.utils.dataclass_strings import DataclassStringMixin, auto_str_repr


class SampleEnum(Enum):
    """Sample enum for testing."""
    VALUE_A = 1
    VALUE_B = 2


@dataclass
class SimpleDataclass(DataclassStringMixin):
    """Simple dataclass with few fields for testing."""
    name: str
    value: int
    active: bool = True


@dataclass
class ComplexDataclass(DataclassStringMixin):
    """Complex dataclass with many fields for testing multi-line output."""
    field1: str
    field2: Optional[int] = None
    field3: Optional[str] = None
    field4: bool = False
    field5: Optional[bytes] = None


@dataclass
class DataclassWithEnum(DataclassStringMixin):
    """Dataclass with enum field for testing."""
    id: str
    status: Optional[SampleEnum] = None


@auto_str_repr
@dataclass
class DecoratedDataclass:
    """Dataclass using decorator approach."""
    name: str
    count: int = 0


class TestDataclassStringMixin:
    """Tests for DataclassStringMixin."""

    def test_simple_dataclass_str(self):
        """Test __str__ for simple dataclass with few fields."""
        obj = SimpleDataclass(name="test", value=42, active=True)
        result = str(obj)
        
        assert "SimpleDataclass(" in result
        assert "name='test'" in result
        assert "value=42" in result
        assert "active=True" in result
        # Should be single line for <= 3 fields
        assert "\n" not in result

    def test_simple_dataclass_repr(self):
        """Test __repr__ returns same as __str__."""
        obj = SimpleDataclass(name="test", value=42)
        assert repr(obj) == str(obj)

    def test_complex_dataclass_multiline(self):
        """Test multi-line output for dataclass with many fields."""
        obj = ComplexDataclass(
            field1="value1",
            field2=100,
            field3="value3",
            field4=True,
            field5=b"bytes"
        )
        result = str(obj)
        
        # Should be multi-line for > 3 fields
        assert "\n" in result
        assert "field1='value1'" in result
        assert "field2=100" in result

    def test_none_handling(self):
        """Test proper handling of None values."""
        obj = ComplexDataclass(field1="only_this")
        result = str(obj)
        
        assert "field1='only_this'" in result
        assert "field2=None" in result
        assert "field3=None" in result

    def test_string_quoting(self):
        """Test that string values are properly quoted."""
        obj = SimpleDataclass(name="hello", value=1)
        result = str(obj)
        
        assert "name='hello'" in result
        # Integer should not be quoted
        assert "value=1" in result

    def test_enum_formatting(self):
        """Test proper enum value formatting."""
        obj = DataclassWithEnum(id="test", status=SampleEnum.VALUE_A)
        result = str(obj)
        
        assert "SampleEnum.VALUE_A" in result

    def test_bytes_formatting(self):
        """Test bytes field formatting."""
        obj = ComplexDataclass(field1="test", field5=b"\x01\x02\x03")
        result = str(obj)
        
        assert "field5=b'" in result

    def test_long_bytes_truncation(self):
        """Test that long bytes are truncated."""
        long_bytes = b"a" * 50
        obj = ComplexDataclass(field1="test", field5=long_bytes)
        result = str(obj)
        
        assert "..." in result

    def test_to_dict(self):
        """Test to_dict() method."""
        obj = SimpleDataclass(name="test", value=42, active=True)
        result = obj.to_dict()
        
        assert result == {"name": "test", "value": 42, "active": True}

    def test_to_dict_with_none(self):
        """Test to_dict() with None values."""
        obj = ComplexDataclass(field1="test")
        result = obj.to_dict()
        
        assert result["field1"] == "test"
        assert result["field2"] is None


class TestAutoStrReprDecorator:
    """Tests for @auto_str_repr decorator."""

    def test_decorated_dataclass_str(self):
        """Test __str__ for decorated dataclass."""
        obj = DecoratedDataclass(name="decorated", count=5)
        result = str(obj)
        
        assert "DecoratedDataclass(" in result
        assert "name='decorated'" in result
        assert "count=5" in result

    def test_decorated_dataclass_repr(self):
        """Test __repr__ for decorated dataclass."""
        obj = DecoratedDataclass(name="test", count=0)
        assert repr(obj) == str(obj)

    def test_decorator_on_non_dataclass_raises(self):
        """Test that decorator raises TypeError on non-dataclass."""
        with pytest.raises(TypeError, match="can only be applied to dataclasses"):
            @auto_str_repr
            class NotADataclass:
                pass


class TestIntegrationWithTokenClasses:
    """Integration tests with actual token classes."""

    def test_token_relationship_str(self):
        """Test TokenRelationship string generation."""
        from hiero_sdk_python.tokens.token_relationship import TokenRelationship
        from hiero_sdk_python.tokens.token_id import TokenId
        
        token_id = TokenId(shard=0, realm=0, num=123)
        relationship = TokenRelationship(
            token_id=token_id,
            symbol="TEST",
            balance=1000
        )
        
        result = str(relationship)
        assert "TokenRelationship(" in result
        assert "0.0.123" in result
        assert "symbol='TEST'" in result
        assert "balance=1000" in result

    def test_token_update_params_str(self):
        """Test TokenUpdateParams string generation."""
        from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateParams
        from hiero_sdk_python.account.account_id import AccountId
        
        params = TokenUpdateParams(
            treasury_account_id=AccountId(0, 0, 456),
            token_name="Updated Token"
        )
        
        result = str(params)
        assert "TokenUpdateParams(" in result
        assert "0.0.456" in result
        assert "token_name='Updated Token'" in result

    def test_token_update_keys_str(self):
        """Test TokenUpdateKeys string generation."""
        from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateKeys
        
        keys = TokenUpdateKeys()
        result = str(keys)
        
        assert "TokenUpdateKeys(" in result
        # All keys should be None
        assert "admin_key=None" in result

    def test_custom_fee_subclass_str(self):
        """Test CustomFixedFee string generation (via inheritance)."""
        from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
        from hiero_sdk_python.account.account_id import AccountId
        
        fee = CustomFixedFee(
            amount=100,
            fee_collector_account_id=AccountId(0, 0, 789)
        )
        
        result = str(fee)
        # CustomFixedFee has its own custom __str__ format
        assert "CustomFixedFee" in result
        # Should include inherited fields and own fields
        assert "100" in result
        assert "0.0.789" in result


class TestDynamicFieldInclusion:
    """Tests verifying that new fields are automatically included."""

    def test_new_fields_automatically_included(self):
        """Verify that adding fields doesn't require __str__ updates."""
        @dataclass
        class ExtendableClass(DataclassStringMixin):
            original_field: str
            # Simulate adding a new field
            new_field: Optional[str] = None
            another_new_field: int = 0
        
        obj = ExtendableClass(
            original_field="original",
            new_field="new",
            another_new_field=42
        )
        
        result = str(obj)
        
        # All fields should be included without any code changes
        assert "original_field='original'" in result
        assert "new_field='new'" in result
        assert "another_new_field=42" in result
