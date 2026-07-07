
# EcoTi — Economic Trust Intelligence

### ET AI Hackathon 2026 · Problem Statement #6 — AI for Digital Public Safety

**Tagline:** *"From point-of-complaint to point-of-contact — one self-healing trust brain for India's financial frontline."*

**One-liner:** EcoTi is a multi-agent **swarm** that fuses live digital-arrest scam detection, fraud-network graph mapping, counterfeit-currency vision, geospatial crime patterning, and a multilingual citizen shield into one command centre — detecting threats *at the point of contact, before money moves*. It keeps working offline via on-device small LLMs and recovers from its own failures via a self-healing planner.

> **Name:** EcoTi = **Eco**nomic **T**rust **I**ntelligence — ET-panel aligned, fraud-theme exact.

---

## 0. Theme alignment (90 / 10)

This build is **~90% PS#6** and **~10% beyond-the-brief innovation** — exactly where the Innovation score (25%) is won.

- **90% = the brief.** Every one of EcoTi's six modules maps 1:1 to PS#6's own "What You May Build" list and its "Suggested Technologies." Nothing invented off-theme.
- **10% = the edge.** Three modern layers the brief doesn't ask for but every judge will reward: **agentic swarms**, **on-device small LLMs** (privacy + offline resilience), and a **self-healing** control plane (a public-safety system must never go dark).

---

## 1. PS#6 → EcoTi module map (1:1, plain working names)

Every module = a **swarm** of specialist sub-agents under a planner, not a single LLM call.

| PS#6 "What You May Build"                 | EcoTi module (working name)                       | Swarm sub-agents                                                                 | Reuse source                                      | Edge / self-healing layer                                                                                                    |
| ----------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Digital Arrest Scam Detection & Alerting  | **Scam-Call Detection Agent**               | transcriber · script-matcher · voice-spoof detector · verdict-writer          | ET AI News Pipeline (scam-script feed)            | On-device transcribe + first-pass classify (Gemma 4 E4B) so it works on a low-end phone with no cloud                        |
| Counterfeit Currency Identification Agent | **Counterfeit Currency Vision Agent**       | feature-locator · microprint checker · serial validator · authenticity scorer | Your pathology CV (H-Optimus / tile-MIL transfer) | Runs fully offline on a teller's phone via on-device VLM (Qwen-VL 7B / Gemma 4 multimodal)                                   |
| Fraud Network Graph Intelligence          | **Fraud-Network Graph Agent**               | ingest · GNN scorer · cluster-builder · evidence-packager                     | DRISHTI-PRAVAHA GNN                               | Self-healing: degrades to rule-based linkage if GNN service drops                                                            |
| Geospatial Crime Pattern Intelligence     | **Geospatial Crime-Pattern Command Centre** | hotspot mapper · patrol prioritiser · inter-district alerter                   | DRISHTI-PRAVAHA geo + Next.js front               | —                                                                                                                           |
| Citizen Fraud Shield (Multi-channel)      | **Citizen Fraud Shield**                    | risk assessor · guided-reporter (I4C/NCRB) · advisory generator                | NYAYA-RAKSHAK (≈70% drop-in)                     | On-device multilingual SLM (Qwen 3.6 edge, 12+ Indic langs) → instant verdicts even offline / in low-connectivity districts |
| *(orchestration — the glue)*           | **Fusion Orchestrator**                     | planner · correlator · escalation-gate · watchdog                             | ERAYA backbone                                    | Self-healing planner: reroutes around any failed agent; watchdog respawns crashed swarm nodes                                |

---

## 2. Architecture

```
  Channels                ┌──────────────────────────────────────────────┐
 ┌──────────┐             │           FUSION ORCHESTRATOR                 │
 │ WhatsApp │──┐          │  Swarm control plane: planner · correlator ·  │
 │  IVR     │──┼─►Citizen ─┤  escalation-gate · WATCHDOG (self-healing)    │
 │  App     │──┘  Shield  │  LangGraph + Swarms(SwarmRouter) + MCP + A2A   │
 └──────────┘             └───┬──────────┬──────────┬───────────┬─────────┘
                              ▼          ▼          ▼           ▼
                         Scam-Call   Counterfeit  Fraud-Graph  Geo Command
                          Detection    Vision      Agent        Centre
                          (swarm)     (swarm)     (swarm)       (swarm)
  ── Compute tiers ───────────────────────────────────────────────────────
  EDGE (phone / teller device): small LLMs — verdicts, transcription,
        note-vision — run locally for privacy + offline resilience.
  CLOUD (your GCP L4 GPU): heavy reasoning, GNN training, cross-signal
        fusion, big-context RAG.
  SELF-HEALING: if cloud is unreachable or an agent errors, the planner
        reroutes to the edge fallback and the watchdog restarts the node —
        the citizen is never left unprotected.
```

