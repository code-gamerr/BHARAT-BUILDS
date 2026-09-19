# CasePacket — ML / RL Spec (AWS Bedrock + GRPO)

Dark-web intel for LE — **extraction + risk ranking**.  
Training and inference stay on **AWS** (Bedrock + Lambda). No offline-only Colab as the Ship It story.

Related: [resources.md](./resources.md) · [backend.md](./backend.md) · [frontend.md](./frontend.md)

---

## 1. Goal

Two ML layers:

| Layer | Type | Job |
|-------|------|-----|
| **L1 Extract** | Rules + optional LLM (Bedrock) | Entities + short summary |
| **L2 Rank** | **RL — GRPO** via Bedrock Reinforcement Fine-Tuning | Learn which case briefs / triage order analysts prefer |

**Hard requirement:** GRPO training uses **group size &gt; 12** (generate **more than 12** candidate responses per prompt for relative scoring). Also use **≥ 12** training prompts in the dataset.

Official AWS behavior: Bedrock RFT “generates several responses per prompt… trained through **Group Relative Policy Optimization (GRPO)**.”  
Docs: https://docs.aws.amazon.com/bedrock/latest/userguide/reinforcement-fine-tuning.html  
Rewards: https://docs.aws.amazon.com/bedrock/latest/userguide/reward-functions.html

---

## 2. Why GRPO here (not random DL)

LE triage is a **preference** problem: given the same noisy listing, which summary/risk framing should surface first?  
GRPO fits: sample many candidate briefs → reward function scores them → policy improves. Chatbot-only Bedrock invoke ≠ learning a triage policy.

---

## 3. GRPO configuration (must exceed 12)

| Parameter | Minimum for this project | Notes |
|-----------|--------------------------|--------|
| **Group size** (candidates per prompt) | **≥ 13** (&gt; 12) | Set in RFT job / training config; document in README |
| Training prompts (JSONL rows) | **≥ 12** | Prefer 24–48 for a stronger demo |
| Reward Lambda timeout | ≤ seconds (AWS guidance) | Fast, deterministic scoring |
| Checkpoints | Save ≥ 1 mid-run | Show in Bedrock console for judges |
| Base model | Bedrock Nova / supported RFT model in account | Enable model access first |

### Training data shape (JSONL)

Each line = one triage prompt (fixture-derived):

```json
{"prompt": "Rank/write an LE triage brief for this SIMULATED listing:\nTITLE: ...\nBODY: ...\nENTITIES: ...\nPrefer: clear risk, entities first, no hype."}
```

Store dataset in **S3** `s3://…/ml/grpo/train.jsonl` (≥ 12 lines).

---

## 4. Reward function (Lambda on AWS)

**RLVR-style** verifiable rewards (no human in the loop at train time):

| Signal | Score contribution |
|--------|--------------------|
| Contains ≥ 1 extracted entity verbatim | +2 |
| Mentions risk level / numeric risk | +2 |
| Marks data as SIMULATED / TLP | +2 |
| Length 40–120 words | +1 |
| Banned hype (“guaranteed hack”, real onion URLs) | −5 |
| Empty / garbage | 0 |

Implement as **`RewardFunction`** Lambda (ARN attached to Bedrock RFT job).  
Keep pure CPU; no long external calls.

Pseudo:

```python
def handler(event, context):
    # event contains model output(s) for a prompt — follow Bedrock RFT reward contract
    text = extract_text(event)
    score = 0.0
    score += 2.0 if "SIMULATED" in text.upper() or "TLP" in text.upper() else 0
    score += 2.0 if has_entity_overlap(text, event) else 0
    score += 2.0 if looks_like_risk(text) else 0
    score += 1.0 if 40 <= word_count(text) <= 120 else 0
    score -= 5.0 if is_unsafe_hype(text) else 0
    return {"score": score}  # adapt to exact Bedrock reward response schema
```

---

## 5. Inference path (production weekend)

```
Case body + entities
        │
        ▼
Bedrock InvokeModel (base OR RFT-custom model)
        │  optional if RFT not finished
        ▼
ml_risk / triage_brief
        │
        ▼
Blend with rules risk: final_risk = 0.6 * rules + 0.4 * ml_risk
        │
        ▼
DynamoDB + frontend ML panel
```

**Fallback:** if custom model / Bedrock down → rules-only; packet still ships (`enrichment: degraded`).

---

## 6. L1 extraction (classic ML-lite)

| Method | AWS | Priority |
|--------|-----|----------|
| Regex NER (email, IN phone, URL, wallet, handle) | Lambda | P0 |
| Bedrock classify/summarize | `InvokeModel` | P1 |
| Embeddings cluster (optional) | Bedrock Titan Embed + cosine in Lambda | P2 |

No need for SageMaker training jobs for NER on a weekend — keep SageMaker out unless you already know it; **Bedrock RFT is the RL story**.

---

## 7. Folder layout

```
ml/
  datasets/
    grpo_train.jsonl          # ≥ 12 prompts
    grpo_train_readme.md      # how generated from fixtures
  reward/
    app.py                    # Lambda reward (deployed via SAM)
  notebooks/                  # optional local prototyping ONLY
  eval/
    rubric.md                 # human spot-check of 5 briefs
  docs_grpo_job.md            # screenshots + group_size=13+ 
```

Wire reward Lambda through **backend SAM** (`RewardFunction` in [backend.md](./backend.md)).

---

## 8. Build steps (ML track)

1. [x] Generate **≥ 12** prompts from fixtures → `ml/datasets/grpo_train.jsonl`  
2. [x] Deploy reward Lambda via SAM (`RewardFunction`) — ARN in outputs  
3. [ ] Bedrock console → **Reinforcement fine-tuning** (account)  
   - Dataset S3 URI  
   - Reward Lambda ARN  
   - **Configure group size &gt; 12** (e.g. 13 or 16)  
4. [ ] Start job; wait for ≥ 1 checkpoint  
5. [ ] Provisioned/custom model access for invoke  
6. [x] Wire `ScoreFunction` blend + `ENABLE_BEDROCK` degraded path  
7. [x] Log `group_size` (≥13) into packet `ml` block  
8. [ ] Screenshot Bedrock RFT job + CloudWatch reward invocations for demo  

---

## 9. Packet `ml` block (required for judges)

```json
{
  "ml": {
    "extractor": "regex+bedrock",
    "ranker": "bedrock-rft-grpo",
    "group_size": 13,
    "train_prompts": 24,
    "rft_job_arn": "arn:aws:bedrock:...",
    "rules_risk": 72,
    "ml_risk": 81,
    "final_risk": 76,
    "enrichment": "full"
  }
}
```

**Acceptance:** `group_size` **must be &gt; 12** in shipped packet + README.

---

## 10. Eval bar (quick)

| Check | Pass |
|-------|------|
| Reward prefers entity-rich brief over empty | Yes on 10/10 unit tests |
| Group size documented &gt; 12 | Yes |
| Degraded mode without Bedrock | Packet still builds |
| No real PII in train JSONL | Fixtures only |

---

## 11. Ethics

- Train **only** on simulated fixtures  
- Reward **penalizes** operational dark-web how-to language  
- UI + packet always say SIMULATED  

---

## 12. What to say in the 3-min video (ML)

> “We don’t just call a chatbot. We run **Bedrock reinforcement fine-tuning with GRPO**, group size **thirteen**—more than twelve candidates scored by a Lambda reward that prefers entity-rich, TLP-aware triage briefs. Then Step Functions compiles the case packet on AWS.”

---

*ML/RL path is AWS-native (Bedrock GRPO). That is the Agents-track differentiator for Bharat Builds.*
