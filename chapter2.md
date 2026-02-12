# Chapter 2: Connecting FastAPI to a Database (Async SQLAlchemy + SQLite)

A step-by-step explanation of how your current project connects FastAPI to a SQLite database using **SQLAlchemy (async)**, **aiosqlite**, and **python-dotenv**.

We’ll walk through:

- How the database URL is loaded from `.env`
- How the async engine and session are created
- How the `Post` model is defined
- How FastAPI initializes the database on startup

---

## Overview of the Files

In this chapter we focus on three main files:

| File              | Purpose (simple explanation)                                       |
| ----------------- | ------------------------------------------------------------------ |
| `app/db/db.py`    | Database core: loads config, sets up async engine & sessions.     |
| `app/db/db_model.py` | Database models: defines the `Post` table using SQLAlchemy ORM. |
| `app/app.py`      | FastAPI application: starts the app and (currently) mock routes.  |

You also have a `.env` file at the project root that stores the actual database URL:

```env
DATABASE_URL="sqlite+aiosqlite:///./database.db"
```

---

## Step 1: Load the Database URL from `.env` (`app/db/db.py`)

### Code (simplified)

```python
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_database_url() -> str:
    """
    Read the async database URL from the environment.
    """
    load_dotenv()

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url.strip().strip('"').strip("'")


DATABASE_URL: str = get_database_url()
```

### What this does in simple terms

- **`load_dotenv()`**:
  - Reads the `.env` file in your project root.
  - Loads key/value pairs (like `DATABASE_URL=...`) into environment variables.
- **`os.getenv("DATABASE_URL")`**:
  - Looks up the `DATABASE_URL` value from the environment.
  - If it’s missing, you **fail fast** with a clear `RuntimeError`.
- **`strip().strip('"').strip("'")`**:
  - Cleans up any surrounding spaces or quotes, in case `.env` has `"value"` or `'value'`.
- **`DATABASE_URL`**:
  - Now holds a clean string like:  
    `sqlite+aiosqlite:///./database.db`

### Why this is good

- You keep secrets and config **out of code**.
- You can change the database (e.g., to PostgreSQL) by editing `.env`, not code.
- Errors happen at startup if misconfigured, so bugs aren’t hidden.

---

## Step 2: Create the Async Engine and Session Factory (`app/db/db.py`)

### Code (simplified)

```python
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)
```

### What each part means

- **`create_async_engine(DATABASE_URL, echo=False)`**:
  - Builds an **async SQLAlchemy engine** using the `DATABASE_URL`.
  - `echo=False` means it won’t log every SQL statement (you can set `True` for debugging).
  - Manages a pool of connections to your database (SQLite in this case).

- **`async_sessionmaker(engine, expire_on_commit=False)`**:
  - A **factory** that creates `AsyncSession` objects.
  - `expire_on_commit=False`:
    - After you commit a transaction, objects stay “live” and usable without refreshing from the DB.
    - More ergonomic for most FastAPI use cases.

---

## Step 3: Provide `get_async_session` for FastAPI Dependencies (`app/db/db.py`)

### Code

```python
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get an AsyncSession.
    """
    async with async_session_maker() as session:
        yield session
```

### What this does

- Wraps the session lifecycle in an **async context manager**:
  - Opens an `AsyncSession` from the factory.
  - Yields it to your FastAPI path operation.
  - Closes it automatically when the request is done.

### How you’ll use it later

In a route, you’ll be able to do:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_async_session


@app.get("/posts-from-db")
async def list_posts(session: AsyncSession = Depends(get_async_session)):
    # use `session` to query the Post table
    ...
```

This connects your HTTP request directly to a database session, safely and cleanly.

---

## Step 4: Define the `Post` Model (`app/db/db_model.py`)

### Code

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.db import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### What this does in simple terms

- **`class Post(Base)`**:
  - Declares a table mapped to a Python class.
  - Inherits from `Base`, so SQLAlchemy knows it’s an ORM model.

- **`__tablename__ = "posts"`**:
  - The table name in the database is `posts`.

- **Columns:**
  - `id`:
    - `UUID` primary key, stored as a UUID.
    - Auto-generated using `uuid.uuid4()`.
  - `caption`:
    - Optional text field (`nullable=True`).
  - `url`:
    - String, required (`nullable=False`).
    - Could store the image URL or resource link.
  - `file_type`:
    - String, required.
    - Could be `"image"`, `"video"`, etc.
  - `file_name`:
    - String, required.
    - Original or logical file name.
  - `created_at`:
    - `DateTime`, defaults to the current UTC time when a row is created.

### Relationship to the engine

- This class doesn’t know about the engine directly.
- It just attaches its table definition to `Base.metadata`.
- The engine is used later (in `create_db_and_tables`) to create the actual tables.

---

## Step 5: Create Tables on App Startup (`app/app.py` + `app/db/db.py`)

### The startup hook in `app/app.py`

```python
from fastapi import FastAPI, HTTPException
from app.schemas.post import Post, PostCreate, PostUpdate
from app.db.db import create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    await create_db_and_tables()
    # Yield control back to FastAPI to start the server
    yield


