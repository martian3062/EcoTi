"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { connectFeed } from "@/lib/ws";
import { api } from "@/lib/api";
import SelfHealToast, { Toast } from "./components/SelfHealToast";
import CitizenShieldTool from "./components/CitizenShieldTool";
import NumberCheckTool from "./components/NumberCheckTool";
import AdvisoryCopilotTool from "./components/AdvisoryCopilotTool";

// Leaflet touches `window` on import → load the map client-side only.
const MapPanel = dynamic(() => import("./components/MapPanel"), {
  ssr: false,
  loading: () => <div className="glass-card h-[420px] p-4 text-sm text-ink3">loading map…</div>,
});

export default function Dashboard() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastId = useRef(0);

  useEffect(() => {
    const off = connectFeed((m) => {
      if (m.kind === "toast") {
        setToasts((prev) => [...prev, { id: toastId.current++, message: String(m.data.message), level: String(m.data.level || "info") }]);
      }
    });
    return off;
  }, []);

  const runDemo = useCallback(async () => {
    const id = "+919812345678";
    await api.scamCall({ identifier: id, audio_ref: "demo_scam_call.wav" });
    await new Promise((r) => setTimeout(r, 600));
    await api.fraudGraph({ identifier: id });
  }, []);

  const runP1Core = useCallback(async () => {
    await api.p1Core({ identifier: "+919812345678", lang: "hi" });
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-ink">
            Fusion Orchestrator <span className="text-gradient">Command Centre</span>
          </h1>
          <p className="text-sm text-ink2">Self-healing multi-agent swarm · point-of-contact fraud defence</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={runP1Core} className="btn-ghost">Run P1 Shield demo</button>
          <button onClick={runDemo} className="btn-primary">▶ Run fusion demo</button>
        </div>
      </div>

      {/* Map (column size) with Number Check to its right */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <MapPanel />
        <div className="glass-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink">Number Check</h3>
          <NumberCheckTool />
        </div>
      </div>

      {/* Citizen tools — Shield · Advisory Copilot */}
      <h2 className="text-sm font-semibold text-ink2">Citizen tools</h2>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="glass-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink">Citizen Shield</h3>
          <CitizenShieldTool />
        </div>
        <div className="glass-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink">Advisory Copilot</h3>
          <AdvisoryCopilotTool />
        </div>
      </div>

      <SelfHealToast toasts={toasts} />
    </div>
  );
}
