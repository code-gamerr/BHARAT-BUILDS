# CasePacket — Frontend Spec (AWS Amplify)

Dark-web intel for LE — **analyst console** only. Hosted on **AWS Amplify Hosting** (Ship It URL).

Related: [resources.md](./resources.md) · [backend.md](./backend.md) · [ml.md](./ml.md)

---

## 1. Goal

A judge-ready SPA where an LE analyst:

1. Sees a **risk-sorted triage queue**  
2. Opens a **case** (entities, cluster links, excerpt)  
3. Triggers **Generate CasePacket** and downloads JSON  
4. Always sees **SIMULATED DATA** banner  

**Not a chatbot.** Chat is optional stretch; core UX is queue → case → packet.

---

## 2. AWS hosting & wiring

| Piece | Choice |
|-------|--------|
| Host | **Amplify Hosting** (CI from GitHub) or `amplify publish` |
| Region | `ap-south-1` (CDN global) |
| Config | `VITE_API_URL` = API Gateway URL from SAM outputs |
| Auth header | `x-api-key` from Amplify env (demo) — or Cognito later |
| CORS | Backend must allow Amplify origin |

### Amplify checklist

- [ ] Connect GitHub repo / `web/` app root  
- [ ] Build: `npm ci && npm run build`  
- [ ] Artifact: `dist/`  
- [ ] Env vars in Amplify Console  
- [ ] Custom domain optional — default Amplify URL is enough for Ship It  

Docs: https://aws.amazon.com/amplify/ · Amplify Gen 2 Bedrock (optional): https://docs.amplify.aws/react/build-a-backend/data/custom-business-logic/connect-bedrock/

---

## 3. Stack

| Lib | Why |
|-----|-----|
| Vite + React 18/19 + TypeScript | Fast SPA |
| React Router | `/` queue, `/cases/:id` |
| TanStack Query (optional) | API cache |
| CSS modules or plain CSS | No purple-AI slop; ops-console look |

---

## 4. Screens

### 4.1 App shell
- Brand **CasePacket** hero-level in header  
- Green/red **Health** pill (`GET /healthz` every 30s)  
- Sticky banner: `SIMULATED FIXTURE DATA — NOT OPERATIONAL INTEL`

### 4.2 Queue `/`
| Column / card field | Source |
|---------------------|--------|
| Title | `case.title` |
| Risk | `case.risk` (0–100) + color |
| Category | `case.category` badge |
| Cluster | `case.cluster_id` |
| Updated | `case.created_at` |

Sort: risk desc. Click → case detail.

### 4.3 Case `/cases/:id`
- Left: title, TLP, raw excerpt  
- Right: entity chips (`email`, `phone`, `wallet`, `url`, `handle`)  
- Linked cases list  
- **ML panel:** base risk vs **GRPO-ranked** score (from backend) if present  
- Actions: `Generate packet` → poll status → `Download JSON`

### 4.4 Ops strip (footer)
- Last Step Functions status  
- `execution_arn` truncated + copy  
- Link text: “Show this ARN in AWS console for judges”

---

## 5. API client

```ts
// web/src/api/client.ts
const base = import.meta.env.VITE_API_URL;
const key = import.meta.env.VITE_API_KEY;

export async function api(path: string, init?: RequestInit) {
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      "x-api-key": key,
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

| Call | Method |
|------|--------|
| Health | `GET /healthz` (no key OK) |
| List | `GET /cases` |
| Detail | `GET /cases/:id` |
| Start packet | `POST /cases/:id/packet` |
| Packet meta | `GET /cases/:id/packet` |

---

## 6. UX / a11y bar

- [ ] Keyboard reachable buttons  
- [ ] Contrast on risk badges  
- [ ] Empty / loading / error states  
- [ ] Mobile: queue usable on phone (judges check phones)

---

## 7. Folder layout

```
web/
  index.html
  package.json
  src/
    main.tsx
    App.tsx
    api/client.ts
    pages/Queue.tsx
    pages/Case.tsx
    components/Banner.tsx
    components/HealthPill.tsx
    components/EntityChips.tsx
    styles/
```

---

## 8. Demo clicks (frontend only)

1. Open Amplify URL  
2. Health green  
3. Open highest-risk case  
4. Generate → Download  
5. (Narrate) “Backend on API Gateway + Step Functions — next clip AWS console”

---

## 9. Out of scope (frontend)

- Rendering full Tor pages  
- Training UI for GRPO (training is Bedrock console / backend job)  
- Admin user management (Cognito stretch)

---

*Frontend ships on Amplify so the Ship It URL is 100% AWS-hosted.*
