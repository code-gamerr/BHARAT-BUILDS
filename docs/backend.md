# CasePacket — Backend Spec (AWS SAM / Serverless)

Dark-web intel for LE — **API, ingest, evidence, orchestration**. All runtime on **AWS**.

Related: [resources.md](./resources.md) · [frontend.md](./frontend.md) · [ml.md](./ml.md)

---

## 1. Goal

Deterministic compile path:

`fixtures/S3 raw → ingest → DynamoDB → extract/score → Step Functions → S3 packet`

Agents/LLM optional; **compiler always works**.

---

## 2. AWS architecture

```
Amplify SPA
    │
    ▼
API Gateway (HTTP API) ── x-api-key
    │
    ├─ Lambda ApiHandler          → DynamoDB
    ├─ Lambda Health
    └─ POST .../packet            → StartExecution Step Functions
                                        │
                         CasePacketCompile (Standard)
                           1. ExtractEnrich (Lambda)  ← regex + optional Bedrock
                           2. ScoreCluster (Lambda)   ← rules + GRPO ranker score
                           3. RenderPacket (Lambda)   → S3 packets/
                           4. UpdateCase (Lambda)     → DynamoDB

S3 raw/ ──EventBridge──► Lambda IngestNormalize ──► DynamoDB
```

**IaC:** AWS SAM `template.yaml` (preferred for First Commit speed).  
**Region:** `ap-south-1`.

---

## 3. SAM resources (template checklist)

| Logical ID | Type | Notes |
|------------|------|-------|
| `RawBucket` | `AWS::S3::Bucket` | versioning on; event → ingest |
| `PacketBucket` | `AWS::S3::Bucket` | packet JSON |
| `CasesTable` | `AWS::DynamoDB::Table` | PAY_PER_REQUEST; PK/SK |
| `HttpApi` | `AWS::Serverless::HttpApi` | CORS for Amplify origin |
| `ApiKey` / usage plan | API key | demo auth |
| `HealthFunction` | Lambda | `GET /healthz` |
| `ApiFunction` | Lambda | cases CRUD-ish |
| `IngestFunction` | Lambda | S3 trigger |
| `ExtractFunction` | Lambda | NER + optional Bedrock |
| `ScoreFunction` | Lambda | rules + ML rank score |
| `CompileFunction` | Lambda | write packet |
| `RewardFunction` | Lambda | **GRPO reward** (see ml.md) |
| `CompileStateMachine` | Step Functions | Standard (history for judges) |
| `AppLogGroup` | CloudWatch Logs | retention 14d |

Outputs: `ApiUrl`, `RawBucketName`, `PacketBucketName`, `StateMachineArn`, `AmplifyHint`.

---

## 4. API contract

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/healthz` | none | `{status, version, checks:{ddb,s3,bedrock?}}` |
| GET | `/cases` | api-key | `[{id,title,risk,ml_risk,category,cluster_id,created_at}]` |
| GET | `/cases/{id}` | api-key | full case + entities |
| POST | `/cases/{id}/packet` | api-key | `{executionArn}` |
| GET | `/cases/{id}/packet` | api-key | `{status, downloadUrl, sha256}` |
| POST | `/ingest` | api-key | upload fixture JSON (hackathon) |

Errors: JSON `{error, code}` with 4xx/5xx.

---

## 5. DynamoDB model

| pk | sk | Attributes |
|----|-----|------------|
| `CASE#&lt;id&gt;` | `META` | title, risk, ml_risk, category, raw_s3_key, raw_sha256, cluster_id, status, tlp, created_at |
| `CASE#&lt;id&gt;` | `ENT#&lt;type&gt;#&lt;hash&gt;` | type, value, confidence |
| `CLUSTER#&lt;id&gt;` | `CASE#&lt;id&gt;` | link |

GSI optional: `GSI1PK=STATUS#open`, `GSI1SK=RISK#&lt;padded&gt;` for queue sort.

---

## 6. Ingest path

1. Seed script uploads `fixtures/*.json` → `s3://raw/...`  
2. EventBridge / S3 notification → `IngestNormalize`  
3. Validate schema · sha256 · write META + ENT items  
4. `simulated: true` required — reject if missing  

---

## 7. Step Functions — `CasePacketCompile`

| State | Lambda | Failure |
|-------|--------|---------|
| ExtractEnrich | extract | Catch → continue with regex-only |
| ScoreCluster | score | Fail run (rules always available) |
| RenderPacket | compile | Fail run |
| UpdateCase | api/update | Fail run |

Show this graph in the judge video (Step Functions console).

---

## 8. Packet object (S3)

See PRD §8.3. Must include:

- `chain_of_custody[]` with `execution_arn`  
- `disclaimer` simulated  
- `ml` block: `{ ranker: "grpo"|"rules", group_size, ml_risk }`  

---

## 9. Folder layout

```
backend/   (or repo root with template.yaml)
  template.yaml
  samconfig.toml
  src/
    api/app.py
    ingest/handler.py
    extract/handler.py
    score/handler.py
    compile/handler.py
    reward/handler.py      # Bedrock RFT reward Lambda
    shared/db.py
    shared/hashutil.py
  fixtures/
  scripts/seed.py
  tests/
```

---

## 10. Deploy commands

```bash
export AWS_DEFAULT_REGION=ap-south-1
sam build
sam deploy --guided   # stack name: casepacket
python scripts/seed.py --bucket $(aws cloudformation describe-stacks ...)
curl "$API_URL/healthz"
```

---

## 11. Security

- [ ] No secrets in git  
- [ ] IAM: each Lambda least privilege  
- [ ] S3 buckets block public access (packets via signed URL)  
- [ ] API key in SSM; rotate after hackathon  
- [ ] CloudWatch billing alarm  

---

## 12. Demo evidence (backend)

1. API Gateway → hit `/cases`  
2. Step Functions → successful execution graph  
3. S3 → `raw/` + `packets/` objects  
4. DynamoDB → item browser  
5. CloudWatch → log lines for compile  

---

## 13. Out of scope

- Self-hosted Tor gateways  
- Running OpenCTI/MISP in ECS for v1  
- Multi-tenant enterprise RBAC  

---

*Backend is 100% AWS serverless so Ship It architecture/cost scoring is obvious.*
