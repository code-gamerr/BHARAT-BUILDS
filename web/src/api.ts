import { getApiKey } from "./auth";

const base = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

function headers(path: string, init?: HeadersInit): Headers {
  const h = new Headers(init);
  if (!h.has("content-type") && !(init && "Content-Type" in (init as object))) {
    h.set("content-type", "application/json");
  }
  const key = getApiKey();
  if (key && !path.includes("healthz")) {
    h.set("x-api-key", key);
  }
  return h;
}

export function apiUrl(path: string): string {
  if (path.startsWith("http")) return path;
  if (!base) {
    throw new Error("VITE_API_URL is not set — copy web/.env.example to web/.env");
  }
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), {
    ...init,
    headers: headers(path, init?.headers),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

/** Authenticated download (works when API key is set; relative URLs get API base). */
export async function downloadPacket(caseId: string, downloadUrl?: string | null): Promise<void> {
  const path = downloadUrl?.startsWith("http")
    ? downloadUrl
    : downloadUrl
      ? apiUrl(downloadUrl)
      : apiUrl(`/cases/${caseId}/packet/download`);
  const res = await fetch(path, { headers: headers(path) });
  if (!res.ok) throw new Error(await res.text());
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${caseId}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}
