import { Panel } from "../components/ui.jsx";

const TTPS = [
  { id: "T1566", name: "Phishing / social engineering", note: "OTP bots, fake cyber cell" },
  { id: "T1589", name: "Gather victim identity info", note: "KYC / PAN / Aadhaar themes" },
  { id: "T1657", name: "Financial theft", note: "UPI mule, wallet cashout" },
  { id: "T1586", name: "Compromise accounts", note: "Credential dumps / fullz chatter" },
];

export default function Ttps() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-3xl font-bold text-white">TTPs</h1>
        <p className="mt-1 text-sm text-muted">ATT&CK-flavoured labels mapped from fixture categories — educational only.</p>
      </header>
      <div className="grid gap-3 md:grid-cols-2">
        {TTPS.map((t) => (
          <Panel key={t.id}>
            <div className="font-mono text-xs text-cyan">{t.id}</div>
            <div className="mt-1 text-lg font-semibold">{t.name}</div>
            <p className="mt-1 text-sm text-muted">{t.note}</p>
          </Panel>
        ))}
      </div>
    </div>
  );
}
