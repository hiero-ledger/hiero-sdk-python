from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KeyGenerationResponse:
    key: str = None
    privateKeys: list[str] = field(default_factory=list)
