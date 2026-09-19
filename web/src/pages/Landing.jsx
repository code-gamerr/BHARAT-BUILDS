import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowRight, Binary, Network, Shield, Sparkles } from "lucide-react";
import HeroScene from "../components/HeroScene.jsx";

const BEATS = [
  {
    id: "signal",
    kicker: "01 · Ingest",
    title: "Noisy dark-web signal in.",
    body: "Synthetic fixtures land as immutable raw objects. SHA-256 is sealed before any analysis runs.",
    image: "/media/hex-grid.jpg",
    align: "left",
  },
  {
    id: "extract",
    kicker: "02 · Extract & correlate",
    title: "Entities become a living graph.",
    body: "Phones, wallets, domains, handles — MISP-style links with confidence edges across cases.",
    image: "/media/data-tunnel.png",
    align: "right",
  },
  {
    id: "packet",
    kicker: "03 · Compile",
    title: "LE-ready CasePacket out.",
    body: "Step Functions compile STIX-lite JSON, a proof chain, and an auditable AWS execution ARN.",
    image: "/media/ops-isometric.png",
    align: "left",
  },
];

function Reveal({ children, className = "" }) {
  const ref = useRef(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setOn(true);
      },
      { threshold: 0.22 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div ref={ref} className={`reveal ${on ? "reveal-on" : ""} ${className}`}>
      {children}
    </div>
  );
}

