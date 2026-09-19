import { useEffect, useState } from "react";

/**
 * Layered parallax scene using the CasePacket cyber media pack.
 * scroll: 0–1 page progress (ref or number)
 */
export default function HeroScene({ scroll }) {
  const [p, setP] = useState(0);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const next = typeof scroll?.current === "number" ? scroll.current : 0;
      setP((prev) => (Math.abs(prev - next) > 0.001 ? next : prev));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [scroll]);

  return (
    <div className="hero-scene absolute inset-0 overflow-hidden">
      {/* Hex grid floor */}
      <div
        className="absolute inset-[-8%] bg-cover bg-center opacity-70"
        style={{
          backgroundImage: "url(/media/hex-grid.jpg)",
          transform: `translate3d(0, ${p * -120}px, 0) scale(${1.08 + p * 0.12})`,
          filter: "saturate(1.15) brightness(0.85)",
        }}
      />

      {/* Data tunnel — scrolls “into” the void */}
      <div
        className="absolute left-1/2 top-1/2 h-[140vmax] w-[140vmax] -translate-x-1/2 -translate-y-1/2"
        style={{
          backgroundImage: "url(/media/data-tunnel.png)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          opacity: 0.55 + p * 0.25,
          transform: `translate3d(-50%, -50%, 0) scale(${1.05 + p * 0.55}) rotate(${p * 18}deg)`,
          mixBlendMode: "screen",
        }}
      />

      {/* Ops isometric — floats on the right */}
      <div
        className="absolute right-[-4%] top-[8%] hidden h-[78%] w-[58%] md:block"
        style={{
          transform: `translate3d(${p * -40}px, ${p * 60}px, 0) scale(${1.02 - p * 0.05})`,
        }}
      >
        <img
          src="/media/ops-isometric.png"
          alt=""
          className="hero-float h-full w-full object-contain object-right drop-shadow-[0_0_40px_rgba(34,211,238,0.35)]"
          draggable={false}
        />
      </div>

      {/* Mobile hero image */}
      <div
        className="absolute inset-x-0 bottom-0 h-[45%] md:hidden"
        style={{ transform: `translateY(${p * 40}px)`, opacity: 1 - p * 1.4 }}
      >
        <img src="/media/ops-isometric.png" alt="" className="h-full w-full object-contain object-bottom" />
      </div>

      {/* Scanline + vignette */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_20%,#050816_78%)]" />
      <div className="hero-scanlines pointer-events-none absolute inset-0 opacity-[0.07]" />
      <div className="hero-particles pointer-events-none absolute inset-0" />
    </div>
  );
}
