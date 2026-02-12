# Chapter 3: Building a Production-Style Files API (Upload + Feed)

A step-by-step learning guide for everything we implemented for the Files API: from model usage and router structure to validation, storage, pagination, and testing.

---

## Overview

In this chapter, we built a real Files API flow:

- `POST /upload` to accept an image file + caption
- Save the file to local storage (`uploads/`)
- Save metadata to the database (`posts` table)
- Return a typed response body with created resource details
- `GET /feed` with pagination (`limit`, `offset`) and total count

We also added:

- Stronger validation (file type, size, empty file checks)
- Safe error handling (no raw DB errors leaked to clients)
- Better code organization (config module + schemas + router helpers)
- Docstrings (pydoc style) for maintainability

---

## Project Files Used in This Chapter

| File | Purpose |
| ---- | ------- |
| `app/db/db_model.py` | Defines the `Post` ORM model used to store file metadata. |
| `app/core/config.py` | Centralized upload configuration (dir, max size, allowed content types). |
| `app/schemas/file.py` | Pydantic response models for upload/feed endpoints. |
| `app/routers/files.py` | File API routes and helper functions. |
| `app/app.py` | Includes router and mounts static files (`/uploads`). |
| `main.py` | Runs app with Uvicorn in development. |

---

## Step 1: Reuse the Database Model for File Metadata

### What we used

`app/db/db_model.py` already had a table model:

```python
class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Purpose

Store metadata about uploaded files:

- `url`: where file is served from (e.g., `/uploads/<file-name>`)
- `file_type`: MIME type (`image/png`, etc.)
- `file_name`: stored file name on disk
- `caption`: optional text from user
- `created_at`: timeline sorting for feed

### Why this is good

- Keeps binary file on disk and metadata in DB (clean separation).
- Makes feed queries efficient and structured.
- Easy to replace local storage with cloud storage later.

---

## Step 2: Create Central Upload Config (`app/core/config.py`)

### What we added

```python
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024)))
ALLOWED_UPLOAD_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
```

### Purpose

Move hardcoded upload settings into one place.

### Why this is industry standard

- Follows 12-factor configuration style (env-driven config).
- Single source of truth for limits and upload policy.
- Reduces hidden coupling across files.

### Optional `.env` entries

```env
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_BYTES=5242880
```

If these are missing, safe defaults are used.

---

## Step 3: Add Typed Response Schemas (`app/schemas/file.py`)

### What we added

- `FilePostOut`
- `UploadResponse`
- `FeedResponse`

```python
class UploadResponse(BaseModel):
    message: str
    post: FilePostOut


class FeedResponse(BaseModel):
    posts: list[FilePostOut]
    limit: int
    offset: int
    total: int
```

### Purpose

Define a strict API contract for clients.

### Why this matters

- Better OpenAPI docs (`/docs`).
- Better client integration (predictable response shape).
- Response filtering/validation from FastAPI/Pydantic.

---

## Step 4: Create a Dedicated Router (`app/routers/files.py`)

### What we did

Used `APIRouter()` and moved file endpoints into their own module.

```python
router = APIRouter()
```

Then included router in `app/app.py`:

```python
app.include_router(files_router, tags=["Files"])
```

### Purpose

Keep app modular and maintainable as features grow.

### Why this is better than one huge `app.py`

- Clear feature boundaries.
- Easier testing and ownership.
- Cleaner onboarding for new developers.

---

## Step 5: Add Helper Functions for Validation and Mapping

In `app/routers/files.py`, we added focused helpers:

- `_ensure_upload_dir()`
- `_validate_upload_file_type(file)`
- `_read_file_content(file)`
- `_build_storage_name(original_filename)`
- `_serialize_post(post)`

### Purpose

Keep route handlers small and readable.

### Why this is important

- Avoids repeated logic.
- Makes behavior easier to test and reason about.
- Separates HTTP concerns from utility logic.

---

## Step 6: Implement `POST /upload` Properly

### Final behavior

1. Accept multipart form: `file` + `caption`
2. Validate MIME type
3. Validate file size and reject empty file
4. Create upload directory if needed
5. Generate safe unique filename (`uuid4 + suffix`)
6. Save file bytes to disk
7. Save metadata row in DB
8. Return `201 Created` with full typed response

### Endpoint signature

```python
@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
```

### Error handling strategy

- `session.rollback()` on DB failure
- Server-side `logger.exception(...)`
- Client gets safe error message (`"Failed to save upload metadata."`)
- Partial file cleanup if DB write fails (`storage_path.unlink(...)`)

### Why this is production-friendly

- Prevents internal exception leakage.
- Keeps DB and file-system state consistent.
- Returns a complete resource representation, not only `"success"`.

---

## Step 7: Mount Static Files for Uploaded Content

In `app/app.py`:

```python
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
```

### Purpose

Serve stored files directly via URL paths.

### Example

If saved file is `uploads/abc123.png`, API stores:

```text
url = "/uploads/abc123.png"
```

Client can access that path from your API host.

---

## Step 8: Implement `GET /feed` with Pagination

### What we implemented

```python
@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
)
```

### Query logic

- Fetch posts in reverse chronological order.
- Apply `limit` and `offset`.
- Return `total` count in same response.

### Why this matters

- Prevents unbounded reads (important as data grows).
- Supports infinite scroll / “load more” UI patterns.
- Gives frontend enough metadata to paginate properly.

---

## Step 9: Run and Test the APIs Manually

### Start server

```bash
uv run main.py
```

### Upload test with `curl`

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "caption=my first file" \
  -F "file=@/absolute/path/to/image.png"
```

