# AI Customer Support Knowledge Assistant

Upload your company's documents, then ask questions in plain language and get answers with citations, drawn only from those documents.

## Features

- Hybrid search (vector + keyword) with reranking
- Streaming answers with source citations
- Follow-up questions that understand the conversation so far
- Separate workspaces per company, with team members and per-document sharing
- Analytics and answer feedback

**Stack:** FastAPI, React + TypeScript (Vite), PostgreSQL with pgvector (SQLite for local use). Works with Gemini (default), OpenAI, or Groq.

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and set:

- `GEMINI_API_KEY`: your Gemini API key
- `SECRET_KEY`: a random string of at least 32 characters. To generate one:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`

Then start it and open http://localhost:8080:

```bash
docker compose up --build
```

## Run without Docker

Requires Python 3.12 and Node.js 18+. Create `backend/.env` as above first.

**Backend** (http://localhost:8000, API docs at `/docs`):

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend** (http://localhost:5173):

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
pytest
```

## Deployment

See [DEPLOY.md](./DEPLOY.md) to deploy on Render.

## Security

Keep API keys in `backend/.env`, which is ignored by git. Never commit real keys.
