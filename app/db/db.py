import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv

# AsyncGenerator:
#   - Allows us to create async generator functions (functions that can pause and continue later).
#   - Useful in FastAPI for streaming data or handling many items one-by-one asynchronously.

#   - 'AsyncSession': Lets us interact with the database asynchronously (good for FastAPI speed!).
#   - 'create_async_engine': Creates an async database connection (needed for async operations).
#   - 'async_sessionmaker': Factory for creating AsyncSession objects.
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

#   - 'DeclarativeBase': Makes a base class for our database models (all models inherit from this).
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


def get_database_url() -> str:
    """
    Read the async database URL from the environment.

    We fail fast if it is missing instead of guessing, so misconfiguration
    shows up clearly on startup.
    """
    # Load values from .env into environment variables (if .env exists).
    load_dotenv()

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    # In case the value in .env is quoted, strip surrounding quotes.
    return url.strip().strip('"').strip("'")


DATABASE_URL: str = get_database_url()

# Async engine and session factory shared across the app.
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get an AsyncSession.

    Example:
        async def endpoint(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables() -> None:
    """
    Create all tables defined on `Base.metadata`.

    Call this once at startup (e.g. FastAPI startup event).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

