# Architecture & Design Decisions

This document records the *why* behind the system — the decisions that shaped it,
including the ones deliberately deferred. It is written for a reviewer who wants
to know whether the choices were made on purpose.

## 1. Which agents are actually agents

The original design specified nine "agents" in a linear chain. Most were not
agents at all — embedding is `model.encode()`, cleaning is regex normalization,
retrieval is a `SELECT ... ORDER BY embedding <=> $1`. None reason, plan, or
branch. Wrapping deterministic functions in LLM agent scaffolding burns tokens
and latency for zero benefit.

The system uses LLM reasoning in exactly the places that need it:

- **Resume parsing** — a single structured-output call, not a multi-step chain.
- **Interview generation** — a real LangGraph state machine (see §4).
- **Report generation** — a single structured call (see §4).

Everything else — text extraction, normalization, embedding, scoring, ranking,
retrieval — is deterministic service code. This is the central architectural
stance: *reserve the graph for genuine conditional reasoning; make everything
else a plain, testable, cheap function.*

## 2. Three processing modes

- **Batch (resume processing):** async background job. A parse takes 15–45s, so
  it cannot block an HTTP request. The pipeline uses three short transactions —
  mark processing (commit, release connection), do the slow LLM + embedding work
  holding NO DB connection, then write results in a fresh transaction. This is
  what keeps a 50–200 resume batch from exhausting the connection pool.
- **Triggered (ranking):** synchronous deterministic computation, no LLM.
- **Interactive (interview/report):** on-demand, streamed over SSE.

## 3. Deterministic, evidence-backed scoring

Ranking is deterministic and LLM-free — correct because a recruiter acts on the
number, and non-determinism has no place there. Five sub-scores, each normalized
to [0, 1] on the **same scale** before weighting (the property that makes a
weighted sum meaningful rather than arithmetic noise):

| Factor | Weight | Method |
|--------|--------|--------|
| Skills | 35% | Blended: exact lexical (full credit) + semantic fallback (discounted) |
| Experience | 25% | Saturating `min(years/required, 1.0)` — over-qualification doesn't inflate |
| Education | 15% | Degree-level ranking + field alignment |
| Semantic | 15% | Full-document cosine, rescaled to [0, 1] |
| Certifications | 10% | Fraction of JD skill areas with a matching cert |

The lexical-vs-semantic tension is resolved *inside* the skill sub-score, not by
a global weight tilt: exact matches are high-precision and count fully; semantic
matches are high-recall and count at a discount. The disagreement becomes typed
evidence (`exact` vs `semantic@0.81`), not a hidden bias. Every sub-score ships
with its evidence, so `0.73` is a defensible artifact.

Weights renormalize to sum 1.0 defensively, and are configurable per job.

## 4. Interview = graph, report = call

Both are named "agents," but only one needs a graph.

**Interview → LangGraph state machine.** It genuinely needs conditional control
flow: generate per category, loop across categories without repetition, then
*conditionally* loop into follow-up probes when required skills are unmet. That
is a cycle with conditional edges and accumulating state (additive reducers on
`questions` and `covered_categories`), bounded by `max_followup_rounds` so it
always terminates.

**Report → single structured call.** It has all inputs up front (profile,
scoring evidence, JD) and produces one object. No branching, no cycle. Wrapping
it in a graph would repeat the anti-pattern from §1. It is a plain call, and the
code says so.

## 5. Model routing and embeddings

- **LLM parsing:** Groq (`llama-3.3-70b`) when reachable, Gemma (`gemma3:4b` via
  Ollama) offline. Selected by a 3s health check in `auto` mode.
- **Embeddings:** in-process `sentence-transformers` (bge-small, 384-dim) by
  default — so the container stack needs no external model server — or
  nomic-embed via Ollama (768-dim) for a fully-offline path. The embedding
  interface carries `.dimension`; the pgvector column and migration read it from
  config, so switching providers is a config + migration change, not a rewrite.

Groq and Gemma are LLMs and produce no embeddings; the embedding path is always
a separate model. This separation is deliberate and load-bearing.

## 6. Authentication and SSE

JWT access (15m) + refresh (7d) with rotation and single-use refresh tokens.
Passwords use bcrypt directly (no passlib version trap); tokens use PyJWT (not
the unmaintained python-jose).

The frontend SSE client is built on `fetch` + `ReadableStream`, **not**
`EventSource` — because every request is bearer-authenticated and `EventSource`
cannot set headers. This is the one frontend detail that silently breaks a naive
SSE implementation against a JWT backend.

## Known limitations & deferred decisions

These are deliberate deferrals, not oversights.

- **In-process background tasks.** Resume parsing uses FastAPI `BackgroundTasks`.
  A process restart mid-parse orphans the task (resume stuck in `processing`,
  no retry). Fine for this scale; production needs Celery + Redis and a startup
  reconciliation sweep. Named here so it's a decision, not an accident.
- **Skill semantic fallback cost.** Matching embeds unmatched JD skills against
  candidate skills at rank time — O(jd × candidate) embedding calls. The fix is
  to cache skill vectors at parse time and do pure cosine at rank time.
- **Scoring context recompute.** The report/interview agents recompute the
  deterministic `MatchResult` rather than reading a persisted evidence blob. This
  reflects *current* job config, which is correct, but means a weights change
  between rank and report changes the report's evidence.
- **Token storage.** The frontend stores tokens in `localStorage` — simple, but
  XSS-exposed. Production wants httpOnly cookies and a backend cookie-auth path.
- **Frontend tests.** The backend has hermetic unit tests; the React layer has
  none. Playwright E2E through the streaming flow would close this.
