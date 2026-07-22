"use client";
import { useEffect, useState } from "react";
import EcotiGem from "./EcotiGem";
import AiTvBox from "./AiTvBox";

export default function Splash() {
  // Rendered by default (also in server HTML) so it covers the page immediately —
  // no flash of the dashboard before the loader appears.
  const [phase, setPhase] = useState<"loading" | "ready">("loading");
  const [hide, setHide] = useState(false);
  const [gone, setGone] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    // Already entered this session → remove the overlay right away.
    if (sessionStorage.getItem("ecoti_entered") === "1") {
      setGone(true);
      return;
    }
    const t = setTimeout(() => setPhase("ready"), 2000); // loading -> ready
    return () => clearTimeout(t);
  }, []);

  const enter = () => {
    try { sessionStorage.setItem("ecoti_entered", "1"); } catch {}
    setHide(true);
    setTimeout(() => setGone(true), 650);
  };

  if (gone) return null;

  return (
    <div className={`splash ${hide ? "splash-hide" : ""}`} aria-hidden={hide}>
      <div className="splash-glow" />
      <div className="relative z-10 flex flex-col items-center">
        <div className="gem-float">
          <EcotiGem size={140} />
        </div>
        <div className="mt-7 text-4xl font-extrabold tracking-tight">
          <span className="splash-wordmark">EcoTi</span>
        </div>
        <div className="mt-1 text-xs font-medium uppercase tracking-[0.28em] text-pink-200/70">
          Economic Trust Intelligence
        </div>
        <div className="mt-1.5 max-w-xs text-center text-[11px] text-pink-100/45">
          Self-healing fraud-intelligence swarm for India&apos;s financial frontline
        </div>

        {phase === "loading" ? (
          <div className="mt-9 flex flex-col items-center">
            <div className="splash-bar-track"><div className="splash-bar" /></div>
            <div className="mt-3 text-[11px] text-pink-100/50">Initialising fraud-intelligence swarm…</div>
          </div>
        ) : (
          <div className="splash-fade-in mt-9 flex flex-col items-center">
            <button onClick={enter} className="splash-enter">
              <EcotiGem size={22} glow={false} />
              Enter Command Centre
              <span className="splash-enter-arrow">→</span>
            </button>
            <div className="mt-6 flex items-center gap-2 text-[11px] text-pink-100/40">
              <span className="splash-mini-dot" /> Live · agents online
            </div>
          </div>
        )}
      </div>

      {phase === "ready" && <AiTvBox />}
    </div>
  );
}
