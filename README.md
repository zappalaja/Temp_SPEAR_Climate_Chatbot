# SPEAR Climate Chatbot

A three-service stack for querying NOAA GFDL SPEAR and CMIP6 climate model data via a conversational interface.

```
Chatbot_03102026/
├── start.sh                  # Main launcher — starts all three services
├── chatbot.conf              # Your local config (create from template)
├── chatbot.conf.template     # Template for chatbot.conf
├── chatbot/                  # Streamlit web UI (port 8501)
├── mcp-server/               # MCP server with climate data tools (port 8000)
└── rag-service/              # RAG document retrieval service (port 8002)
```

---

## Prerequisites

Install these before anything else.

### 1. `uv` (Python package/project manager)
Used to run the MCP server. Install from https://github.com/astral-sh/uv or:
```bash
curl -LsSf https://astral.uv.dev/install.sh | sh
```

### 2. Miniconda
Used to run the RAG service in its own conda environment. The launcher expects it at `~/miniconda3`.
Install from https://docs.conda.io/en/latest/miniconda.html, then:
```bash
conda create -n rag python=3.11
conda activate rag
pip install -r rag-service/requirements.txt
```
The conda environment name defaults to `rag`. You can change it in `chatbot.conf`.

### 3. Python 3.x (for the chatbot venv)
The chatbot creates its own `venv` automatically on first run using whatever `python3` is on your PATH.

### 4. A ChromaDB vector database
The RAG service requires a pre-built ChromaDB database of ingested climate documents.
Set the path to it in `chatbot.conf` (see Configuration below).
If you don't have one, set `RAG_ENABLED=false` in `chatbot/.env` to run without RAG.

### 5. At least one LLM API key
The chatbot supports:
- **Anthropic Claude** — get a key at https://console.anthropic.com
- **Google Gemini** — get a key at https://aistudio.google.com
- **Ollama** (local, no key required) — install from https://ollama.com, then pull a model:
  ```bash
  ollama pull gemma3
  ```

---

## Configuration

### Step 1 — `chatbot.conf` (top-level, required)

Copy the template and fill in the path to your ChromaDB database:

```bash
cp chatbot.conf.template chatbot.conf
```

Edit `chatbot.conf`:

```bash
# Path to your ChromaDB vector store (built from ingested documents)
CHROMA_PERSIST_DIR="/absolute/path/to/your/chroma_db"

# ChromaDB collection name — must match the name used during ingestion
CHROMA_COLLECTION="nougat_merged"

# Sentence transformer model used to embed query text (must match ingestion model)
EMBED_MODEL="sentence-transformers/all-MiniLM-L6-v2"

# Name of the conda environment that has the RAG service dependencies
CONDA_ENV="rag"
```

> **Note:** `CHROMA_COLLECTION` and `EMBED_MODEL` must match exactly what was used when the
> ChromaDB database was built. If you ingested with a different model or collection name, update
> these values accordingly.

---

### Step 2 — `chatbot/.env` (chatbot API keys, required)

```bash
cp chatbot/.env.example chatbot/.env
```

Edit `chatbot/.env`:

```bash
# --- LLM API Keys (at least one required) ---
ANTHROPIC_API_KEY=sk-ant-api03-...
GEMINI_API_KEY=AIzaSy...

# --- Service URLs (defaults work if running locally via start.sh) ---
MCP_SERVER_URL=http://localhost:8000
RAG_ENABLED=true
RAG_TOP_K=2
RAG_API_URL=http://localhost:8002

# --- Ollama (only if using a local model) ---
# OLLAMA_BASE_URL=http://localhost:11434
```

> **Never commit `.env` to version control.** It contains your API keys.

---

## Running the Stack

```bash
./start.sh
```

This starts all three services in order, waits for each to be ready, then opens the chatbot in the foreground. Press `Ctrl+C` to stop everything cleanly.

| Service | URL | Purpose |
|---|---|---|
| Chatbot UI | http://localhost:8501 | Streamlit web interface |
| MCP Server | http://localhost:8000 | Climate data tools (SPEAR + CMIP6) |
| RAG Service | http://localhost:8002 | Document retrieval |

**Logs** for the background services are written to:
```
/tmp/climate_chatbot_zarr_pids/rag.log
/tmp/climate_chatbot_zarr_pids/mcp.log
```
Tail them while the stack is running:
```bash
tail -f /tmp/climate_chatbot_zarr_pids/rag.log
tail -f /tmp/climate_chatbot_zarr_pids/mcp.log
```

