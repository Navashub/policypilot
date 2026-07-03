# PolicyPilot — Phase 1: Auth & Multi-Tenancy Skeleton

An AI-powered HR/handbook assistant, built as a real multi-tenant SaaS product
(not a single-user demo) on top of a RAG core. This phase lays the foundation
everything else plugs into: organizations, users, JWT auth, API keys, and
org-scoped document records.

## What's in this phase

- **Postgres models**: `Org`, `User`, `Document`, `Conversation`, `Message`, `ApiKey`, `UsageEvent`
- **JWT auth**: signup (creates an org + owner user), login, refresh, `/auth/me`
- **API keys**: create/list/revoke, for programmatic access to the product later
- **Org-scoped documents**: `POST /documents/upload`, `GET /documents`, `DELETE /documents/{id}`
  — records are created and scoped to the caller's org, but ingestion (chunk/embed/index)
  is intentionally stubbed here; that's Phase 2 + Phase 4.
- **Alembic migrations**: schema is versioned from day one, not `create_all()`

## What's deliberately NOT here yet

- The actual RAG pipeline (retrieval, reranking, generation) — Phase 2
- Streaming answers + conversation memory — Phase 3
- Background ingestion via Celery — Phase 4
- Evaluation harness — Phase 5
- React frontend — Phase 6

This phase should run end-to-end on its own: you can sign up, log in, and
upload/list/delete documents (as inert records) through `/docs` right now.

## Running it

```bash
cp .env.example .env
# edit .env — at minimum set a real JWT_SECRET_KEY

docker compose up --build
```

This starts Postgres, Redis, Qdrant (unused until Phase 2+), and the API.
The `api` container runs `alembic upgrade head` automatically before starting
uvicorn, so the schema is created for you.

Visit `http://localhost:8000/docs`.

### Try it
1. `POST /auth/signup` with `org_name`, `email`, `password` → get back access + refresh tokens
2. Authorize in Swagger UI with the access token
3. `POST /documents/upload` with any file → creates a `pending` document record
4. `GET /documents` → see it scoped to your org

## Why these choices

- **JWT rolled by hand, not a managed provider** — deliberate, so the auth flow
  (hashing, token creation/verification, dependency-based guards) is fully
  visible and explainable, not hidden behind a third-party SDK.
- **Alembic from the start** — `Base.metadata.create_all()` is fine for a
  weekend project; a real product needs versioned, reversible schema changes.
- **Org-scoping baked into every query** — every document/conversation/usage
  query filters by `org_id` from the authenticated user's token, not from a
  client-supplied parameter. This is the actual mechanism that keeps tenants
  isolated — worth being able to explain precisely in an interview.

## Next: Phase 2

Wire `documents/ingestion.py` (the Day 1 extract/chunk logic) into a real
ingestion path, stand up Qdrant collections scoped by `org_id`, and build the
LangGraph retrieval pipeline: query rewrite → hybrid search (BM25 + vector via
`EnsembleRetriever`) → cross-encoder rerank → grounded generation.
