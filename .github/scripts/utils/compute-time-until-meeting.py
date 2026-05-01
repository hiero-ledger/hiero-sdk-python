"""Compute human-readable time remaining until a meeting.

Usage:
    python3 compute-time-until-meeting.py <MEETING_HOUR> [MOCK_TIME]

Arguments:
    MEETING_HOUR  Meeting hour in UTC (0-23)
    MOCK_TIME     Optional mock time in HH:MM or HH:MM:SS format (for testing)

Output:
    A human-readable string like "3 hours and 7 minutes" printed to stdout.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from math import ceil


def _parse_mock_time(mock_time):
    """Parse a mock time string into (hour, minute, second) components."""
    parts = mock_time.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("MOCK_TIME must be in HH:MM or HH:MM:SS format.")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    except ValueError as exc:
        raise ValueError("MOCK_TIME must contain only numeric components.") from exc

    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise ValueError("MOCK_TIME values must be within valid UTC ranges.")
    return hour, minute, second


def _pluralize(value, singular):
    """Return singular or plural form based on value."""
    return singular if value == 1 else f"{singular}s"


def _format_duration(hours, minutes):
    """Format hours and minutes into a human-readable string."""
    if hours > 0 and minutes > 0:
        return f"{hours} {_pluralize(hours, 'hour')} and {minutes} {_pluralize(minutes, 'minute')}"
    if hours > 0:
        return f"{hours} {_pluralize(hours, 'hour')}"
    return f"{minutes} {_pluralize(minutes, 'minute')}"


def compute_time_until_meeting(meeting_hour, mock_time=None):
    """Compute the human-readable time remaining until the meeting.

    Args:
        meeting_hour: The meeting hour in UTC (0-23).
        mock_time: Optional mock time string in "HH:MM" or "HH:MM:SS" format.

    Returns:
        A string like "3 hours and 7 minutes".
    """
    now = datetime.now(timezone.utc)

    if mock_time is not None:
        hour, minute, second = _parse_mock_time(mock_time)
        now = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

    meeting = now.replace(hour=meeting_hour, minute=0, second=0, microsecond=0)

    # If the computed meeting time is more than 12 hours in the past,
    # it means the cron job is running late the day before the meeting.
    if (meeting - now).total_seconds() < -12 * 3600:
        meeting += timedelta(days=1)

    diff = meeting - now
    if diff.total_seconds() <= 0:
        return "has already started"

    total_minutes = max(ceil(diff.total_seconds() / 60), 0)

    return _format_duration(total_minutes // 60, total_minutes % 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 compute-time-until-meeting.py <MEETING_HOUR> [MOCK_TIME]", file=sys.stderr)
        sys.exit(1)

    try:
        meeting_hour = int(sys.argv[1])
        if not 0 <= meeting_hour <= 23:
            raise ValueError("MEETING_HOUR must be an integer between 0 and 23.")
        mock_time = sys.argv[2] if len(sys.argv) > 2 else None
        print(compute_time_until_meeting(meeting_hour, mock_time))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
