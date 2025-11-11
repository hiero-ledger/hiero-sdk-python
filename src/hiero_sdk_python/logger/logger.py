"""
Simple logger module for the Hiero SDK.

This module provides a custom wrapper around Python's standard logging module,
adding support for custom log levels (TRACE, DISABLED) and simplifying log
configuration within the SDK.
"""

import logging
import sys
from typing import Optional, Union, Sequence
from hiero_sdk_python.logger.log_level import LogLevel

# Register custom levels on import
_DISABLED_LEVEL = LogLevel.DISABLED.value
_TRACE_LEVEL = LogLevel.TRACE.value
logging.addLevelName(_DISABLED_LEVEL, "DISABLED")
logging.addLevelName(_TRACE_LEVEL, "TRACE")

class Logger:
    """
    Custom logger that wraps Python's logging module for Hiero SDK use.

    This class handles configuration, formatting, and logging operations across
    various log levels, including custom SDK levels (TRACE, DISABLED).
    """
    
    def __init__(self, level: Optional[LogLevel] = None, name: Optional[str] = None) -> None:
        """
        Initializes the Logger instance for the Hiero SDK.
        
        Args:
            level (LogLevel, optional): The current minimum log level. Defaults to TRACE.
            name (str, optional): The logger name. Defaults to "hiero_sdk_python".
        """
        
        # Get logger name
        if name is None:
            name = "hiero_sdk_python"
        # Get logger and set level
        self.name: str = name
        self.internal_logger: logging.Logger = logging.getLogger(name)
        self.level: LogLevel = level or LogLevel.TRACE
        
        # Add handler if needed
        if not self.internal_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            # Configure formatter to structure log output with logger name, timestamp, level and message
            formatter = logging.Formatter('[%(name)s] [%(asctime)s] %(levelname)-8s %(message)s')
            handler.setFormatter(formatter)
            self.internal_logger.addHandler(handler)
        
        # Set level
        self.set_level(self.level)
    
    def set_level(self, level: Union[LogLevel, str]) -> "Logger":
        """
        Sets the current logging level for the SDK logger.

        Args:
            level (Union[LogLevel, str]): The new minimum log level. Can be a LogLevel enum or a string (e.g., "INFO").

        Returns:
            Logger: The current Logger instance (for chaining).
        """
        if isinstance(level, str):
            level = LogLevel.from_string(level)
            
        self.level = level
        
        # If level is DISABLED, turn off logging by disabling the logger
        if level == LogLevel.DISABLED:
            self.internal_logger.disabled = True
        else:
            self.internal_logger.disabled = False
        
        self.internal_logger.setLevel(level.to_python_level())
        return self
    
    def get_level(self) -> LogLevel:
        """
        Retrieves the current logging level set for the SDK logger.

        Returns:
            LogLevel: The current minimum logging level.
        """
        return self.level
    
    def set_silent(self, is_silent: bool) -> "Logger":
        """
        Enables or disables silent mode (disabling all logging output).

        Args:
            is_silent (bool): If True, disables logging entirely. If False, logging is re-enabled.

        Returns:
            Logger: The current Logger instance (for chaining).
        """
        if is_silent:
            self.internal_logger.disabled = True
        else:
            self.internal_logger.disabled = False

        return self
    
    def _format_args(self, message: str, args: Sequence[object]) -> str:
        """
        Formats a message with optional key-value pairs into a clean string format.

        Args:
            message (str): The main log message.
            args (Sequence[object]): A sequence of objects supplied as alternating
                keys and values (e.g., "key1", value1, "key2", value2).

        Returns:
            str: The formatted log string, or just the original message if arguments
                are not supplied correctly (not an even number).
        """
        if not args or len(args) % 2 != 0:
            return message
        pairs = []
        for i in range(0, len(args), 2):
            pairs.append(f"{args[i]} = {args[i+1]}")
        return f"{message}: {', '.join(pairs)}"
    
    def trace(self, message: str, *args: object) -> None:
        """
        Logs a message at the TRACE level (lowest verbosity).

        Args:
            message (str): The main log message.
            *args (object): Optional key-value pairs (key, value, key, value, ...) to be appended to the message.
        """
        if self.internal_logger.isEnabledFor(_TRACE_LEVEL):
            self.internal_logger.log(_TRACE_LEVEL, self._format_args(message, args))
    
    def debug(self, message: str, *args: object) -> None:
        """
        Logs a message at the DEBUG level.

        Args:
            message (str): The main log message.
            *args (object): Optional key-value pairs (key, value, key, value, ...) to be appended to the message.
        """
        if self.internal_logger.isEnabledFor(LogLevel.DEBUG.value):
            self.internal_logger.debug(self._format_args(message, args))
    
    def info(self, message: str, *args: object) -> None:
        """
        Logs a message at the INFO level.

        Args:
            message (str): The main log message.
            *args (object): Optional key-value pairs (key, value, key, value, ...) to be appended to the message.
        """
        if self.internal_logger.isEnabledFor(LogLevel.INFO.value):
            self.internal_logger.info(self._format_args(message, args))

    def warning(self, message: str, *args: object) -> None:
        """
        Logs a message at the WARNING level.

        Args:
            message (str): The main log message.
            *args (object): Optional key-value pairs (key, value, key, value, ...) to be appended to the message.
        """
        if self.internal_logger.isEnabledFor(LogLevel.WARNING.value):
            self.internal_logger.warning(self._format_args(message, args))

    def error(self, message: str, *args: object) -> None:
        """
        Logs a message at the ERROR level.

        Args:
            message (str): The main log message.
            *args (object): Optional key-value pairs (key, value, key, value, ...) to be appended to the message.
        """
        if self.internal_logger.isEnabledFor(LogLevel.ERROR.value):
            self.internal_logger.error(self._format_args(message, args))

def get_logger(
    level: Optional[LogLevel] = None,
    name: Optional[str] = None,
) -> Logger:
    return Logger(level, name)
