from __future__ import annotations

import os

from hypothesis import HealthCheck, settings


def load_hypothesis_profile() -> None:
    """Register and load the active Hypothesis profile."""
    settings.register_profile(
        "ci",
        settings(
            derandomize=True,
            max_examples=300,
            deadline=750,
            suppress_health_check=[HealthCheck.too_slow],
        ),
    )
    settings.register_profile(
        "local",
        settings(
            derandomize=False,
            max_examples=1000,
            deadline=None,
        ),
    )

    requested = os.getenv("HYPOTHESIS_PROFILE")
    if requested:
        settings.load_profile(requested)
        return

    settings.load_profile("ci" if os.getenv("CI") else "local")
