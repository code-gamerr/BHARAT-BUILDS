import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, relativeTime } from "../api.js";
import { Panel, RiskPill } from "../components/ui.jsx";

export default function Cases() {
  const [rows, setRows] = useState([]);
  const [band, setBand] = useState("all");
  const [cat, setCat] = useState("all");
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .cases()
      .then((d) => setRows(d.cases || []))
      .catch((e) => setErr(e.message));
  }, []);

  const filtered = useMemo(
    () =>
      rows.filter(
        (c) => (band === "all" || c.risk_band === band) && (cat === "all" || c.category === cat),
      ),
    [rows, band, cat],
  );

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Intelligence queue</h1>
          <p className="mt-1 text-sm text-muted">Risk-ranked signals · open a case → investigate → packet</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {["all", "high", "medium", "low"].map((b) => (
            <button
              key={b}
              type="button"
              onClick={() => setBand(b)}
              className={`rounded-full border px-3 py-1 text-xs uppercase tracking-wide ${
                band === b ? "border-cyan/40 bg-cyan/10 text-cyan" : "border-line text-muted"
              }`}
            >
              {b}
            </button>
          ))}
          <select
            value={cat}
            onChange={(e) => setCat(e.target.value)}
            className="rounded-md border border-line bg-panel px-2 py-1 text-xs text-white"
          >
            <option value="all">All categories</option>
            <option value="fraud">Fraud</option>
            <option value="credentials">Credentials</option>
            <option value="docs">Documents</option>
            <option value="other">Other</option>
          </select>
        </div>
      </header>

      {err && <p className="text-sm text-red-400">{err}</p>}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((c) => (
          <Link key={c.id} to={`/cases/${c.id}`} className="block">
            <Panel className="h-full transition hover:border-cyan/35">
              <div className="flex items-start justify-between gap-2">
                <div className="font-mono text-sm text-cyan">{c.id}</div>
                <RiskPill band={c.risk_band} />
              </div>
              <h2 className="mt-2 line-clamp-2 text-base font-semibold text-white">{c.title}</h2>
              <div className="mt-3 flex items-end justify-between gap-2">
                <div>
                  <div className="font-mono text-2xl font-bold text-white">{c.risk}</div>
                  <div className="text-[10px] uppercase tracking-wider text-muted">/ 100 risk</div>
                </div>
                <div className="text-right text-xs text-muted">
                  <div className="uppercase tracking-wide">{c.category}</div>
                  <div>{(c.entities || []).length} entities</div>
                  <div>{(c.linked_cases || []).length} linked</div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-1">
                {(c.entities || []).slice(0, 4).map((e) => (
                  <span key={e.type + e.value} className="rounded border border-line px-1.5 py-0.5 text-[10px] uppercase text-muted">
                    {e.type}
                  </span>
                ))}
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-muted">
                <span>{c.source_label}</span>
                <span className="font-mono">{relativeTime(c.created_at)}</span>
              </div>
            </Panel>
          </Link>
        ))}
      </div>
    </div>
  );
}
