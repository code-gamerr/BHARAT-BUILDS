# CasePacket — Build Plan

Executable weekend plan for First Commit **Ship It**.  
Source of truth for requirements: [CasePacket-PRD.md](./CasePacket-PRD.md).

**Stack default:** AWS SAM · Python 3.12 Lambdas · DynamoDB · Step Functions · Vite React SPA · `ap-south-1`  
**Brand:** CasePacket  
**Invariant:** Packet compiles even if Bedrock is off (fixtures only — no live Tor).

---

## Timeline overview

| Phase | Focus | Timebox | Exit criteria |
|-------|--------|---------|----------------|
| 0 | Repo + IaC skeleton | 30–60 min | `sam build` works |
| 1 | Data + health | 2–3 h | `/healthz` 200 + 20 fixtures seeded |
| 2 | Extract + score + API | 3–4 h | `GET /cases` returns ranked queue |
| 3 | CasePacket compile | 2–3 h | Step Functions → S3 packet JSON |
| 4 | Analyst console | 3–4 h | Queue + Case pages on live URL |
| 5 | Ship evidence | 1–2 h | Demo script rehearsed + cost write-up |
| 6 | Polish | 1 h | Degraded mode + banner + README |

**Total:** ~14–18 h (one focused weekend / pair).

---

## Phase 0 — Repo skeleton

- [ ] Create `casepacket/` SAM app (`template.yaml`)
- [ ] Folders:
  ```
  fixtures/
  src/api/
  src/ingest/
  src/extract/
  src/compile/
  src/shared/
  web/
  docs/
  ```
- [ ] `.env.example` (API key placeholder only)
- [ ] `.gitignore` (`.aws-sam/`, `.env`, `node_modules/`)
- [ ] README stub: problem · architecture diagram · deploy commands
- [ ] `sam build` succeeds with empty Hello health Lambda

**Done when:** empty stack deploys or at least builds cleanly.

---

## Phase 1 — Data + health

- [ ] DynamoDB table `CasePacket` (PK/SK design from PRD §8)
- [ ] S3 buckets: `raw/`, `packets/` (+ static hosting bucket or Amplify later)
- [ ] Write **20** fixture JSON files under `fixtures/` (`simulated: true`, fake Indian-theme cybercrime copy)
- [ ] `scripts/seed.py` — upload fixtures → trigger ingest
- [ ] Lambda `IngestNormalize` (S3 ObjectCreated or seed CLI)
- [ ] Lambda `ApiHealth` → `GET /healthz`
- [ ] API Gateway HTTP API wired
- [ ] Deploy: note stack outputs (`ApiUrl`, `BucketName`)

**Done when:** `curl $ApiUrl/healthz` → 200 and DynamoDB has ≥20 cases after seed.

---

## Phase 2 — Extract + score + list API

- [ ] `src/extract/ner.py` — regex: email, IN phone, URL, wallet-like, @handle
- [ ] Unit tests for NER (pytest)
- [ ] `risk_rules.yaml` — keyword + entity-density scoring → 0–100
- [ ] Cluster: shared high-value entity → `cluster_id`
- [ ] Persist entities on case item
- [ ] `GET /cases` (sort by risk desc)
- [ ] `GET /cases/{id}` (detail + entities + linked ids)
- [ ] API key auth (`x-api-key`) on non-health routes

**Done when:** Postman/curl shows ranked queue and Case-001 detail.

---

## Phase 3 — CasePacket compile

- [ ] Step Functions state machine `CasePacketCompile`
  1. Extract/enrich (idempotent if already done)
  2. Score/cluster refresh
  3. Render packet JSON (PRD §8.3)
  4. Put `packets/{case_id}/{ts}.json`
  5. Update case `status=packet_ready` + `execution_arn`
- [ ] `POST /cases/{id}/packet` → start execution
- [ ] `GET /cases/{id}/packet` → metadata + signed download URL
- [ ] Chain-of-custody fields: ingest sha256 + compile ARN

**Done when:** POST packet → JSON in S3 with `disclaimer` + `objects[]` (STIX-lite).

---

## Phase 4 — Console (SPA)

- [ ] Vite + React (or Next static export) in `web/`
- [ ] Env: `VITE_API_URL`, `VITE_API_KEY`
- [ ] Screens:
  - Queue (risk sort, category badges)
  - Case (excerpt · entities · Generate / Download)
  - Ops strip (`/healthz` + last SF status)
- [ ] Persistent **SIMULATED DATA** banner
- [ ] Deploy static site → CloudFront / S3 / Amplify
- [ ] CORS on API for console origin

**Done when:** Judge can click through queue → case → download without CLI.

---

## Phase 5 — Ship evidence (First Commit)

- [ ] Public GitHub repo + clear README
- [ ] Live Ship It URL in README
- [ ] Cost estimate paragraph (`ap-south-1`, light traffic)
- [ ] Architecture diagram ( mermaid or image )
- [ ] Rehearse 3-min demo (PRD §14):
  - Queue → Case-001 → Generate → JSON → AWS console (S3, SF, CloudWatch)
- [ ] AWS Builder Center write-up draft
- [ ] Screenshot checklist for video

**Done when:** dry-run video under 3:00 with AWS evidence on screen.

---

## Phase 6 — Polish / fallbacks

- [ ] Optional Bedrock summarize/classify (feature flag)
- [ ] `enrichment: degraded` when Bedrock fails
- [ ] Re-seed once on cold account
- [ ] Remove debug logs / rotate demo API key notes
- [ ] Final link check: health · console · sample packet

**Done when:** packet still succeeds with Bedrock disabled.

---

## Daily / hour checkpoints

| Checkpoint | Must see |
|------------|----------|
| End Phase 1 | Green health + seeded data |
| End Phase 3 | Packet JSON downloadable |
| End Phase 4 | Live console URL |
| Submit | Repo + URL + 2–3 min video + write write-up |

---

## Owners (fill in)

| Area | Owner |
|------|--------|
| IaC / AWS | |
| Extract / compile | |
| Web UI | |
| Fixtures / demo video | |

---

## Out of plan (do not start)

- Live Tor / onion crawl  
- Full OpenCTI or MISP  
- Cognito (unless time surplus)  
- PDF export (P2 — only after P0 green)  

---

## Commands cheat sheet (target)

```bash
sam build && sam deploy --guided
python scripts/seed.py
curl -s "$API_URL/healthz"
curl -s -H "x-api-key: $KEY" "$API_URL/cases" | jq .
cd web && npm i && npm run build
```

---

*Plan derived from CasePacket PRD v1.0 — keep this file as the checklist; update boxes as you ship.*
