export const NAV = [
  { href: "#top", label: "INDEX" },
  { href: "#01", label: "/01" },
  { href: "#02", label: "/02" },
  { href: "#03", label: "/03" },
  { href: "#04", label: "/04" },
] as const;

export const PRINCIPLES = [
  {
    code: "01",
    title: "INGEST",
    body: "Simulated listings land hashed. Immutable raw before triage.",
  },
  {
    code: "02",
    title: "EXTRACT",
    body: "NER pulls phone, email, wallet, handle from noisy fixtures.",
  },
  {
    code: "03",
    title: "SCORE",
    body: "Rules + optional GRPO rank risk. Cluster on shared entities.",
  },
  {
    code: "04",
    title: "SEAL",
    body: "Step Functions / local compile → court-friendly CasePacket JSON.",
  },
  {
    code: "05",
    title: "AUDIT",
    body: "sha256 + execution ARN. Degraded mode when Bedrock is off.",
  },
] as const;

export const MODULES = [
  { id: "MOD_QUEUE", label: "TRIAGE_QUEUE", tag: "DASHBOARD" },
  { id: "MOD_INTEL", label: "INTEL_SEARCH", tag: "MONITOR" },
  { id: "MOD_PKT", label: "PACKET_COMPILE", tag: "OUTPUT" },
  { id: "MOD_CUST", label: "CHAIN_CUSTODY", tag: "EVIDENCE" },
] as const;
