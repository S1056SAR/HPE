# HPE Backend Scripts

## Migration Note:

> **Status**: Scripts are stable and have been integrated with Frontend-UI.

> These backend scripts and programs were initially developed and tested on a local development repository.

> All essential backend components and logic have been imported.

> Legacy or experimental modules are clearly labeled with `_OLD`.

> Commit history of the files have been maintained.

---

## Structure Overview

```text
Backend_Scripts/
├── server_routes/             -> Main API endpoints (MCP, admin, RAG, topology)
├── server_tools/              -> Core backend logic (agents, LLM services, analyzers, scrapers)
├── MAIN_app.py                -> Unified FastAPI app launcher => Backend MAIN Code.
├── groq_orchestrator.py       -> Orchestrator for LLM and toolchain routing
├── migrate_db.py              -> DB migration logic
├── requirements.txt           -> Python dependencies
```

MAIN_app.py is the primary launcher that initializes all backend routes and services.
It connects the API endpoints under server_routes and integrates the toolchains from server_tools.

---

## Environment Configuration

Sensitive and environment-specific settings are managed through the following:

-   **`.env`**: This file stores environment variables such as API keys, database URIs, and service endpoints.
-   **`environment.py`** : A helper utility that loads and accesses `.env` variables programmatically using `os.environ` or `dotenv`.
-   The `.env` file contains configuration for API keys, scraping parameters, vector DB paths, LLM models, and web search behavior — all loaded via `environment.py`, using `python-dotenv`.

---

## Initial Setup and Running

Follow these steps to set up and launch the backend:

### 1. Clone the repository

```bash
git clone https://github.com/S1056SAR/HPE.git
cd Backend_Scripts/
```

### 2. Install the dependencies.

Make sure you're using Python 3.8+ and install all required packages:

```bash
pip install -r requirements.txt
```

### 3. Configure environment.

Create a `.env` file in the `Backend_Scripts` directory with necessary API keys and other settings.
Refer to the `environment.py` for required variables.

### 4. Run the backend server.

Start the FastAPI backend using the main entry point:

```bash
uvicorn MAIN_app:app --host 0.0.0.0 --port 8000 --reload
```

The backend will now be live and it will listen for incoming requests from frontend/UI at http://localhost:8000
