"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Summary = {
  available: boolean; running_exits?: number; bad_exits?: number;
  top_exit_as?: { as_name: string; exits: number }[];
};
type Anomaly = {
  nickname: string; country: string; as_name: string; bandwidth_mbps: number;
  flags: string[]; is_exit: boolean; age_days: number; reasons: string[]; score: number;
};
type Anomalies = { available: boolean; sampled_relays?: number; mean_bandwidth_mbps?: number; anomalies: Anomaly[] };
type TorIp = {
  available: boolean; is_tor?: boolean; is_exit?: boolean; bad_exit?: boolean;
  nickname?: string; country?: string; as_name?: string; flags?: string[]; bandwidth_mbps?: number;
};

function scoreColor(s: number) {
  return s >= 0.8 ? "text-danger" : s >= 0.5 ? "text-warn" : "text-ink2";
}

export default function TorPage() {
  const [sum, setSum] = useState<Summary | null>(null);
  const [anom, setAnom] = useState<Anomalies | null>(null);
  const [ip, setIp] = useState("");
  const [ipRes, setIpRes] = useState<TorIp | null>(null);
  const [loading, setLoading] = useState(true);
  const [ipLoading, setIpLoading] = useState(false);

  useEffect(() => {
    Promise.all([api.torSummary(), api.torAnomalies()])
      .then(([s, a]) => { setSum(s); setAnom(a); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const checkIp = async () => {
    if (!ip.trim()) return;
    setIpLoading(true);
    try { setIpRes((await api.torCheckIp({ ip })) as TorIp); }
    finally { setIpLoading(false); }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="hero-tor p-6">
        <div className="relative z-10">
          <h1 className="text-2xl font-extrabold tracking-tight">
            Tor / Dark-Web <span className="text-gradient-tor">Traffic Intelligence</span>
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-violet-100/80">
            Live Tor relay & exit-node analysis via the Tor Project&apos;s Onionoo API, with
            statistical + rule-based anomaly detection (BadExit flags, bandwidth outliers, sybil /
            injection indicators). Fraud gangs route C2, mule coordination and cash-out through Tor.
          </p>
          {sum?.available && (
            <div className="mt-4 flex flex-wrap gap-6 text-sm">
              <Stat label="Running exits" value={sum.running_exits} />
              <Stat label="Bad exits" value={sum.bad_exits} danger />
              <Stat label="Anomalies found" value={anom?.anomalies.length} danger />
              <Stat label="Mean bw (sampled)" value={anom?.mean_bandwidth_mbps ? `${anom.mean_bandwidth_mbps} Mbps` : "—"} />
            </div>
          )}
        </div>
      </div>

      {/* IP -> Tor check */}
      <div className="glass-card p-4">
        <div className="mb-2 text-sm font-semibold text-ink2">Is this IP a Tor node?</div>
        <div className="flex flex-wrap gap-3">
          <input value={ip} onChange={(e) => setIp(e.target.value)} placeholder="e.g. 185.220.101.1" className="glass-input flex-1 px-3 py-2 font-mono" onKeyDown={(e) => e.key === "Enter" && checkIp()} />
          <button onClick={checkIp} disabled={ipLoading} className="btn-primary">{ipLoading ? "Checking…" : "Check IP"}</button>
        </div>
        {ipRes && (
          <div className="mt-3 rounded-xl bg-white/60 p-3 text-sm">
            {ipRes.is_tor ? (
              <div className={ipRes.bad_exit ? "text-danger" : "text-warn"}>
                ⚠ <b>Tor {ipRes.is_exit ? "EXIT" : "relay"} node</b>
                {ipRes.bad_exit && " · BadExit (malicious)"} — {ipRes.nickname}, {ipRes.country},{" "}
                {ipRes.as_name} · {ipRes.bandwidth_mbps} Mbps · flags: {ipRes.flags?.join(", ")}
              </div>
            ) : ipRes.available ? (
              <div className="text-ok">✓ Not a known Tor relay/exit node.</div>
            ) : (
              <div className="text-ink3">Tor lookup unavailable.</div>
            )}
          </div>
        )}
      </div>

      {/* anomalies table */}
      <div className="glass-card p-4">
        <div className="mb-3 text-sm font-semibold text-ink2">
          Relay anomalies {anom?.sampled_relays ? `· ${anom.sampled_relays} sampled` : ""}
        </div>
        {loading && <div className="text-xs text-ink3">loading live Tor data…</div>}
        <div className="max-h-[460px] space-y-2 overflow-y-auto">
          {anom?.anomalies.map((a, i) => (
            <div key={i} className="rounded-lg bg-white/50 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono font-semibold text-ink">
                  {a.nickname} <span className="text-ink3">· {a.country} · {a.as_name}</span>
                </span>
                <span className={`font-bold ${scoreColor(a.score)}`}>{a.score}</span>
              </div>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {a.is_exit && <span className="rounded bg-danger/10 px-1.5 text-danger">EXIT</span>}
                {a.flags.includes("BadExit") && <span className="rounded bg-danger/15 px-1.5 text-danger">BadExit</span>}
                <span className="rounded bg-ink/5 px-1.5 text-ink2">{a.bandwidth_mbps} Mbps</span>
                <span className="rounded bg-ink/5 px-1.5 text-ink2">{a.age_days}d old</span>
              </div>
              <ul className="mt-1 list-disc pl-4 text-ink2">
                {a.reasons.map((r, j) => <li key={j}>{r}</li>)}
              </ul>
            </div>
          ))}
          {anom && anom.anomalies.length === 0 && <div className="text-xs text-ink3">no anomalies in sample</div>}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, danger }: { label: string; value?: number | string; danger?: boolean }) {
  return (
    <div>
      <div className={`text-2xl font-extrabold ${danger ? "text-rose-300" : "text-white"}`}>{value ?? "—"}</div>
      <div className="text-[11px] uppercase tracking-wide text-violet-100/60">{label}</div>
    </div>
  );
}
