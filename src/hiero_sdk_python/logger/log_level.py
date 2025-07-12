"""
Log level module for the Hiero SDK.

This module defines the log levels used throughout the SDK.
"""

import os
from enum import IntEnum

class LogLevel(IntEnum):
    """
    Enumeration of log levels
    """
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    DISABLED = 60

    #Old warn method will be depreciated
    WARN = WARNING

    def to_python_level(self) -> int:
        """Convert to Python's logging level
        
        Returns:
            int: The Python logging level
        """
        return self.value

    @classmethod
    def from_string(cls, level_str: str) -> "LogLevel":
        """Convert a string to a LogLevel
        
        Args:
            level_str: The string to convert
        
        Returns:
            LogLevel: The LogLevel enum value
        """
        if level_str is None:
            return cls.ERROR

        try:
            return cls[level_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid log level: {level_str}")
        
    @classmethod
    def from_env(cls) -> "LogLevel":
        """
        Get log level from environment variable
        
        Returns:
            LogLevel: The LogLevel enum value
        """
        level_str = os.getenv('LOG_LEVEL')
        return cls.from_string(level_str)