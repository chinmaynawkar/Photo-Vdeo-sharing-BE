from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.core.config import UPLOAD_DIR
from app.db.db import create_db_and_tables
from app.schemas.post import Post, PostCreate, PostUpdate
from app.routers.files import router as files_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App startup/shutdown lifecycle.

    Creates required database tables and upload storage directory.
    """
    await create_db_and_tables()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(lifespan=lifespan)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include domain routers (single app, modular routes)
app.include_router(
    files_router,
    tags=["Files"],
)

# In-memory store for legacy text posts (GET/POST /posts). Replace with DB when ready.
text_posts: dict[int, dict] = {1: {"title": "First", "content": "Hello"}}

# Route: GET /posts
# - Returns all posts as JSON.
# - FastAPI automatically converts dicts (and Pydantic models) to JSON for APIs.
@app.get("/posts")
def get_all_posts(limit: int = None):
    if limit:
        # What does this do?
        # Converts the dictionary of posts into a list (so we can slice it).
        # Then, gets only the first 'limit' items from that list.
        #
        # Why do we do this?
        # Sometimes the user only wants to see a few posts, for example, the most recent 3.
        # This helps avoid sending too much data at once.
        #
        # Example:
        # If limit = 2, it will return the first two posts:
        # [
        #   {"title": "...", "content": "..."},
        #   {"title": "...", "content": "..."}
        # ]
        return list(text_posts.values())[:limit]
    else:
        return text_posts

# Route: GET /posts/{id}
# - {id} is a path parameter (dynamic part of the URL).
# - id: int means FastAPI expects an integer and will give an error for non-integers.
# - Returns the post for that ID or None if not found.
# - Raises HTTPException 404 if the post is not found.
@app.get("/posts/{id}")
def get_post(id: int):
    if id not in text_posts:
        raise HTTPException(status_code=404, detail=f"Post with id {id} not found")
    return text_posts.get(id)


# This decorator tells FastAPI: Whenever someone sends a POST request to /posts, use the function below.
@app.post("/posts") 
 # This function runs when a POST request comes to /posts. FastAPI automatically takes JSON from the request body
 # and turns it into a PostCreate object (with title & content fields). 
def create_post(post: PostCreate) -> PostCreate: # -> means the function returns a PostCreate object for documentation purposes
    # Create a new dictionary for the post using the title and content sent by the client.
    new_post = {"title": post.title, "content": post.content}  # This line makes a new post using the data from the request.
    
    # Find the highest existing post ID so the new post can have a unique ID. 
    # max(text_posts.keys()) gets the highest post ID number.
    # We then add 1, so the new post always gets the next available ID.
    next_id = max(text_posts.keys(), default=0) + 1
    text_posts[next_id] = new_post 
    # FastAPI will turn this Python dictionary into JSON automatically.
    return {"message": "Post created successfully", "post": new_post} 