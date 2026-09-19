import { riskTone } from "../api.js";

export function RiskPill({ band }) {
  const tone = riskTone(band || "low");
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${tone.pill}`}>
      {band || "low"}
    </span>
  );
}

export function RiskGauge({ value = 0, outOfTen = 0 }) {
  const r = 54;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value)) / 100;
  const offset = c * (1 - pct);
  const color = value >= 80 ? "#ef4444" : value >= 55 ? "#f59e0b" : "#22c55e";

  return (
    <div className="relative mx-auto h-40 w-40">
      <svg viewBox="0 0 140 140" className="-rotate-90 h-full w-full">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#1e2f4d" strokeWidth="10" />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="font-mono text-3xl font-bold text-white">{outOfTen}</div>
        <div className="text-[11px] uppercase tracking-wider text-muted">/ 10 risk</div>
      </div>
    </div>
  );
}

export function EntityIcon({ type }) {
  const map = {
    phone: "☎",
    email: "@",
    wallet: "₿",
    url: "⛓",
    handle: "⌘",
    domain: "🌐",
    onion: "🧅",
    ip: "#",
    hash: "∑",
    cve: "!",
    aadhaar: "ID",
    pan: "PAN",
  };
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded border border-cyan-500/30 bg-cyan-500/10 font-mono text-xs text-cyan-300">
      {map[type] || "•"}
    </span>
  );
}

export function Panel({ title, action, children, className = "" }) {
  return (
    <section className={`glass rounded-xl p-4 md:p-5 ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title ? (
            <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{title}</h2>
          ) : (
            <span />
          )}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
