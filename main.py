import uvicorn


# This block ensures the server only starts if we run this file directly (not if imported as a module)
if __name__ == "__main__":
    # Start the Uvicorn server:
    # "app.app:app" = module path to the FastAPI app (module 'app.app', FastAPI object 'app')
    # host="0.0.0.0" = listen on all available network interfaces (so it works in Docker/cloud)
    # port=8000 = run the server on port 8000 (default FastAPI port)
    # reload=True = auto-reload when code changes (great for development)
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True)
