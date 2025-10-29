"""Simple logger module for the Hiero SDK."""

import logging
import sys
from typing import Optional, Union, Sequence
import warnings

from hiero_sdk_python.logger.log_level import LogLevel

# Register custom levels on import
_DISABLED_LEVEL: int = LogLevel.DISABLED.value
_TRACE_LEVEL: int = LogLevel.TRACE.value
logging.addLevelName(_DISABLED_LEVEL, "DISABLED")
logging.addLevelName(_TRACE_LEVEL, "TRACE")


class Logger:
    """Custom logger that wraps Python's logging module.

    This logger sets up custom log levels and provides convenience methods
    for logging at various levels (trace, debug, info, warning, error). It
    wraps a standard :class:`logging.Logger` instance but exposes a simpler
    API tailored for the Hiero SDK.
    """

    def __init__(self, level: Optional[LogLevel] = None, name: Optional[str] = None) -> None:
        """Initialize a new Logger instance.

        Args:
            level (Optional[LogLevel]): The initial log level. Defaults to :class:`LogLevel.TRACE`
                if not provided.
            name (Optional[str]): The logger name. If not provided, defaults to
                ``"hiero_sdk_python"``.

        Returns:
            None
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
        """Set the logging level for this logger.

        Args:
            level (Union[LogLevel, str]): The log level to set. Accepts either a
                :class:`LogLevel` enum or a string representation of the level.

        Returns:
            Logger: The logger instance (self), enabling method chaining.

        Raises:
            ValueError: If a string level is provided that does not correspond to a valid
                :class:`LogLevel`.
        """
        if isinstance(level, str):
            level = LogLevel.from_string(level)
        self.level = level  # type: ignore
        # If level is DISABLED, turn off logging by disabling the logger
        if level == LogLevel.DISABLED:
            self.internal_logger.disabled = True
        else:
            self.internal_logger.disabled = False
        self.internal_logger.setLevel(level.to_python_level())
        return self

    def get_level(self) -> LogLevel:
        """Get the current log level.

        Returns:
            LogLevel: The current logging level for this logger.
        """
        return self.level

    def set_silent(self, is_silent: bool) -> "Logger":
        """Enable or disable silent mode.

        Silent mode disables all logging output for this logger.

        Args:
            is_silent (bool): If ``True``, disable logging; if ``False``, enable logging.

        Returns:
            Logger: The logger instance (self), enabling method chaining.
        """
        if is_silent:
            self.internal_logger.disabled = True
        else:
            self.internal_logger.disabled = False
        return self

    def _format_args(self, message: str, args: Sequence[object]) -> str:
        """Format a log message with additional key–value pairs.

        Given a sequence of objects, interpret them as alternating keys and values
        and append ``"key=value"`` pairs to the message. If an odd number of
        arguments is provided, the message is returned unchanged.

        Args:
            message (str): The log message.
            args (Sequence[object]): A sequence containing an even number of elements,
                interpreted as key–value pairs (e.g. ``("user", "alice", "action", "login")``).

        Returns:
            str: The formatted message with appended key–value pairs, or the original
            message if the arguments sequence is empty or has an odd length.
        """
        if not args or len(args) % 2 != 0:
            return message
        pairs = []
        for i in range(0, len(args), 2):
            pairs.append(f"{args[i]} = {args[i+1]}")
        return f"{message}: {', '.join(pairs)}"

    def trace(self, message: str, *args: object) -> None:
        """Log a message at TRACE level.

        Args:
            message (str): The message to log.
            *args (object): Additional key–value pairs to include in the message.

        Returns:
            None
        """
        if self.internal_logger.isEnabledFor(_TRACE_LEVEL):
            self.internal_logger.log(_TRACE_LEVEL, self._format_args(message, args))

    def debug(self, message: str, *args: object) -> None:
        """Log a message at DEBUG level.

        Args:
            message (str): The message to log.
            *args (object): Additional key–value pairs to include in the message.

        Returns:
            None
        """
        if self.internal_logger.isEnabledFor(LogLevel.DEBUG.value):
            self.internal_logger.debug(self._format_args(message, args))

    def info(self, message: str, *args: object) -> None:
        """Log a message at INFO level.

        Args:
            message (str): The message to log.
            *args (object): Additional key–value pairs to include in the message.

        Returns:
            None
        """
        if self.internal_logger.isEnabledFor(LogLevel.INFO.value):
            self.internal_logger.info(self._format_args(message, args))

    def warning(self, message: str, *args: object) -> None:
        """Log a message at WARNING level.

        Args:
            message (str): The warning message to log.
            *args (object): Additional key–value pairs to include in the message.

        Returns:
            None
        """
        if self.internal_logger.isEnabledFor(LogLevel.WARNING.value):
            self.internal_logger.warning(self._format_args(message, args))

    def warn(self, message: str, *args) -> None:
        """Deprecated legacy method for logging warnings.

        This method is deprecated; use :meth:`warning` instead.

        Args:
            message (str): The warning message.
            *args: Additional key–value pairs to include in the message.

        Returns:
            None

        Deprecated:
            Use :meth:`Logger.warning` instead of this method.
        """
        warnings.warn(
            "Logger.warn() is deprecated; use Logger.warning()", category=FutureWarning, stacklevel=2,
        )
        # Redirects to activate the new method
        self.warning(message, *args)

    def error(self, message: str, *args: object) -> None:
        """Log a message at ERROR level.

        Args:
            message (str): The error message to log.
            *args (object): Additional key–value pairs to include in the message.

        Returns:
            None
        """
        if self.internal_logger.isEnabledFor(LogLevel.ERROR.value):
            self.internal_logger.error(self._format_args(message, args))


def get_logger(
    level: Optional[LogLevel] = None,
    name: Optional[str] = None,
) -> Logger:
    """Create and return a new :class:`Logger` instance.

    This is a legacy convenience wrapper for creating a :class:`Logger`. The
    recommended usage is to pass the ``level`` first and then the ``name``. The
    older signature ``(name, level)`` is deprecated and will be removed in a
    future release.

    Args:
        level (Optional[LogLevel]): The logging level to use for the new logger.
        name (Optional[str]): The name for the new logger.

    Returns:
        Logger: A new :class:`Logger` configured with the provided level and name.

    Raises:
        DeprecationWarning: If the deprecated argument order is used.

    """
    # Legacy method: pass in name, level
    if isinstance(level, str) and isinstance(name, LogLevel):
        warnings.warn(
            "get_logger(name, level) will be deprecated; use get_logger(level, name)",
            DeprecationWarning,
            stacklevel=2,
        )
        # Swaps them to correct sequence to follow init
        level, name = name, level
    return Logger(level, name)