### Expected response shape

```json
{
  "message": "File uploaded successfully",
  "post": {
    "id": "uuid-string",
    "caption": "my first file",
    "url": "/uploads/generated-name.png",
    "file_type": "image/png",
    "file_name": "generated-name.png",
    "created_at": "2026-02-12T07:42:07.277807"
  }
}
```

### Feed test

```bash
curl "http://127.0.0.1:8000/feed?limit=20&offset=0"
```

### Expected response shape

```json
{
  "posts": [
    {
      "id": "uuid-string",
      "caption": "my first file",
      "url": "/uploads/generated-name.png",
      "file_type": "image/png",
      "file_name": "generated-name.png",
      "created_at": "2026-02-12T07:42:07.277807"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 1
}
```

---

## Step 10: Quick Automated API Check with `TestClient`

You can run a lightweight smoke test without writing full pytest files yet:

```bash
uv run python -c "
from fastapi.testclient import TestClient
from app.app import app

with TestClient(app) as client:
    upload = client.post(
        '/upload',
        files={'file': ('demo.png', b'fakepng', 'image/png')},
        data={'caption': 'demo'}
    )
    print('upload', upload.status_code, upload.json())

    feed = client.get('/feed')
    print('feed', feed.status_code, feed.json())
"
```

### Why this helps

- Fast feedback loop during development.
- Verifies request parsing + DB write + response schema together.
- Good first step before adding formal test suite.

---

## Step 11: Common Errors and Fixes

### 1) Error: `Directory 'uploads' does not exist`

**Cause:** `StaticFiles` needs the directory at mount time.  
**Fix:** Ensure `UPLOAD_DIR.mkdir(parents=True, exist_ok=True)` runs before `app.mount(...)`.

### 2) `415 Unsupported Media Type`

**Cause:** MIME type not in allowlist.  
**Fix:** Upload supported images only, or add additional MIME types in `ALLOWED_UPLOAD_CONTENT_TYPES`.

### 3) `413 Request Entity Too Large`

**Cause:** File exceeds `MAX_UPLOAD_SIZE_BYTES`.  
**Fix:** Upload smaller file or increase the configured limit.

### 4) Empty file rejected (`400`)

**Cause:** Uploaded file had no content.  
**Fix:** Validate source file before upload.

---

## Step 12: What We Improved vs Initial Version

| Area | Before | Now |
| ---- | ------ | --- |
| Upload response | Only message string | Typed full response with created post |
| Validation | No file checks | MIME + size + empty checks |
| Storage | Dummy URL/filename | Real file saved to `uploads/` + served URL |
| Feed API | Returned all rows | Paginated (`limit`, `offset`, `total`) |
| Error handling | Raw exception detail to client | Safe client errors + server logging |
| Code structure | Route-heavy function | Helper functions + schemas + config modules |
| Documentation | Minimal | Rich pydoc docstrings and clear contracts |

---

## Visual Flow: Request to Response

```text
1) Client sends multipart/form-data to POST /upload
   - caption + file

2) Router validates file
   - MIME type allowlist
   - non-empty
   - max size check

3) Router writes file to disk
   - uploads/<uuid>.<ext>

4) Router writes metadata row to DB
   - caption, url, file_type, file_name, created_at

5) Router returns 201 with UploadResponse
   - message + post details

6) Client requests GET /feed?limit=20&offset=0
   - DB query with order + limit + offset + total
   - returns FeedResponse
```

---

## Final Summary

In this chapter, we moved from a basic upload endpoint to a cleaner, production-style Files API:

- Stronger validation
- Real file persistence
- Safe and explicit error handling
- Typed response contracts
- Pagination-ready feed
- Better module boundaries and documentation

This gives you a maintainable foundation. Next, you can evolve storage from local disk to cloud (S3/ImageKit), add auth, and introduce repository/service layers for even cleaner architecture.

---

## References (Official)

- FastAPI: Request Files (`UploadFile`)  
  https://fastapi.tiangolo.com/tutorial/request-files/

- FastAPI: Response Status Code (`201 Created`)  
  https://fastapi.tiangolo.com/tutorial/response-status-code/

- FastAPI: `APIRouter` and `response_model` reference  
  https://fastapi.tiangolo.com/reference/apirouter/

- SQLAlchemy 2.0: Async ORM (`AsyncSession.scalars`)  
  https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

