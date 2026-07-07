"use client";
import { useState } from "react";
import { api } from "@/lib/api";

type Footprint = {
  identifier: string;
  kind: string;
  verdict: string;
  risk_score: number;
  attributes: Record<string, unknown>;
  findings: string[];
  sources: string[];
  osint_summary: string;
};

const SAMPLES = ["+91 98123 45678", "9812345678@okhdfcbank", "someone@mailinator.com"];
const KIND_ICON: Record<string, string> = { phone: "📱", email: "✉️", upi: "💸", username: "👤" };
const V: Record<string, string> = {
  scam: "text-danger", suspicious: "text-warn", safe: "text-ok", unknown: "text-ink2",
};

export default function FootprintPage() {
  const [id, setId] = useState(SAMPLES[0]);
  const [fp, setFp] = useState<Footprint | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try { setFp((await api.footprint({ identifier: id })) as Footprint); }
    finally { setLoading(false); }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">Digital <span className="text-gradient">Footprint · OSINT</span></h1>
        <p className="text-sm text-ink2">
          Enter a phone, email, UPI handle or username for a broader OSINT picture — identity
          validation, live reputation, fraud-graph linkage and an investigator summary. Lookups
          stream to the Command Centre live feed.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {SAMPLES.map((s) => (
          <button key={s} onClick={() => setId(s)} className="rounded-full border border-black/10 bg-white/60 px-3 py-1 font-mono text-xs text-ink2 transition hover:border-crimson hover:text-crimson">{s}</button>
        ))}
      </div>

      <div className="glass-card p-4">
        <div className="flex flex-wrap gap-3">
          <input value={id} onChange={(e) => setId(e.target.value)} placeholder="phone / email / upi@bank / username" className="glass-input flex-1 px-3 py-2 font-mono" onKeyDown={(e) => e.key === "Enter" && run()} />
          <button onClick={run} disabled={loading} className="btn-primary">{loading ? "Tracing…" : "Trace footprint"}</button>
        </div>
      </div>

      {fp && (
        <div className="glass-card space-y-4 p-5">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{KIND_ICON[fp.kind] ?? "🔎"}</span>
              <div>
                <div className="font-mono text-sm text-ink">{fp.identifier}</div>
                <div className="text-xs uppercase text-ink3">{fp.kind}</div>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-lg font-extrabold uppercase ${V[fp.verdict] ?? "text-ink2"}`}>{fp.verdict}</div>
              <div className="text-xs text-ink3">risk {fp.risk_score}</div>
            </div>
          </div>

          <p className="rounded-xl bg-white/60 p-3 text-sm text-ink">{fp.osint_summary}</p>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <div className="mb-1 text-xs font-semibold text-ink3">Attributes</div>
              <ul className="space-y-0.5 text-xs text-ink2">
                {Object.entries(fp.attributes).filter(([, v]) => v !== null && v !== "" && v !== undefined).map(([k, v]) => (
                  <li key={k}><span className="text-ink3">{k}:</span> {String(Array.isArray(v) ? v.join(", ") : v)}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="mb-1 text-xs font-semibold text-ink3">Findings</div>
              <ul className="list-disc space-y-0.5 pl-4 text-xs text-ink2">
                {fp.findings.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5 border-t border-black/5 pt-3">
            <span className="text-xs text-ink3">Sources checked:</span>
            {fp.sources.map((s) => (
              <span key={s} className="rounded bg-rosegold/15 px-1.5 text-[11px] text-rosegold">{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