export default function Landing() {
  const scroll = useRef(0);
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      const p = Math.min(1, Math.max(0, window.scrollY / max));
      scroll.current = p;
      setProgress(p);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    const t = setTimeout(() => setReady(true), 40);
    return () => {
      window.removeEventListener("scroll", onScroll);
      clearTimeout(t);
    };
  }, []);

  return (
    <div className="landing-root relative min-h-[340vh] bg-[#050816] text-white">
      <div className="pointer-events-none fixed inset-0 z-0">
        {ready && <HeroScene scroll={scroll} />}
        <div className="absolute inset-0 bg-gradient-to-r from-[#050816] via-[#050816]/55 to-transparent md:via-[#050816]/35" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-transparent to-[#050816]/50" />
      </div>

      <div className="fixed top-0 left-0 z-50 h-[3px] bg-gradient-to-r from-cyan-400 via-amber-300 to-cyan-400 transition-[width] duration-150" style={{ width: `${progress * 100}%` }} />

      <header className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-5 py-4 backdrop-blur-md md:px-10">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center border border-cyan-400/70 font-mono text-xs font-bold text-cyan-300 shadow-[0_0_24px_rgba(34,211,238,0.4)]">
            CP
          </div>
          <span className="text-sm font-bold tracking-[0.22em]">CASEPACKET</span>
        </div>
        <nav className="hidden items-center gap-7 text-sm text-white/65 md:flex">
          <a href="#signal" className="hover:text-cyan-300">
            Pipeline
          </a>
          <a href="#extract" className="hover:text-cyan-300">
            Graph
          </a>
          <a href="#packet" className="hover:text-cyan-300">
            Packet
          </a>
          <Link
            to="/app"
            className="rounded-full border border-cyan-400/40 bg-cyan-500/10 px-4 py-1.5 text-cyan-200 transition hover:bg-cyan-500/20 hover:shadow-[0_0_20px_rgba(34,211,238,0.25)]"
          >
            Open console
          </Link>
        </nav>
      </header>

      {/* HERO — brand first, one CTA group, full-bleed image plane */}
      <section className="relative z-10 flex min-h-screen items-center px-5 pt-20 md:px-10">
        <div
          className="max-w-xl"
          style={{
            opacity: Math.max(0, 1 - progress * 2.4),
            transform: `translate3d(0, ${progress * -90}px, 0)`,
          }}
        >
          <div className="mb-5 inline-flex items-center gap-2 border border-amber-400/30 bg-amber-500/10 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-amber-100">
            <Shield size={12} /> Dark-web signal → LE packet on AWS
          </div>
          <h1 className="text-5xl font-bold leading-[0.95] tracking-tight text-white md:text-7xl lg:text-8xl">
            <span className="block text-cyan-300 drop-shadow-[0_0_30px_rgba(34,211,238,0.45)]">CasePacket</span>
          </h1>
          <p className="mt-6 max-w-md text-base leading-relaxed text-white/70 md:text-lg">
            Triage noisy fixtures into an auditable case file — entities, risk, proof chain, Step Functions. Not a chatbot.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link
              to="/app"
              className="group inline-flex items-center gap-2 rounded-full bg-cyan-400 px-7 py-3.5 text-sm font-bold text-[#041018] shadow-[0_0_40px_rgba(34,211,238,0.45)] transition hover:bg-cyan-300"
            >
              Enter analyst console
              <ArrowRight size={16} className="transition group-hover:translate-x-1" />
            </Link>
            <a
              href="#signal"
              className="inline-flex items-center gap-2 rounded-full border border-white/20 px-5 py-3 text-sm text-white/80 hover:border-cyan-400/50 hover:text-cyan-200"
            >
              Scroll the pipeline <ArrowDown size={14} className="animate-bounce" />
            </a>
          </div>
          <p className="mt-7 font-mono text-[11px] uppercase tracking-[0.22em] text-amber-200/75">
            Simulated data only · no live Tor
          </p>
        </div>
      </section>

      {/* Feature strip */}
      <section className="relative z-10 px-5 py-8 md:px-10">
        <Reveal className="grid gap-3 md:grid-cols-3">
          {[
            { icon: Binary, label: "Regex NER + STIX-lite" },
            { icon: Network, label: "Confidence-scored graph" },
            { icon: Sparkles, label: "AWS Step Functions compile" },
          ].map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-3 border border-cyan-500/20 bg-[#0b1220]/50 px-4 py-3 backdrop-blur-md"
            >
              <Icon className="text-cyan-300" size={18} />
              <span className="text-sm text-white/80">{label}</span>
            </div>
          ))}
        </Reveal>
      </section>

      {BEATS.map((sec) => (
        <section key={sec.id} id={sec.id} className="relative z-10 flex min-h-[85vh] items-center px-5 py-16 md:px-10">
          <Reveal
            className={`grid w-full max-w-6xl items-center gap-8 md:grid-cols-2 ${
              sec.align === "right" ? "md:[&>*:first-child]:order-2" : ""
            }`}
          >
            <div>
              <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.22em] text-cyan-300/85">{sec.kicker}</div>
              <h2 className="text-3xl font-semibold text-white md:text-5xl">{sec.title}</h2>
              <p className="mt-4 max-w-md text-sm leading-relaxed text-white/65 md:text-base">{sec.body}</p>
            </div>
            <div className="group relative overflow-hidden border border-cyan-500/25 bg-[#0b1220]/40 shadow-[0_0_50px_rgba(34,211,238,0.12)]">
              <img
                src={sec.image}
                alt=""
                className="h-64 w-full object-cover transition duration-700 group-hover:scale-105 md:h-80"
                style={sec.id === "extract" ? { mixBlendMode: "screen", background: "#050816" } : undefined}
              />
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#050816]/80 via-transparent to-transparent" />
            </div>
          </Reveal>
        </section>
      ))}

      <section className="relative z-10 flex min-h-[70vh] flex-col items-start justify-center px-5 pb-28 md:px-10">
        <Reveal>
          <h2 className="max-w-3xl text-4xl font-bold text-white md:text-6xl">
            Ready to triage <span className="text-cyan-300">CASE-001</span>?
          </h2>
          <p className="mt-5 max-w-lg text-white/65">
            Risk queue · entity graph · evidence vault · CasePacket compiler — all on simulated fixtures.
          </p>
          <Link
            to="/app"
            className="mt-9 inline-flex items-center gap-2 rounded-full bg-cyan-400 px-8 py-4 text-sm font-bold text-[#041018] shadow-[0_0_50px_rgba(34,211,238,0.5)] transition hover:scale-[1.02] hover:bg-cyan-300"
          >
            Launch console <ArrowRight size={16} />
          </Link>
        </Reveal>
      </section>
    </div>
  );
}
