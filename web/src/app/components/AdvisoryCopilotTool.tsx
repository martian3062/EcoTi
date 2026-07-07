"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Source = { n: number; authority: string; title: string; url: string; score: number };
type Answer = { answer: string; sources: Source[]; grounded: boolean };
type SourceRow = { authority: string; title: string; url: string; origin: string; chunks: number };

const SAMPLES = [
  "Is a CBI 'digital arrest' call real?",
  "Bank SMS wants my OTP for KYC — safe?",
  "Courier 'seized by customs' — scam?",
  "How fast to report money lost to fraud?",
];

export default function AdvisoryCopilotTool() {
  const [q, setQ] = useState(SAMPLES[0]);
  const [ans, setAns] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<SourceRow[]>([]);

  useEffect(() => { api.ragSources().then(setSources).catch(() => {}); }, []);

  const ask = async () => {
    setLoading(true);
    try { setAns((await api.ragAsk({ question: q })) as Answer); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <p className="text-sm text-ink2">
        Cited answers over official I4C / RBI / DoT advisories (Kimi / Groq).
      </p>
      <div className="flex flex-wrap gap-2">
        {SAMPLES.map((s) => (
          <button key={s} onClick={() => setQ(s)} className="rounded-full border border-black/10 bg-white/60 px-3 py-1 text-xs text-ink2 transition hover:border-crimson hover:text-crimson">
            {s}
          </button>
        ))}
      </div>
      <textarea value={q} onChange={(e) => setQ(e.target.value)} rows={2} className="glass-input w-full p-3 text-sm" />
      <button onClick={ask} disabled={loading} className="btn-primary">{loading ? "Consulting advisories…" : "Ask"}</button>

      {ans && (
        <div className="rounded-2xl border-2 border-crimson/30 bg-white/50 p-4">
          <p className="whitespace-pre-line text-[15px] leading-relaxed text-ink">{ans.answer}</p>
          {ans.sources.length > 0 && (
            <div className="mt-3 border-t border-black/10 pt-3">
              <div className="mb-2 text-xs font-semibold text-ink3">Sources</div>
              <ul className="space-y-1 text-xs">
                {ans.sources.map((s) => (
                  <li key={s.n} className="text-ink2">
                    <span className="font-semibold text-crimson">[{s.n}]</span>{" "}
                    <span className="rounded bg-crimson/10 px-1.5 text-crimson">{s.authority}</span> {s.title}
                    <span className="ml-1 text-ink3">· sim {s.score}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="rounded-xl bg-white/50 p-3">
        <div className="mb-1 text-xs font-semibold text-ink3">Ingested corpus ({sources.reduce((a, s) => a + s.chunks, 0)} chunks)</div>
        <ul className="space-y-0.5 text-xs text-ink2">
          {sources.map((s, i) => (
            <li key={i}><span className="rounded bg-rosegold/15 px-1.5 text-rosegold">{s.authority}</span> {s.title} <span className="text-ink3">· {s.chunks} chunks</span></li>
          ))}
          {sources.length === 0 && <li className="text-ink3">no corpus ingested</li>}
        </ul>
      </div>
    </div>
  );
}
