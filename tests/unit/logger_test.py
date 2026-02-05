import os
import pytest
from src.hiero_sdk_python.logger.logger import Logger
from src.hiero_sdk_python.logger.log_level import LogLevel

pytestmark = pytest.mark.unit


def test_set_level():
    """Test that changing log level affects what will be logged."""
    logger = Logger(LogLevel.DEBUG, "test_logger")
    logger.set_level(LogLevel.ERROR)
    assert logger.level == LogLevel.ERROR


def test_get_level():
    """Test getting the current log level."""
    logger = Logger(level=LogLevel.DEBUG)
    assert logger.get_level() == LogLevel.DEBUG

    logger.set_level(LogLevel.ERROR)
    assert logger.get_level() == LogLevel.ERROR


def test_logger_creation():
    logger = Logger(LogLevel.DEBUG, "test_logger")
    assert logger.name == "test_logger"
    assert logger.level == LogLevel.DEBUG


def test_logger_creation_from_env():
    os.environ["LOG_LEVEL"] = "CRITICAL"
    logger = Logger(LogLevel.from_env())
    assert logger.level == LogLevel.CRITICAL


def test_logger_output(capsys):
    """Test that logger outputs the expected messages to stdout.

    This test uses pytest's capsys fixture to capture the actual log output,
    allowing verification of the exact content written to stdout by the logger.
    """
    # Create a logger that logs to the captured stdout with UNIQUE name
    logger = Logger(LogLevel.TRACE, "test_logger_output")

    # Log messages at different levels with key-value pairs
    logger.trace("trace message", "traceKey", "traceValue")
    logger.debug("debug message", "debugKey", "debugValue")
    logger.info("info message", "infoKey", "infoValue")
    logger.warning("warning message", "warningKey", "warningValue")
    logger.error("error message", "errorKey", "errorValue")

    # Get the captured output
    captured = capsys.readouterr()

    # Verify that each message appears in the output
    assert "trace message: traceKey = traceValue" in captured.out
    assert "debug message: debugKey = debugValue" in captured.out
    assert "info message: infoKey = infoValue" in captured.out
    assert "warning message: warningKey = warningValue" in captured.out
    assert "error message: errorKey = errorValue" in captured.out
    # Test silent mode
    logger.set_silent(True)
    logger.error("this should not appear")
    captured = capsys.readouterr()
    assert captured.out == ""

    # Test re-enabling logging
    logger.set_silent(False)
    logger.info("this should appear")
    captured = capsys.readouterr()
    assert "this should appear" in captured.out


def test_logger_respects_level(capsys):
    """Test that logger only outputs messages at or above its level.

    Uses pytest's capsys fixture to verify that log filtering works correctly
    by examining which messages actually appear in the captured output based on
    the configured log level.
    """
    # Create a logger that logs to the captured stdout with UNIQUE name
    logger = Logger(LogLevel.INFO, "test_logger_respects_level")

    # These should not be logged
    logger.trace("trace message")
    logger.debug("debug message")

    # These should be logged
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    # Get the captured output
    captured = capsys.readouterr()
    logger.info(captured.out)

    # Check that appropriate messages were logged or not logged
    assert "trace message" not in captured.out
    assert "debug message" not in captured.out
    assert "info message" in captured.out
    assert "warning message" in captured.out
    assert "error message" in captured.out
