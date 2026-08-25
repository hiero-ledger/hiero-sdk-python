from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateFileResponse:
    """Response payload for createFile."""

    fileId: str | None = None
    status: str | None = None


@dataclass
class GetFileContentsResponse:
    """Response payload for getFileContents."""

    contents: str | None = None
