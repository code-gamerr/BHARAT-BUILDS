const SESSION_KEY = "cp_session";
const API_KEY_STORE = "cp_api_key";

export type Session = {
  name: string;
  role: string;
  enteredAt: string;
};

export function getSession(): Session | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function isAuthed(): boolean {
  return getSession() != null;
}

export function login(name: string, apiKey?: string): Session {
  const session: Session = {
    name: name.trim() || "Demo Analyst",
    role: "cyber-cell",
    enteredAt: new Date().toISOString(),
  };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  if (apiKey?.trim()) {
    sessionStorage.setItem(API_KEY_STORE, apiKey.trim());
  }
  return session;
}

export function logout(): void {
  sessionStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(API_KEY_STORE);
}

/** Session override → env → empty */
export function getApiKey(): string {
  try {
    const fromSession = sessionStorage.getItem(API_KEY_STORE);
    if (fromSession) return fromSession;
  } catch {
    /* ignore */
  }
  return import.meta.env.VITE_API_KEY ?? "";
}
