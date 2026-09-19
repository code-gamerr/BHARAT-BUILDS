import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Link2, Sparkles } from "lucide-react";
import { api } from "../api.js";
import PacketModal from "../components/PacketModal.jsx";
import { EntityIcon, Panel, RiskGauge, RiskPill } from "../components/ui.jsx";

const TABS = ["Overview", "Entities", "Graph", "Evidence", "Timeline"];
const KEY = import.meta.env.VITE_API_KEY || "casepacket-demo-key";

function highlight(text, entities) {
  if (!text) return text;
  const values = (entities || []).map((e) => e.value).filter(Boolean).sort((a, b) => b.length - a.length);
  if (!values.length) return text;
  const escaped = values.map((v) => v.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const re = new RegExp(`(${escaped.join("|")})`, "gi");
  return text.split(re).map((part, i) =>
    values.some((v) => v.toLowerCase() === part.toLowerCase()) ? (
      <mark key={i} className="rounded bg-cyan-500/20 px-0.5 text-cyan-100">
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

function MiniGraph({ caseId, linked, entities }) {
  const top = (linked || []).slice(0, 4);
  const hub = (entities || []).find((e) => ["phone", "email", "wallet", "domain"].includes(e.type)) || entities?.[0];
  return (
    <div className="relative min-h-[220px] overflow-hidden rounded-xl border border-line bg-ink/60 p-4">
      <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-xl border border-cyan-400/50 bg-cyan-500/10 px-4 py-3 text-center glow-cyan">
        <div className="font-mono text-sm font-bold text-cyan-200">{caseId}</div>
        <div className="text-[10px] text-muted">case hub</div>
      </div>
      {hub && (
        <div className="absolute left-1/2 top-6 -translate-x-1/2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-center">
          <div className="text-[10px] uppercase text-amber-200">{hub.type}</div>
          <div className="max-w-[180px] truncate font-mono text-xs text-white">{hub.value}</div>
        </div>
      )}
      <div className="mt-24 grid gap-3 sm:grid-cols-2">
        {top.map((l) => (
          <Link
            key={l.case_id}
            to={`/cases/${l.case_id}`}
            className="rounded-lg border border-line bg-panel/80 px-3 py-2 hover:border-cyan-500/40"
          >
            <div className="font-mono text-sm text-cyan-300">{l.case_id}</div>
            <div className="text-[11px] text-muted">
              shared {l.shared_type} · {l.confidence}%
            </div>
          </Link>
        ))}
        {!top.length && <p className="text-sm text-muted">No correlated cases yet.</p>}
      </div>
    </div>
  );
}

export default function CaseDetail() {
  const { id } = useParams();
  const [c, setC] = useState(null);
  const [packet, setPacket] = useState(null);
  const [tab, setTab] = useState("Overview");
  const [modal, setModal] = useState({ open: false, active: 0, done: false, error: "", arn: "", sha: "" });
  const [err, setErr] = useState("");

  async function load() {
    const detail = await api.case(id);
    setC(detail);
    if (detail.status === "packet_ready") {
      try {
        setPacket(await api.getPacket(id));
      } catch {
        setPacket(null);
      }
    }
  }

  useEffect(() => {
    setPacket(null);
    setTab("Overview");
    load().catch((e) => setErr(e.message));
  }, [id]);

  async function generate() {
    setModal({ open: true, active: 0, done: false, error: "", arn: "", sha: "" });
    for (let i = 0; i < 7; i += 1) {
      setModal((m) => ({ ...m, active: i }));
      await new Promise((r) => setTimeout(r, 280 + i * 80));
    }
    try {
      const started = await api.startPacket(id);
      const ready = await api.getPacket(id);
      setPacket(ready);
      await load();
      setModal({
        open: true,
        active: 7,
        done: true,
        error: "",
        arn: started.execution_arn || ready.execution_arn,
        sha: ready.sha256,
      });
    } catch (e) {
      setModal((m) => ({ ...m, error: e.message, done: false }));
    }
  }

  async function downloadPdf() {
    const res = await fetch(`/cases/${id}/packet/pdf`, { headers: { "x-api-key": KEY } });
    if (!res.ok) throw new Error("PDF brief failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${id}-brief.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const excerpt = useMemo(() => highlight(c?.body, c?.entities), [c]);

  if (!c) {
    return <p className="text-muted">{err || "Loading case…"}</p>;
  }

  return (
    <div className="space-y-6">
      <Link to="/cases" className="inline-flex items-center gap-2 text-sm text-muted hover:text-cyan-300">
        <ArrowLeft size={14} /> Back to triage
      </Link>

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <h1 className="font-mono text-3xl font-bold text-white">{c.id}</h1>
            <RiskPill band={c.risk_band} />
            <span className="font-mono text-lg text-white/80">{c.risk}/100</span>
            <span className="rounded border border-line px-2 py-0.5 text-xs text-muted">{c.tlp}</span>
            <span className="rounded border border-line px-2 py-0.5 text-xs text-muted">{c.source_label}</span>
          </div>
          <p className="max-w-2xl text-muted">{c.title}</p>
        </div>
        <button
          type="button"
          onClick={generate}
          className="glow-cyan inline-flex items-center gap-2 rounded-lg bg-blue-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-400"
        >
          <Sparkles size={16} /> Generate Packet
        </button>
      </header>

      <div className="flex flex-wrap gap-2 border-b border-line pb-2">
        {TABS.map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => setTab(name)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              tab === name ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/40" : "text-muted hover:text-white"
            }`}
          >
            {name}
          </button>
        ))}
      </div>

      {tab === "Overview" && (
        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-4">
            <Panel title="Signal excerpt">
              <p className="relative whitespace-pre-wrap text-[15px] leading-7 text-white/90">{excerpt}</p>
            </Panel>
            <Panel title="Linked cases · MISP correlation">
              {(c.linked_cases || []).length === 0 && <p className="text-sm text-muted">No shared high-value entity.</p>}
              <ul className="space-y-2">
                {(c.linked_cases || []).map((l) => (
                  <li key={l.case_id}>
                    <Link
                      to={`/cases/${l.case_id}`}
                      className="flex items-center gap-3 rounded-lg border border-line px-3 py-3 hover:border-cyan-500/40 hover:bg-cyan-500/5"
                    >
                      <Link2 size={16} className="text-cyan-300" />
                      <div className="min-w-0 flex-1">
                        <div className="font-mono text-cyan-300">{l.case_id}</div>
                        <div className="truncate text-xs text-muted">
                          shared {l.shared_type} · {l.shared_value}
                        </div>
                      </div>
                      <div className="font-mono text-sm text-amber-300">{l.confidence}%</div>
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>

          <div className="space-y-4">
            <Panel title="Risk score">
              <RiskGauge value={c.risk} outOfTen={c.risk_out_of_ten} />
              <ul className="mt-2 space-y-2">
                {(c.risk_factors || []).map((f) => (
                  <li key={f.label} className="flex items-center gap-3 text-sm">
                    <span className="w-44 truncate text-muted">{f.label}</span>
                    <span className="h-1.5 flex-1 overflow-hidden rounded bg-line">
                      <span className="block h-full bg-cyan-400" style={{ width: `${Math.min(100, (f.points || 0) * 2)}%` }} />
                    </span>
                    <span className="w-10 text-right font-mono text-xs text-amber-200">+{f.points || 0}</span>
                  </li>
                ))}
              </ul>
            </Panel>
            <Panel title="Key entities">
              <div className="space-y-2">
                {(c.entities || []).slice(0, 6).map((e) => (
                  <div key={`${e.type}-${e.value}`} className="flex items-center gap-3">
                    <EntityIcon type={e.type} />
                    <div className="min-w-0 flex-1">
                      <div className="text-[10px] uppercase text-muted">{e.type}</div>
                      <div className="truncate font-mono text-xs text-white">{e.value}</div>
                    </div>
                    <span className="font-mono text-[10px] text-cyan-300">{Math.round((e.confidence || 0.9) * 100)}%</span>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </div>
      )}

      {tab === "Entities" && (
        <Panel title="Observables · OpenCTI-style">
          <div className="grid gap-3 sm:grid-cols-2">
            {(c.entities || []).map((e) => (
              <div key={`${e.type}-${e.value}`} className="rounded-lg border border-line bg-ink/40 px-3 py-3">
                <div className="mb-2 flex items-center gap-3">
                  <EntityIcon type={e.type} />
                  <div className="min-w-0 flex-1">
                    <div className="text-[11px] uppercase tracking-wider text-muted">{e.type}</div>
                    <div className="truncate font-mono text-sm text-white">{e.value}</div>
                  </div>
                  <div className="font-mono text-xs text-cyan-300/80">{Math.round((e.confidence || 0.9) * 100)}%</div>
                </div>
                <div className="space-y-1 font-mono text-[10px] text-muted">
                  <div>stix {e.stix_id}</div>
                  <div>first {e.first_seen}</div>
                  <div>source {e.source}</div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {tab === "Graph" && (
        <Panel
          title="Relationship graph"
          action={
            <Link to="/graph" className="text-sm text-cyan-300 hover:underline">
              Open full graph →
            </Link>
          }
        >
          <MiniGraph caseId={c.id} linked={c.linked_cases} entities={c.entities} />
          <ul className="mt-4 space-y-2">
            {(c.relationships || []).map((r, i) => (
              <li key={i} className="rounded border border-line px-3 py-2 font-mono text-xs text-muted">
                {r.source_case} —{r.confidence}%→ {r.target_case} · {r.source_entity?.type}={r.source_entity?.value}
              </li>
            ))}
          </ul>
        </Panel>
      )}

      {tab === "Evidence" && (
        <Panel title="Evidence vault · proof chain">
          {(c.evidence || []).map((ev) => (
            <div key={ev.sha256} className="mb-4 rounded-lg border border-line bg-ink/50 p-4">
              <div className="text-[11px] uppercase tracking-wider text-cyan-300">Raw object</div>
              <div className="mt-1 break-all font-mono text-sm text-white">{ev.s3}</div>
              <div className="mt-2 break-all font-mono text-[11px] text-muted">SHA-256 {ev.sha256}</div>
              <div className="mt-1 text-xs text-muted">
                Source {ev.source} · Captured {ev.captured_at}
              </div>
            </div>
          ))}
          <div className="mb-2 text-[11px] uppercase tracking-wider text-muted">Proof chain</div>
          <ol className="space-y-2">
            {(c.proof_chain || []).map((step, i) => (
              <li key={i} className="rounded border border-line px-3 py-2 text-sm">
                <div className="font-semibold capitalize text-white">{step.event}</div>
                <div className="text-xs text-muted">
                  {step.component} · {step.timestamp}
                </div>
                {step.output_sha256 && (
                  <div className="break-all font-mono text-[10px] text-cyan-200/60">out {step.output_sha256}</div>
                )}
              </li>
            ))}
          </ol>
        </Panel>
      )}

      {tab === "Timeline" && (
        <Panel title="Investigation timeline">
          <ol className="relative space-y-4 border-l border-line pl-5">
            {(c.timeline || c.proof_chain || []).map((ev, i) => (
              <li key={`${ev.event}-${i}`} className="relative">
                <span className="absolute -left-[1.4rem] top-1 h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
                <div className="font-mono text-[11px] text-muted">{ev.timestamp || ev.at}</div>
                <div className="text-sm font-semibold capitalize text-white">{ev.event}</div>
                <div className="text-sm text-muted">{ev.detail || ev.component}</div>
              </li>
            ))}
          </ol>
        </Panel>
      )}

      {packet && (
        <Panel title="Latest CasePacket">
          <p className="mb-2 break-all font-mono text-[11px] text-muted">
            {packet.execution_arn}
            <br />
            packet sha256 {packet.sha256}
          </p>
          <pre className="max-h-72 overflow-auto rounded-lg border border-line bg-ink p-3 font-mono text-[11px] text-cyan-100/80">
            {JSON.stringify(packet.packet, null, 2)}
          </pre>
        </Panel>
      )}

      <PacketModal
        open={modal.open}
        activeIndex={modal.active}
        done={modal.done}
        error={modal.error}
        caseId={c.id}
        executionArn={modal.arn || packet?.execution_arn}
        sha256={modal.sha || packet?.sha256}
        downloadUrl={packet?.download_url}
        onDownloadPdf={packet ? downloadPdf : null}
        packet={packet?.packet}
        onClose={() => setModal((m) => ({ ...m, open: false }))}
      />
    </div>
  );
}
