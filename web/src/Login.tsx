import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { getSession, login } from "./auth";

export default function Login() {
  const navigate = useNavigate();
  const existing = getSession();
  const [name, setName] = useState("Demo Analyst");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);

  if (existing) return <Navigate to="/app" replace />;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    login(name, apiKey);
    navigate("/app", { replace: true });
  }

  return (
    <div className="auth">
      <div className="auth-banner">Simulated fixture data — not operational intel</div>
      <div className="auth-bg" aria-hidden="true" />
      <main className="auth-panel">
        <Link to="/" className="auth-brand">
          <span className="auth-mark" aria-hidden="true" />
          <span>
            <strong>
              CASEP<em>_</em>
            </strong>
            <small>AUTH_GATE // DEMO</small>
          </span>
        </Link>
        <h1>REQUEST_ACCESS</h1>
        <p className="auth-lead">
          &gt; DEMO_GATE — optional API key overrides <code>VITE_API_KEY</code> for this session.
        </p>
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            <span>Display name</span>
            <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="nickname" />
          </label>
          <label>
            <span>
              API key <em>(optional)</em>
            </span>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Leave blank to use env key"
              autoComplete="off"
            />
          </label>
          <button type="submit" className="auth-submit" disabled={busy}>
            {busy ? "VERIFYING…" : "START_CONSOLE ↗"}
          </button>
        </form>
        <p className="auth-hint">
          <Link to="/">← Back to landing</Link>
        </p>
      </main>
    </div>
  );
}