---

## Authentication (Optional)

Auth is **off by default**. The single toggle is `AUTH_ENABLED` in `chatbot/.env`.

### Enabling auth

```bash
# 1. Turn it on
echo "AUTH_ENABLED=true" >> chatbot/.env

# 2. Generate a random cookie secret and set it in users.yaml
python3 -c "import secrets; print(secrets.token_hex(32))"
# → paste the output as the value of cookie.key in chatbot/users.yaml

# 3. Add your first user
python chatbot/manage_users.py add

# 4. Restart the stack
./start.sh
```

The chatbot will show a login screen. After signing in, a **Logout** button appears in the sidebar.

### Managing users

```bash
python chatbot/manage_users.py add               # add a user (interactive)
python chatbot/manage_users.py remove <username> # remove a user
python chatbot/manage_users.py list              # list all users
```

Credentials are stored as bcrypt hashes in `chatbot/users.yaml`. Passwords are never stored in plaintext.

### Disabling auth

```bash
# In chatbot/.env, set:
AUTH_ENABLED=false
```

Restart the stack. The login screen disappears and the app runs as a single-user instance exactly as before.

### Per-user chat logs

When auth is enabled, each user's chat history is written to a separate file:
```
chatbot/chat_logs/chat_history_<username>_latest.json
```
When auth is disabled, all history goes to `chat_history_default_latest.json`.

---

## What Each Component Needs

### `rag-service/`

- **Runtime:** Python in the `rag` conda environment (or whatever `CONDA_ENV` is set to)
- **Entry point:** `uvicorn rag_service:app` — run automatically by `start.sh`
- **Required env vars (set via `chatbot.conf`):**
  - `CHROMA_PERSIST_DIR` — path to ChromaDB on disk
  - `CHROMA_COLLECTION` — collection name
  - `EMBED_MODEL` — embedding model name
- **Docker alternative:** If you prefer containers, update `CHROMA_PERSIST_DIR` in your shell
  environment and run:
  ```bash
  cd rag-service
  docker-compose up
  ```

### `mcp-server/`

- **Runtime:** Python 3.13+ managed by `uv` (uv installs dependencies automatically from `uv.lock`)
- **Entry point:** `uv run python -m spear_mcp --transport sse --host 0.0.0.0 --port 8000`
  — run automatically by `start.sh`
- **No additional configuration required** — connects to public AWS S3 buckets anonymously
- **Data sources (public, no credentials needed):**
  - SPEAR NetCDF: `s3://noaa-gfdl-spear-large-ensembles-pds/`
  - CMIP6 Zarr: `s3://cmip6-pds/`

### `chatbot/`

- **Runtime:** Python venv created automatically on first run
- **Entry point:** `streamlit run chatbot_app.py` — run automatically by `start.sh`
- **Required:** `chatbot/.env` with at least one LLM API key
- **Dependencies installed automatically** from `requirements.txt` on first run

---

## Running Without RAG

If you don't have a ChromaDB database, disable RAG in `chatbot/.env`:

```bash
RAG_ENABLED=false
```

The chatbot will still work — it just won't retrieve document context to augment responses.
You can also skip setting `CHROMA_PERSIST_DIR` in `chatbot.conf` in this case (the RAG service
will still start but won't be queried).

---

## Troubleshooting

**`ERROR: Missing config file: .../chatbot.conf`**
→ Run `cp chatbot.conf.template chatbot.conf` and fill in `CHROMA_PERSIST_DIR`.

**`ERROR: Directory not found: .../rag-service`** (or `mcp-server`, `chatbot`)**
→ Make sure you're running `start.sh` from the `Chatbot_03102026` directory.

**RAG service times out on startup**
→ Check `CONDA_ENV` in `chatbot.conf` — the named conda environment must exist and have the
RAG dependencies installed (`pip install -r rag-service/requirements.txt`).

**MCP server times out on startup**
→ Make sure `uv` is installed and on your PATH. The first run may take a minute to download
dependencies.

**Chatbot starts but shows no LLM models**
→ Check that at least one API key is set in `chatbot/.env`, or that Ollama is running locally.

**`conda activate` fails inside start.sh**
→ Make sure Miniconda is installed at `~/miniconda3`. If it's elsewhere, the launch script
will need to be updated — open `start.sh` and change the path in the conda prerequisites check
and `source` line.
