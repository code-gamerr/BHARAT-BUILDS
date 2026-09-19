# CasePacket

<<<<<<< HEAD
**LE dark-web intel triage → court-friendly case packet on AWS**  
First Commit / Bharat Builds **Ship It** · fixtures only · not a chatbot · not a live Tor crawler

> SIMULATED FIXTURE DATA — NOT OPERATIONAL INTEL

Inspired by KAVACH Cyph3r research ([`Executive Summary.pdf`](./Executive%20Summary.pdf)): collect → normalize → correlate/score → **legally credible report**.  
“CID Track” is undocumented publicly — we do not claim it.
=======
**Dark-web *signal* → LE-ready *case packet* on AWS.**  
First Commit / Bharat Builds — Ship It. Simulated fixtures only. No live Tor.

Indian cyber cells get noisy marketplace chatter (fake KYC, UPI mules, credential dumps). Today that becomes a chatbot summary or a WhatsApp forward — no entities, no hash trail, no file. Enterprise TIPs (OpenCTI / MISP) take weeks to stand up.

CasePacket is the thin slice: **ingest → extract → score → cluster → compile**. The product is the packet, not a chat box.

All listings are fake (`simulated: true`). The UI banner never turns off.

---

## What you are looking at

```
fixtures/*.json          20 fake Indian-theme listings
        │
        ▼
   ingest + SHA-256      immutable raw copy (S3 or .local/s3/raw)
        │
        ▼
 regex NER               phone · email · URL · wallet · @handle
        │
        ▼
 risk rules              0–100 from category + keywords + entity density
        │
        ▼
 cluster                 shared phone / email / wallet → CL-xxxxxx
        │
        ▼
 Step Functions          extract → score → render STIX-lite JSON → packets/
 (local: same steps, synchronous)
        │
        ▼
 analyst console         queue → case → Generate packet → download JSON
```

**Invariant:** a packet still compiles if Bedrock is off. Enrichment falls back to rules and marks `enrichment: degraded` only if you *enable* Bedrock and it fails.

---

## How to run it (you, today)

You already have **Python** (`py`) and **Node**. You do **not** need AWS, SAM, or Docker for the full demo.

### 1. Seed the 20 cases

```powershell
cd "C:\Users\tanis\Desktop\Bharat Build\BHARAT-BUILDS"
py scripts/seed.py
```

### 2. Start the API (leave this terminal open)

```powershell
py scripts/local_server.py
```

