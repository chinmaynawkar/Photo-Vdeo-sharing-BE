"""
This __init__.py file makes it easy to import the FastAPI app from the app module.
By writing 'from .app import app', it lets us do 'from app import app' elsewhere
and keeps our project organized. In simple terms: this file connects the app object
so it's easy to use in other parts of our code (for example, for starting the server).
"""
from .app import app
