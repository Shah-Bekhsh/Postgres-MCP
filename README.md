# pg-mcp — PostgreSQL MCP Server + Ollama Client

A learning project that implements a fully local AI assistant grounded in real database data. Built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), it connects a local Ollama LLM to a PostgreSQL database through a custom MCP server and interactive client.

---

## What This Project Does

The user chats with a local LLM (Ollama) in a terminal. Instead of guessing or hallucinating, the model uses MCP tools to query a real PostgreSQL database before answering. Every response is grounded in actual data.

```
You: Which customer has spent the most money?
→ LLM calls list_tables
→ LLM calls describe_table on customers, orders, order_items
→ LLM calls run_query with a JOIN query
→ LLM answers: "Alice Müller with $168.96"
```

---

## Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL (local, WSL2) |
| DB driver | asyncpg (async Python) |
| MCP framework | `mcp[cli]` — Anthropic's official Python SDK |
| LLM runtime | Ollama (`qwen2.5:7b`) |
| LLM hardware | NVIDIA Quadro RTX 4000 (8GB VRAM) |
| Environment | Python 3.14, uv, WSL2 Ubuntu |

---

## Project Structure

```
db-mcp-test/
├── .env                    # DB + Ollama config (never committed)
├── .gitignore
├── README.md
├── main.py                 # Test runner for database.py functions
├── pyproject.toml          # uv project config + entry point
├── uv.lock
└── src/
    └── pg_mcp/
        ├── __init__.py
        ├── database.py     # PostgreSQL connection pool + query helpers
        ├── server.py       # MCP server — tools and resources
        └── client.py       # MCP client — Ollama tool calling loop
```

---

## File Descriptions

### `database.py`
The PostgreSQL layer. All functions are async using `asyncpg`.

| Function | Description |
|---|---|
| `get_pool()` | Creates a connection pool (min 1, max 5 connections) |
| `fetch_all(pool, query, *args)` | Runs a query, returns list of dicts |
| `fetch_one(pool, query, *args)` | Runs a query, returns single dict or None |
| `get_table_names(pool)` | Returns list of table names from `information_schema` |
| `get_table_schema(pool, table_name)` | Returns column info for a table |
| `get_row_count(pool, table_name)` | Returns row count for a table |

### `server.py`
The MCP server built with `FastMCP`. Exposes tools and resources over stdio transport.

**Tools** (actions the LLM can invoke):

| Tool | Description |
|---|---|
| `list_tables` | Returns all table names in the database |
| `describe_table(table_name)` | Returns schema for a specific table |
| `run_query(query)` | Executes a SELECT query and returns results |

**Security**: `run_query` rejects anything that doesn't start with `SELECT` (case-insensitive). This prevents the LLM from running destructive queries.

**Resources** (data the LLM can read as context):

| Resource URI | Description |
|---|---|
| `schema://database` | Full schema of all tables — names and column types |

### `client.py`
The interactive MCP client. Starts the server as a subprocess, connects via stdio, and runs a persistent chat loop with Ollama.

**Flow per user message:**
1. Append user message to conversation history
2. Send messages + available tools to Ollama
3. If Ollama responds with tool calls → execute each against MCP server → append results → loop
4. If Ollama responds with text → print answer → wait for next user input

**Memory**: The `messages` list persists across the entire session, giving Ollama full conversation history.

---

## Database Schema

A demo e-commerce database (`pg_mcp_demo`) with 4 tables:

```
customers → orders → order_items ← products
```

| Table | Rows | Description |
|---|---|---|
| `customers` | 5 | name, email, country |
| `orders` | 6 | customer_id, status, total_amount |
| `order_items` | 12 | order_id, product_id, quantity, unit_price |
| `products` | 8 | name, category, price, stock |

---

## Setup

### Prerequisites
- WSL2 Ubuntu
- Python 3.14+
- `uv` package manager
- PostgreSQL installed and running
- Ollama installed and running with `qwen2.5:7b` pulled

