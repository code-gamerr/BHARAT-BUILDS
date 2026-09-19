import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, relativeTime } from "../api.js";
import { Panel, RiskPill } from "../components/ui.jsx";

export default function IntelFeed() {
  const [cases, setCases] = useState([]);
  useEffect(() => {
    api.cases().then((d) => setCases(d.cases || [])).catch(() => setCases([]));
  }, []);

  const events = useMemo(
    () =>
      [...cases]
        .sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)))
        .map((c) => ({
          id: c.id,
          title: c.title,
          source: c.source_label,
          band: c.risk_band,
          when: c.created_at,
          entities: (c.entities || []).length,
        })),
    [cases],
  );

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-3xl font-bold text-white">Intel feed</h1>
        <p className="mt-1 text-sm text-muted">Simulated listings as a live-style feed — fixtures only.</p>
      </header>
      <Panel>
        <ul className="space-y-2">
          {events.map((e) => (
            <li key={e.id}>
              <Link
                to={`/cases/${e.id}`}
                className="flex items-center justify-between gap-3 rounded-lg border border-line px-3 py-3 hover:border-cyan/30"
              >
                <div className="min-w-0">
                  <div className="font-mono text-xs text-cyan">{e.id}</div>
                  <div className="truncate text-sm text-white">{e.title}</div>
                  <div className="text-xs text-muted">
                    {e.source} · {e.entities} IOCs · {relativeTime(e.when)}
                  </div>
                </div>
                <RiskPill band={e.band} />
              </Link>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