app = FastAPI(lifespan=lifespan)
```

### The `create_db_and_tables` function (`app/db/db.py`)

```python
async def create_db_and_tables() -> None:
    """
    Create all tables defined on `Base.metadata`.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### How this works together

1. **When FastAPI starts**:
   - The `lifespan` function runs before the server begins serving requests.
2. **`await create_db_and_tables()`**:
   - Opens a connection using the async engine.
   - Calls `Base.metadata.create_all` in a thread-safe way via `run_sync`.
   - SQLAlchemy looks at all models that inherit from `Base` (like `Post`) and creates tables if they don’t exist.
3. **After that**:
   - The app starts and is ready to accept requests.

### Why this is useful

- Your database schema (tables) is ensured to exist every time the app starts.
- You don’t have to manually run SQL to create the `posts` table during development.

---

## Step 6: Current API Routes (Still Using In-Memory Data)

Right now, `app/app.py` still uses a **mock in-memory database** (`text_posts` dict) for routes like:

- `GET /posts`
- `GET /posts/{id}`
- `POST /posts`

Example snippet:

```python
text_posts = {
    1: {"title": "Welcome to FastAPI", "content": "This is the first mock post."},
    2: {"title": "Learning FastAPI", "content": "FastAPI makes building APIs fun and easy."},
    # ...
}
```

These are **great for learning** how routes and Pydantic models work, but they **don’t yet use the real database**.

In a next step, you will:

- Replace `text_posts` with actual database queries using `AsyncSession`.
- Map your Pydantic models (`PostCreate`, `PostUpdate`, etc.) to the `Post` ORM model.

---

## Visual Flow: From .env to Database Tables

```
1. .env file
   - DATABASE_URL="sqlite+aiosqlite:///./database.db"

2. db.py
   - load_dotenv()
   - get_database_url() → DATABASE_URL
   - create_async_engine(DATABASE_URL)
   - async_session_maker(...)

3. db_model.py
   - class Post(Base): defines posts table

4. app.py (lifespan)
   - await create_db_and_tables()
   - Base.metadata.create_all(engine) creates tables if needed
```

---

## Summary Table: DB Setup Components

| Piece                         | Location         | Responsibility                                           |
| ----------------------------- | ---------------- | -------------------------------------------------------- |
| `.env`                        | project root     | Stores `DATABASE_URL` and other secrets/config.          |
| `load_dotenv()`              | `app/db/db.py`   | Loads `.env` values into environment variables.          |
| `get_database_url`           | `app/db/db.py`   | Reads and validates `DATABASE_URL`.                      |
| `engine` (async)             | `app/db/db.py`   | Manages async DB connections using SQLAlchemy.           |
| `async_session_maker`        | `app/db/db.py`   | Factory for `AsyncSession` objects.                      |
| `get_async_session`          | `app/db/db.py`   | FastAPI dependency to inject a DB session into routes.   |
| `Base`                       | `app/db/db.py`   | Base ORM class; all models inherit from it.              |
| `Post` model                 | `app/db/db_model.py` | ORM representation of the `posts` table.             |
| `create_db_and_tables`       | `app/db/db.py`   | Creates all tables on startup.                           |
| `lifespan` startup function  | `app/app.py`     | Calls `create_db_and_tables` before serving requests.    |

---

## Next Steps (Chapter 3 Ideas)

- Replace the in-memory `text_posts` with real database queries using `AsyncSession`.
- Implement CRUD operations (Create, Read, Update, Delete) against the `Post` table.
- Add migrations later (e.g., using Alembic) once the schema stabilizes.
- Introduce repository/services layers to keep routes thin and business logic reusable.

