"""
Simple logger module for the Hiero SDK.
"""

import logging
import sys
from typing import Optional, Union, Sequence

from hiero_sdk_python.logger.log_level import LogLevel

# Register custom levels on import
_DISABLED_LEVEL = LogLevel.DISABLED.value
_TRACE_LEVEL = LogLevel.TRACE.value
logging.addLevelName(_DISABLED_LEVEL, "DISABLED")
logging.addLevelName(_TRACE_LEVEL,   "TRACE")

class Logger:
    """
    Custom logger that wraps Python's logging module
    """
    
    def __init__(self, level: Optional[LogLevel] = None, name: Optional[str] = None) -> None:
        """
        Constructor
        
        Args:
            level (LogLevel, optional): the current log level
            name (str, optional): logger name, defaults to class name
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
        """Set log level"""
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
        """Get current log level"""
        return self.level
    
    def set_silent(self, is_silent: bool) -> "Logger":
        """Enable/disable silent mode"""
        if is_silent:
            self.internal_logger.disabled = True
        else:
            self.internal_logger.disabled = False

        return self
    
    def _format_args(self, message: str, args: Sequence[object]) -> str:
        """Format key-value pairs into string"""
        if not args or len(args) % 2 != 0:
            return message
        pairs = []
        for i in range(0, len(args), 2):
            pairs.append(f"{args[i]} = {args[i+1]}")
        return f"{message}: {', '.join(pairs)}"
    
    def trace(self, message: str, *args: object) -> None:
        """Log at TRACE level"""
        if self.internal_logger.isEnabledFor(_TRACE_LEVEL):
            self.internal_logger.log(_TRACE_LEVEL, self._format_args(message, args))
    
    def debug(self, message: str, *args: object) -> None:
        """Log at DEBUG level"""
        if self.internal_logger.isEnabledFor(LogLevel.DEBUG.value):
            self.internal_logger.debug(self._format_args(message, args))
    
    def info(self, message: str, *args: object) -> None:
        """Log at INFO level"""
        if self.internal_logger.isEnabledFor(LogLevel.INFO.value):
            self.internal_logger.info(self._format_args(message, args))

    def warning(self, message: str, *args: object) -> None:
        """Log at WARNING level"""
        if self.internal_logger.isEnabledFor(LogLevel.WARN.value):
            self.internal_logger.warning(self._format_args(message, args))

    def error(self, message: str, *args: object) -> None:
        """Log at ERROR level"""
        if self.internal_logger.isEnabledFor(LogLevel.ERROR.value):
            self.internal_logger.error(self._format_args(message, args))

def get_logger(level: Optional[LogLevel] = None,
               name:  Optional[str]      = None) -> Logger:
    """Get a logger instance."""
    return Logger(level, name)
