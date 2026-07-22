"use client";
import { useState } from "react";
import { api } from "@/lib/api";

type Signals = Record<string, number>;
type GraphStats = { cluster_size?: number; districts?: string[]; route?: string };
type Validation = { line_type?: string; carrier?: string; region?: string; valid?: boolean };
type Result = {
  number: string;
  verdict: string;
  risk_score: number;
  reasons: string[];
  recommended_actions: string[];
  advisory: string;
  signals: Signals;
  graph: GraphStats;
  validation?: Validation;
};

const LANGS = ["en", "hi", "ta", "kn", "te", "ml", "mr", "gu", "bn", "pa"];
const SAMPLES = ["+91 98123 45678", "+1 202 555 0100", "+91 91234 56780"];
const STYLE: Record<string, string> = {
  scam: "border-danger/40 bg-danger/8 text-danger",
  suspicious: "border-warn/40 bg-warn/8 text-warn",
  safe: "border-ok/40 bg-ok/8 text-ok",
};
const LABEL: Record<string, string> = {
  scam: "⛔ Likely SCAM", suspicious: "⚠ Suspicious", safe: "✓ No strong fraud signal",
};
const SIGNAL_KEYS = ["graph", "reputation", "community", "history", "heuristic"];

export default function NumberCheckTool() {
  const [number, setNumber] = useState(SAMPLES[0]);
  const [lang, setLang] = useState("en");
  const [res, setRes] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);

  const check = async () => {
    setLoading(true);
    try { setRes((await api.numberCheck({ number, lang })) as Result); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {SAMPLES.map((s) => (
          <button key={s} onClick={() => setNumber(s)} className="rounded-full border border-white/10 bg-white/10 px-3 py-1 font-mono text-xs text-ink2 transition hover:border-crimson hover:text-crimson">{s}</button>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <input value={number} onChange={(e) => setNumber(e.target.value)} placeholder="+91 XXXXX XXXXX" className="glass-input flex-1 px-3 py-2 font-mono" onKeyDown={(e) => e.key === "Enter" && check()} />
        <select value={lang} onChange={(e) => setLang(e.target.value)} className="glass-input px-3 py-2">
          {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <button onClick={check} disabled={loading} className="btn-primary">{loading ? "Checking…" : "Check number"}</button>
      </div>

      {res && (
        <div className={`rounded-2xl border-2 p-4 ${STYLE[res.verdict] ?? "border-white/10"}`}>
          <div className="flex items-center justify-between gap-3">
            <span className="text-lg font-extrabold">{LABEL[res.verdict] ?? res.verdict}</span>
            <span className="badge bg-white/10 font-mono text-ink2">{res.number}</span>
          </div>
          <div className="mt-2">
            <div className="mb-1 flex justify-between text-xs text-ink3"><span>Risk</span><span>{Math.round(res.risk_score * 100)}%</span></div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-black/10">
              <div className="h-full rounded-full" style={{ width: `${Math.round(res.risk_score * 100)}%`, background: res.verdict === "scam" ? "#dc2626" : res.verdict === "suspicious" ? "#d97706" : "#059669" }} />
            </div>
          </div>
          <p className="mt-2 text-sm text-ink">{res.advisory}</p>
          {res.validation?.carrier && (
            <div className="mt-1 text-xs text-ink3">Carrier: {res.validation.carrier} · {res.validation.line_type} · {res.validation.region}</div>
          )}
          <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-ink2">
            {res.reasons.slice(0, 4).map((r, i) => <li key={i}>{r}</li>)}
          </ul>
          <div className="mt-2 grid grid-cols-5 gap-1 text-center text-[10px]">
            {SIGNAL_KEYS.map((k) => (
              <div key={k} className="rounded bg-white/10 p-1">
                <div className="text-ink3">{k.slice(0, 4)}</div>
                <div className="font-mono text-ink">{res.signals?.[k] ?? 0}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
