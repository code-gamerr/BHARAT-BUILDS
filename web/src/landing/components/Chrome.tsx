import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { NAV } from "../data";

function SysTime() {
  const [t, setT] = useState(() => new Date().toISOString().slice(11, 19));
  useEffect(() => {
    const id = setInterval(() => setT(new Date().toISOString().slice(11, 19)), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="cb-sys">
      SYS_TIME <strong>{t}Z</strong>
    </span>
  );
}

export function Banner() {
  return (
    <div className="cb-banner" role="status">
      <span>SIMULATED_FIXTURE_DATA</span>
      <span>NOT_OPERATIONAL_INTEL</span>
    </div>
  );
}

export function Nav() {
  return (
    <header className="cb-nav">
      <a className="cb-logo" href="#top">
        CASEP<span>_</span>
      </a>
      <nav className="cb-links" aria-label="Primary">
        {NAV.map((n) => (
          <a key={n.href} href={n.href}>
            {n.label}
          </a>
        ))}
      </nav>
      <div className="cb-nav-right">
        <SysTime />
        <Link className="cb-btn solid" to="/login">
          START_CONSOLE <i aria-hidden="true">↗</i>
        </Link>
      </div>
    </header>
  );
}
