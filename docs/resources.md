# CasePacket — AWS Resources & Builder Center Pack

Everything needed to build for **Bharat Builds / First Commit (Ship It)** with **AWS at the core** (not a README mention).

**Region:** `ap-south-1` (Mumbai)  
**Accounts:** Free-tier / Student / credits from First Commit ($200 start; request more if needed)

---

## 1. Mandatory links (register & learn)

| Resource | URL | Why |
|----------|-----|-----|
| First Commit event | https://www.wemakedevs.org/aws/first-commit | Rules, Ship It vs Build It, demo requirements |
| Bharat Builds tour | https://www.wemakedevs.org/aws | Series context, prizes, Amazon fast-track |
| **AWS Builder Center** | https://builder.aws.com/ | Hub for courses, labs, community write-ups (required blog prize track) |
| AWS Console | https://ap-south-1.console.aws.amazon.com/ | Deploy + demo evidence |
| Rules | https://www.wemakedevs.org/aws/rules | Judging / AWS-at-core |

### Builder Center deliverables (hackathon)

- [ ] Builder Center profile active  
- [ ] Post write-up: problem · stack · what broke · architecture (Top 5 blogs → Logitech prize)  
- [ ] Link write-up in submission  

---

## 2. AWS services bill of materials (must appear in architecture)

| Layer | Service | CasePacket use | Builder / docs |
|-------|---------|----------------|----------------|
| Frontend host | **Amplify Hosting** (or S3 + CloudFront) | Analyst SPA | https://aws.amazon.com/amplify/ |
| Auth (optional) | **Cognito** | Demo analyst login | Amplify Gen 2 / Cognito docs |
| API | **API Gateway HTTP API** | `/healthz`, `/cases`, `/packet` | API Gateway console |
| Compute | **Lambda** (Python 3.12) | API, ingest, NER, reward, compile | Lambda docs |
| Orchestration | **Step Functions** | `CasePacketCompile` (auditable) | https://docs.aws.amazon.com/step-functions/ |
| Data | **DynamoDB** on-demand | cases, entities, clusters | DynamoDB docs |
| Evidence store | **S3** | `raw/`, `packets/`, model artifacts | S3 docs |
| Events | **EventBridge** | S3 ObjectCreated → ingest | EventBridge docs |
| GenAI | **Bedrock** InvokeModel | Summarize / classify (optional path) | https://aws.amazon.com/bedrock/ |
| **RL / GRPO** | **Bedrock Reinforcement Fine-Tuning** | Risk-triage policy via **GRPO** | https://docs.aws.amazon.com/bedrock/latest/userguide/reinforcement-fine-tuning.html |
| Reward | **Lambda reward function** | Scores ranked case briefs (RLVR) | https://docs.aws.amazon.com/bedrock/latest/userguide/reward-functions.html |
| Secrets | **SSM Parameter Store** / Secrets Manager | API keys, model IDs | SSM docs |
| Observability | **CloudWatch** Logs + Metrics | Judge video evidence | CloudWatch docs |
| IaC | **SAM** (primary) or CDK | One-command Ship It deploy | https://docs.aws.amazon.com/serverless-application-model/ |
| Identity (IAM) | **IAM roles** | Least privilege per Lambda | IAM docs |

### Ship It scoring alignment

Judges look for: idea · **AWS implementation** · demo · usability · architecture/cost.  
Every row above should show up in the 3-min video or architecture diagram.

---

## 3. Open-source / standards (reference only — not the runtime)

| Project | Use as inspiration | Link |
|---------|--------------------|------|
| OpenCTI | TIP ingest → graph → export | https://github.com/OpenCTI-Platform/opencti |
| MISP | TLP / IOC sharing concepts | https://www.misp-project.org/ |
| TheHive + Cortex | Case + observables UX | https://github.com/TheHive-Project/TheHive |
| STIX 2.1 | Lite export shape | https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html |
| security-audit-skill | Machine-readable findings JSON | https://github.com/cloudflare/security-audit-skill |
| brag | Ship It demo video from repo | https://github.com/latent-spaces/brag |
| awesome-ai-security-tools | AI + CTI tool landscape | https://github.com/scadastrangelove/awesome-ai-security-tools |
| Trendshift | Discover rising OSS | https://trendshift.io/ |

Do **not** self-host OpenCTI for the weekend — stay on AWS serverless.

### Executive Summary (local)

See [`Executive Summary.pdf`](../Executive%20Summary.pdf) — KAVACH/Cyph3r context, SecNinjaz-style architecture, legal/ethics. **CID Track: undocumented** — do not claim.

---

## 4. Workshops & samples (hands-on)

| Workshop / sample | Stack | Link |
|-------------------|-------|------|
| Bedrock Serverless Workshop | SAM + Lambda + Cognito + Amplify UI + Bedrock | https://github.com/aws-samples/bedrock-serverless-workshop |
| Amplify ↔ Bedrock | Amplify Gen 2 custom query → Bedrock | https://docs.amplify.aws/react/build-a-backend/data/custom-business-logic/connect-bedrock/ |
| Serverless + Bedrock registration workshop | SAM + API GW + Lambda + Bedrock | AWS Workshop Studio catalog (search “serverless registration Bedrock”) |
| Bedrock RFT (GRPO) | Automated GRPO training loop | https://docs.aws.amazon.com/bedrock/latest/userguide/reinforcement-fine-tuning.html |

---

## 5. Local tooling checklist

| Tool | Install | Check |
|------|---------|-------|
| AWS CLI v2 | https://aws.amazon.com/cli/ | `aws sts get-caller-identity` |
| SAM CLI | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html | `sam --version` |
| Node 20+ | nodejs.org | `node -v` (frontend) |
| Python 3.12 | python.org | `python -V` (Lambdas) |
| Git + GitHub | | Public repo for submission |
| jq (optional) | | API debugging |

```bash
aws configure  # ap-south-1
sam build && sam deploy --guided
```

---

## 6. Credits & cost guardrails

| Item | Note |
|------|------|
| First Commit credits | New account up to ~$200; request more from organizers if needed |
| Bedrock | Enable model access in console (region may be `us-east-1` for some FMs — document cross-region if used) |
| RFT / GRPO | Training job cost — use **small** dataset (≥12 prompts, group size **>12**); stop early after checkpoint |
| Amplify / S3 / Lambda / DDB | Pennies for demo traffic |
| Budget alarm | CloudWatch billing alarm at $20 |

---

## 7. Split build docs (this repo)

| File | Scope |
|------|--------|
| [frontend.md](./frontend.md) | Amplify SPA — queue, case, ops |
| [backend.md](./backend.md) | SAM API, ingest, Step Functions, S3, DynamoDB |
| [ml.md](./ml.md) | NER + Bedrock + **GRPO (group size > 12)** risk policy |
| [plan.md](./plan.md) | Phase checklist |
| [CasePacket-PRD.md](./CasePacket-PRD.md) | Full product requirements |

---

## 8. Submission resource pack

- [ ] Public GitHub  
- [ ] Live Amplify/CloudFront URL  
- [ ] `/healthz` green  
- [ ] 2–3 min demo (show **AWS console**: Step Functions, S3, Bedrock RFT job or invoke logs)  
- [ ] Builder Center write-up URL  
- [ ] Architecture + cost paragraph  

---

*AWS-first for Bharat Builds. No non-AWS runtime for core path except browser SPA assets hosted on Amplify/S3.*
