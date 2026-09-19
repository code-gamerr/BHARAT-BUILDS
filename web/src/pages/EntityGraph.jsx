import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { Panel } from "../components/ui.jsx";

export default function EntityGraph() {
  const [data, setData] = useState({ nodes: [], edges: [] });
  const [selected, setSelected] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .graph()
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  const cases = useMemo(() => data.nodes.filter((n) => n.kind === "case"), [data]);
  const entities = useMemo(() => data.nodes.filter((n) => n.kind === "entity"), [data]);

  const selectedMeta = useMemo(() => {
    if (!selected) return null;
    if (selected.kind === "entity") {
      const related = data.edges
        .filter((e) => e.from === selected.id || e.to === selected.id)
        .map((e) => (e.from === selected.id ? e.to : e.from))
        .filter((id) => id.startsWith("CASE-"));
      return { ...selected, relatedCases: [...new Set(related)] };
    }
    const related = data.edges
      .filter((e) => e.from === selected.id || e.to === selected.id)
      .map((e) => (e.from === selected.id ? e.to : e.from))
      .filter((id) => id.startsWith("ENT::"));
    return { ...selected, relatedEntities: [...new Set(related)] };
  }, [selected, data]);

  // Layout: cases in a circle, entities in inner ring
  const positioned = useMemo(() => {
    const w = 720;
    const h = 520;
    const cx = w / 2;
    const cy = h / 2;
    const pos = {};
    cases.forEach((n, i) => {
      const a = (i / Math.max(cases.length, 1)) * Math.PI * 2 - Math.PI / 2;
      pos[n.id] = { x: cx + Math.cos(a) * 210, y: cy + Math.sin(a) * 170, ...n };
    });
    entities.forEach((n, i) => {
      const a = (i / Math.max(entities.length, 1)) * Math.PI * 2;
      pos[n.id] = { x: cx + Math.cos(a) * 95, y: cy + Math.sin(a) * 75, ...n };
    });
    return { pos, w, h };
  }, [cases, entities]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-white">Entity graph</h1>
        <p className="mt-1 text-sm text-muted">
          OpenCTI / Axiom-inspired relationship view · confidence-scored shared observables
        </p>
      </header>

      {err && <p className="text-sm text-red-400">{err}</p>}

      <div className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
        <Panel>
          <svg viewBox={`0 0 ${positioned.w} ${positioned.h}`} className="h-auto w-full">
            {data.edges.map((e, i) => {
              const a = positioned.pos[e.from];
              const b = positioned.pos[e.to];
              if (!a || !b) return null;
              return (
                <g key={i}>
                  <line
                    x1={a.x}
                    y1={a.y}
                    x2={b.x}
                    y2={b.y}
                    stroke="rgba(34,211,238,0.35)"
                    strokeWidth="1.2"
                  />
                  <text
                    x={(a.x + b.x) / 2}
                    y={(a.y + b.y) / 2 - 4}
                    fill="#94a3b8"
                    fontSize="9"
                    textAnchor="middle"
                    fontFamily="IBM Plex Mono"
                  >
                    {e.confidence}%
                  </text>
                </g>
              );
            })}
            {Object.values(positioned.pos).map((n) => (
              <g
                key={n.id}
                onClick={() => setSelected(n)}
                className="cursor-pointer"
                style={{ outline: "none" }}
              >
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={n.kind === "case" ? 22 : 16}
                  fill={n.kind === "case" ? "rgba(59,130,246,0.25)" : "rgba(232,165,75,0.2)"}
                  stroke={n.kind === "case" ? "#3b82f6" : "#e8a54b"}
                  strokeWidth={selected?.id === n.id ? 2.5 : 1.2}
                />
                <text
                  x={n.x}
                  y={n.y + 3}
                  fill="#e8eef8"
                  fontSize="8"
                  textAnchor="middle"
                  fontFamily="IBM Plex Mono"
                >
                  {n.kind === "case" ? n.label : (n.type || "").slice(0, 4)}
                </text>
              </g>
            ))}
          </svg>
          <p className="mt-2 text-xs text-muted">
            {cases.length} cases · {entities.length} shared entities · {data.relationship_count || data.edges.length} edges
          </p>
        </Panel>

        <Panel title="Inspector">
          {!selectedMeta && <p className="text-sm text-muted">Click a node to inspect.</p>}
          {selectedMeta?.kind === "case" && (
            <div className="space-y-3 text-sm">
              <Link to={`/cases/${selectedMeta.id}`} className="font-mono text-lg text-cyan-300 hover:underline">
                {selectedMeta.id}
              </Link>
              <p className="text-muted">{selectedMeta.title}</p>
              <p>
                Risk <span className="font-mono text-white">{selectedMeta.risk}</span>
              </p>
              <div>
                <div className="mb-1 text-[11px] uppercase text-muted">Linked entities</div>
                <ul className="space-y-1 font-mono text-xs text-amber-200/90">
                  {(selectedMeta.relatedEntities || []).map((id) => (
                    <li key={id}>{id.replace("ENT::", "")}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          {selectedMeta?.kind === "entity" && (
            <div className="space-y-3 text-sm">
              <div className="text-[11px] uppercase tracking-wider text-amber-300">{selectedMeta.type}</div>
              <div className="break-all font-mono text-white">{selectedMeta.label}</div>
              <p>
                Edge confidence <span className="font-mono text-cyan-300">{selectedMeta.confidence}%</span>
              </p>
              <div>
                <div className="mb-1 text-[11px] uppercase text-muted">Related cases</div>
                <ul className="space-y-1">
                  {(selectedMeta.relatedCases || []).map((id) => (
                    <li key={id}>
                      <Link className="font-mono text-cyan-300 hover:underline" to={`/cases/${id}`}>
                        {id}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
