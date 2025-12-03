AI Loan Assistant (watsonx.ai + LangChain design)

# Loan Assistant — Streamlit + Watsonx.ai (starter)

This repository contains a lightweight, developer-friendly scaffold for a Loan Assistant application. The app combines a chat interface, document analysis (vision + OCR), a small relational database for demo loan/user data, and a retrieval-augmented generation (RAG) surface for answering contextual questions.

The codebase is organized to make it easy to swap in real LLMs, wire production RAG connectors, and add tools (APR calculators, eligibility checkers, etc.). It is intended as a starting point for building an internal or prototype loan-assistant tool.

**Key features**

- Streamlit front-end with a chat UI and an "Applied Loans" viewer
- Typed session state wrapper (`src/state.py`) for safer session management
- Agent abstraction (ReAct-style) wired to a Watsonx adapter (mockable)
- Simple SQLite demo database seeded with loan and user examples
- Document upload + vision OCR helpers (PDF -> images -> vision model) and a simple local chunk index

## Directory overview

- `src/` — main application code (agent, db, rag, prompt, UI)
- `src/app.py` — Streamlit app and UI
- `src/state.py` — typed AppState stored in `st.session_state`
- `src/db.py` — demo database initialization and helpers
- `src/agent.py`, `src/llm.py`, `src/rag.py`, `src/tools.py` — agent + tooling glue
- `data/`, `documents/`, `chroma_db/` — sample data and local vector store folder

## Quick start (development)

1. Create and activate a virtual environment, then install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy or provide required secrets (recommended using a `.env` file or Streamlit secrets):

- `WATSONX_API_KEY` — required to call IBM watsonx.ai
- Optional: `WATSONX_PROJECT_ID`, `WATSONX_MODEL_ID`, `WATSONX_VISION_MODEL_ID`, `WATSONX_API_URL`, `WATSONX_VISION_API_URL`

You can create a `.env` at the repo root and Streamlit will read it in development.

Run the Streamlit app:

```bash
streamlit run src/app.py
```

Open the URL printed by Streamlit in your browser. Use the sidebar to select a user, upload documents (optional), and switch between Chat and Applied Loans.

## Configuration notes

- The project contains sensible defaults in code for testing, but for production you should set environment variables for Watsonx credentials and endpoints.
- The SQLite database used for demo data is initialized by `src/db.py` and seeded on first run. For concurrent or production workloads consider using PostgreSQL or another server RDBMS.

## Developer notes

- All heavy resources (LLM client, DB connection, RAG index, agent instance) are created once and stored in a typed `AppState` to avoid reinitialization across Streamlit reruns.
- Chat UI stores a short UI-only chat history (in `AppState.chat_history`) while the agent is expected to manage long-term memory if needed.
- Text normalization utilities are applied before rendering to handle invisible unicode characters (narrow no‑break spaces, zero‑width joiners) frequently introduced by OCR or serialized model outputs.

## Testing and debugging

- There are example notebooks and utilities for running the agent in `mock` mode (no external API calls) for unit tests and offline development.
- Add `print`/logging in `src/agent.py` and `src/llm.py` to debug request/response flows when integrating an LLM provider.

## Security & privacy

- Uploaded documents are stored locally in `/uploads` and indexed locally. Treat this as sensitive data and remove or secure files before sharing the environment.
- Do not commit secrets to Git. Use `.env` files or Streamlit secrets for private configuration.

## Next steps you might consider

- Add streaming responses to the chat UI for better UX with long LLM responses
- Persist chat history in a secure store if you need multi-session continuity
- Replace SQLite with a managed DB for multi-user, concurrent access
- Add more tool integrations (APR calculator, eligibility calculators, loan comparison table)

## Credits

- Built as a starter scaffold to explore combining Streamlit + Watsonx + RAG for domain-specific assistants.

## License

- MIT-style; adapt and extend as needed.
