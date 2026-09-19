/** Lightweight ambient particles for the analyst console (no WebGL). */
export default function AmbientScene() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage: "url(/media/hex-grid.jpg)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          filter: "blur(2px) brightness(0.35) saturate(0.9)",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-[#070d18]/70 via-[#070d18]/85 to-[#070d18]" />
      <div className="hero-particles absolute inset-0 opacity-60" />
    </div>
  );
}
