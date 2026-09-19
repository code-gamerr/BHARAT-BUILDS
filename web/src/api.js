const API = import.meta.env.VITE_API_URL || "";
const KEY = import.meta.env.VITE_API_KEY || "casepacket-demo-key";

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "content-type": "application/json",
      "x-api-key": KEY,
      ...(options.headers || {}),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || `HTTP ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  health: () => request("/healthz"),
  ops: () => request("/ops"),
  graph: () => request("/graph"),
  cases: () => request("/cases"),
  case: (id) => request(`/cases/${id}`),
  startPacket: (id) => request(`/cases/${id}/packet`, { method: "POST" }),
  getPacket: (id) => request(`/cases/${id}/packet`),
  packetPdfUrl: (id) => `${API}/cases/${id}/packet/pdf`,
  ingest: (listing) =>
    request("/ingest", { method: "POST", body: JSON.stringify(listing) }),
};

export function relativeTime(iso) {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso;
  const diff = Date.now() - t;
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 48) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

export function riskTone(band) {
  if (band === "high") return { pill: "bg-red-500/15 text-red-400 border-red-500/40", bar: "bg-red-500" };
  if (band === "medium") return { pill: "bg-amber-500/15 text-amber-300 border-amber-500/40", bar: "bg-amber-400" };
  return { pill: "bg-emerald-500/15 text-emerald-400 border-emerald-500/40", bar: "bg-emerald-400" };
}
