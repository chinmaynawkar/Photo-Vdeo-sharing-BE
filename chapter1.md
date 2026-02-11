# Chapter 1: FastAPI Project Setup — Step-by-Step Guide

A beginner-friendly walkthrough of what we did and why.

---

## Overview

We set up a new FastAPI project using **uv** (a Python package manager). Each step below explains what we did, why we did it, and what each file or command does in simple terms.

---

## Step 1: Install uv

**What we did:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Purpose:**  
Install **uv**, a tool that manages Python packages and virtual environments.

**What it does in simple terms:**

- **uv** = A fast Python package manager (like `pip`, but faster and more modern).
- It downloads and installs Python libraries for you.
- It can create isolated “workspaces” (virtual environments) so each project has its own dependencies.

**Why use uv instead of pip?**

- Faster installs.
- Handles virtual environments automatically.
- Creates a lock file (`uv.lock`) so everyone gets the same dependency versions.

---

## Step 2: Create the Project Folder

**What we did:**

```bash
cd ~/Desktop/personal/fast-api
```

**Purpose:**  
Open the folder where our FastAPI project will live.

**What it does in simple terms:**

- `cd` = change directory.
- `~/Desktop/personal/fast-api` = path to your project folder (on your Desktop).
- All project files (like `main.py`, `pyproject.toml`) will be inside this folder.

---

## Step 3: Initialize the Project with uv

**What we did:**

```bash
uv init --app
```

**Purpose:**  
Create a new Python application project with a standard structure.

**What it does in simple terms:**

- `uv init` = “Start a new project here.”
- `--app` = “This is an application” (not a library).
- uv creates:
  - `pyproject.toml` – project config and dependencies
  - `main.py` – entry point file
  - `README.md` – project description
  - `.python-version` – which Python version to use

---

## Step 4: Add FastAPI as a Dependency

**What we did:**

```bash
uv add fastapi --extra standard
```

**Purpose:**  
Install FastAPI and its “standard” extras (server, docs, etc.).

**What it does in simple terms:**

- `uv add` = “Add this package to the project.”
- `fastapi` = the web framework.
- `--extra standard` = also install:
  - **Uvicorn** – server that runs your app
  - **OpenAPI/Swagger** – tools for auto-generated docs
- uv also:
  - Creates a `.venv` folder (virtual environment)
  - Generates `uv.lock` to lock exact versions

---

## Step 5: Define the FastAPI App in main.py

**What we did:**  
We wrote this code in `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Purpose:**  
Define a minimal FastAPI application with two endpoints.

**What each part does in simple terms:**

| Line / Block                        | What it does                                                        |
| ----------------------------------- | ------------------------------------------------------------------- |
| `from fastapi import FastAPI`       | Imports the FastAPI class.                                          |
| `app = FastAPI()`                   | Creates the app instance.                                           |
| `@app.get("/")`                     | Registers a route for the root URL (e.g. `http://localhost:8000/`). |
| `async def root():`                 | Function that runs when someone visits `/`.                         |
| `return {"message": "Hello World"}` | Returns JSON.                                                       |
| `@app.get("/health")`               | Registers a route for `/health`.                                    |
| `return {"status": "ok"}`           | Returns a simple health check response.                             |

---

## Step 6: Run the Development Server

**What we did:**

```bash
uv run fastapi dev
```

**Purpose:**  
Start the FastAPI app in development mode.

**What it does in simple terms:**

- `uv run` = Run a command inside the project’s virtual environment.
- `fastapi dev` = Start the FastAPI dev server.
- Effects:
  - Starts the server (usually at `http://127.0.0.1:8000`).
  - Watches for code changes and reloads.
  - Serves the interactive docs at `/docs`.

---

## What Each Project File Does