**Fusion logic:** each swarm emits a typed event `{module, signal, payload, confidence, ts}` on the A2A bus → orchestrator correlates by identifier (number / UPI handle / device) in a short window → if ≥2 independent signals cross threshold, it fires a single fused **TrustRisk** event → Citizen Shield alerts the victim + Command Centre drafts an auditable, court-admissible evidence packet (human-approval gate before any authority-facing report).

---

## 3. The 10% edge layer (your differentiators — say these out loud)

### a) Agentic swarms (not solo agents)

Each module is a small specialist team coordinated by a planner — parallel execution, hierarchical delegation, semantic routing. This is the 2026 production standard and directly serves the PS's "multi-source intelligence fusion." Use **Swarms (SwarmRouter + MCP)** or **LangGraph** for the graph; pick the pattern per module (sequential for Counterfeit, hierarchical for Fusion) and swap without rewriting agents.

### b) On-device / edge small LLMs

Public safety in India = unreliable connectivity + privacy-sensitive data (call audio, financial info). So the citizen-facing and field tools run **locally**:

- **Citizen Shield verdicts & advisories** → Qwen 3.6 edge (broad Indic multilingual) or Gemma 4 E4B, quantised, served via Ollama/llama.cpp on phone.
- **Scam-call transcription + first-pass score** → Gemma 4 E4B (native audio) on-device.
- **Counterfeit note check** → on-device VLM (Qwen-VL 7B / Gemma 4 multimodal) on a teller's phone — no image leaves the device.
- Cloud (L4) only for the heavy fusion, GNN, and big-context RAG.

This is privacy-by-design + a genuine accessibility story (works in a Tier-3 town with patchy 4G).

### c) Latest GenAI

RAG over MHA/I4C/RBI advisories + NCRB guidance using a current long-context model for the cloud reasoning tier; synthetic scam-script generation across 12 languages to bootstrap training data; voice anti-spoof for AI-generated scam voices (the brief explicitly flags AI-voice scams).

### d) Self-healing control plane

The orchestrator's **planner + watchdog**: on any agent error it finds an alternative route (cloud→edge fallback, GNN→rule-based), restarts crashed nodes, and logs every reroute. Maps straight onto Scalability (15%) and the "must be reliable" reality of safety infrastructure — and almost no hackathon team will demo graceful degradation.

---

## 4. Killer demo (build the product around THIS)

1. **00:00** — Judge's phone gets a mock WhatsApp/IVR "CBI digital-arrest" call (synthetic AI voice + fake-portal link).
2. **00:20** — **Scam-Call Detection** transcribes on-device, flags the script + synthetic voice → **Citizen Shield** pushes a red verdict *in the judge's language*: "Digital-arrest scam. No agency arrests over video. Do not pay." — *and you pull the network cable to prove it still works offline on the edge model.*
3. **00:40** — Same number/UPI hits **Fraud-Network Graph** → graph lights up: linked to a 14-node mule cluster across 3 districts.
4. **01:00** — **Geo Command Centre** pulses the hotspot, auto-drafts an I4C/MHA evidence packet (call metadata + graph + timestamps), human-approval gate visible.
5. **01:20** — **Counterfeit Vision**: hold a real + printed-fake ₹500 to the cam → instant verdict, failing security feature highlighted, all on-device.
6. **01:40** — **Fusion Orchestrator** dashboard: one fused TrustRisk event, five signals, one coordinated response — *before any money moved* — and a live "agent failed → rerouted" toast proving self-healing.

---

## 5. Tech stack (current, June 2026)

| Layer                  | Choice                                                                                | Note                                     |
| ---------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------- |
| Swarm orchestration    | LangGraph +**Swarms (SwarmRouter, MCP)** + A2A                                  | ERAYA backbone; swap patterns per module |
| Backend                | FastAPI                                                                               | your default                             |
| Command-centre UI      | Next.js + Tailwind + MapLibre/deck.gl                                                 | DRISHTI geo-front reuse                  |
| Citizen UI             | NYAYA-RAKSHAK multilingual conversational front                                       | ≈70% reuse                              |
| Edge LLM (citizen)     | **Qwen 3.6 edge** (multilingual) / **Gemma 4 E4B** via Ollama / llama.cpp | offline, on phone                        |
| Edge VLM (counterfeit) | **Qwen-VL 7B** / **Gemma 4 multimodal**                                   | on-device note vision                    |
| Speech                 | faster-whisper + voice anti-spoof (ASVspoof-trained)                                  | AI-voice detection                       |
| Counterfeit CV         | PyTorch tile-MIL + feature-localisation head                                          | transfer H-Optimus pattern               |
| Fraud graph            | PyTorch Geometric (GraphSAGE/GAT) +**Neo4j**                                    | DRISHTI GNN reuse                        |
| Cloud reasoning + RAG  | current long-context model on GCP L4 +**pgvector**                              | MHA/I4C/RBI corpus                       |
| Channels               | WhatsApp Business API + Asterisk/Twilio IVR                                           | NYAYA channel layer                      |
| Serving                | Ollama (edge) · vLLM / TensorRT-LLM (cloud)                                          |                                          |

