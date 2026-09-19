import { Panel } from "../components/ui.jsx";

export default function ThreatActors() {
  const actors = [
    { name: "SIM-KYC Desk", motif: "Fake KYC / Aadhaar packs", cases: "CASE-001 · CASE-007" },
    { name: "Dump Broker", motif: "Credential / combo lists", cases: "CASE-002 · CASE-012" },
    { name: "Mule Cashout", motif: "UPI / wallet cashout", cases: "CASE-005 · CASE-015" },
  ];
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-3xl font-bold text-white">Threat actors</h1>
        <p className="mt-1 text-sm text-muted">
          Synthetic personas derived from clusters — not real attribution. Demo taxonomy only.
        </p>
      </header>
      <div className="grid gap-3 md:grid-cols-3">
        {actors.map((a) => (
          <Panel key={a.name}>
            <div className="text-lg font-semibold text-white">{a.name}</div>
            <p className="mt-1 text-sm text-muted">{a.motif}</p>
            <p className="mt-3 font-mono text-xs text-cyan">{a.cases}</p>
          </Panel>
        ))}
      </div>
    </div>
  );
}
