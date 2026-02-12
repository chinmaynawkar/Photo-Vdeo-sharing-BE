"""
File upload and feed API endpoints.

This module applies production-style API patterns:
- typed responses
- input validation
- paginated feed
- safe error responses with server-side logging
"""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import (
    ALLOWED_UPLOAD_CONTENT_TYPES,
    MAX_UPLOAD_SIZE_BYTES,
    UPLOAD_DIR,
)
from app.db.db import get_async_session
from app.db.db_model import Post
from app.schemas.file import FeedResponse, FilePostOut, UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _ensure_upload_dir() -> None:
    """Create the upload directory if it does not already exist."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validate_upload_file_type(file: UploadFile) -> str:
    """Validate upload MIME type and return a normalized value."""
    content_type = (file.content_type or "").strip().lower()
    if content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_CONTENT_TYPES))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{content_type or 'unknown'}'. "
                f"Allowed types: {allowed}"
            ),
        )
    return content_type


async def _read_file_content(file: UploadFile) -> bytes:
    """
    Read upload content with an explicit size cap.

    We read at most MAX_UPLOAD_SIZE_BYTES + 1 to detect oversized payloads
    without reading arbitrarily large files into memory.
    """
    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds max allowed size of {MAX_UPLOAD_SIZE_BYTES} bytes.",
        )
    return content


def _build_storage_name(original_filename: str | None) -> str:
    """Create a safe storage filename preserving only a short suffix."""
    suffix = Path(original_filename or "").suffix.lower()
    if len(suffix) > 10:
        suffix = ""
    return f"{uuid4().hex}{suffix}"


def _serialize_post(post: Post) -> FilePostOut:
    """Convert ORM Post into API response model."""
    return FilePostOut(
        id=str(post.id),
        caption=post.caption,
        url=post.url,
        file_type=post.file_type,
        file_name=post.file_name,
        created_at=post.created_at,
    )


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
) -> UploadResponse:
    """
    Upload a file and persist its metadata in the database.

    Returns:
        UploadResponse: Confirmation message plus the stored post metadata.
    """
    content_type = _validate_upload_file_type(file)
    content = await _read_file_content(file)
    _ensure_upload_dir()

    stored_name = _build_storage_name(file.filename)
    storage_path = UPLOAD_DIR / stored_name
    storage_path.write_bytes(content)

    post = Post(
        caption=caption.strip() or None,
        url=f"/uploads/{stored_name}",
        file_type=content_type,
        file_name=stored_name,
    )

    try:
        session.add(post)
        await session.commit()
        await session.refresh(post)
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Failed to persist uploaded post metadata.")
        storage_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save upload metadata.",
        )
    finally:
        await file.close()

    return UploadResponse(
        message="File uploaded successfully",
        post=_serialize_post(post),
    )


@router.get(
    "/feed",
    response_model=FeedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_feed(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> FeedResponse:
    """
    Return a paginated feed of uploaded posts sorted by newest first.
    """
    try:
        stmt = (
            select(Post)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        posts = (await session.scalars(stmt)).all()
        total = (await session.scalar(select(func.count(Post.id)))) or 0
    except SQLAlchemyError:
        logger.exception("Failed to fetch feed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feed.",
        )

    return FeedResponse(
        posts=[_serialize_post(post) for post in posts],
        limit=limit,
        offset=offset,
        total=int(total),
    )
