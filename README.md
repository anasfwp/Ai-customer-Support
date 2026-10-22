# AI Customer Support Knowledge Assistant

A Retrieval-Augmented Generation (RAG) system that lets a company upload its documents once, then allows employees and/or customers to ask natural-language questions and get accurate, cited answers pulled from that company's own knowledge base — not from general internet knowledge.

See [`PRD_AI_Customer_Support_Knowledge_Assistant.md`](./PRD_AI_Customer_Support_Knowledge_Assistant.md) for the full product spec and [`projectmap.md`](./projectmap.md) for the codebase layout.

## Project structure

```
backend/    FastAPI backend (API, auth, RAG pipeline, DB models)
frontend/   Admin/dashboard app (scaffolded, in progress)
widget/     Embeddable chat widget (scaffolded, in progress)
docs/       Additional documentation
infra/      Deployment/infra config
scripts/    Utility scripts
```

## Backend setup

**Prerequisites:** Python 3.11+ and pip.

```bash
cd backend

# create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate   # Git Bash on Windows
# venv\Scripts\activate.bat    # cmd.exe
# venv\Scripts\Activate.ps1    # PowerShell

# install dependencies
pip install -r requirements.txt

# configure environment variables
cp .env.example .env
```

Then open `backend/.env` and fill in your own values:

| Variable | Description |
|---|---|
| `DATABASE_URL` | DB connection string. Defaults to local SQLite (`sqlite:///./knowledge.db`); use a Postgres URL (with `pgvector`) for production. |
| `LLM_PROVIDER` | Which LLM provider to use: `gemini` (default), `openai`, or `groq`. Switching providers changes the embedding model, so re-upload your documents afterwards. |
| `OPENAI_API_KEY` | Required if `LLM_PROVIDER=openai`. |
| `GEMINI_API_KEY` | Required if `LLM_PROVIDER=gemini`. |
| `GEMINI_MODEL` | Optional comma-separated chat models, tried in order (default `gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-flash-lite-latest`). |
| `GROQ_API_KEY` | Required if `LLM_PROVIDER=groq`. |
| `SECRET_KEY` | Secret used to sign auth tokens — generate a random string, don't reuse examples. |
| `ALGORITHM` | JWT signing algorithm (default `HS256`). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Auth token lifetime in minutes. |
| `DEBUG` | `True`/`False` — enables FastAPI debug behavior. |
| `ALLOWED_ORIGINS` | JSON list of origins allowed by CORS, e.g. `["http://localhost:3000"]`. |

**Never commit `.env`** — it's already listed in `.gitignore`. Use `.env.example` as the template for what needs to be set.

Run the API:

```bash
uvicorn app.main:app --reload
```

- API root: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Frontend setup

**Prerequisites:** Node.js 18+.

```bash
cd frontend
npm install
cp .env.example .env   # only needed for a production build; local dev proxies to localhost:8000 automatically
npm run dev
```

- App: http://localhost:5173

## Follow-up questions (query rewriting)

A follow-up like *"How long does it take?"* means nothing to a search engine on its own. When a conversation already has earlier turns, the LLM first rewrites the follow-up into a standalone query (*"How long does international shipping take?"*) from the last 3 turns, and the answer is generated from it too. The UI shows it as "Searched for: …".

- The original wording is searched alongside the rewrite and the results are fused, so a poor rewrite can't hide what was actually asked.
- If the rewrite fails or takes over 10 seconds, it falls back to *previous question + follow-up*, which needs no LLM call.
- History comes only from the asking user's own turns in that conversation.
- `QUERY_REWRITE` = `followups` (default), `always` or `off`. Measured on 16 ambiguous follow-ups (`backend/eval/followups.jsonl`, hybrid + rerank, Gemini): MRR 0.541 searching the follow-up as asked, 0.797 with the LLM rewrite, 0.875 with the previous-question fallback; the right chunk is in the top 5 for all 16 with either. Without the reranker the rewrite scores 0.906; the reranker demotes the right chunk on a few follow-ups.

## Teams and document permissions

- Registering creates a new company with you as its **admin**. Admins add teammates in **Settings → Team**.
- Each document is visible to **everyone in the company** (the default) or **only specific people**. Its uploader and the company's admins can always see it, and only they can change its sharing or delete it.
- The check runs inside retrieval itself (`app/core/permissions.py`), so a restricted document's text can never reach another user's answer or citations. Members see only their own chat history; admins see everyone's, plus analytics.

## Deploying to Render

See [`DEPLOY.md`](./DEPLOY.md) for a step-by-step guide to deploying the backend, frontend, and a managed Postgres database using the included `render.yaml` Blueprint.

## Contributing

Standard flow: create a branch, make your changes, commit, and push. Keep secrets out of commits — only `.env.example` files should ever be tracked, never `.env` itself.
