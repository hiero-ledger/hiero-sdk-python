from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateAccountResponse:
    accountId: str | None = None
    status: str | None = None
