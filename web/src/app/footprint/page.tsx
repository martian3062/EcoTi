"use client";
import { useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";

const FootprintGraph = dynamic(() => import("../components/FootprintGraph"), { ssr: false });

type Breach = { name: string; date: string; pwn_count?: number; sensitive?: boolean; classes?: string[] };
type Footprint = {
  identifier: string;
  kind: string;
  verdict: string;
  risk_score: number;
  attributes: Record<string, unknown>;
  findings: string[];
  sources: string[];
  osint_summary: string;
  graph?: { nodes: { id: string; label: string; type: string; risk?: number }[]; edges: { src: string; dst: string; rel?: string }[] };
  cached?: boolean;
};

const SAMPLES = ["+91 98123 45678", "someone@mailinator.com", "torvalds", "185.220.101.1", "9812345678@okhdfcbank"];
const KIND_ICON: Record<string, string> = { phone: "📱", email: "✉️", upi: "💸", username: "👤", ip: "🌐" };
const V: Record<string, string> = { scam: "text-danger", suspicious: "text-warn", safe: "text-ok", unknown: "text-ink2" };
// attributes rendered specially, hide from the raw list
const HIDE_ATTR = new Set(["breach_timeline", "breach_names", "stealer_log_domains"]);

export default function FootprintPage() {
  const [id, setId] = useState(SAMPLES[0]);
  const [fp, setFp] = useState<Footprint | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try { setFp((await api.footprint({ identifier: id })) as Footprint); }
    finally { setLoading(false); }
  };

  const timeline = (fp?.attributes.breach_timeline as Breach[] | undefined) ?? [];
  const stealer = (fp?.attributes.stealer_log_domains as string[] | undefined) ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">Digital <span className="text-gradient">Footprint · OSINT</span></h1>
        <p className="text-sm text-ink2">
          Phone · email · UPI · IP · username → breach exposure (HIBP), account enumeration (holehe),
          DNS/reputation, Tor + fraud-graph linkage, fused into one identity graph.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {SAMPLES.map((s) => (
          <button key={s} onClick={() => setId(s)} className="rounded-full border border-white/10 bg-white/10 px-3 py-1 font-mono text-xs text-ink2 transition hover:border-crimson hover:text-crimson">{s}</button>
        ))}
      </div>

      <div className="glass-card p-4">
        <div className="flex flex-wrap gap-3">
          <input value={id} onChange={(e) => setId(e.target.value)} placeholder="phone / email / upi@bank / ip / username" className="glass-input flex-1 px-3 py-2 font-mono" onKeyDown={(e) => e.key === "Enter" && run()} />
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
                <div className="text-xs uppercase text-ink3">{fp.kind}{fp.cached ? " · cached" : ""}</div>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-lg font-extrabold uppercase ${V[fp.verdict] ?? "text-ink2"}`}>{fp.verdict}</div>
              <div className="text-xs text-ink3">risk {fp.risk_score}</div>
            </div>
          </div>

          {stealer.length > 0 && (
            <div className="rounded-xl border-2 border-danger/50 bg-danger/10 p-3 text-sm text-danger">
              ⚠ Credentials found in malware <b>stealer logs</b> for {stealer.length} site(s) — high account-takeover risk.
            </div>
          )}

          <p className="rounded-xl bg-white/10 p-3 text-sm text-ink">{fp.osint_summary}</p>

          {/* identity graph */}
          {fp.graph && fp.graph.nodes.length > 1 && <FootprintGraph graph={fp.graph} />}

          {/* breach timeline */}
          {timeline.length > 0 && (
            <div>
              <div className="mb-1 text-xs font-semibold text-ink3">Breach exposure ({timeline.length})</div>
              <div className="flex flex-wrap gap-1.5">
                {timeline.map((b, i) => (
                  <span key={i} title={(b.classes || []).join(", ")}
                    className={`rounded px-2 py-0.5 text-[11px] ${b.sensitive ? "bg-danger/15 text-danger" : "bg-warn/15 text-warn"}`}>
                    {b.name}<span className="ml-1 text-ink3">{b.date?.slice(0, 4)}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <div className="mb-1 text-xs font-semibold text-ink3">Attributes</div>
              <ul className="space-y-0.5 text-xs text-ink2">
                {Object.entries(fp.attributes).filter(([k, v]) => !HIDE_ATTR.has(k) && v !== null && v !== "" && v !== undefined).map(([k, v]) => (
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

          <div className="flex flex-wrap gap-1.5 border-t border-white/10 pt-3">
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