---

## 6. Data sources (honest confidence)

| Module           | Data                       | Source                                                                                       | Confidence                                |
| ---------------- | -------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Scam scripts     | call templates/transcripts | I4C/MHA & Sanchar Saathi advisories + LLM-synthesised 12-lang                                | **75%**                             |
| Voice anti-spoof | AI-voice vs human          | ASVspoof / public deepfake-audio                                                             | **85%**                             |
| Counterfeit      | genuine vs fake notes      | RBI security-feature spec + captured genuine notes + augmentation (no large public FICN set) | **60% — frame as proof-of-method** |
| Fraud graph      | mule networks              | Elliptic (proxy) + synthetic UPI graphs                                                      | **70%**                             |
| Geo              | complaint/seizure points   | NCRB aggregates + district shapefiles + synthetic                                            | **80%**                             |

> State proxy/synthetic data explicitly in the deck — the PS eval focus literally rewards explicit, testable assumptions and penalises overclaiming.

---

## 7. Build plan (~36h, reuse-first)

| Phase      | Hrs    | Do                                                                                                                                                                |
| ---------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P0 Lift    | 0–4   | Merge ERAYA orchestrator + NYAYA front + DRISHTI geo/GNN into one repo; bring up LangGraph+Swarms skeleton with 6 stub agents + A2A bus + watchdog stub           |
| P1 Core    | 4–14  | Citizen Shield (rewire NYAYA to fraud advisory, wire edge Qwen) + Scam-Call Detection (whisper + script-match + voice-spoof). Demo steps 1–2 incl. offline proof |
| P2 Graph   | 14–22 | Fraud-Network Graph: Elliptic→Neo4j, train GraphSAGE, number→cluster lookup + self-healing rule-based fallback. Demo 3–4                                       |
| P3 Wow     | 22–28 | Counterfeit Vision: tile-MIL + localisation overlay, on-device VLM path. Demo 5                                                                                   |
| P4 Fuse+UI | 28–33 | Orchestrator correlation + Command Centre dashboard + visible self-healing toast. Demo 6                                                                          |
| P5 Polish  | 33–36 | Demo video, deck, architecture diagram, 2 rehearsals                                                                                                              |

Cut order if time slips: drop Counterfeit Vision first; never cut the Scam-Call → Shield → Graph → Fusion spine.

---

## 8. PS#6 "Suggested Technologies" coverage (proves the 90%)

| PS#6 suggested tech                             | EcoTi                                             |
| ----------------------------------------------- | ------------------------------------------------- |
| Computer Vision (counterfeit, deepfake ID)      | Counterfeit Vision Agent + voice-spoof detector   |
| Graph AI & Network Analysis                     | Fraud-Network Graph Agent (GraphSAGE/GAT + Neo4j) |
| NLP / LLMs (scam script & voice classification) | Scam-Call Detection swarm + edge SLMs             |
| Geospatial Intelligence (crime mapping, patrol) | Geospatial Crime-Pattern Command Centre           |
| Speech AI (voice spoofing / AI-voice detection) | faster-whisper + ASVspoof anti-spoof              |
| Agentic AI for multi-source intelligence fusion | Fusion Orchestrator + per-module swarms           |

Full house — every suggested tech is covered.

## 9. Metrics (mirror PS#6 Evaluation Focus)

- Counterfeit detection accuracy across denominations & print quality (report per security-feature).
- Digital-arrest scam **precision & recall** (recall first — a miss = a victim).
- Fraud-network detection **lead time before mass victimisation** (cluster-growth curve).
- **Citizen-tool false-positive rate — keep very low, state explicitly.**
- Auditability: % of evidence packets fully timestamped + traceable.

## 10. Deck outline (rubric-weighted: Innovation 25 / Impact 25 / Tech 20 / Scale 15 / UX 15)

