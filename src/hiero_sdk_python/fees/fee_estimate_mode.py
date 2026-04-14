"""Enumeration of fee estimation modes. 

Defines the available strategies for calculating fee estimates.
"""

from enum import Enum


class FeeEstimateMode(str, Enum):
    """Supported modes for fee estimation."""

    STATE = "STATE"
    INTRINSIC = "INTRINSIC"