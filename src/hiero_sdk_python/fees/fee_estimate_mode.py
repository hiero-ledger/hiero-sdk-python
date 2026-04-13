"""Enumeration of fee estimation modes.

Defines the available strategies for calculating fee estimates.
"""

from enum import Enum

class FeeEstimateMode(str, Enum):
    STATE = "STATE"
    INTRINSIC = "INTRINSIC"