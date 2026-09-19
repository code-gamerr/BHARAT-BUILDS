import {
  Link,
  NavLink,
  Navigate,
  Outlet,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, downloadPacket } from "./api";
import { getSession, isAuthed, logout } from "./auth";

export type CaseRow = {
  id: string;
  title: string;
  risk: number;
  ml_risk?: number;
  category?: string;
  cluster_id?: string;
  status?: string;
  created_at?: string;
  body?: string;
  entities?: Entity[];
  linked_case_ids?: string[];
  tlp?: string;
};

type Health = { status: string; mode?: string; cases?: number };
type Entity = { type: string; value: string; confidence?: number };

function riskBand(risk: number): 0 | 1 | 2 | 3 {
  return Math.min(3, Math.floor((risk || 0) / 25)) as 0 | 1 | 2 | 3;
}

function priorityLabel(risk: number): "High" | "Medium" | "Low" {
  if (risk >= 70) return "High";
  if (risk >= 40) return "Medium";
  return "Low";
}

export function RequireAuth({ children }: { children: ReactNode }) {
  if (!isAuthed()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function ConsoleLayout() {
  const navigate = useNavigate();
  const session = getSession();
  const [health, setHealth] = useState<Health | null>(null);

  const refreshHealth = useCallback(() => {
    api<Health>("/healthz")
      .then(setHealth)
      .catch(() => setHealth({ status: "offline" }));
  }, []);

  useEffect(() => {
    refreshHealth();
    const t = setInterval(refreshHealth, 30000);
    return () => clearInterval(t);
  }, [refreshHealth]);

  return (
    <div className="shell">
      <div className="banner" role="status">
        Simulated fixture data — not operational intel
      </div>
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark" aria-hidden="true" />
          CASEP<em>_</em>
        </Link>
        <nav className="top-nav" aria-label="Primary">
          <NavLink to="/app" end>
            Dashboard
          </NavLink>
          <NavLink to="/app/intelligence">Intelligence</NavLink>
          <NavLink to="/app/queue">Investigations</NavLink>
        </nav>
        <div className="top-right">
          <span className="session-chip">{session?.name ?? "Analyst"}</span>
          <span className={`pill ${health?.status === "ok" ? "ok" : "bad"}`}>
            <span className="pill-dot" />
            {health?.status ?? "…"}
          </span>
          <button
            type="button"
            className="ghost-btn"
            onClick={() => {
              logout();
              navigate("/login", { replace: true });
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="shell-body">
        <aside className="sidebar" aria-label="Modules">
          <NavLink to="/app" end>
            Overview
          </NavLink>
          <NavLink to="/app/intelligence">Dark-web monitor</NavLink>
          <NavLink to="/app/queue">Threats / queue</NavLink>
          <NavLink to="/app/intelligence">Entities</NavLink>
          <button type="button" className="side-seed" onClick={() => api("/seed", { method: "POST" }).then(() => window.location.reload())}>
            Reload fixtures
          </button>
        </aside>
        <div className="shell-main">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export function Dashboard() {
  const [rows, setRows] = useState<CaseRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<CaseRow[]>("/cases")
      .then(setRows)
      .catch((e) => setErr(String(e)));
  }, []);

  const sorted = useMemo(() => [...rows].sort((a, b) => (b.risk || 0) - (a.risk || 0)), [rows]);
  const high = sorted.filter((r) => (r.risk || 0) >= 70).length;
  const mid = sorted.filter((r) => (r.risk || 0) >= 40 && (r.risk || 0) < 70).length;

  return (
    <main className="page">
      <header className="page-head">
        <div>
          <h1>Threat intelligence overview</h1>
          <p className="muted">Simulated monitoring of fixture markets and forum-style dumps.</p>
        </div>
      </header>
      {err && <p className="err">{err}</p>}
      <div className="kpi-row">
        <div className="kpi">
          <span>Monitored fixtures</span>
          <strong>{sorted.length || "—"}</strong>
          <em className="up">demo set</em>
        </div>
        <div className="kpi">
          <span>Active threats</span>
          <strong className="danger">{high + mid}</strong>
          <em className="down">risk ≥ 40</em>
        </div>
        <div className="kpi">
          <span>High priority</span>
          <strong className="danger">{high}</strong>
          <em className="down">risk ≥ 70</em>
        </div>
        <div className="kpi">
          <span>Packets ready</span>
          <strong>{sorted.filter((r) => r.status === "packet_ready").length}</strong>
          <em className="up">compiled</em>
        </div>
      </div>

      <div className="dash-grid">
        <section className="panel map-panel">
          <h2>Threat activity map</h2>
          <p className="muted sm">Illustrative India HUD — simulated hotspots only</p>
          <div className="map-wrap">
            <svg viewBox="0 0 320 360" className="india-map" aria-hidden="true">
              <ellipse cx="160" cy="180" rx="130" ry="150" fill="#0a1520" />
              <path
                d="M160 36c22 10 52 26 64 56 14 34 34 48 40 82 8 32-2 60-20 84-16 22-34 48-56 60-18 10-40 8-56-2-26-14-42-44-48-72-10-36-4-66 10-96 12-26 34-48 50-64 10-10 18-22 26-48z"
                fill="none"
                stroke="#3ec6ff"
                strokeWidth="2.4"
              />
              {[
                [150, 90],
                [190, 130],
                [210, 180],
                [170, 220],
                [130, 260],
                [110, 160],
              ].map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r="6" fill="#ff4d4d" opacity={0.9} />
              ))}
            </svg>
            <div className="map-legend">
              <span>
                <i className="hi" /> High
              </span>
              <span>
                <i className="md" /> Medium
              </span>
              <span>
                <i className="lo" /> Low
              </span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Recent detections</h2>
            <Link to="/app/intelligence">View all</Link>
          </div>
          <ul className="detect-list">
            {sorted.slice(0, 6).map((r) => {
              const p = priorityLabel(r.risk || 0);
              return (
                <li key={r.id}>
                  <Link to={`/app/intelligence?id=${r.id}`}>
                    <div>
                      <strong>{r.title}</strong>
                      <span>
                        {r.category ?? "signal"} · {r.id}
                      </span>
                    </div>
                    <em className={`prio p-${p.toLowerCase()}`}>{p}</em>
                  </Link>
                </li>
              );
            })}
            {!sorted.length && !err && <li className="muted">No cases — reload fixtures</li>}
          </ul>
        </section>
      </div>
    </main>
  );
}

export function Intelligence() {
  const [rows, setRows] = useState<CaseRow[]>([]);
  const [selected, setSelected] = useState<CaseRow | null>(null);
  const [q, setQ] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [params, setParams] = useSearchParams();

  const load = useCallback(() => {
    api<CaseRow[]>("/cases")
      .then(async (list) => {
        setRows(list);
        const want = params.get("id");
        const first = want ? list.find((c) => c.id === want) : list[0];
        if (first) {
          const full = await api<CaseRow>(`/cases/${first.id}`);
          setSelected(full);
        }
      })
      .catch((e) => setErr(String(e)));
  }, [params]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const sorted = [...rows].sort((a, b) => (b.risk || 0) - (a.risk || 0));
    if (!needle) return sorted;
    return sorted.filter(
      (r) =>
        r.title?.toLowerCase().includes(needle) ||
        r.id?.toLowerCase().includes(needle) ||
        r.category?.toLowerCase().includes(needle),
    );
  }, [rows, q]);

  async function pick(id: string) {
    setParams({ id });
    const full = await api<CaseRow>(`/cases/${id}`);
    setSelected(full);
  }

  return (
    <main className="page intel">
      <header className="page-head">
        <div>
          <h1>Search dark-web intelligence</h1>
          <p className="muted">Search across simulated fixtures — markets, dumps, channels.</p>
        </div>
      </header>

      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault();
        }}
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder='Try "aadhaar", "wallet", "credentials"…'
          aria-label="Search intelligence"
        />
        <button type="submit">Search</button>
      </form>

      {err && <p className="err">{err}</p>}

      <div className="intel-split">
        <section className="results">
          <p className="results-count">{filtered.length} results found</p>
          <ul>
            {filtered.map((r) => {
              const p = priorityLabel(r.risk || 0);
              const active = selected?.id === r.id;
              return (
                <li key={r.id}>
                  <button type="button" className={active ? "result active" : "result"} onClick={() => pick(r.id)}>
                    <div className="result-top">
                      <strong>{r.title}</strong>
                      <em className={`prio p-${p.toLowerCase()}`}>{p}</em>
                    </div>
                    <span className="result-meta">
                      {r.category} · {r.id}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="detail panel">
          {!selected ? (
            <p className="muted">Select a result</p>
          ) : (
            <>
              <div className="detail-head">
                <h2>{selected.title}</h2>
                <em className={`prio p-${priorityLabel(selected.risk || 0).toLowerCase()}`}>
                  {priorityLabel(selected.risk || 0)}
                </em>
              </div>
              <dl className="meta-grid">
                <div>
                  <dt>Source</dt>
                  <dd>fixture · simulated</dd>
                </div>
                <div>
                  <dt>Category</dt>
                  <dd>{selected.category ?? "—"}</dd>
                </div>
                <div>
                  <dt>Risk</dt>
                  <dd>{selected.risk}</dd>
                </div>
                <div>
                  <dt>TLP</dt>
                  <dd>{selected.tlp ?? "AMBER"}</dd>
                </div>
              </dl>
              <h3 className="h3">Excerpt</h3>
              <pre className="excerpt">{selected.body}</pre>
              <h3 className="h3">Entities</h3>
              <div className="chips">
                {(selected.entities || []).map((e) => (
                  <span key={e.type + e.value} className="chip">
                    <em>{e.type}</em> {e.value}
                  </span>
                ))}
                {!(selected.entities || []).length && <span className="muted">none</span>}
              </div>
              <Link className="lp-cta" to={`/app/cases/${selected.id}`}>
                Add to investigation →
              </Link>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

export function Queue() {
  const [rows, setRows] = useState<CaseRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "high">("all");
  const [q, setQ] = useState("");

  useEffect(() => {
    api<CaseRow[]>("/cases")
      .then(setRows)
      .catch((e) => setErr(String(e)));
  }, []);

  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return [...rows]
      .sort((a, b) => (b.risk || 0) - (a.risk || 0))
      .filter((r) => {
        if (filter === "high" && (r.risk || 0) < 50) return false;
        if (!needle) return true;
        return (
          r.title?.toLowerCase().includes(needle) ||
          r.id?.toLowerCase().includes(needle) ||
          r.category?.toLowerCase().includes(needle)
        );
      });
  }, [rows, filter, q]);

  return (
    <main className="page">
      <header className="page-head">
        <div>
          <h1>Investigations queue</h1>
          <p className="muted">Risk-sorted cases ready for CasePacket compile.</p>
        </div>
      </header>
      <div className="filters">
        <input className="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter…" />
        <div className="seg">
          <button type="button" className={filter === "all" ? "seg-active" : ""} onClick={() => setFilter("all")}>
            All
          </button>
          <button type="button" className={filter === "high" ? "seg-active" : ""} onClick={() => setFilter("high")}>
            Risk ≥ 50
          </button>
        </div>
      </div>
      {err && <p className="err">{err}</p>}
      <div className="table">
        {visible.map((r) => (
          <Link key={r.id} to={`/app/cases/${r.id}`} className="row">
            <div className="risk-cell">
              <span className={`risk r${riskBand(r.risk || 0)}`}>{r.risk}</span>
              <span className="risk-meta">{priorityLabel(r.risk || 0)}</span>
            </div>
            <span className="grow">
              <span className="title">{r.title}</span>
              <span className="meta">{r.id}</span>
            </span>
            <span className="cat">{r.category}</span>
            <span className={`status-badge s-${r.status ?? "open"}`}>{r.status ?? "open"}</span>
          </Link>
        ))}
      </div>
    </main>
  );
}

export function CaseDetail() {
  const { id } = useParams();
  const [data, setData] = useState<CaseRow | null>(null);
  const [packet, setPacket] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState<"idle" | "start" | "compile" | "ready" | "error">("idle");

  useEffect(() => {
    if (!id) return;
    api<CaseRow>(`/cases/${id}`)
      .then(setData)
      .catch((e) => {
        setMsg(String(e));
        setPhase("error");
      });
    api(`/cases/${id}/packet`)
      .then((p) => {
        setPacket(p);
        if (p?.downloadUrl || p?.status === "packet_ready") setPhase("ready");
      })
      .catch(() => undefined);
  }, [id]);

  async function generate() {
    if (!id) return;
    setBusy(true);
    setPhase("start");
    setMsg("Starting compile…");
    try {
      await api(`/cases/${id}/packet`, { method: "POST" });
      setPhase("compile");
      setMsg("Compiling CasePacket…");
      for (let i = 0; i < 20; i++) {
        await new Promise((r) => setTimeout(r, i === 0 ? 200 : 1000));
        const p = await api<any>(`/cases/${id}/packet`);
        setPacket(p);
        if (p.downloadUrl || p.status === "packet_ready") {
          setPhase("ready");
          setMsg("Packet ready");
          setData(await api(`/cases/${id}`));
          return;
        }
      }
      setMsg("Still compiling — check Step Functions on AWS");
    } catch (e) {
      setPhase("error");
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!data) return <main className="page">{msg || "Loading…"}</main>;

  const ready =
    phase === "ready" ||
    packet?.downloadUrl ||
    packet?.status === "packet_ready" ||
    data.status === "packet_ready";

  return (
    <main className="page case">
      <Link to="/app/queue" className="back">
        ← Investigations
      </Link>
      <div className="case-grid">
        <section>
          <p className="eyebrow">{data.id}</p>
          <h1>{data.title}</h1>
          <div className="case-meta-row">
            <span className={`risk-pill r${riskBand(data.risk || 0)}`}>Risk {data.risk}</span>
            <span className="meta-chip">{data.category}</span>
            <span className="meta-chip">{data.tlp}</span>
            <span className={`status-badge s-${data.status}`}>{data.status}</span>
          </div>
          <h2 className="h2">Raw signal</h2>
          <pre className="excerpt">{data.body}</pre>
          <h2 className="h2">Entities</h2>
          <div className="chips">
            {(data.entities || []).map((e) => (
              <span key={e.type + e.value} className="chip">
                <em>{e.type}</em> {e.value}
              </span>
            ))}
          </div>
          {(data.linked_case_ids || []).length > 0 && (
            <>
              <h2 className="h2">Linked</h2>
              <div className="chips">
                {data.linked_case_ids!.map((cid) => (
                  <Link key={cid} to={`/app/cases/${cid}`} className="chip link">
                    {cid}
                  </Link>
                ))}
              </div>
            </>
          )}
        </section>
        <aside className="case-aside">
          <div className="panel">
            <h2 className="h2 tight">Compile CasePacket</h2>
            <ol className="steps">
              <li className={phase !== "idle" ? "done" : ""}>Start execution</li>
              <li className={phase === "compile" || phase === "ready" ? "done" : ""}>Extract · score · render</li>
              <li className={ready ? "done" : ""}>Download sealed JSON</li>
            </ol>
            <div className="ml-panel">
              <span>rules {data.risk}</span>
              <span>ml {data.ml_risk ?? data.risk}</span>
              <span>{packet?.enrichment ?? "rules"}</span>
            </div>
            <div className="actions">
              <button type="button" disabled={busy} onClick={generate}>
                {busy ? "Working…" : ready ? "Regenerate packet" : "Generate CasePacket"}
              </button>
              {ready && (
                <button
                  type="button"
                  className="secondary"
                  onClick={async () => {
                    try {
                      await downloadPacket(id!, packet?.downloadUrl);
                      setMsg("Downloaded");
                    } catch (e) {
                      setMsg(String(e));
                    }
                  }}
                >
                  Download JSON
                </button>
              )}
            </div>
            {msg && <p className={`aside-msg ${phase === "error" ? "err" : "muted"}`}>{msg}</p>}
          </div>
          <div className="panel">
            <h2 className="h2 tight">Chain of custody</h2>
            {packet?.sha256 ? (
              <p className="ops mono">sha256 · {packet.sha256}</p>
            ) : (
              <p className="muted">Hash appears after compile.</p>
            )}
            {packet?.execution_arn && <p className="ops mono">exec · {packet.execution_arn}</p>}
          </div>
        </aside>
      </div>
    </main>
  );
}