### PostgreSQL Setup
```bash
sudo service postgresql start

sudo -u postgres psql -c "CREATE USER pgmcp WITH PASSWORD 'pgmcp_dev' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE pg_mcp_demo OWNER pgmcp;"
```

### Seed the Database
```bash
psql -h localhost -U pgmcp -d pg_mcp_demo << 'EOF'
-- (paste full seed SQL here)
EOF
```

### Python Environment
```bash
uv sync
```

### Environment Variables
Create a `.env` file in the project root:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pg_mcp_demo
DB_USER=pgmcp
DB_PASSWORD=pgmcp_dev
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

---

## Running

### Interactive chat
```bash
python src/pg_mcp/client.py
```

Type your question, press Enter. Type `exit` or `quit` to end the session.

### MCP Inspector (for development)
```bash
mcp dev src/pg_mcp/server.py
```

Opens a browser-based UI to manually call tools and resources.

### Test database layer
```bash
python main.py
```

---

## Key Design Decisions

### Why MCP?
MCP (Model Context Protocol) is an open standard for connecting LLMs to external data and tools. Using it means the server is not Ollama-specific — any MCP-compatible client could connect to it.

### Tools vs Resources
- **Tools** are actions — the LLM invokes them to do something (`run_query`, `list_tables`)
- **Resources** are data — the LLM reads them for context (`schema://database`)

### Why asyncpg?
asyncpg is a high-performance async PostgreSQL driver. Since MCP servers are async by nature, using a synchronous driver would block the event loop. asyncpg integrates cleanly.

### Why `qwen2.5:7b`?
Best tool-calling performance at a reasonable size (~4.7GB). Runs entirely on the RTX 4000 GPU. Other good options: `qwen2.5:14b` or `qwen2.5:72b` for better accuracy.

### Read-only security
`run_query` rejects non-SELECT queries. This is intentional — the LLM should never be able to modify or delete data. For a production system, consider also running the DB user with read-only PostgreSQL permissions.

### sys.path hack in server.py
`mcp dev` runs `server.py` as a standalone script, bypassing the `src/` package structure. The `sys.path.insert` at the top of `server.py` works around this by explicitly adding the project root to Python's module search path. This is a known limitation of how `mcp dev` loads files.

### System prompt
Ollama needs explicit instructions to always use tools before answering. Without the system prompt, `qwen2.5:7b` sometimes describes a query instead of running it, or guesses column names instead of calling `describe_table` first.

---

## Known Issues / Quirks

- **Duplicate answers**: `qwen2.5:7b` occasionally repeats its final answer twice in `message.content`. This is a model behaviour quirk, not a code bug.
- **`mcp dev` and imports**: The `sys.path` hack is required because `mcp dev` loads server files as standalone scripts. The `pyproject.toml` entry point (`pg-mcp = "src.pg_mcp.server:mcp"`) works correctly for production use but not for `mcp dev`.
- **WSL2 PostgreSQL startup**: PostgreSQL does not auto-start on WSL2 boot. Run `sudo service postgresql start` before using the project.

---

## What's Next (Real Project)

This demo project established the foundation. The real project will build on:

- The same MCP server + client architecture
- The same `database.py` pattern for async PostgreSQL access
- The same tool calling loop in the client
- A real production database schema (replacing the demo e-commerce data)
- Likely additional tools (INSERT/UPDATE with validation, more complex queries)
- Better error handling and logging
- Possibly a web frontend instead of a terminal client

---

## Dependencies

```toml
dependencies = [
    "asyncpg>=0.31.0",
    "mcp[cli]>=1.26.0",
    "ollama>=0.6.1",
    "python-dotenv>=1.2.2",
]
```

---

## Services

To start all required services on WSL2:
```bash
sudo service postgresql start
sudo service ollama start   # if not already running as a service
```
