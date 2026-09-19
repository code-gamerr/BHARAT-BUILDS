import { useOutletContext } from "react-router-dom";
import { Panel } from "../components/ui.jsx";

export default function AuditLog() {
  const { ops } = useOutletContext();
  const rows = [
    ops?.last_at && {
      at: ops.last_at,
      event: "packet_compile",
      detail: `${ops.last_case_id} · ${ops.last_status}`,
      arn: ops.last_execution_arn,
    },
    {
      at: new Date().toISOString(),
      event: "console_session",
      detail: "Analyst console online · simulated fixtures",
    },
    {
      at: "2026-09-18T10:00:00Z",
      event: "seed",
      detail: "20 fixture listings ingested",
    },
  ].filter(Boolean);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-3xl font-bold text-white">Audit log</h1>
        <p className="mt-1 text-sm text-muted">Lightweight ops trail for demo evidence (CloudWatch analogue).</p>
      </header>
      <Panel>
        <ol className="space-y-3">
          {rows.map((r, i) => (
            <li key={i} className="rounded-lg border border-line px-3 py-3">
              <div className="font-mono text-[11px] text-muted">{r.at}</div>
              <div className="text-sm font-semibold capitalize text-white">{r.event}</div>
              <div className="text-sm text-muted">{r.detail}</div>
              {r.arn && <div className="mt-1 break-all font-mono text-[10px] text-cyan/70">{r.arn}</div>}
            </li>
          ))}
        </ol>
      </Panel>
    </div>
  );
}
