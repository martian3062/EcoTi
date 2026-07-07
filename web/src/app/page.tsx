"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { connectFeed } from "@/lib/ws";
import { api } from "@/lib/api";
import AgentRail from "./components/AgentRail";
import EventFeed from "./components/EventFeed";
import SelfHealToast, { Toast } from "./components/SelfHealToast";
import CitizenShieldTool from "./components/CitizenShieldTool";
import NumberCheckTool from "./components/NumberCheckTool";

// Leaflet touches `window` on import → load the map client-side only.
const MapPanel = dynamic(() => import("./components/MapPanel"), {
  ssr: false,
  loading: () => <div className="glass-card h-[420px] p-4 text-sm text-ink3">loading map…</div>,
});

type FeedItem = { kind: string; data: Record<string, unknown>; at: number };

export default function Dashboard() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [tick, setTick] = useState(0);
  const [tool, setTool] = useState<"shield" | "number">("shield");
  const toastId = useRef(0);

  useEffect(() => {
    const off = connectFeed((m) => {
      if (m.kind === "hello") return;
      setItems((prev) => [{ kind: m.kind, data: m.data, at: Date.now() }, ...prev].slice(0, 60));
      if (m.kind === "toast") {
        setToasts((prev) => [...prev, { id: toastId.current++, message: String(m.data.message), level: String(m.data.level || "info") }]);
        setTick((t) => t + 1);
      }
      if (m.kind === "fused") setTick((t) => t + 1);
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
    const id = "+919812345678";
    await api.p1Core({ identifier: id, lang: "hi" });
    setTick((t) => t + 1);
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
          <button onClick={runP1Core} className="btn-ghost">
            Run P1 Shield demo
          </button>
          <button onClick={runDemo} className="btn-primary">
            ▶ Run fusion demo
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <MapPanel />
        </div>
        <div className="space-y-4">
          <AgentRail tick={tick} />
        </div>
        <div className="lg:col-span-1">
          <EventFeed items={items} />
        </div>
      </div>

      {/* Citizen tools — Shield + Number Check merged into the Command Centre */}
      <div className="glass-card p-4">
        <div className="mb-3 flex items-center gap-2">
          <h2 className="mr-2 text-sm font-semibold text-ink2">Citizen tools</h2>
          <button
            onClick={() => setTool("shield")}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${tool === "shield" ? "bg-crimson text-white" : "bg-white/60 text-ink2 hover:text-crimson"}`}
          >
            Citizen Shield
          </button>
          <button
            onClick={() => setTool("number")}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${tool === "number" ? "bg-crimson text-white" : "bg-white/60 text-ink2 hover:text-crimson"}`}
          >
            Number Check
          </button>
        </div>
        {tool === "shield" ? <CitizenShieldTool /> : <NumberCheckTool />}
      </div>

      <SelfHealToast toasts={toasts} />
    </div>
  );
}
