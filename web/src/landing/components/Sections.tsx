import { Link } from "react-router-dom";
import { MODULES, PRINCIPLES } from "../data";

export function Principles() {
  return (
    <section className="cb-sec" id="02">
      <div className="cb-sec-head">
        <p className="cb-idx">/02 — CORE_PIPELINE</p>
        <h2>HOW_IT_COMPILES</h2>
      </div>
      <div className="cb-principles">
        {PRINCIPLES.map((p) => (
          <article key={p.code} className="cb-cell">
            <div className="cb-ico" aria-hidden="true">
              <svg viewBox="0 0 48 48" width="40" height="40" fill="none">
                <rect x="4" y="4" width="40" height="40" stroke="#444" />
                <path d="M12 24h24M24 12v24" stroke="#dfff00" strokeWidth="1.5" />
              </svg>
            </div>
            <h3>
              <span>{p.code}</span> {p.title}
            </h3>
            <p>{p.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function Modules() {
  return (
    <section className="cb-sec" id="03">
      <div className="cb-sec-head">
        <p className="cb-idx">/03 — SELECTED_MODULES</p>
        <h2>CONSOLE_SURFACE</h2>
      </div>
      <div className="cb-mods">
        {MODULES.map((m) => (
          <Link key={m.id} to="/login" className="cb-mod">
            <div className="cb-mod-preview" aria-hidden="true">
              <span>{m.id}</span>
            </div>
            <div className="cb-mod-foot">
              <div>
                <strong>{m.label}</strong>
                <em>{m.tag}</em>
              </div>
              <i aria-hidden="true">↗</i>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

export function Status() {
  return (
    <section className="cb-sec cb-status" id="04">
      <div className="cb-sec-head">
        <p className="cb-idx">/04 — SYSTEM_STATUS</p>
        <h2>DEMO_READINESS</h2>
      </div>
      <div className="cb-status-grid">
        <div className="cb-stat-block">
          <span>FIXTURES</span>
          <div className="cb-bar">
            {Array.from({ length: 16 }).map((_, i) => (
              <i key={i} className={i < 14 ? "on" : ""} />
            ))}
          </div>
          <strong>20 / 20 LOADED</strong>
        </div>
        <div className="cb-stat-block">
          <span>PACKET_PATH</span>
          <div className="cb-bar">
            {Array.from({ length: 16 }).map((_, i) => (
              <i key={i} className={i < 16 ? "on" : ""} />
            ))}
          </div>
          <strong>COMPILE_OK · BEDROCK_OPTIONAL</strong>
        </div>
        <div className="cb-stat-block">
          <span>AUTH_GATE</span>
          <div className="cb-bar">
            {Array.from({ length: 16 }).map((_, i) => (
              <i key={i} className={i < 8 ? "on" : ""} />
            ))}
          </div>
          <strong>DEMO_SESSION · API_KEY_ENV</strong>
        </div>
      </div>
      <form
        className="cb-sub"
        onSubmit={(e) => {
          e.preventDefault();
          window.location.href = "/login";
        }}
      >
        <input placeholder="ANALYST_CALLSIGN" aria-label="Callsign" />
        <button type="submit">ENTER_CONSOLE</button>
      </form>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="cb-foot" id="01">
      <div className="cb-foot-grid">
        <div>
          <h3>CASEPACKET_</h3>
          <p>LE triage console. Simulated dark-web style fixtures → sealed CasePacket.</p>
        </div>
        <div>
          <h3>NAV</h3>
          <a href="#top">INDEX</a>
          <a href="#02">PIPELINE</a>
          <a href="#03">MODULES</a>
          <Link to="/login">LOGIN</Link>
        </div>
        <div>
          <h3>STACK</h3>
          <span>AWS SAM · Amplify</span>
          <span>DynamoDB · S3 · SFN</span>
          <span>Vite · React</span>
        </div>
        <div className="cb-node">
          <h3>GLOBAL_NODE</h3>
          <div className="cb-node-map" aria-hidden="true">
            <span>DEL</span>
            <span>BLR</span>
            <span>HYD</span>
          </div>
          <p>ap-south-1 · MUMBAI</p>
        </div>
      </div>
      <div className="cb-hazard">
        <span>&gt; ACCESS_GRANTED_</span>
        <span>CASEPACKET // SIMULATED</span>
      </div>
    </footer>
  );
}
