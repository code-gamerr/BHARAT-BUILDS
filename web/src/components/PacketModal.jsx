import { CheckCircle2, Circle, Loader2 } from "lucide-react";

const DEFAULT_STAGES = [
  { id: "normalize", label: "Normalize input" },
  { id: "extract", label: "Extract entities" },
  { id: "risk", label: "Calculate risk" },
  { id: "correlate", label: "Correlate cases" },
  { id: "evidence", label: "Build evidence chain" },
  { id: "stix", label: "Compile STIX objects" },
  { id: "s3", label: "Write packet to S3" },
];

export default function PacketModal({
  open,
  activeIndex,
  done,
  error,
  onClose,
  onDownloadPdf,
  downloadUrl,
  executionArn,
  sha256,
  caseId,
  packet,
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="glass glow-cyan w-full max-w-xl rounded-2xl p-6">
        <div className="mb-1 text-xs uppercase tracking-[0.2em] text-cyan-300">CasePacket compiler</div>
        <h3 className="mb-1 text-xl font-semibold text-white">
          {done ? "CasePacket generated" : "Generate case packet"}
        </h3>
        <p className="mb-5 font-mono text-xs text-muted">{caseId}</p>

        <ul className="space-y-2">
          {DEFAULT_STAGES.map((stage, i) => {
            const state = error
              ? i === activeIndex
                ? "error"
                : i < activeIndex
                  ? "done"
                  : "pending"
              : done
                ? "done"
                : i < activeIndex
                  ? "done"
                  : i === activeIndex
                    ? "running"
                    : "pending";
            return (
              <li key={stage.id} className="flex items-center gap-3 rounded-lg border border-line bg-ink/50 px-3 py-2">
                {state === "done" && <CheckCircle2 className="text-green" size={16} />}
                {state === "running" && <Loader2 className="animate-spin text-cyan-300" size={16} />}
                {state === "pending" && <Circle className="text-muted" size={16} />}
                {state === "error" && <Circle className="text-red" size={16} />}
                <span className={state === "pending" ? "text-muted text-sm" : "text-sm text-white"}>{stage.label}</span>
              </li>
            );
          })}
        </ul>

        <div className="mt-4 rounded-lg border border-line bg-panel-2/80 p-3 text-xs text-muted">
          <div className="mb-2 text-[11px] uppercase tracking-wider text-cyan-300/80">AWS Step Functions</div>
          <p className="mb-2">Lambda → Lambda → Lambda → S3</p>
          <p className="break-all font-mono text-[10px] text-cyan-200/70">{executionArn || "pending…"}</p>
          {sha256 && <p className="mt-2 break-all font-mono text-[10px]">SHA-256 {sha256}</p>}
        </div>

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

        <div className="mt-5 flex flex-wrap gap-2">
          {done && downloadUrl && (
            <a
              href={downloadUrl}
              target="_blank"
              rel="noreferrer"
              className="rounded-md bg-cyan-500 px-4 py-2 text-sm font-semibold text-ink hover:bg-cyan-400"
            >
              Download JSON
            </a>
          )}
          {done && onDownloadPdf && (
            <button
              type="button"
              onClick={onDownloadPdf}
              className="rounded-md border border-line px-4 py-2 text-sm text-white hover:bg-white/5"
            >
              Download PDF brief
            </button>
          )}
          {done && packet && (
            <button
              type="button"
              onClick={() => {
                const w = window.open("", "_blank");
                if (!w) return;
                w.document.write(
                  `<pre style="font-family:IBM Plex Mono,monospace;white-space:pre-wrap;padding:24px;background:#0b1220;color:#e8eef8">${JSON.stringify(packet, null, 2)}</pre>`,
                );
                w.document.close();
                w.print();
              }}
              className="rounded-md border border-line px-4 py-2 text-sm text-white hover:bg-white/5"
            >
              Print
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="ml-auto rounded-md border border-line px-4 py-2 text-sm text-muted hover:text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
