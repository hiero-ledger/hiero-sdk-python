from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateFileResponse:
    """Response payload for createFile."""

    fileId: str | None = None
    status: str | None = None


@dataclass
class DeleteFileResponse:
    """Response payload for deleteFile."""

    status: str | None = None
