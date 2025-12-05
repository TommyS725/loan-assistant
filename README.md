# Loan Assistant — Streamlit + Watsonx.ai

This repository is a focused prototype implementation of a Loan Assistant that combines an interactive chat interface, a small demo relational database, and a retrieval-augmented generation (RAG) layer for contextual answers.

This prototype is designed for evaluation and rapid iteration rather than production deployment. Use it to validate interaction patterns, inspect RAG behavior, and prototype tool integrations (APR calculators, eligibility checks, etc.).

**Highlights**

- ReAct-style agent architecture powered by LangChain concepts.
- Streamlit UI with a simple chat interface and an "Applied Loans" viewer.
- Lightweight RAG index and local vector store for quick retrieval experiments.
- Small seeded SQLite demo DB with example loans and users for local testing.
- IBM Granite Guardians for prompt filtering and safety.

**Repository layout**

- `src/` — application code (agent, RAG, prompts, UI)
- `src/app.py` — Streamlit app entrypoint
- `src/state.py` — typed `AppState` wrapper for `st.session_state`
- `src/db.py` — demo DB initialization and helpers
- `src/agent.py`, `src/llm.py`, `src/rag.py`, `src/tools.py` — agent and integration glue
- `data/`, `documents/`, `chroma_db/` — sample content and local vector store

**Quick start (development)**

1. Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Provide credentials and optional overrides (recommended via a `.env` file or Streamlit secrets). Example variables used in this repo's `.env.example`:

- `WATSONX_URL` — watsonx.ai endpoint
- `WATSONX_APIKEY` — watsonx API key
- `WATSONX_MODEL_ID` — default model identifier
- `WATSONX_PROJECT_ID` — optional project context

3. Run the app locally:

```bash
streamlit run src/app.py
```

Then open the URL printed by Streamlit. Use the sidebar to pick a demo user, upload documents (optional), and switch between Chat and Applied Loans.

**Github Repository**
[https://github.com/TommyS725/loan-assistant](https://github.com/TommyS725/loan-assistant)
