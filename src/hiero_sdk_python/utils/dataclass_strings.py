"""
hiero_sdk_python.utils.dataclass_strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides automatic __str__ and __repr__ generation for dataclasses.

This module eliminates manual maintenance of string methods by dynamically
generating them based on dataclass fields. When new fields are added, they
are automatically included in the string representation.

Usage:
    @dataclass
    class MyTokenClass(DataclassStringMixin):
        field1: str
        field2: Optional[int] = None
        
    # Or use the decorator approach:
    @auto_str_repr
    @dataclass
    class MyTokenClass:
        field1: str
        field2: Optional[int] = None
"""

import dataclasses
from typing import Any, Dict


class DataclassStringMixin:
    """
    Mixin class that provides automatic __str__ and __repr__ implementations
    for dataclasses based on their fields.
    
    This mixin automatically generates string representations that include
    all dataclass fields, handling None values and nested objects appropriately.
    
    Features:
        - Zero maintenance: new fields are automatically included
        - Proper None handling for optional fields
        - Clean formatting (multi-line for >3 fields)
        - Enum value formatting (shows EnumClass.VALUE)
        - String quoting for clarity
        - Dictionary conversion for serialization
    
    Example:
        >>> @dataclass
        ... class TokenInfo(DataclassStringMixin):
        ...     token_id: str
        ...     symbol: Optional[str] = None
        ...     balance: int = 0
        ...
        >>> token = TokenInfo("0.0.123", "TEST", 1000)
        >>> str(token)
        "TokenInfo(token_id='0.0.123', symbol='TEST', balance=1000)"
    """
    
    def __str__(self) -> str:
        """Generate string representation dynamically from dataclass fields."""
        if not dataclasses.is_dataclass(self):
            return f"{self.__class__.__name__}()"
        
        field_strings = []
        for field in dataclasses.fields(self.__class__):
            field_value = getattr(self, field.name)
            formatted_value = self._format_field_value(field_value)
            field_strings.append(f"{field.name}={formatted_value}")
        
        # Choose formatting based on number of fields
        class_name = self.__class__.__name__
        if len(field_strings) <= 3:
            return f"{class_name}({', '.join(field_strings)})"
        else:
            fields_str = ",\n    ".join(field_strings)
            return f"{class_name}(\n    {fields_str}\n)"
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return self.__str__()
    
    def _format_field_value(self, value: Any) -> str:
        """Format a field value for string representation."""
        if value is None:
            return "None"
        
        # Handle string values - add quotes for clarity
        if isinstance(value, str):
            return f"'{value}'"
        
        # Handle bytes - show truncated representation
        if isinstance(value, bytes):
            if len(value) > 20:
                return f"b'{value[:20].hex()}...'"
            return f"b'{value.hex()}'"
        
        # Handle enum values - show EnumClass.VALUE format
        if hasattr(value, '__class__') and hasattr(value.__class__, '__mro__'):
            for base in value.__class__.__mro__:
                if base.__name__ == 'Enum':
                    return f"{value.__class__.__name__}.{value.name}"
                    
        # For other objects, use their string representation
        return str(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the dataclass.
        """
        if not dataclasses.is_dataclass(self):
            return {}
        
        result = {}
        for field in dataclasses.fields(self.__class__):
            value = getattr(self, field.name)
            if hasattr(value, 'to_dict'):
                result[field.name] = value.to_dict()
            elif dataclasses.is_dataclass(value) and not isinstance(value, type):
                result[field.name] = dataclasses.asdict(value)
            else:
                result[field.name] = value
        return result


def auto_str_repr(cls):
    """
    Class decorator that automatically adds __str__ and __repr__ methods
    to dataclasses using dynamic field introspection.
    
    This decorator is an alternative to using DataclassStringMixin inheritance.
    
    Usage:
        @auto_str_repr
        @dataclass  
        class TokenClass:
            field1: str
            field2: Optional[int] = None
    
    Args:
        cls: The dataclass to decorate.
        
    Returns:
        The decorated class with __str__ and __repr__ methods.
        
    Raises:
        TypeError: If the decorated class is not a dataclass.
    """
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"@auto_str_repr can only be applied to dataclasses, got {cls.__name__}")
    
    def _format_value(value: Any) -> str:
        """Format a field value for string representation."""
        if value is None:
            return "None"
        if isinstance(value, str):
            return f"'{value}'"
        if isinstance(value, bytes):
            if len(value) > 20:
                return f"b'{value[:20].hex()}...'"
            return f"b'{value.hex()}'"
        if hasattr(value, '__class__') and hasattr(value.__class__, '__mro__'):
            for base in value.__class__.__mro__:
                if base.__name__ == 'Enum':
                    return f"{value.__class__.__name__}.{value.name}"
        return str(value)
    
    def __str__(self) -> str:
        """Generate string representation dynamically from dataclass fields."""
        field_strings = []
        for field in dataclasses.fields(self.__class__):
            field_value = getattr(self, field.name)
            formatted_value = _format_value(field_value)
            field_strings.append(f"{field.name}={formatted_value}")
        
        if len(field_strings) <= 3:
            return f"{cls.__name__}({', '.join(field_strings)})"
        else:
            fields_str = ",\n    ".join(field_strings)
            return f"{cls.__name__}(\n    {fields_str}\n)"
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return self.__str__()
    
    cls.__str__ = __str__
    cls.__repr__ = __repr__
    
    return cls
