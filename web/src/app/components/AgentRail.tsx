"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type AgentStatus = {
  agent: string;
  status: string;
  detail: string;
  fallback_used: string;
  has_fallback: boolean;
};

const DOT: Record<string, string> = {
  healthy: "bg-ok",
  degraded: "bg-warn",
  crashed: "bg-danger",
  restarted: "bg-crimson",
  unknown: "bg-ink3",
};

export default function AgentRail({ tick }: { tick: number }) {
  const [rows, setRows] = useState<AgentStatus[]>([]);

  useEffect(() => {
    api.agentsStatus().then(setRows).catch(() => {});
  }, [tick]);

  return (
    <div className="glass-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-ink2">Agent Swarm · health rail</h2>
      <ul className="space-y-2">
        {rows.map((r) => (
          <li key={r.agent} className="flex items-center gap-3 text-sm">
            <span className={`h-2.5 w-2.5 rounded-full ${DOT[r.status] ?? "bg-ink3"} animate-pulse-glow`} />
            <span className="flex-1 font-mono text-ink">{r.agent}</span>
            <span className="text-xs text-ink3">{r.status}</span>
            {r.fallback_used && (
              <span className="badge bg-warn/15 text-warn">↪ {r.fallback_used}</span>
            )}
          </li>
        ))}
        {rows.length === 0 && <li className="text-xs text-ink3">connecting…</li>}
      </ul>
    </div>
  );
}
