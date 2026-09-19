# CasePacket — Product Requirements Document (Build)

**Product:** CasePacket  
**Tagline:** Dark-web *signal* → LE-ready *case packet* on AWS  
**Event:** First Commit / Bharat Builds — **Ship It** track  
**Niche:** Cyber (India) — LE dark-web intel (lineage: KAVACH Cyph3r, CID ecode Track)  
**Version:** 1.0  
**Date:** 2026-09-19  
**Status:** Ready to build  

---

## 0. Research basis (agent-reach scan)

| Source | What we took |
|--------|----------------|
| [OpenCTI](https://github.com/OpenCTI-Platform/opencti) (~10k★) | TIP pattern: ingest → normalize → graph → export; connectors + workers + STIX |
| [MISP](https://www.misp-project.org/) | Share / store / correlate IOCs; taxonomies (TLP, ATT&CK); automation over chat |
| [TheHive](https://github.com/TheHive-Project/TheHive) + [Cortex](https://github.com/TheHive-Project/Cortex) | Case management + observable analysis engines |
| [Watcher](https://github.com/thalesgroup-cert/Watcher) | AI-powered CTI hunting (Django/React) — UI as analyst console |
| STIX 2.1 (OASIS) | Standard objects for indicators, observed-data, reports — export friendliness |
| AWS LE-style pipelines (e.g. serverless S3→EventBridge→Lambda→enrich) | Immutable raw evidence in S3; push-based orchestration; auditability |
| OpenCTI-on-AWS patterns (ECS + OpenSearch + Redis + S3) | Too heavy for a weekend — **borrow ideas, not the stack** |
| First Commit rules | Live URL, AWS at core, 2–3 min demo, architecture + cost scored |

**Design rule:** Steal *workflow* from OpenCTI/MISP/TheHive; ship a **thin AWS serverless slice** that produces a case packet. Fixtures only for ingest in v1 (no live Tor crawl in demo).

---

## 1. Problem

Indian cybercrime / LE analysts receive noisy dark-web / deep-web style chatter (stolen dumps, fake KYC, scam tooling mentions). Today:

1. Paste into a **chatbot** → get a summary → still no case file.  
2. Manual Excel / WhatsApp forwarding → no entity linking, no evidence hash trail.  
3. Enterprise TIP (OpenCTI/MISP) → powerful but weeks to stand up; overkill for a hackathon *and* for many district units.

**Job to be done:** In under 3 minutes, turn a noisy listing into a **court-friendly one-pager** with entities, risk, linked posts, and an auditable AWS run ID.

---

## 2. Vision & anti-goals

### Vision
CasePacket is a **two-pass ship pipeline**: specialist agents *reason* (classify, extract, narrate); **Step Functions + Lambda compile** a deterministic case packet; the **live URL** is the product.

### Goals (v1 / Ship It weekend)
- G1: Live `/healthz` + analyst console on AWS.  
- G2: Ingest ≥20 synthetic listings → triage queue.  
- G3: Open a case → see entities, score, cluster links.  
- G4: Export CasePacket JSON (+ optional PDF).  
- G5: Demo video shows **AWS console** (Step Functions execution, S3 object, CloudWatch).  
- G6: Architecture + rough cost in README / Builder write-up.

### Non-goals (explicit)
- ❌ Live Tor / onion crawling instructions or credentials.  
- ❌ Exploit kits, phishing kits, malware detonation.  
- ❌ Full OpenCTI/MISP deployment.  
- ❌ Chat-only “ask me about the dark web” UI as the core product.  
- ❌ Production LE accreditation / legal discovery readiness.

---

## 3. Personas

| Persona | Need | Success |
|---------|------|---------|
| **Cyber cell analyst** | Triage queue, entity highlights, export brief | Case-001 exported in &lt;60s |
| **Supervisor** | Risk ranking, audit trail | Can see who/what/when in CloudWatch |
| **Hackathon judge** | Working URL + AWS story | Understands architecture in 3 min |

---

## 4. User journeys

### 4.1 Happy path — triage to packet
1. Analyst opens `https://<cloudfront>/`  
2. Sees queue sorted by risk.  
3. Opens **Case-001** (pre-seeded).  
4. Reviews entities (phone, email, wallet, domain, handle).  
5. Clicks **Generate packet** → Step Functions run.  
6. Downloads JSON/PDF; notes `evidence_sha256` + `execution_arn`.  

### 4.2 Ingest path (demo)
1. Operator drops fixture JSON into S3 `raw/` (or POSTs to `/ingest`).  
2. EventBridge → Lambda parse → DynamoDB items.  
3. Item appears in queue within ~30s.

### 4.3 Failure path (anti-chatbot proof)
1. Bedrock unavailable → regex/NER fallback still extracts phones/emails/wallets.  
2. `/healthz` remains 200; packet marks `enrichment: degraded`.

---

## 5. Functional requirements

### 5.1 Ingest
| ID | Requirement | Priority |
|----|-------------|----------|
| IN-01 | Accept fixture listings as JSON (schema below) via S3 put or API | P0 |
| IN-02 | Store immutable raw object in S3 `raw/{yyyy}/{mm}/{id}.json` | P0 |
| IN-03 | Compute SHA-256 of raw body; store on item | P0 |
| IN-04 | Deduplicate by content hash | P1 |
| IN-05 | Optional: scheduled seed of demo fixtures on deploy | P0 |

### 5.2 Extract & enrich
| ID | Requirement | Priority |
|----|-------------|----------|
| EX-01 | Regex extract: email, phone (IN), URL, crypto wallet-like strings, @handles | P0 |
| EX-02 | LLM (Bedrock) optional: title, summary, category, language | P1 |
| EX-03 | Risk score 0–100 from rules (keyword + entity density + category) | P0 |
| EX-04 | Cluster posts sharing ≥1 high-value entity | P0 |
| EX-05 | Map categories to simple taxonomy (fraud, credentials, docs, other) | P1 |

### 5.3 Case management
| ID | Requirement | Priority |
|----|-------------|----------|
| CM-01 | Triage list: title, risk, category, created_at | P0 |
| CM-02 | Case detail: raw excerpt, entities, linked cases, timeline | P0 |
| CM-03 | Generate CasePacket (JSON) via Step Functions | P0 |
| CM-04 | Optional PDF one-pager | P2 |
| CM-05 | Analyst note field (local to case) | P2 |

### 5.4 Export / interoperability
| ID | Requirement | Priority |
|----|-------------|----------|
| XP-01 | CasePacket JSON includes STIX-inspired `objects[]` (indicator / observed-data / report lite) | P1 |
| XP-02 | Export includes `tlp`, `chain_of_custody[]`, `aws_execution_arn` | P0 |
| XP-03 | Download via signed S3 URL (5–15 min TTL) | P1 |

### 5.5 Ops / demo
| ID | Requirement | Priority |
|----|-------------|----------|
| OP-01 | `GET /healthz` → `{ status, version, checks }` | P0 |
| OP-02 | Seed button or CLI `npm run seed` / `make seed` | P0 |
| OP-03 | CloudWatch dashboard or documented log group names | P1 |

---

## 6. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF-01 | Cold path: packet generation &lt; 30s for fixture case |
| NF-02 | Console usable on laptop + phone (responsive enough for judges) |
| NF-03 | All PII in fixtures synthetic / clearly fake |
| NF-04 | Region: `ap-south-1` (Mumbai) preferred for Bharat Builds |
| NF-05 | Weekend cost target: &lt; $15 with free tier / credits |
| NF-06 | Secrets in SSM/Secrets Manager — never in git |
| NF-07 | IaC: SAM or CDK — one `sam deploy` / `cdk deploy` |

---

## 7. System architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              Analyst Console (SPA)           │
                    │         CloudFront + S3 (Amplify OK)        │
                    └──────────────────┬──────────────────────────┘
                                       │ HTTPS
                    ┌──────────────────▼──────────────────────────┐
                    │         API Gateway (HTTP API)              │
                    │   /healthz  /cases  /cases/{id}/packet      │
                    │   /ingest (demo)                            │
                    └──────────────┬───────────────┬──────────────┘
                                   │               │
              ┌────────────────────▼──┐     ┌──────▼──────────────┐
              │   Lambda: API         │     │ Step Functions      │
              │   CRUD / queue        │     │ CasePacketCompile   │
              └──────────┬────────────┘     │ 1 extract           │
                         │                  │ 2 score/cluster     │
                         │                  │ 3 render JSON       │
                         │                  │ 4 put S3 packets/   │
                         │                  └──────┬──────────────┘
              ┌──────────▼────────────┐            │
              │ DynamoDB              │◄───────────┘
              │ cases | entities      │
              │ clusters              │
              └──────────▲────────────┘
                         │
              ┌──────────┴────────────┐     ┌─────────────────────┐
              │ S3                    │     │ Bedrock (optional)  │
              │ raw/  packets/        │     │ summarize/classify  │
              └──────────▲────────────┘     └─────────────────────┘
                         │
              EventBridge (S3 Object Created) → Lambda: IngestNormalize
```

### Why this shape (from research)
| Pattern borrowed | From | Weekend mapping |
|------------------|------|-----------------|
| Immutable raw evidence | LE serverless pipelines | S3 `raw/` + SHA-256 |
| Async workers | OpenCTI workers / RabbitMQ | Step Functions + Lambda |
| Case + observables | TheHive + Cortex | Case detail + entities table |
| Structured IOCs | MISP / STIX | CasePacket JSON `objects[]` |
| Analyst UI | Watcher / OpenCTI UI | Thin React/Next SPA |

---

## 8. Data model

### 8.1 Fixture listing (`raw/*.json`)
```json
{
  "id": "fix-001",
  "source": "fixture://marketplace-sim",
  "captured_at": "2026-09-18T10:00:00Z",
  "title": "Selling fake KYC packs (SIMULATED)",
  "body": "Contact +91-90000-00001 or seller@example.invalid ...",
  "category_hint": "docs",
  "tlp": "TLP:AMBER",
  "meta": { "language": "en", "simulated": true }
}
```

### 8.2 Case (DynamoDB)
| Field | Type | Notes |
|-------|------|-------|
| `pk` | `CASE#&lt;id&gt;` | |
| `sk` | `META` | |
| `title` | string | |
| `risk` | number 0–100 | |
| `category` | string | |
| `entities` | list&lt;map&gt; | `{type,value,confidence}` |
| `raw_s3_key` | string | |
| `raw_sha256` | string | |
| `cluster_id` | string? | |
| `status` | `open\|packet_ready` | |
| `created_at` | ISO8601 | |

### 8.3 CasePacket export (P0)
```json
{
  "packet_version": "1.0",
  "case_id": "CASE-001",
  "generated_at": "...",
  "tlp": "TLP:AMBER",
  "summary": "...",
  "risk": 78,
  "entities": [],
  "linked_case_ids": [],
  "chain_of_custody": [
    { "event": "ingest", "at": "...", "s3": "raw/...", "sha256": "..." },
    { "event": "compile", "at": "...", "execution_arn": "arn:aws:states:..." }
  ],
  "objects": [
    { "type": "indicator", "pattern": "[email-addr:value = 'seller@example.invalid']" }
  ],
  "disclaimer": "SIMULATED FIXTURE DATA — NOT OPERATIONAL INTEL"
}
```

---

## 9. API (HTTP)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/healthz` | public | Liveness + dependency checks |
| GET | `/cases` | demo key / Cognito optional | List triage queue |
| GET | `/cases/{id}` | same | Case detail |
| POST | `/cases/{id}/packet` | same | Start Step Functions; return execution id |
| GET | `/cases/{id}/packet` | same | Latest packet metadata + download URL |
| POST | `/ingest` | demo key | Upload fixture JSON (hackathon only) |

**Auth for weekend:** single `x-api-key` in API Gateway is enough; Cognito = stretch.

---

## 10. Agent split (anti-chatbot)

| Agent / role | Input | Output | Must be LLM? |
|--------------|-------|--------|--------------|
| Ingest normalizer | Raw JSON | Validated case stub | No |
| Entity extractor | Body text | Entities[] | No (regex first) |
| Classifier | Body + entities | category, risk deltas | Optional Bedrock |
| Narrator | Case | summary paragraph | Optional Bedrock |
| Compiler | All above | CasePacket JSON in S3 | No (deterministic) |

**Invariant:** Packet must generate even if Bedrock is off.

---

## 11. UI requirements

### Screens
1. **Queue** — table/cards sorted by risk; badges for category.  
2. **Case** — left: excerpt; right: entities + links; bottom: Generate / Download.  
3. **Ops strip** — show last Step Functions status + `/healthz` green.

### Brand
Pick one name and put it hero-level: **CasePacket** (default) | NyayNet | TraceVault.

### Design notes (hackathon UI)
- Dark ops console is fine *if* contrast is WCAG-ish; avoid generic purple AI slop.  
- Show **SIMULATED DATA** banner always.

---

## 12. AWS bill of materials (Ship It)

| Service | Use |
|---------|-----|
| S3 | raw + packets + static site (or Amplify Hosting) |
| API Gateway HTTP API | Public API |
| Lambda (Python 3.12 or Node 20) | API, ingest, extract, compile |
| Step Functions Standard | Auditable CasePacketCompile |
| DynamoDB on-demand | cases / entities |
| EventBridge | S3 → ingest |
| CloudWatch Logs + optional dashboard | Demo evidence |
| Bedrock (Claude Haiku / Titan) | Optional summarize |
| SSM Parameter Store | API keys, model ids |
| IAM least privilege | Separate roles per Lambda |

**Rough cost (light demo traffic):** DynamoDB + Lambda + S3 pennies; Bedrock only if used; CloudFront free tier friendly.

---

## 13. Build plan (end-to-end)

### Phase 0 — Repo (30–60 min)
- [ ] `sam init` or CDK app `casepacket`  
- [ ] Folders: `fixtures/`, `src/api/`, `src/ingest/`, `src/compile/`, `web/`  
- [ ] README with architecture diagram  
- [ ] `.env.example` (no secrets)

### Phase 1 — Data + health (2–3 h)
- [ ] Fixture pack (20 JSON files, Indian cybercrime *themes*, all fake)  
- [ ] S3 buckets + DynamoDB table via IaC  
- [ ] Ingest Lambda + seed script  
- [ ] `/healthz` deployed  

### Phase 2 — Extract + score (3–4 h)
- [ ] Regex NER module + unit tests  
- [ ] Risk rules YAML  
- [ ] Cluster by shared entity  
- [ ] API `GET /cases`, `GET /cases/{id}`  

### Phase 3 — CasePacket compile (2–3 h)
- [ ] Step Functions definition  
- [ ] Compile Lambda → S3 `packets/`  
- [ ] `POST/GET .../packet`  

### Phase 4 — Console (3–4 h)
- [ ] SPA (Vite React or Next static export)  
- [ ] Queue + Case pages  
- [ ] Wire to API  
- [ ] SIMULATED banner  

### Phase 5 — Ship evidence (1–2 h)
- [ ] Custom domain optional; CloudFront URL required  
- [ ] Screenshot list for video (console + AWS)  
- [ ] Cost estimate paragraph  
- [ ] Builder Center write-up  

### Phase 6 — Polish / fallbacks (1 h)
- [ ] Bedrock optional path  
- [ ] Degraded mode flag  
- [ ] Load test seed once  

---

## 14. Demo script (2–3 min) — judging

| Time | Action | Say |
|------|--------|-----|
| 0:00 | Title slide / live URL | “CasePacket turns noisy dark-web *fixtures* into LE case files on AWS.” |
| 0:20 | Queue | “Risk-sorted triage — not a chatbot sidebar.” |
| 0:50 | Open Case-001 | Entities + cluster links |
| 1:20 | Generate packet | Step Functions running |
| 1:50 | Download JSON | Chain of custody + SHA-256 |
| 2:10 | AWS console | S3 raw/, Step Functions graph, CloudWatch |
| 2:40 | Cost + fallback | “Works without Bedrock; architecture is the product.” |

---

## 15. Security & ethics

1. All fixtures marked `simulated: true` and bannered in UI.  
2. No collection of real PII; no live marketplace access in repo.  
3. TLP field present; default `TLP:AMBER` for demo.  
4. API key rotated post-hackathon if URL stays up.  
5. README: “For educational / LE-analyst workflow demo only.”  

---

## 16. Success metrics

| Metric | Target |
|--------|--------|
| Health check | 200 on judge open |
| Seeded cases | ≥ 20 |
| Packet generation | &lt; 30s |
| Demo | Shows AWS evidence without narration only |
| Differentiation | Clear vs OpenCTI (thin), vs chatbot (compiled packet) |

---

## 17. Open questions

1. SAM vs CDK — default **SAM** for faster First Commit Ship It.  
2. PDF export — drop if timeboxed.  
3. Cognito — skip unless required by workshop.  
4. Brand name finalization.

---

## 18. Appendix — competitor / inspiration map

| System | Role | We copy | We skip |
|--------|------|---------|---------|
| OpenCTI | Full TIP | STIX-ish export, connector mindset | Graph DB, workers fleet |
| MISP | IOC sharing | Taxonomy / TLP | Sync network |
| TheHive | Cases | Case UX metaphor | Full IR playbooks |
| Cortex | Analyzers | “Observable → enrich” | Heavy analyzers |
| Watcher | AI CTI UI | Analyst console feel | Django monolith |
| KAVACH Cyph3r / CID Track | India LE wins | Problem framing | Live crawl claims in demo |

---

## 19. Deliverables checklist (submission)

- [ ] Public GitHub repo  
- [ ] Live Ship It URL  
- [ ] 2–3 min demo video  
- [ ] AWS architecture + cost write-up  
- [ ] Fixtures + seed instructions  
- [ ] `/healthz` green  

---

*PRD generated after agent-reach architecture scan (GitHub `gh search`, Jina Reader on STIX/MISP/OpenCTI/AWS, web synthesis). Agent Reach v1.5.0.*