Check: [http://127.0.0.1:8080/healthz](http://127.0.0.1:8080/healthz) should return `"status": "ok"`.

### 3. Start the console (second terminal)

```powershell
cd "C:\Users\tanis\Desktop\Bharat Build\BHARAT-BUILDS\web"
npm install
npm run dev
```

Open **[http://127.0.0.1:5173](http://127.0.0.1:5173)**.

Demo API key (already wired in the UI): `casepacket-demo-key`.

### 4. Click through (2–3 min demo)

1. **Dashboard** — priority triage (High / Medium / Low pills).
2. **Cases** → open **CASE-001**. Tabs: Overview · Entities · Linked Posts · Timeline.
3. Follow a **linked case** (CASE-001 ↔ CASE-007 via shared phone).
4. **Generate Packet** → staged compile modal → JSON with `disclaimer`, `chain_of_custody`, STIX-lite `objects[]`.
5. **Reports** / **AWS Pipeline** for packet list + Step Functions demo graph.

Other built-in clusters:

| Shared entity | Cases |
|---------------|--------|
| `+91-90000-00001` | CASE-001, CASE-007 |
| `dump_broker@example.invalid` | CASE-002, CASE-012 |
| `1FakeWalletDemo000000000000000001` | CASE-005, CASE-015 |

### Tests

```powershell
py -m unittest tests/test_pipeline.py
```

---

## How it works (internals)

| Piece | Role | LLM? |
|-------|------|------|
| `src/shared/pipeline.py` | Ingest, extract, score, cluster, compile | No |
| `src/shared/ner.py` | Regex observables | No |
| `src/shared/scoring.py` | Risk 0–100 | No |
| `src/shared/packet.py` | CasePacket JSON + STIX-lite `objects[]` | No |
| `scripts/local_server.py` | Same HTTP API as Lambda | No |
| `src/api/handler.py` | API Gateway adapter | No |
| Step Functions `CasePacketCompile` | Auditable compile on AWS | No |
| `src/shared/bedrock.py` | Optional summary | Optional |

**Local vs AWS:** if `CASEPACKET_LOCAL=1` (default on your laptop), data lives in `.local/`. If `TABLE_NAME` + `BUCKET_NAME` are set (SAM), the same code uses DynamoDB + S3 + Step Functions.

**Auth:** `x-api-key` on every route except `/healthz`.

| Method | Path | What |
|--------|------|------|
| GET | `/healthz` | Liveness + store/S3 checks |
| GET | `/cases` | Risk-sorted queue |
| GET | `/cases/{id}` | Excerpt, entities, linked ids |
| POST | `/cases/{id}/packet` | Compile (local sync / SF start) |
| GET | `/cases/{id}/packet` | Metadata + download URL |
| POST | `/ingest` | Push one more simulated listing |

---

## What you need to do next

**For local use / rehearsal — nothing else.** Seed, start API, start web.

**For First Commit “live URL + AWS evidence”:**

1. Create an AWS account (or use the workshop one). Region **`ap-south-1`**.
2. Install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
3. `aws configure` with an IAM user that can create Lambda, API Gateway, DynamoDB, S3, Step Functions, IAM roles.
4. Deploy:

```powershell
sam build
sam deploy --guided
```

5. Note outputs `ApiUrl`, `BucketName`, `StateMachineArn`.
6. Point the console at the live API:

```powershell
cd web
# web/.env
# VITE_API_URL=https://xxxx.execute-api.ap-south-1.amazonaws.com
# VITE_API_KEY=the-key-you-set
npm run build
```

Host `web/dist` on S3 + CloudFront or Amplify. Put that URL in this README.

7. Seed on AWS: put the files in `fixtures/` to `s3://$BucketName/raw/2026/09/` **or** `POST /ingest` each file with the API key.

8. Record the 3-minute video: queue → CASE-001 → Generate → JSON → AWS console (Step Functions graph, S3 `raw/` + `packets/`, CloudWatch).

**Do not** add live onion crawls, exploit kits, or real PII.

---
>>>>>>> Tanish-local

## Architecture

```mermaid
flowchart LR
<<<<<<< HEAD
  SPA[Amplify SPA] --> APIGW[API Gateway]
  APIGW --> API[Api Lambda]
  API --> DDB[(DynamoDB)]
  Raw[S3 raw/] --> Ingest[Ingest Lambda]
  Ingest --> DDB
  API --> SFN[Step Functions]
  SFN --> Ext[Extract]
  Ext --> Score[Score]
  Score --> Comp[Compile]
  Comp --> Pkt[S3 packets/]
  Reward[Reward Lambda] -.-> Bedrock[Bedrock RFT GRPO ≥13]
```

Local path (no AWS): `uvicorn local.server:app` + Vite — same analyst flow.

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/CasePacket-PRD.md](docs/CasePacket-PRD.md) | Full PRD |
| [docs/plan.md](docs/plan.md) | Build phases |
| [docs/frontend.md](docs/frontend.md) / [backend.md](docs/backend.md) / [ml.md](docs/ml.md) | Specs |
| [docs/demo.md](docs/demo.md) | 3-min demo script |
| [docs/resources.md](docs/resources.md) | AWS Builder Center + Trendshift refs |

Cursor rule: `.cursor/rules/casepacket.mdc`

## Quick start (local — no AWS)

All case content lives in `fixtures/*.json` or arrives via `POST /ingest`.  
Risk weights live in `config/risk_rules.yaml`. API URL/key come from env only.

```bash
# one-shot smoke (API must be up)
pip install -r local/requirements.txt
uvicorn local.server:app --host 127.0.0.1 --port 8000
# other terminal:
python scripts/smoke_e2e.py

# frontend
cd web
cp .env.example .env   # VITE_API_URL=http://127.0.0.1:8000
npm i && npm run dev   # http://127.0.0.1:5173
```

Windows helper: `powershell -File scripts/run_local.ps1`

**Analyst flow:** open queue → Reload fixtures → open case → Generate CasePacket → Download JSON.

## Deploy (Ship It / AWS)

```bash
sam build
sam deploy --guided   # DemoApiKey via parameter (not in app code), region ap-south-1

python scripts/seed.py --api https://YOUR_API --api-key YOUR_KEY
# or: python scripts/seed.py --bucket YOUR_RAW_BUCKET

cd web
# .env: VITE_API_URL=https://YOUR_API  VITE_API_KEY=YOUR_KEY
npm run build   # → Amplify Hosting (web/amplify.yml)

# GRPO dataset (≥12 prompts from fixtures)
python scripts/build_grpo_dataset.py
# aws s3 cp ml/datasets/grpo_train.jsonl s3://$RAW/ml/grpo/train.jsonl
# Bedrock RFT: RewardFunctionArn output, group_size ≥ 13
```

## Cost estimate (`ap-south-1`, light demo)

| Service | Rough monthly @ hackathon traffic |
|---------|-----------------------------------|
| Lambda + API GW | &lt; $1 |
| DynamoDB on-demand | &lt; $1 |
| S3 + Step Functions | &lt; $1 |
| Amplify Hosting | free tier / few $ |
| Bedrock RFT (optional) | job-time only — disable for free-tier demo |

Weekend judge load stays well under **~$5** without a long RFT run.

## Trendshift / OSS we borrowed ideas from

- [security-audit-skill](https://github.com/cloudflare/security-audit-skill) — machine-readable `findings[]` in packets  
- [brag](https://github.com/latent-spaces/brag) — optional Ship It demo video  
- [Trendshift](https://trendshift.io/) — discovery  

## Legal

Educational / hackathon demo. No live onion crawling. Comply with IT Act / DPDP when handling real data (we don’t).

## License

MIT (hackathon demo code)
=======
  UI[Analyst console] -->|HTTPS + x-api-key| API[HTTP API]
  API --> L[Lambda API]
  API --> SF[Step Functions CasePacketCompile]
  SF --> X[Extract]
  SF --> S[Score / cluster]
  SF --> C[Compile packet]
  L --> DDB[(DynamoDB)]
  X --> DDB
  S --> DDB
  C --> DDB
  C --> S3[(S3 raw / packets)]
  EB[EventBridge S3 Object Created] --> IN[IngestNormalize]
  IN --> DDB
  S3 --> EB
```

**Rough weekend cost (`ap-south-1`, light traffic):** DynamoDB on-demand + Lambda + S3 + HTTP API = pennies. CloudFront free-tier friendly. Bedrock is off by default (`EnableBedrock=0`). Stay well under $15.

---

## Ethics

Educational / LE-analyst **workflow** demo only. Every fixture is synthetic. Rotate the demo API key if you leave a public URL up after the event.
>>>>>>> Tanish-local
