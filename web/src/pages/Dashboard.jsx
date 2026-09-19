import { useEffect, useMemo, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import {
  AlertTriangle,
  ArrowUpRight,
  Database,
  FileJson2,
  Link2,
  Package,
  Radar,
  Search,
} from "lucide-react";
import { api, relativeTime } from "../api.js";
import { Panel, RiskPill } from "../components/ui.jsx";

const DAYS = ["Sep 13", "Sep 14", "Sep 15", "Sep 16", "Sep 17", "Sep 18", "Sep 19"];

function ThreatChart({ series }) {
  const w = 420;
  const h = 180;
  const pad = 24;
  const max = Math.max(1, ...series.flatMap((s) => s.values));
  const colors = { fraud: "#ff4d4d", credentials: "#00e5ff", docs: "#ffb84d", other: "#64748b" };

  function path(values) {
    return values
      .map((v, i) => {
        const x = pad + (i * (w - pad * 2)) / (values.length - 1);
        const y = h - pad - (v / max) * (h - pad * 2);
        return `${i === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ");
  }

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-44 w-full">
      {[0.25, 0.5, 0.75].map((g) => (
        <line
          key={g}
          x1={pad}
          x2={w - pad}
          y1={h - pad - g * (h - pad * 2)}
          y2={h - pad - g * (h - pad * 2)}
          stroke="rgba(26,39,56,0.9)"
          strokeDasharray="3 4"
        />
      ))}
      {series.map((s) => (
        <path key={s.key} d={path(s.values)} fill="none" stroke={colors[s.key] || "#00e5ff"} strokeWidth="2" />
      ))}
      {DAYS.map((d, i) => (
        <text
          key={d}
          x={pad + (i * (w - pad * 2)) / (DAYS.length - 1)}
          y={h - 6}
          fill="#7d8da6"
          fontSize="9"
          textAnchor="middle"
          fontFamily="IBM Plex Mono"
        >
          {d.replace("Sep ", "")}
        </text>
      ))}
    </svg>
  );
}

function ThreatMap({ high, medium, low }) {
  const nodes = [
    { x: 120, y: 90, r: high },
    { x: 210, y: 70, r: medium },
    { x: 280, y: 110, r: low },
    { x: 160, y: 140, r: medium },
    { x: 250, y: 150, r: high },
    { x: 90, y: 130, r: low },
  ];
  return (
    <svg viewBox="0 0 360 200" className="h-44 w-full">
      <ellipse cx="180" cy="100" rx="150" ry="70" fill="none" stroke="rgba(0,229,255,0.12)" strokeWidth="1" />
      <ellipse cx="180" cy="100" rx="100" ry="48" fill="none" stroke="rgba(0,229,255,0.08)" strokeWidth="1" />
      <path d="M80,110 C140,60 220,60 280,100" fill="none" stroke="rgba(255,77,77,0.35)" strokeWidth="1.2" />
      <path d="M100,140 C180,90 240,130 300,120" fill="none" stroke="rgba(0,229,255,0.3)" strokeWidth="1.2" />
      <path d="M70,90 C150,150 230,40 310,95" fill="none" stroke="rgba(255,184,77,0.3)" strokeWidth="1.2" />
      {nodes.map((n, i) => (
        <circle
          key={i}
          cx={n.x}
          cy={n.y}
          r={5}
          fill={n.r === "high" ? "#ff4d4d" : n.r === "medium" ? "#ffb84d" : "#00e5ff"}
          opacity="0.9"
        />
      ))}
    </svg>
  );
}

export default function Dashboard() {
  const { ops } = useOutletContext();
  const [cases, setCases] = useState([]);
  const [iocTab, setIocTab] = useState("all");

  useEffect(() => {
    api.cases().then((d) => setCases(d.cases || [])).catch(() => setCases([]));
  }, []);

  const stats = useMemo(() => {
    const high = cases.filter((c) => c.risk_band === "high").length;
    const entities = cases.reduce((n, c) => n + (c.entities?.length || 0), 0);
    const packets = cases.filter((c) => c.status === "packet_ready").length;
    const relationships = ops?.stats?.relationships ?? 0;
    return { high, signals: cases.length, iocs: entities + relationships, packets };
  }, [cases, ops]);

  const series = useMemo(() => {
    const cats = ["fraud", "credentials", "docs", "other"];
    return cats.map((key) => ({
      key,
      values: DAYS.map((_, i) => {
        const base = cases.filter((c) => c.category === key).length;
        return Math.max(0, Math.round(base * (0.4 + i * 0.1) + (key === "fraud" ? i : 0)));
      }),
    }));
  }, [cases]);

  const feed = useMemo(() => {
    return cases.slice(0, 8).map((c, i) => ({
      id: c.id,
      title:
        i % 3 === 0
          ? `New signal · ${c.source_label}`
          : i % 3 === 1
            ? `IOC correlated · ${c.entities?.[0]?.type || "entity"}`
            : `Risk update · ${c.risk_band}`,
      detail: c.snippet,
      when: relativeTime(c.created_at),
      band: c.risk_band,
    }));
  }, [cases]);

  const indicators = useMemo(() => {
    const rows = [];
    for (const c of cases) {
      for (const e of c.entities || []) {
        rows.push({
          type: e.type,
          value: e.value,
          source: c.source_label,
          first: e.first_seen || c.created_at,
          confidence: Math.round((e.confidence || 0.9) * 100),
          caseId: c.id,
        });
      }
    }
    rows.sort((a, b) => b.confidence - a.confidence);
    return rows;
  }, [cases]);

  const filteredIocs = indicators.filter((r) => iocTab === "all" || r.type === iocTab).slice(0, 8);
  const recent = cases.slice(0, 5);
  const latestPacket = cases.find((c) => c.status === "packet_ready") || cases[0];
  const checks = ops?.health?.checks || {};
  const ok = ops?.health?.status === "ok";

  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">
            {greet}, Tanish
          </h1>
          <p className="mt-1 text-sm text-muted">Cyber intelligence overview · Signal → Investigate → Packet</p>
        </div>
        <Link
          to="/cases"
          className="inline-flex items-center gap-1 rounded-lg border border-cyan/30 bg-cyan/10 px-3 py-2 text-sm text-cyan hover:bg-cyan/15"
        >
          Open triage <ArrowUpRight size={14} />
        </Link>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "High priority cases", value: stats.high, delta: "+2", tone: "text-red", icon: AlertTriangle },
          { label: "New signals", value: stats.signals, delta: "+18%", tone: "text-cyan", icon: Radar },
          { label: "IOC matches", value: stats.iocs, delta: "links", tone: "text-amber", icon: Link2 },
          { label: "Case packets generated", value: stats.packets, delta: "+33%", tone: "text-emerald-400", icon: FileJson2 },
        ].map(({ label, value, delta, tone, icon: Icon }) => (
          <Panel key={label} className="!p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-[11px] uppercase tracking-wider text-muted">{label}</div>
                <div className="mt-2 font-mono text-3xl font-bold">{value}</div>
                <div className={`mt-1 text-xs ${tone}`}>{delta}</div>
              </div>
              <Icon className={tone} size={18} />
            </div>
          </Panel>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title="Threat activity overview" className="hex-bg xl:col-span-1">
          <ThreatChart series={series} />
          <div className="mt-1 flex flex-wrap gap-3 text-[10px] uppercase tracking-wider text-muted">
            <span className="text-red">● Fraud</span>
            <span className="text-cyan">● Credentials</span>
            <span className="text-amber">● Docs</span>
            <span>● Other</span>
          </div>
        </Panel>
        <Panel title="Global intelligence">
          <ThreatMap high="high" medium="medium" low="low" />
          <div className="flex gap-3 text-[10px] uppercase tracking-wider text-muted">
            <span className="text-red">● High</span>
            <span className="text-amber">● Medium</span>
            <span className="text-cyan">● Low</span>
          </div>
        </Panel>
        <Panel title="Live intel feed">
          <ul className="max-h-48 space-y-2 overflow-y-auto pr-1">
            {feed.map((f) => (
              <li key={f.id + f.title}>
                <Link
                  to={`/cases/${f.id}`}
                  className="block rounded-lg border border-line/80 px-3 py-2 hover:border-cyan/30 hover:bg-cyan/5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-white/90">{f.title}</span>
                    <span className="font-mono text-[10px] text-muted">{f.when}</span>
                  </div>
                  <div className="mt-0.5 truncate text-xs text-muted">{f.detail}</div>
                </Link>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Panel
          className="lg:col-span-3"
          title="Top indicators"
          action={
            <div className="flex flex-wrap gap-1">
              {["all", "phone", "email", "domain", "wallet", "handle"].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setIocTab(t)}
                  className={`rounded px-2 py-0.5 text-[10px] uppercase tracking-wide ${
                    iocTab === t ? "bg-cyan/15 text-cyan" : "text-muted hover:text-white"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead>
                <tr className="border-b border-line text-[10px] uppercase tracking-wider text-muted">
                  <th className="px-2 py-2">Type</th>
                  <th className="px-2 py-2">Value</th>
                  <th className="px-2 py-2">Source</th>
                  <th className="px-2 py-2">First seen</th>
                  <th className="px-2 py-2">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filteredIocs.map((r) => (
                  <tr key={`${r.caseId}-${r.type}-${r.value}`} className="border-b border-line/50 hover:bg-white/[0.02]">
                    <td className="px-2 py-2.5 font-mono text-xs uppercase text-muted">{r.type}</td>
                    <td className="px-2 py-2.5">
                      <Link to={`/cases/${r.caseId}`} className="font-mono text-xs text-cyan hover:underline">
                        {r.value.length > 36 ? `${r.value.slice(0, 34)}…` : r.value}
                      </Link>
                    </td>
                    <td className="px-2 py-2.5 text-xs text-muted">{r.source}</td>
                    <td className="px-2 py-2.5 font-mono text-[11px] text-muted">{relativeTime(r.first)}</td>
                    <td className="px-2 py-2.5">
                      <span
                        className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                          r.confidence >= 90
                            ? "border-emerald-500/40 text-emerald-400"
                            : r.confidence >= 80
                              ? "border-amber-500/40 text-amber-300"
                              : "border-line text-muted"
                        }`}
                      >
                        {r.confidence >= 90 ? "High" : r.confidence >= 80 ? "Medium" : "Low"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Recent investigations" className="lg:col-span-2">
          <ul className="space-y-2">
            {recent.map((c) => (
              <li key={c.id}>
                <Link
                  to={`/cases/${c.id}`}
                  className="flex items-center justify-between gap-2 rounded-lg border border-line px-3 py-2.5 hover:border-cyan/30"
                >
                  <div className="min-w-0">
                    <div className="font-mono text-sm text-cyan">{c.id.replace("CASE-", "C-")}</div>
                    <div className="truncate text-xs text-muted">{c.title}</div>
                  </div>
                  <RiskPill band={c.risk_band} />
                </Link>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Latest case packet">
          {latestPacket ? (
            <>
              <div className="font-mono text-lg text-white">{latestPacket.id}</div>
              <p className="mt-1 text-sm text-muted">{latestPacket.title}</p>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
                <span>IOC {(latestPacket.entities || []).length}</span>
                <span>Links {(latestPacket.linked_cases || []).length}</span>
                <span>{latestPacket.status}</span>
              </div>
              <Link
                to={`/cases/${latestPacket.id}`}
                className="mt-4 inline-flex glow-cyan rounded-lg bg-cyan px-4 py-2 text-sm font-semibold text-ink hover:brightness-110"
              >
                View packet →
              </Link>
            </>
          ) : (
            <p className="text-sm text-muted">No cases seeded.</p>
          )}
        </Panel>

        <Panel title="Investigation pipeline">
          <div className="flex flex-wrap items-center justify-between gap-2 py-2">
            {[
              { label: "Ingest", icon: Database },
              { label: "Enrich", icon: Link2 },
              { label: "Analyze", icon: Search },
              { label: "Package", icon: Package },
            ].map(({ label, icon: Icon }, i, arr) => (
              <div key={label} className="flex items-center gap-2">
                <div className="flex flex-col items-center gap-1">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-cyan/30 bg-cyan/10 text-cyan">
                    <Icon size={16} />
                  </div>
                  <span className="text-[10px] uppercase tracking-wider text-muted">{label}</span>
                </div>
                {i < arr.length - 1 && <div className="mb-4 hidden h-px w-6 bg-cyan/40 sm:block" />}
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-muted">STIX-lite JSON · SHA-256 · Step Functions ARN</p>
          <Link to="/aws" className="mt-2 inline-block text-sm text-cyan hover:underline">
            Open AWS pipeline →
          </Link>
        </Panel>

        <Panel title="System status">
          <ul className="space-y-2 text-sm">
            {[
              ["API Gateway", ok ? "Healthy" : "Down"],
              ["DynamoDB / store", checks.store === "ok" ? "Healthy" : checks.store || "…"],
              ["S3 storage", checks.s3 === "ok" ? "Healthy" : checks.s3 || "…"],
              ["Step Functions", ops?.last_status || "Ready"],
              ["Bedrock AI", checks.bedrock === "enabled" ? "Enabled" : "Optional · off"],
            ].map(([name, status]) => (
              <li key={name} className="flex items-center justify-between border-b border-line/60 py-1.5">
                <span className="text-muted">{name}</span>
                <span className="font-mono text-xs text-emerald-400">{status}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
