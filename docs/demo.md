# CasePacket — 3-minute demo script (docs/plan Phase 5)

## Local (no AWS)

1. Open http://127.0.0.1:5173 — health pill green, **SIMULATED** banner  
2. Triage queue → open highest-risk case  
3. **Generate CasePacket** → **Download JSON**  
4. Show `chain_of_custody`, `findings[]`, `ml.group_size` (≥13)

## AWS (Ship It)

1. Amplify URL → same clicks  
2. AWS Console → Step Functions → successful `CasePacketCompile`  
3. S3 → `raw/` + `packets/`  
4. DynamoDB → `CASE#…` META + ENT  
5. (ML) Bedrock RFT job with group size **13** + Reward Lambda CloudWatch  

Narration beat: “Not a chatbot — fixtures in, court-friendly packet out on AWS.”
