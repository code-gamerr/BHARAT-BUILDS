import { useOutletContext } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import { Panel } from "../components/ui.jsx";

const NODES = [
  { id: "ingest", label: "Ingest", sub: "S3 raw / EventBridge" },
  { id: "extract", label: "Extract & Enrich", sub: "NER + score + cluster" },
  { id: "packet", label: "Generate Packet", sub: "STIX-lite compile" },
  { id: "store", label: "Store & Notify", sub: "S3 packets / DynamoDB" },
];

export default function AwsPipeline() {
  const { ops } = useOutletContext();
  const status = ops?.last_status || "IDLE";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-white">AWS pipeline</h1>
        <p className="mt-1 text-sm text-muted">
          Demo evidence view — Step Functions CasePacketCompile graph (local mode simulates the same stages).
        </p>
      </header>

      <Panel title="Step Functions · CasePacketCompile">
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-400">
            {status === "SUCCEEDED" || status === "IDLE" ? "SUCCEEDED / ready" : status}
          </span>
          <span className="font-mono text-xs text-muted">{ops?.last_case_id || "no execution yet"}</span>
        </div>

        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          {NODES.map((n, i) => (
            <div key={n.id} className="flex flex-1 items-center gap-3">
              <div className="glass glow-cyan flex min-w-[140px] flex-1 flex-col rounded-xl border-cyan-500/20 px-4 py-4">
                <div className="mb-2 flex items-center gap-2 text-cyan-300">
                  <CheckCircle2 size={16} />
                  <span className="text-sm font-semibold text-white">{n.label}</span>
                </div>
                <div className="text-[11px] text-muted">{n.sub}</div>
              </div>
              {i < NODES.length - 1 && (
                <div className="hidden h-px flex-1 bg-gradient-to-r from-cyan-500/60 to-transparent md:block" />
              )}
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Last execution">
          <dl className="space-y-2 font-mono text-xs text-muted">
            <div>
              <dt className="text-[10px] uppercase tracking-wider">ARN</dt>
              <dd className="break-all text-cyan-200/80">{ops?.last_execution_arn || "—"}</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-wider">S3 key</dt>
              <dd className="break-all">{ops?.last_s3_key || "—"}</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-wider">At</dt>
              <dd>{ops?.last_at || "—"}</dd>
            </div>
          </dl>
        </Panel>
        <Panel title="Bill of materials">
          <ul className="space-y-2 text-sm text-muted">
            <li>S3 · raw/ + packets/</li>
            <li>DynamoDB · CasePacket table</li>
            <li>Lambda · API / ingest / extract / score / compile</li>
            <li>Step Functions · CasePacketCompile</li>
            <li>API Gateway HTTP API · CloudWatch logs</li>
            <li>Bedrock · optional (off by default)</li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}
