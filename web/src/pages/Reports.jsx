import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download } from "lucide-react";
import { api, relativeTime } from "../api.js";
import { Panel, RiskPill } from "../components/ui.jsx";

export default function Reports() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api.cases().then(async (d) => {
      const ready = (d.cases || []).filter((c) => c.status === "packet_ready");
      const enriched = await Promise.all(
        ready.map(async (c) => {
          try {
            const p = await api.getPacket(c.id);
            return { ...c, packetMeta: p };
          } catch {
            return c;
          }
        }),
      );
      setRows(enriched);
    });
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-white">Reports</h1>
        <p className="mt-1 text-sm text-muted">Compiled CasePackets with chain-of-custody hashes (STIX-lite JSON).</p>
      </header>

      <div className="grid gap-4">
        {rows.length === 0 && <Panel><p className="text-sm text-muted">No packets yet. Open a case and Generate Packet.</p></Panel>}
        {rows.map((c) => (
          <Panel key={c.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <Link to={`/cases/${c.id}`} className="font-mono text-lg text-cyan-300 hover:underline">
                  {c.id}
                </Link>
                <p className="mt-1 text-sm text-muted">{c.title}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <RiskPill band={c.risk_band} />
                  <span className="font-mono text-[11px] text-muted">{relativeTime(c.packet_generated_at)}</span>
                </div>
                {c.packetMeta?.sha256 && (
                  <p className="mt-2 break-all font-mono text-[10px] text-muted">sha256 {c.packetMeta.sha256}</p>
                )}
              </div>
              {c.packetMeta?.download_url && (
                <a
                  href={c.packetMeta.download_url}
                  className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm text-white hover:border-cyan-500/40"
                >
                  <Download size={14} /> JSON
                </a>
              )}
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}