| File                | Purpose (simple explanation)                                               |
| ------------------- | -------------------------------------------------------------------------- |
| **main.py**         | Your FastAPI app. Defines routes and logic.                                |
| **pyproject.toml**  | Project name, version, and list of dependencies.                           |
| **uv.lock**         | Exact versions of all packages. Ensures reproducible installs.             |
| **.venv/**          | Virtual environment. Holds Python and installed packages for this project. |
| **.python-version** | Tells uv which Python version to use (e.g. 3.12).                          |
| **.gitignore**      | Tells Git which files to ignore (e.g. `.venv`, `__pycache__`).             |
| **README.md**       | Short project description and how to run it.                               |

---

## Visual Flow: From Setup to Running

```
1. Install uv          →  You have a package manager
2. Create folder       →  You have a place for the project
3. uv init --app       →  Project scaffold is created
4. uv add fastapi      →  FastAPI is installed
5. Write main.py       →  App logic is defined
6. uv run fastapi dev  →  Server runs and serves your API
```

---

## Summary

| Step | Command/Action                    | Purpose                           |
| ---- | --------------------------------- | --------------------------------- |
| 1    | Install uv                        | Get a fast Python package manager |
| 2    | `cd` to project folder            | Go to project directory           |
| 3    | `uv init --app`                   | Create project structure          |
| 4    | `uv add fastapi --extra standard` | Add FastAPI and its tools         |
| 5    | Edit `main.py`                    | Define routes and responses       |
| 6    | `uv run fastapi dev`              | Run the app in dev mode           |

---

## Learning Notes: Additional Dependencies

We added two more packages to `pyproject.toml` for real-world apps. Here’s what they do:

---

### python-dotenv

**What we did:**
```bash
uv add "python-dotenv"
```

**Purpose:**  
Load configuration from a `.env` file instead of hardcoding secrets.

**What it does in simple terms:**

- **Environment variables** = Key-value pairs that hold config (e.g. database URL, API keys).
- **`.env` file** = A text file in your project root with those values (e.g. `DATABASE_URL=postgresql://...`).
- **python-dotenv** = Reads `.env` and loads its values into `os.environ` so your app can use them.

**Why use it?**

- Keeps secrets out of code (no passwords in Git).
- Different config per environment (dev, staging, prod).
- Follows the [Twelve-Factor App](https://12factor.net/config) style.

**Example usage:**
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env from project root
db_url = os.getenv("DATABASE_URL")
```

---

### fastapi-users[sqlalchemy]

**What we did:**
```bash
uv add "fastapi-users[sqlalchemy]"
```

**Purpose:**  
Add pre-built user auth (register, login, password reset) using SQLAlchemy with FastAPI.

**What it does in simple terms:**

- **fastapi-users** = Auth library for FastAPI (registration, login, password hashing, JWT).
- **[sqlalchemy]** = Extra that adds SQLAlchemy support.
- **SQLAlchemy** = ORM that lets you talk to databases (PostgreSQL, SQLite, etc.) using Python instead of raw SQL.

**Why use it?**

- Get full auth flows without writing everything yourself.
- Store users in a real database (not in memory).
- Easy to plug in different backends (SQLAlchemy, MongoDB, etc.).

**What the `[sqlalchemy]` extra gives you:**

- SQLAlchemy models for users.
- Adapters to store users in the database.
- Automatic table creation via migrations.

---

### aiosqlite

**What we did:**
```bash
uv add "aiosqlite"
```

**Purpose:**  
Use SQLite asynchronously so database calls don’t block your FastAPI app.

**What it does in simple terms:**

- **SQLite** = File-based database, no separate server needed.
- **aiosqlite** = Async version of the built-in `sqlite3` module for `asyncio` event loops.
- All connection and cursor operations (`connect`, `execute`, `fetch`) are `async`/`await`.

**Why use it?**

- Keeps FastAPI async handlers non-blocking.
- Works well with SQLAlchemy + FastAPI for async SQLite.
- Useful for dev and small apps (single file, no server setup).

**What it gives you:**

- `async with aiosqlite.connect("db.sqlite")` for connections.
- `await db.execute(...)` for queries.
- Async iterators for query results.

---

### imagekitio

**What we did:**
```bash
uv add "imagekitio"
```

**Purpose:**  
Integrate ImageKit’s image CDN and upload into your app.

**What it does in simple terms:**

- **ImageKit** = Cloud service for image storage, optimization, and delivery.
- **imagekitio** = Official Python SDK to talk to ImageKit.
- You can upload images, resize/transform them via URLs, and serve optimized images.

**Why use it?**

- Store and serve images without managing your own storage.
- Auto-optimization (compression, format, resizing).
- Signed URLs for private content.
- CDN delivery for faster loading.

**What it gives you:**

- URL generation and transformations.
- File upload API.
- Sync and async clients (httpx-based).

---

### uvicorn[standard]

**What we did:**
```bash
uv add "uvicorn[standard]"
```

**Purpose:**  
Run your FastAPI app as an ASGI server.

**What it does in simple terms:**

- **Uvicorn** = ASGI server that runs FastAPI (and other async Python web apps).
- **[standard]** = Extra with optional deps (e.g. `watchfiles` for auto-reload in dev).
- `fastapi dev` uses Uvicorn under the hood.

**Why add it explicitly?**

- Control which Uvicorn version you use.
- Use `uvicorn main:app` directly if needed.
- Get the standard extras (reload, websockets, etc.) without relying on FastAPI’s extras.

---

### Current Dependencies in pyproject.toml

| Package | Purpose |
| -------- | -------- |
| `aiosqlite` | Async SQLite driver for non-blocking DB ops |
| `fastapi[standard]` | Web framework + server + docs |
| `fastapi-users[sqlalchemy]` | User auth + SQLAlchemy backend |
| `imagekitio` | Image CDN, upload, and transformation |
| `python-dotenv` | Load config from `.env` |
| `uvicorn[standard]` | ASGI server to run the app |

---

## Next Steps (Chapter 2 Topics)

- Add more routes (POST, PUT, DELETE).
- Use path parameters and query parameters.
- Define request/response models with Pydantic.
- Organize code into routers and modules.
