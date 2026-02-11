from pydantic import BaseModel

class Post(BaseModel):
    id: int
    title: str
    content: str

class PostCreate(BaseModel):
    title: str
    content: str

class PostUpdate(BaseModel):
    title: str
    content: str