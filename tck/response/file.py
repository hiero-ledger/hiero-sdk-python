from __future__ import annotations

from dataclasses import dataclass, field

from tck.response.base import StatusOnlyResponse


@dataclass
class CreateFileResponse:
    """Response payload for createFile."""

    fileId: str | None = None
    status: str | None = None


@dataclass
class UpdateFileResponse(StatusOnlyResponse):
    """Response payload for updateFile."""


@dataclass
class GetFileContentsResponse:
    """Response payload for getFileContents."""

    contents: str | None = None


@dataclass
class GetFileInfoResponse:
    fileId: str | None = None
    size: str | None = None
    expirationTime: str | None = None
    isDeleted: bool | None = None
    keys: list[str] = field(default_factory=list)
    memo: str | None = None
    ledgerId: str | None = None
