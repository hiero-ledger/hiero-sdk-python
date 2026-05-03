"""Unit tests for compute-time-until-meeting.py helper.

Run with:
    python3 -m unittest .github/scripts/tests/test_compute_time_until_meeting.py -v

Or from the tests directory:
    python3 -m unittest test_compute_time_until_meeting -v
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

# Add the utils directory to sys.path so we can import the helper
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))

from importlib import import_module

# Import the module using importlib since the filename has hyphens
_mod = import_module("compute-time-until-meeting")
compute_time_until_meeting = _mod.compute_time_until_meeting
_format_duration = _mod._format_duration
_pluralize = _mod._pluralize
_parse_mock_time = _mod._parse_mock_time


class TestComputeTimeUntilMeeting(unittest.TestCase):
    """Tests for the compute_time_until_meeting function."""

    def test_standard_4_hours_before(self):
        """Standard case: 10:00 run for 14:00 meeting = 4 hours."""
        result = compute_time_until_meeting("today", 14, "10:00")
        self.assertEqual(result, "4 hours")

    def test_delayed_run_3h7m(self):
        """Delayed run: 10:53 run for 14:00 meeting = 3 hours and 7 minutes."""
        result = compute_time_until_meeting("today", 14, "10:53")
        self.assertEqual(result, "3 hours and 7 minutes")

    def test_just_minutes_remaining(self):
        """Only minutes left: 13:45 run for 14:00 meeting = 15 minutes."""
        result = compute_time_until_meeting("today", 14, "13:45")
        self.assertEqual(result, "15 minutes")

    def test_exact_whole_hours(self):
        """Exact hours: 12:00 run for 14:00 meeting = 2 hours."""
        result = compute_time_until_meeting("today", 14, "12:00")
        self.assertEqual(result, "2 hours")

    def test_past_meeting_time(self):
        """Past meeting: 15:00 run for 14:00 meeting = has already started."""
        result = compute_time_until_meeting("today", 14, "15:00")
        self.assertEqual(result, "has already started")

    def test_singular_hour(self):
        """Singular: 13:00 run for 14:00 meeting = 1 hour (not '1 hours')."""
        result = compute_time_until_meeting("today", 14, "13:00")
        self.assertEqual(result, "1 hour")

    def test_singular_minute(self):
        """Singular: 12:59 run for 14:00 meeting = 1 hour and 1 minute."""
        result = compute_time_until_meeting("today", 14, "12:59")
        self.assertEqual(result, "1 hour and 1 minute")

    def test_different_meeting_hour(self):
        """Different hour: 08:30 run for 12:00 meeting = 3 hours and 30 minutes."""
        result = compute_time_until_meeting("today", 12, "08:30")
        self.assertEqual(result, "3 hours and 30 minutes")

    def test_rounding_with_seconds(self):
        """Seconds should ceil: 10:53:30 run for 14:00 = 3 hours and 7 minutes."""
        result = compute_time_until_meeting("today", 14, "10:53:30")
        self.assertEqual(result, "3 hours and 7 minutes")

    def test_seconds_just_past_boundary(self):
        """Just past minute: 13:00:01 run for 14:00 rounds up to 1 hour."""
        result = compute_time_until_meeting("today", 14, "13:00:01")
        self.assertEqual(result, "1 hour")

    def test_utc_day_boundary(self):
        """Cross-day: 23:00 run for 02:00 next day = 3 hours."""
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        result = compute_time_until_meeting(tomorrow, 2, "23:00")
        self.assertEqual(result, "3 hours")

    def test_same_day_morning_meeting_already_passed(self):
        """Same-day early hour: 10:00 run with MEETING_HOUR=2 = has already started.

        This is the key edge case that the old -12h rollover heuristic got wrong.
        """
        result = compute_time_until_meeting("today", 2, "10:00")
        self.assertEqual(result, "has already started")

    def test_explicit_date(self):
        """Explicit date: passing a specific YYYY-MM-DD date works correctly."""
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        result = compute_time_until_meeting(tomorrow, 14, "10:00")
        self.assertIn("hour", result)

    def test_meeting_at_exact_time(self):
        """Exact meeting time: 14:00 run for 14:00 meeting = has already started."""
        result = compute_time_until_meeting("today", 14, "14:00")
        self.assertEqual(result, "has already started")

    def test_invalid_date_format(self):
        """Invalid date format raises ValueError."""
        with self.assertRaises(ValueError):
            compute_time_until_meeting("not-a-date", 14, "10:00")

    def test_midnight_meeting_hour_0(self):
        """Edge of range: MEETING_HOUR=0, run at 22:00 yesterday = 2 hours."""
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        result = compute_time_until_meeting(tomorrow, 0, "22:00")
        self.assertEqual(result, "2 hours")

    def test_late_meeting_hour_23(self):
        """Edge of range: MEETING_HOUR=23, run at 20:00 = 3 hours."""
        result = compute_time_until_meeting("today", 23, "20:00")
        self.assertEqual(result, "3 hours")

    def test_one_minute_remaining(self):
        """Edge: 13:59 run for 14:00 meeting = 1 minute."""
        result = compute_time_until_meeting("today", 14, "13:59")
        self.assertEqual(result, "1 minute")

    def test_cli_invocation(self):
        """CLI: calling via subprocess produces expected output."""
        import subprocess
        helper_path = os.path.join(os.path.dirname(__file__), "..", "utils", "compute-time-until-meeting.py")
        result = subprocess.run(
            ["python3", helper_path, "today", "14", "10:00"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "4 hours")

    def test_cli_missing_args(self):
        """CLI: missing arguments should exit with error."""
        import subprocess
        helper_path = os.path.join(os.path.dirname(__file__), "..", "utils", "compute-time-until-meeting.py")
        result = subprocess.run(
            ["python3", helper_path],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)


class TestFormatDuration(unittest.TestCase):
    """Tests for the _format_duration helper."""

    def test_hours_and_minutes(self):
        self.assertEqual(_format_duration(3, 7), "3 hours and 7 minutes")

    def test_only_hours(self):
        self.assertEqual(_format_duration(4, 0), "4 hours")

    def test_only_minutes(self):
        self.assertEqual(_format_duration(0, 15), "15 minutes")

    def test_singular_hour(self):
        self.assertEqual(_format_duration(1, 0), "1 hour")

    def test_singular_minute(self):
        self.assertEqual(_format_duration(0, 1), "1 minute")

    def test_singular_both(self):
        self.assertEqual(_format_duration(1, 1), "1 hour and 1 minute")


class TestPluralize(unittest.TestCase):
    """Tests for the _pluralize helper."""

    def test_singular(self):
        self.assertEqual(_pluralize(1, "hour"), "hour")

    def test_plural(self):
        self.assertEqual(_pluralize(2, "hour"), "hours")

    def test_zero_is_plural(self):
        self.assertEqual(_pluralize(0, "minute"), "minutes")


class TestParseMockTime(unittest.TestCase):
    """Tests for the _parse_mock_time helper."""

    def test_valid_hh_mm(self):
        self.assertEqual(_parse_mock_time("10:30"), (10, 30, 0))

    def test_valid_hh_mm_ss(self):
        self.assertEqual(_parse_mock_time("10:30:45"), (10, 30, 45))

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            _parse_mock_time("10")

    def test_non_numeric(self):
        with self.assertRaises(ValueError):
            _parse_mock_time("ab:cd")

    def test_out_of_range_hour(self):
        with self.assertRaises(ValueError):
            _parse_mock_time("25:00")

    def test_out_of_range_minute(self):
        with self.assertRaises(ValueError):
            _parse_mock_time("10:60")


if __name__ == "__main__":
    unittest.main()
