import { Link } from "react-router-dom";

export function Hero() {
  return (
    <section className="cb-hero" id="top">
      <div className="cb-hero-grid">
        <div className="cb-hero-copy">
          <p className="cb-idx">/01 — PROTOCOL</p>
          <h1>
            CYBER
            <br />
            BRUTALISM
            <br />
            <em>CASEPACKET</em>
          </h1>
          <p className="cb-lead">
            Dark-web signal → sealed LE case file. Entities. Risk. Chain-of-custody. Simulated
            fixtures only — no live Tor crawl. Not a chatbot.
          </p>
          <div className="cb-cta">
            <Link className="cb-btn solid" to="/login">
              REQUEST_ACCESS <i aria-hidden="true">↗</i>
            </Link>
            <a className="cb-btn outline" href="#02">
              READ_PIPELINE
            </a>
          </div>
          <ul className="cb-meta">
            <li>
              <span>REGION</span> ap-south-1
            </li>
            <li>
              <span>MODE</span> SIMULATED
            </li>
            <li>
              <span>STACK</span> AWS_SAM
            </li>
          </ul>
        </div>

        <aside className="cb-stage" aria-hidden="true">
          <div className="cb-cross tl" />
          <div className="cb-cross tr" />
          <div className="cb-cross bl" />
          <div className="cb-cross br" />
          <div className="cb-wire">
            <svg viewBox="0 0 280 320" className="cb-bust">
              <rect x="1" y="1" width="278" height="318" fill="none" stroke="#222" />
              <path
                d="M140 40c-28 0-52 22-52 58v28c0 18-8 28-18 40-12 14-18 30-18 48 0 42 36 76 88 76s88-34 88-76c0-18-6-34-18-48-10-12-18-22-18-40V98c0-36-24-58-52-58z"
                fill="none"
                stroke="#dfff00"
                strokeWidth="1.4"
                opacity="0.85"
              />
              <path d="M88 120h104M100 160h80M110 200h60" stroke="#333" strokeWidth="1" />
              <circle cx="118" cy="118" r="4" fill="#dfff00" />
              <circle cx="162" cy="118" r="4" fill="#dfff00" />
              <text x="16" y="28" fill="#555" fontSize="10" fontFamily="monospace">
                X:0.42 Y:1.08 Z:-0.3
              </text>
              <text x="16" y="300" fill="#dfff00" fontSize="11" fontFamily="monospace">
                &gt; RENDERING_PACKET…
              </text>
            </svg>
            <div className="cb-bits">
              <span />
              <span />
              <span />
              <span />
              <span />
              <span className="on" />
              <span className="on" />
              <span className="on" />
            </div>
          </div>
          <p className="cb-scan">SCAN_LINE // LE_TRIAGE_HUD</p>
        </aside>
      </div>
    </section>
  );
}
