import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, relativeTime } from "../api.js";
import { Panel } from "../components/ui.jsx";

export default function IocSearch() {
  const [params] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const [cases, setCases] = useState([]);

  useEffect(() => {
    setQ(params.get("q") || "");
  }, [params]);

  useEffect(() => {
    api.cases().then((d) => setCases(d.cases || [])).catch(() => setCases([]));
  }, []);

  const hits = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const rows = [];
    for (const c of cases) {
      for (const e of c.entities || []) {
        const hay = `${e.type} ${e.value} ${c.id} ${c.title}`.toLowerCase();
        if (!needle || hay.includes(needle)) {
          rows.push({ ...e, caseId: c.id, title: c.title, source: c.source_label });
        }
      }
    }
    return rows.slice(0, 80);
  }, [cases, q]);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-3xl font-bold text-white">IOC search</h1>
        <p className="mt-1 text-sm text-muted">Search phone, email, wallet, domain, handle across seeded cases.</p>
      </header>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="e.g. +91-90000-00001 or dump_broker@"
        className="w-full max-w-xl rounded-lg border border-line bg-panel px-3 py-2.5 text-sm outline-none focus:border-cyan/40"
      />
      <Panel title={`${hits.length} matches`}>
        <ul className="space-y-2">
          {hits.map((h) => (
            <li key={`${h.caseId}-${h.type}-${h.value}`}>
              <Link
                to={`/cases/${h.caseId}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line px-3 py-2.5 hover:border-cyan/30"
              >
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted">{h.type}</div>
                  <div className="font-mono text-sm text-cyan">{h.value}</div>
                  <div className="text-xs text-muted">
                    {h.caseId} · {h.source} · {relativeTime(h.first_seen)}
                  </div>
                </div>
                <div className="font-mono text-xs text-amber-300">{Math.round((h.confidence || 0.9) * 100)}%</div>
              </Link>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
