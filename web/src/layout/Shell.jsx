import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  FileJson2,
  FileStack,
  LayoutDashboard,
  Network,
  Radio,
  ScrollText,
  Search,
  Settings,
  Shield,
  Sparkles,
  Target,
  UploadCloud,
  Workflow,
  Crosshair,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api.js";

const GROUPS = [
  {
    label: null,
    items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard, end: true }],
  },
  {
    label: "Investigate",
    items: [
      { to: "/cases", label: "Cases", icon: FileStack },
      { to: "/ioc", label: "IOC Search", icon: Search },
      { to: "/graph", label: "Entity Graph", icon: Network },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { to: "/intel", label: "Intel Feed", icon: Radio },
      { to: "/actors", label: "Threat Actors", icon: Crosshair },
      { to: "/ttps", label: "TTPs", icon: Target },
    ],
  },
  {
    label: "Output",
    items: [
      { to: "/reports", label: "Case Packets", icon: FileJson2 },
      { to: "/ingest", label: "Ingest", icon: UploadCloud },
    ],
  },
  {
    label: "System",
    items: [
      { to: "/aws", label: "Pipeline", icon: Workflow },
      { to: "/audit", label: "Audit Log", icon: ScrollText },
      { to: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

function clock() {
  return new Date().toLocaleString(undefined, {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Shell() {
  const [ops, setOps] = useState(null);
  const [q, setQ] = useState("");
  const [now, setNow] = useState(clock);
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    const tick = () =>
      api
        .ops()
        .then((d) => alive && setOps(d))
        .catch(() => alive && setOps(null));
    tick();
    const id = setInterval(tick, 8000);
    const t = setInterval(() => setNow(clock()), 30000);
    return () => {
      alive = false;
      clearInterval(id);
      clearInterval(t);
    };
  }, []);

  const ok = ops?.health?.status === "ok";
  const pipelineOk = ok && (ops?.last_status === "SUCCEEDED" || !ops?.last_status || ops?.last_status === "IDLE");

  function onSearch(e) {
    e.preventDefault();
    navigate(q.trim() ? `/ioc?q=${encodeURIComponent(q.trim())}` : "/ioc");
  }

  return (
    <div className="min-h-screen grid-bg text-white">
      <header className="sticky top-0 z-50 border-b border-line bg-ink/95 backdrop-blur-md">
        <div className="flex flex-wrap items-center gap-3 px-4 py-3 lg:px-5">
          <div className="flex min-w-[180px] items-center gap-2.5">
            <div className="glow-cyan flex h-8 w-8 items-center justify-center rounded border border-cyan/50 font-mono text-[11px] font-bold text-cyan">
              ◈
            </div>
            <div>
              <div className="text-sm font-bold tracking-wide text-white">CasePacket</div>
              <div className="hidden text-[10px] text-muted sm:block">Dark-web signal → LE-ready case packet</div>
            </div>
          </div>

          <form onSubmit={onSearch} className="mx-auto flex min-w-[220px] flex-1 max-w-xl">
            <label className="flex w-full items-center gap-2 rounded-lg border border-line bg-panel px-3 py-2">
              <Search size={14} className="text-muted" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search IP, domain, hash, email, handle, keyword…"
                className="w-full bg-transparent text-sm text-white outline-none placeholder:text-muted"
              />
              <kbd className="hidden rounded border border-line px-1.5 py-0.5 font-mono text-[10px] text-muted md:inline">⌘K</kbd>
            </label>
          </form>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-emerald-400">
              <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-green" : "bg-red"}`} />
              AWS {ok ? "Connected" : "Down"}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan/30 bg-cyan/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-cyan">
              <Sparkles size={10} />
              Pipeline {pipelineOk ? "Healthy" : "Attention"}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan/40 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-cyan/90">
              Simulated Data
            </span>
            <div className="ml-1 hidden items-center gap-2 border-l border-line pl-3 lg:flex">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan/15 font-mono text-[11px] font-bold text-cyan">
                TB
              </div>
              <div className="leading-tight">
                <div className="text-xs font-semibold">Tanish Bhandari</div>
                <div className="text-[10px] text-muted">Analyst · {now}</div>
              </div>
              <span className="ml-1 inline-flex items-center gap-1 text-[10px] text-emerald-400">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green" /> Live
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1600px]">
        <aside className="sticky top-[61px] hidden h-[calc(100vh-61px)] w-[220px] shrink-0 flex-col border-r border-line bg-ink/80 px-3 py-4 md:flex">
          <nav className="flex flex-1 flex-col gap-4 overflow-y-auto">
            {GROUPS.map((group) => (
              <div key={group.label || "root"}>
                {group.label && (
                  <div className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted/80">
                    {group.label}
                  </div>
                )}
                <div className="flex flex-col gap-0.5">
                  {group.items.map(({ to, label, icon: Icon, end }) => (
                    <NavLink
                      key={to}
                      to={to}
                      end={end}
                      className={({ isActive }) =>
                        `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                          isActive ? "nav-active" : "border border-transparent text-muted hover:bg-white/5 hover:text-white"
                        }`
                      }
                    >
                      <Icon size={15} />
                      {label}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>

          <div className="mt-3 overflow-hidden rounded-xl border border-line bg-gradient-to-br from-panel to-ink p-3">
            <div className="mb-2 flex h-16 items-end justify-center rounded-lg bg-[radial-gradient(circle_at_50%_30%,rgba(0,229,255,0.18),transparent_60%)]">
              <Shield className="mb-2 text-cyan/70" size={36} />
            </div>
            <p className="text-center text-[11px] leading-relaxed text-muted">
              Not just data… it&apos;s a story.
              <span className="mt-1 block font-semibold text-cyan">CasePacket</span>
            </p>
            <div className="mt-2 flex items-center justify-center gap-1.5 text-[10px] text-muted">
              <Activity size={10} />
              {ops?.health?.mode || "local"} · v{ops?.health?.version || "1.0"}
            </div>
          </div>
        </aside>

        <main className="min-w-0 flex-1 overflow-auto p-4 md:p-6 lg:p-7">
          <Outlet context={{ ops, searchQuery: q }} />
        </main>
      </div>
    </div>
  );
}
