# CasePacket — Build Plan

Executable weekend plan for First Commit **Ship It**.  
Source of truth for requirements: [CasePacket-PRD.md](./CasePacket-PRD.md).

**Split specs:** [resources.md](./resources.md) · [frontend.md](./frontend.md) · [backend.md](./backend.md) · [ml.md](./ml.md) · [demo.md](./demo.md)

**Build config:** [`../config.yaml`](../config.yaml) — full throttle; `hard_boundaries: none`.

**Stack:** AWS SAM · Amplify · Bedrock RFT (GRPO ≥13) · Python 3.12 · DynamoDB · Step Functions · Vite · `ap-south-1`  
**Local:** `uvicorn local.server:app` — fixtures/env/config only (no hardcoded cases).  
**Invariant:** Packet compiles with Bedrock off (`enrichment: degraded|rules`).

---

## Timeline overview

| Phase | Focus | Exit criteria | Local | AWS |
|-------|--------|---------------|-------|-----|
| 0 | Repo + IaC | `sam build` | ✅ | ⏳ CLI |
| 1 | Data + health | `/healthz` + 20 fixtures | ✅ | ⏳ deploy |
| 2 | Extract + score + API | Ranked `GET /cases` | ✅ | ✅ code |
| 3 | CasePacket compile | Packet JSON + custody | ✅ | ✅ code |
| 4 | Analyst console | Queue → download | ✅ | ⏳ Amplify |
| 5 | Ship evidence | Demo + cost + arch | ✅ docs | ⏳ live URL |
| 6 | Polish | Degraded mode | ✅ | ✅ flag |

---

## Phase 0 — Repo skeleton

- [x] SAM app (`template.yaml`) + RewardFunction
- [x] Folders: `fixtures/`, `src/*`, `web/`, `docs/`, `scripts/`, `ml/`
- [x] `.gitignore` / README architecture + cost
- [x] `sam build` Succeeded (deploy still needs AWS credentials: `sam deploy --guided`)
- [x] Cursor rule `.cursor/rules/casepacket.mdc`

---

## Phase 1 — Data + health

- [x] DynamoDB / S3 / HttpApi defined in `template.yaml`
- [x] 20 fixtures (`simulated: true`)
- [x] `scripts/seed.py` (env API key)
- [x] Local FastAPI auto-seed + health/cases
- [x] Lambda handlers: ingest, api health/cases
- [ ] Deploy + note stack outputs

---

## Phase 2 — Extract + score + list API

- [x] Regex NER in `src/shared/casepacket.py`
- [x] `src/api/test_ner.py` pytest
- [x] `config/risk_rules.yaml`
- [x] Cluster `cluster_id` (local + Lambda score/ingest)
- [x] `GET /cases`, `GET /cases/{id}` + linked ids
- [x] API key when env set

---

## Phase 3 — CasePacket compile

- [x] Step Functions definition in SAM
- [x] Local + Lambda packet with `findings[]`, custody, STIX-lite `objects[]`
- [x] `ml.group_size` ≥ 13 in packet block

---

## Phase 4 — Console (SPA)

- [x] Vite React · env-only API · banner · health · queue · case · generate/download
- [x] `web/amplify.yml`
- [ ] Amplify live URL

---

## Phase 5 — Ship evidence

- [x] Architecture mermaid + cost in README
- [x] [demo.md](./demo.md) 3-min script
- [ ] Public GitHub + live Ship It URL
- [ ] Rehearse video with AWS console

---

## Phase 6 — Polish / ML

- [x] `ENABLE_BEDROCK` flag → degraded extract
- [x] Reward Lambda + `scripts/build_grpo_dataset.py` (≥12 prompts)
- [ ] Run Bedrock RFT job in account (group size 13+)
- [x] Packet ships without Bedrock

---

## Out of plan

- Live Tor · full OpenCTI/MISP · Cognito · PDF (P2)

---

## Commands

```bash
# local
uvicorn local.server:app --host 127.0.0.1 --port 8000
python scripts/smoke_e2e.py
cd web && npm run dev

# AWS
sam build && sam deploy --guided
python scripts/seed.py --api "$API_URL" --api-key "$KEY"
python scripts/build_grpo_dataset.py
```

*Checklist synced to docs specs — update boxes as you ship.*
