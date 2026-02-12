"""
Pydantic response models for file APIs.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FilePostOut(BaseModel):
    """
    Public representation of a persisted file post.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    caption: str | None
    url: str
    file_type: str
    file_name: str
    created_at: datetime | None


class UploadResponse(BaseModel):
    """
    Response body returned after a successful upload.
    """

    message: str
    post: FilePostOut


class FeedResponse(BaseModel):
    """
    Paginated feed response for file posts.
    """

    posts: list[FilePostOut]
    limit: int
    offset: int
    total: int

