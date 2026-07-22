# EcoTi — 7-Slide Pitch Deck
### Economic Trust Intelligence · ET AI Hackathon 2026 · PS#6 (AI for Digital Public Safety)

> **How to use:** each slide below has **① what to put on the slide** (short, big text) and **② what to say** (speaker script, ~15–25s). Keep slide text minimal — talk to it, don't read it. Live demo URL: **http://35.255.196.78/ecoti**

---

## SLIDE 1 — The Problem (Hook)  · *Impact*

**On the slide:**
- **Big:** "Every 4 minutes, an Indian loses money to a 'digital arrest' call."
- ₹1,776 crore lost in 9 months · 1.14M cybercrimes reported
- *"The data to stop it exists. The intelligence to act — at the moment of contact — doesn't."*

**Say:**
> Fraud in India isn't a data problem — it's an *action* problem. Scam calls, mule networks, fake notes, dark-web cash-out: the signals are all there, scattered across silos. By the time a victim reports it, the money is already gone. We built the missing brain that acts **at the point of contact, before money moves.**

---

## SLIDE 2 — The Solution (One-liner)  · *Innovation*

**On the slide:**
- **EcoTi — Economic Trust Intelligence**
- A **self-healing swarm of AI agents** that fuses 6 fraud signals into one verdict — in the citizen's language, on-device, even offline.
- *"From point-of-complaint to point-of-contact — one trust brain for India's financial frontline."*

**Say:**
> EcoTi is one command centre where six specialist AI agents work as a swarm — scam-call detection, a mobile-number risk check, a fraud-network graph, counterfeit-note vision, dark-web/Tor intelligence, and a multilingual citizen shield. A citizen forwards a suspicious number or message; in seconds EcoTi correlates every signal and replies with a verdict — *before any money is transferred.*

---

## SLIDE 3 — How It Works (Architecture)  · *Tech*

**On the slide:** (diagram + these labels)
- **Channels** (WhatsApp / IVR / App) → **Fusion Orchestrator**
- Orchestrator = **planner · correlator · watchdog** over an **A2A event bus**
- 6 agent swarms emit typed events → **≥2 independent signals = one fused "TrustRisk"**
- Auto-drafts a **court-ready evidence packet** (human-approval gate)
- **Self-healing:** any agent fails → planner reroutes, watchdog respawns — *never goes dark*

**Say:**
> Each module is a small swarm of sub-agents on a shared event bus. The orchestrator correlates signals by identifier — phone, UPI, device — and only when two *independent* agents agree does it fire a fused TrustRisk and draft an auditable evidence packet for I4C, gated behind human approval. And because public safety can't go offline, if any agent crashes the planner reroutes to a fallback and a watchdog restarts it — graceful degradation, live on screen.

---

## SLIDE 4 — Live Demo (What it does)  · *UX + Tech*

**On the slide:**
- **Command Centre** — live hotspot map, agent-health rail, fused-event feed, self-heal toasts
- **Citizen tools** — Scam-message Shield (12 Indic languages) · Number Check (5 fused signals) · Advisory Copilot (RAG over I4C/RBI/DoT)
- **Fraud Network** graph · **OSINT Footprint** · **Tor / dark-web Intel** · **Report Fraud**
- *Runs live at 35.255.196.78/ecoti*

**Say:**
> Here's the product, live. Paste a scam message — instant verdict in Hindi, on-device. Check a number — it returns "scam, 0.99," maps the 14-node mule cluster across three districts, and cites the reasons. The Advisory Copilot answers fraud questions grounded in official RBI and I4C advisories. Every citizen report grows a community watchlist. This isn't slides — it's deployed and working.

---

## SLIDE 5 — The Edge (Why us)  · *Innovation + Scale*

**On the slide:**
- **Real ML, zero training:** TabPFN (fraud) · Kimi-vision (counterfeit) · wav2vec2 (AI-voice detection) · PyOD (Tor anomalies)
- **Multi-signal fusion** (not one blocklist) → far fewer false positives
- **Sovereign Indic AI** (Sarvam) — 12 languages, offline-capable
- **OSINT + dark-web layer** (HIBP breach, holehe, Onionoo/Tor) most tools lack
- **Self-healing** control plane — reliability as a feature

**Say:**
> Three things set us apart. One — we fuse *six* independent signals, so a single false flag never triggers an alert. Two — it's genuinely multilingual and offline via India's own Sarvam AI, so it works in a Tier-3 town on patchy 4G. Three — real ML with *zero training*: pretrained TabPFN, vision, and voice-deepfake models plug straight in. And a self-healing core means a safety system that never goes dark.

---

## SLIDE 6 — Impact & Honesty (Metrics)  · *Impact + Tech credibility*

**On the slide:**
- **Recall-first** on scam detection — a miss is a victim
- **Very low citizen false-positive rate** (stated explicitly)
- **Lead time** before mass victimisation (mule-cluster growth curve)
- **100% auditable** — every evidence packet timestamped + traceable
- *Honest data: proxy/synthetic where public data doesn't exist (counterfeit, mule graph) — stated, not overclaimed*

**Say:**
> We optimise recall first — a missed scam is a victim, so we'd rather over-flag to a human than miss. Every fused event is fully timestamped and court-traceable. And we're honest about data: where India has no public dataset — fake notes, mule graphs — we use proxy and synthetic data and say so. We frame those as proof-of-method, not finished accuracy.

---

## SLIDE 7 — Scale, Roadmap & Ask  · *Scalability + Close*

**On the slide:**
- **National-ready:** multilingual, offline-capable, self-healing, cloud-optional
- **Deployed today** on a single VM — scales horizontally per agent
- **Roadmap:** WhatsApp/IVR channels · live OONI censorship map · deeper GNN mule-tracing
- **Ask:** pilot with I4C / a state cyber-cell · access to reported-number feeds
- **Impact:** ₹ and lives protected *before* money moves
- *"One self-healing trust brain for India's financial frontline."*

**Say:**
> EcoTi is built to scale nationally — multilingual, offline-capable, and reliable by design, already deployed and live. Next we plug into WhatsApp and IVR channels and real I4C number feeds. Our ask: a pilot with a state cyber-cell. Because the goal isn't reporting fraud faster — it's stopping it *before the money moves.* Thank you.

---

### Appendix — rubric mapping (for your own reference, don't slide it)
| Rubric | Weight | Where it lands |
|---|---|---|
| Innovation | 25 | Slides 2, 5 (fusion swarm, self-heal, zero-training real ML) |
| Impact | 25 | Slides 1, 6, 7 (₹1,776 cr, recall-first, lives before money moves) |
| Tech | 20 | Slides 3, 4, 6 (architecture, live demo, honest metrics) |
| Scalability | 15 | Slides 5, 7 (offline/multilingual/self-heal, national-ready) |
| UX | 15 | Slide 4 (live product, multilingual, on-device) |

### Delivery tips
- **Total time:** ~3–4 min for 7 slides + a 60–90s live demo on slide 4.
- Open on the **problem's human cost**, close on **"before money moves."**
- On slide 3, click **Run fusion demo** live and let a **self-heal toast** appear — that one moment wins Innovation + Scale.
- Say the numbers out loud once (₹1,776 cr / 4 minutes); don't crowd the slides with them.