1. Hook — ₹1,776 cr digital-arrest loss in 9 months + 1.14M cybercrimes; "data exists, intelligence to act doesn't." *(Impact)*
2. The victim's 4 minutes — anatomy of a digital-arrest call. *(Impact)*
3. EcoTi in one line + the fusion-swarm diagram. *(Innovation)*
4. Live demo / video — incl. the offline + self-healing moments. *(UX + all)*
5. Architecture — six agents, swarm control plane, edge/cloud tiers. *(Tech)*
6. Under the hood — Scam-Call / Graph / Counterfeit method slides. *(Tech)*
7. The 10% edge — swarms + on-device SLMs + self-healing vs single-signal baselines. *(Innovation + Scale)*
8. Scale & deployment — national, multilingual, offline-capable, never-dark. *(Scalability)*
9. Honest metrics + assumptions + proxy-data disclosure. *(Tech credibility)*
10. Impact & ask — ₹/lives protected, roadmap, team. *(Impact)*

---

## 11. Build prompts (paste-ready for Claude Code)

**P0 — Swarm monorepo scaffold**

```
Scaffold a Python+Next.js monorepo "ecoti". Backend FastAPI in /api with a swarm
control plane "orchestrator" using LangGraph + the Swarms framework (SwarmRouter + MCP).
Define a typed A2A event bus (pydantic: {module, signal, payload, confidence, ts}).
Register 6 modules, each itself a sub-agent swarm: scam_call, counterfeit_vision,
fraud_graph, geo_command, citizen_shield, and the orchestrator (planner + correlator +
escalation_gate + watchdog). Implement a self-healing planner: on any sub-agent
exception, reroute to a registered fallback and have the watchdog restart the node;
log every reroute. Frontend Next.js command centre: agent-status rail, map, live fused
event feed with a "self-heal" toast. docker-compose with postgres+pgvector and neo4j.
```

**Scam-Call Detection swarm (with on-device path)**

```
Build the "scam_call" swarm: sub-agents transcriber (faster-whisper), script_matcher
(embedding match vs a pgvector store of digital-arrest scripts in hi/ta/kn/en),
voice_spoof (ASVspoof-trained classifier for synthetic voice), verdict_writer.
Add an EDGE mode that runs transcription + first-pass scoring locally via a quantised
Gemma 4 E4B through Ollama so it works with no network; cloud mode does full fusion.
Emit a typed A2A event with per-sub-agent confidences and the matched pattern.
```

**Counterfeit Currency Vision swarm (on-device VLM)**

```
Build "counterfeit_vision": a PyTorch tile-MIL classifier (genuine vs fake notes) with a
feature-localisation head returning a heatmap/boxes over the failing security feature
(microprint / thread / serial). Dataset loader: genuine note photos + augmentation
(print artifacts, blur, colour shift) to synthesise negatives. Provide an on-device
inference path via a quantised VLM (Qwen-VL 7B) so images never leave the teller's phone.
/verify returns verdict + per-feature scores + overlay. Mirror an H-Optimus tile-MIL design.
```

**Fraud-Network Graph swarm (self-healing fallback)**

```
Build "fraud_graph": load Elliptic into Neo4j, train a GraphSAGE node classifier
(PyTorch Geometric), expose /score(identifier) -> risk + linked-cluster subgraph JSON.
Add a self-healing fallback: if the GNN service is down, the planner switches to a
deterministic rule-based linkage scorer so the swarm still returns a result. Keep the
training loop transferable to a synthetic UPI-mule graph.
```

**Citizen Fraud Shield (adapt NYAYA, edge multilingual)**

```
Adapt the NYAYA-RAKSHAK multilingual conversational front into "citizen_shield": given a
forwarded message, number, or call event, return an instant verdict (safe/suspicious/scam)
+ guided steps + a one-tap I4C/NCRB report draft, localised into 12 Indic languages.
Run the verdict model on-device via a quantised Qwen 3.6 edge model (Ollama) for privacy
and offline operation; fall back to cloud only for complex cases.
```

**Fusion Orchestrator (correlation + escalation)**

```
Implement orchestrator correlation: subscribe to all module events, buffer by identifier
in a short window, emit a fused "TrustRisk" event when >=2 independent signals exceed
threshold. On fuse, trigger citizen_shield (alert) + geo_command (map pulse + auto-draft
evidence packet), gated behind a human-approval flag for any authority report. Surface
the planner's self-heal reroutes and watchdog restarts in the command-centre UI.
```

---

### Next

Say the word for: (1) **architecture diagram** rendered, (2) **10-slide .pptx**, or (3) the **orchestrator + A2A event-schema + self-healing planner code** for P0. Pick the order.
