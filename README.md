# EcoTi — Economic Trust Intelligence

A self-healing **multi-agent swarm** for India's financial-fraud frontline — fusing
digital-arrest scam detection, fraud-network graph mapping, counterfeit-currency
vision, geospatial crime patterning and a multilingual citizen shield into one
command centre. Built for the ET AI Hackathon 2026 (PS#6). See
[`EcoTi_Build_Blueprint.md`](EcoTi_Build_Blueprint.md) for the full brief.

> **This is the P0 scaffold.** The full swarm, A2A event bus, self-healing planner,
> fusion correlator and Command Centre UI all run **end-to-end with zero GPU and no
> API keys** — the ML models are deterministic stubs. Real Ollama/Groq/PyTorch models
> drop in via `api/core/llm.py` and each agent's sub-agent interface in P1+.

## Stack

| Layer         | Choice                                                                                              |
| ------------- | --------------------------------------------------------------------------------------------------- |
| Backend       | Django 5 + DRF +**Channels** (WebSocket live feed) + Celery                                   |
| Frontend      | Next.js 15 (App Router) + Tailwind + MapLibre                                                       |
| AI runtime    | `stub` (default) · **Ollama** (edge/offline) · **Groq** (cloud) — `LLM_PROVIDER` |
| Orchestration | LangGraph swarms wrapped as a Django service                                                        |
| Data          | Postgres + pgvector · Neo4j (optional) · Redis                                                    |

## Run

```bash
cp .env.example .env
docker compose up --build
```

- Command Centre → http://localhost:3000
- Citizen Shield → http://localhost:3000/shield
- Django admin (audit + evidence packets) → http://localhost:8000/admin  (`admin` / `admin`)
- Enable local LLMs: `docker compose --profile ollama up` then `LLM_PROVIDER=ollama`.

### Local backend only (no Docker)

```bash
cd api
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate && python manage.py seed_demo
python manage.py test          # core tests: schema, fusion, self-heal
daphne -b 0.0.0.0 -p 8000 ecoti.asgi:application
```

## Demo script (blueprint §4)

1. **Command Centre** → click **Run fusion demo**. `scam_call` then `fraud_graph` fire on
   the same number `+919812345678`; the correlator emits one **FusedTrustRisk** (≥2 signals),
   visible live in the feed. An **EvidencePacket** (pending approval) appears in Django admin.
2. **Self-healing** → set `FORCE_GNN_FAILURE=1` and re-run: the planner reroutes
   `fraud_graph` GNN → rule-based linkage, the watchdog pushes a **self-heal toast**, and the
   reroute is logged in admin → AgentHealth.
3. **Citizen Shield** → paste a scam message, pick a language, tick **Offline** → instant
   localized verdict + one-tap I4C/1930 report draft, served on-device.

## Self-healing demo toggle

```bash
# in .env
FORCE_GNN_FAILURE=1
```

## Architecture (P0)

```
Channels (WhatsApp/IVR/App)
   │
   ▼
Fusion Orchestrator  ── planner (self-heal) · correlator (≥2 → TrustRisk) · watchdog
   │  A2A event bus {module, signal, payload, confidence, ts}  (Redis + Channels)
   ▼
 scam_call · counterfeit_vision · fraud_graph(+rule fallback) · geo_command · citizen_shield
   each = a swarm of named sub-agents (LangGraph)
```

## Alternatives (swappable, one module each)

- **Async jobs:** Celery+Redis *(chosen)* · Django-Q2 · Dramatiq
- **Graph store:** Neo4j *(chosen)* · Memgraph · Postgres adjacency (`NEO4J_ENABLED=0`)
- **Vector store:** pgvector *(chosen)* · Qdrant · Chroma
- **Map:** MapLibre *(chosen)* · deck.gl · Leaflet

## Layout

```
api/   Django backend — core/ (events·bus·swarm·llm·models) · orchestrator/ · agents/ · apiviews/
web/   Next.js command centre — dashboard · shield · components · lib (ws/api)
```
