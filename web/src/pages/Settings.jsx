import { Panel } from "../components/ui.jsx";

export default function Settings() {
  const apiUrl = import.meta.env.VITE_API_URL || "Vite proxy → :8080";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-muted">Demo posture — inspired by Axiom / OpenCTI ops panels.</p>
      </header>

      <Panel title="Runtime">
        <dl className="grid gap-3 text-sm md:grid-cols-2">
          <div>
            <dt className="text-muted">API</dt>
            <dd className="font-mono text-cyan-300">{apiUrl}</dd>
          </div>
          <div>
            <dt className="text-muted">Auth</dt>
            <dd className="font-mono">x-api-key · casepacket-demo-key</dd>
          </div>
          <div>
            <dt className="text-muted">Enrichment</dt>
            <dd>Rules / regex NER (Bedrock optional)</dd>
          </div>
          <div>
            <dt className="text-muted">Ethics</dt>
            <dd>All fixtures simulated · no live Tor</dd>
          </div>
        </dl>
      </Panel>

      <Panel title="Borrowed patterns (thin slice)">
        <ul className="space-y-2 text-sm text-muted">
          <li>
            <span className="text-white">OpenCTI</span> — observables, confidence, STIX-ish export, entity graph
          </li>
          <li>
            <span className="text-white">TheHive</span> — case detail tabs, observables, timeline, generate action
          </li>
          <li>
            <span className="text-white">MISP</span> — TLP, free-text ingest, scored correlation / linked cases
          </li>
          <li>
            <span className="text-white">Axiom</span> — analyst sidebar, evidence vault, graph + confidence edges
          </li>
          <li>
            <span className="text-white">Night-Watch / Darkwolf / ArgusWatch</span> — richer IOCs, risk factors, proof chain
          </li>
        </ul>
      </Panel>
    </div>
  );
}
