# Project Map — AI Customer Support Knowledge Assistant

This document defines the complete file/folder structure for the project.

```
ai-support-knowledge-assistant/
│
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI app entrypoint
│   │   ├── config.py                      # Env vars, settings (pydantic-settings)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                    # Shared dependencies (auth, db session, tenant scoping)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py                # /auth/login, /auth/register
│   │   │       ├── tenants.py             # /tenants CRUD
│   │   │       ├── documents.py           # upload, list, delete documents
│   │   │       ├── chat.py                # /chat/query, /chat/history
│   │   │       └── analytics.py           # usage stats, unanswered questions
│   │   │
│   │   ├── core/
│   │   │   ├── security.py                # JWT creation/validation, password hashing
│   │   │   └── logging.py                 # App-wide logging config
│   │   │
│   │   ├── db/
│   │   │   ├── base.py                    # SQLAlchemy base, session factory
│   │   │   ├── models/
│   │   │   │   ├── tenant.py
│   │   │   │   ├── user.py
│   │   │   │   ├── document.py
│   │   │   │   ├── chunk.py               # stores text + pgvector embedding + metadata
│   │   │   │   ├── chat_log.py
│   │   │   │   └── feedback.py
│   │   │   └── migrations/                # Alembic migrations
│   │   │
│   │   ├── services/
│   │   │   ├── document_parser.py         # PDF/DOCX/HTML text extraction
│   │   │   ├── chunker.py                 # Splits text into semantic chunks
│   │   │   ├── embedding_service.py       # Calls embedding model, returns vectors
│   │   │   ├── retriever.py               # Vector similarity search (pgvector)
│   │   │   ├── rag_pipeline.py            # Orchestrates retrieval + LLM generation
│   │   │   ├── llm_provider.py            # Abstraction over OpenAI/Gemini/Groq
│   │   │   └── analytics_service.py       # Aggregates usage/unanswered question data
│   │   │
│   │   ├── schemas/
│   │   │   ├── tenant.py                  # Pydantic request/response models
│   │   │   ├── document.py
│   │   │   ├── chat.py
│   │   │   └── user.py
│   │   │
│   │   └── utils/
│   │       ├── file_storage.py            # S3-compatible object storage helper
│   │       └── prompt_templates.py        # Grounding/system prompts for the LLM
│   │
│   ├── tests/
│   │   ├── test_documents.py
│   │   ├── test_chat.py
│   │   ├── test_tenant_isolation.py       # Critical: cross-tenant leakage tests
│   │   └── conftest.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx          # Admin: document management
│   │   │   ├── AnalyticsPage.tsx
│   │   │   └── ChatPage.tsx               # Internal agent chat interface
│   │   │
│   │   ├── components/
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ChatMessage.tsx            # Renders answer + citation
│   │   │   ├── CitationBadge.tsx
│   │   │   └── UsageChart.tsx
│   │   │
│   │   ├── api/
│   │   │   └── client.ts                  # API client (fetch/axios wrapper)
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useChat.ts
│   │   │
│   │   └── styles/
│   │       └── theme.ts                   # Client branding/theming config
│   │
│   ├── package.json
│   └── Dockerfile
│
├── widget/
│   ├── src/
│   │   ├── index.tsx                      # Embeddable widget entrypoint
│   │   ├── ChatBubble.tsx
│   │   └── widgetLoader.ts                # Script-tag loader logic
│   ├── package.json
│   └── build.config.js                    # Bundles widget into a single embeddable JS file
│
├── infra/
│   ├── docker-compose.yml                 # Local dev: backend + frontend + postgres
│   ├── docker-compose.prod.yml
│   └── nginx/
│       └── nginx.conf
│
├── docs/
│   ├── PRD_AI_Customer_Support_Knowledge_Assistant.md
│   ├── onboarding_checklist.md            # Client onboarding steps
│   └── api_reference.md
│
├── scripts/
│   ├── seed_synthetic_data.py             # Loads sample company docs for demos
│   └── evaluate_retrieval.py              # Basic retrieval quality eval script
│
├── .env.example
├── .gitignore
├── README.md
└── projectmap.md                          # This file
```

## Notes on Structure

- **Tenant isolation** is enforced at the `chunk` and `chat_log` model/query level via a required `tenant_id` filter — never optional, never inferred from the frontend alone.
- **`llm_provider.py`** abstracts the actual LLM vendor so you can swap between OpenAI, Gemini, or Groq per client based on cost/quality needs without touching the rest of the pipeline.
- **`widget/`** is a separate build target from `frontend/` because it needs to compile down to a single embeddable script, isolated from the admin dashboard's dependencies.
- **`scripts/seed_synthetic_data.py`** is useful for client demos — populate a fake company's policies/FAQs to show the tool working before a client uploads their real documents.
