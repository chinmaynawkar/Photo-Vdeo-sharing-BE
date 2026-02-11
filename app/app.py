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

# when we call api we talk with JSON for that we use Pydantic models or python dictionaries

# This is a simple in-memory 'database' (just a Python dict)
# Keys = post IDs, Values = dictionary with title and content
text_posts = {
    1: {"title": "Welcome to FastAPI", "content": "This is the first mock post."},
    2: {"title": "Learning FastAPI", "content": "FastAPI makes building APIs fun and easy."},
    3: {"title": "Mock Data Example", "content": "These posts are mock data for development purposes."},
    4: {"title": "Async Endpoints", "content": "You can write async endpoints with FastAPI for speed."},
    5: {"title": "Why FastAPI?", "content": "Because it's fast and uses modern Python features!"},
}


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
    text_posts[max(text_posts.keys()) + 1] = new_post 
    # FastAPI will turn this Python dictionary into JSON automatically.
    return {"message": "Post created successfully", "post": new_post} 