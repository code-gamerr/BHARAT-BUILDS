import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { Panel } from "../components/ui.jsx";

const SAMPLE = `{
  "id": "fix-demo",
  "source": "fixture://marketplace-sim",
  "captured_at": "2026-09-19T12:00:00Z",
  "title": "Demo mule UPI desk (SIMULATED)",
  "body": "Contact +91-90909-09090 or demo.mule@example.invalid. UPI mule chatter only — fixture.",
  "category_hint": "fraud",
  "tlp": "TLP:AMBER",
  "meta": { "language": "en", "simulated": true }
}`;

export default function Ingest() {
  const [text, setText] = useState(SAMPLE);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const listing = JSON.parse(text);
      listing.meta = { ...(listing.meta || {}), simulated: true };
      const created = await api.ingest(listing);
      setResult(created);
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-white">Ingest</h1>
        <p className="mt-1 text-sm text-muted">
          Drop a simulated listing JSON — same path as S3 raw/ → normalize → NER → score → cluster.
        </p>
      </header>

      <Panel title="Fixture JSON">
        <form onSubmit={submit} className="space-y-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={16}
            className="w-full rounded-lg border border-line bg-ink p-3 font-mono text-xs text-cyan-100 outline-none focus:border-cyan-500/40"
          />
          {err && <p className="text-sm text-red-400">{err}</p>}
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-cyan-500 px-4 py-2 text-sm font-semibold text-ink hover:bg-cyan-400 disabled:opacity-50"
          >
            {busy ? "Ingesting…" : "Ingest simulated listing"}
          </button>
        </form>
      </Panel>

      {result && (
        <Panel title="Created case">
          <p className="text-sm text-white">
            <Link className="font-mono text-cyan-300 hover:underline" to={`/cases/${result.id}`}>
              {result.id}
            </Link>{" "}
            · risk {result.risk} · {result.entities?.length || 0} entities
          </p>
        </Panel>
      )}
    </div>
  );
}
