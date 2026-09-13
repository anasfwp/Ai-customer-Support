# Deploying to Render

This repo includes a [`render.yaml`](./render.yaml) Blueprint that provisions three things in one go:

1. **`ai-support-backend`** — the FastAPI API (Python web service)
2. **`ai-support-frontend`** — the React admin dashboard (static site)
3. **`ai-support-db`** — a managed Postgres database (with the `pgvector` extension enabled automatically on first boot)

## 1. Push this branch to GitHub

Render deploys from a connected GitHub repo. This repo already has a remote — push your changes, then continue in the Render dashboard.

## 2. Create the Blueprint

1. Go to <https://dashboard.render.com/> → **New +** → **Blueprint**.
2. Connect the `AI-Customer-Support` GitHub repo (Render will detect `render.yaml` automatically).
3. Render will show the 3 resources above. Click **Apply**.

This creates the services but the backend **will fail to boot** until you set the real secrets in step 3 (they're intentionally left blank in `render.yaml` — see `sync: false`).

## 3. Set backend secrets

In the Render dashboard, open **ai-support-backend → Environment**, and set:

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | Your real OpenAI key (only needed if `LLM_PROVIDER=openai`, the default) |
| `GEMINI_API_KEY` / `GROQ_API_KEY` | Only if you switch `LLM_PROVIDER` to `gemini` or `groq` |

`SECRET_KEY` and `DATABASE_URL` are already generated/wired automatically by the Blueprint — you don't need to touch them.

> **Do not** put real API keys in `render.yaml` or commit them anywhere — always set them through the dashboard's Environment tab, which is encrypted at rest.

## 4. Fix up the cross-service URLs

Render assigns each service a URL like `https://ai-support-backend-xxxx.onrender.com` (the suffix is only added if the plain name is taken). After the first deploy:

1. Copy the frontend's actual URL → set it as `ALLOWED_ORIGINS` on the **backend** service (Environment tab). Comma-separate multiple origins if you add a custom domain later.
2. Copy the backend's actual URL → set it as `VITE_API_BASE_URL` on the **frontend** service, then trigger a manual redeploy of the frontend (Vite env vars are baked in at build time, so this needs a rebuild, not just a restart).

## 5. Verify

- Backend health check: `https://<backend-url>/health` → `{"status": "healthy"}`
- Backend docs: `https://<backend-url>/docs`
- Frontend: open the frontend URL, register a new account, upload `backend/sample_faq.txt`, and ask it a question.

## Notes / limitations to know about

- **Free Postgres expires after 30 days.** Render's free Postgres plan is meant for trials — it's deleted after 30 days unless you upgrade to a paid plan. For anything beyond a demo, upgrade `ai-support-db` to the Starter plan before that window closes, or you'll lose all uploaded documents/chat history.
- **Free web services spin down when idle** and take ~30–60s to wake up on the next request. Fine for a demo; upgrade to a paid instance type for production/customer-facing use.
- **pgvector**: the app automatically runs `CREATE EXTENSION IF NOT EXISTS vector` on startup against the Postgres database. If your Render Postgres plan doesn't permit creating extensions, document uploads will still be accepted but embeddings won't be queryable — check the backend's Render logs after first deploy for `Database initialization failed on startup` and enable the extension manually via the Render Postgres shell if you see that.
- **No Alembic migrations yet** — the app creates tables automatically on startup if they don't exist (`Base.metadata.create_all`). This is fine for a fresh deploy, but if you change model schemas later, you'll need to run a migration manually (or drop/recreate tables) since there's no migration framework wired up yet.
- **Retriever service (`app/services/retriever.py`)** is currently dead code — the real similarity search happens by loading all of a tenant's chunks into memory in `rag_pipeline.py` and computing cosine similarity in Python. That's fine at small scale (a few hundred/thousand chunks per tenant) but won't scale to a very large knowledge base; at that point, switch to a native pgvector `ORDER BY embedding <-> query_vector LIMIT k` query.
