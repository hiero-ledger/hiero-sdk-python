from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SetupResponse:
    message: str = None
    status: str = None

    def __init__(self, message: str):
        self.message = message
        self.status = "SUCCESS"
