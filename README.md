# HPE Backend Scripts

## Migration Note:

> Status: Scripts are Stable and Integrated with Frontend-UI.

> These backend scripts and programs were initially developed and tested on a local development repository.

-   All essential backend components and logic have been imported.

> Legacy or experimental modules are clearly labeled with `_OLD`.

## Structure Overview

Backend_Scripts/
├── server_routes/ # Main API endpoints (MCP, admin, RAG, topology)
├── server_tools/ # Core backend logic (agents, LLM services, analyzers, scrapers)
├── MAIN_app.py # Unified FastAPI app launcher => Backend MAIN Code.
├── groq_orchestrator.py # Orchestrator for LLM and toolchain routing
├── migrate_db.py # DB migration logic
├── requirements.txt # Python dependencies

## 🛠️ Environment Configuration

Sensitive and environment-specific settings are managed through the following:

-   **`.env`**: This file stores environment variables such as API keys, database URIs, and service endpoints.
-   **`environment.py`** : A helper utility that loads and accesses `.env` variables programmatically using `os.environ` or `dotenv`.
-   The `.env` file contains configuration for API keys, scraping parameters, vector DB paths, LLM models, and web search behavior — all loaded via `environment.py`, using `python-dotenv`.
