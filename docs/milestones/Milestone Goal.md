## M0 Goal

- Initialize repo
- Create the clean folder structure
- Bring up Docker services
- Add .env configuration

## M1 Goal - A runnable FastAPI backend

- Reads config from .env (including your Postgres port 5433)
- Proper logging setup
- /health endpoint
- pytest running with at least one test
- Documentation note for M1

## M2 — Milestone Goal

- FastAPI connected to Neo4j
- POST /concepts creates a Concept node in Neo4j
- GET /concepts/{concept_id} fetches the active Concept
- Basic error handling + logging
- Integration tests that actually hit Neo4j (not mocks)

## M3 — Milestone Goal

- POST /concepts/{concept_id}/evolve

    - Creates a new version node (v2, v3…)
    - Marks old active node as deprecated
    - Creates relationship: (new)-[:EVOLVED_FROM]->(old)

- GET /concepts/{concept_id}/history

    - Returns the full version lineage (latest → oldest)
    - Shows each version’s metadata (version, timestamps, status, confidence)

- Tests:

    - evolve creates new version
    - old version becomes deprecated
    - history returns correct ordering and count

- Neo4j constraints/indexes appropriate for versioned nodes

## M4 — Milestone Goal

- Data
    - A Postgres table query_logs storing:
        - query text
        - endpoint/source (where it came from)
        - timestamp
        - optional metadata (JSON)

- API
    - POST /queries/log → log a query signal
    - GET /queries/recent?limit=50 → retrieve recent query signals

- Tests
    - log a query → retrieve it back → pass

## M5 — Milestone Goal

- Embeddings generated when concepts are created/evolved
- concept_embeddings table in Postgres
- GET /search?query=...&limit=... returns similar concepts
- Search is logged to query_logs with metadata: matched concept ids + scores
- Deterministic tests

## M6 — Goal

- Clean environment + config hygiene (.env, .env.example, .gitignore)
- One-command developer workflow (run app, run tests)
- CI-ready test execution (same command locally and in pipelines)
- Test isolation improvements (no accidental deletion of real data)
- Startup checks + health checks (Neo4j, Postgres, Qdrant)
- Logging improvements (request correlation ID + structured logs basics)
- Consistent API docs (fix operation_id warnings, consistent routers)
- Documentation completion for Phase 1