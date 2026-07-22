"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Source = { n: number; authority: string; title: string; url: string; score: number };
type Answer = { answer: string; sources: Source[]; grounded: boolean };
type SourceRow = { authority: string; title: string; url: string; origin: string; chunks: number };

const SAMPLES = [
  "I got a call saying I'm under digital arrest by the CBI. Is it real?",
  "A bank SMS says my KYC expired and I must share an OTP. What do I do?",
  "My courier was 'seized by customs' and they want a video statement. Scam?",
  "How fast should I report money lost to online fraud?",
];

export default function CopilotPage() {
  const [q, setQ] = useState(SAMPLES[0]);
  const [ans, setAns] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<SourceRow[]>([]);

  useEffect(() => {
    api.ragSources().then(setSources).catch(() => {});
  }, []);

  const ask = async () => {
    setLoading(true);
    try {
      setAns((await api.ragAsk({ question: q })) as Answer);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">Advisory <span className="text-gradient">Copilot</span></h1>
        <p className="text-sm text-ink2">
          RAG over official I4C / MHA / RBI / DoT fraud advisories. Grounded answers with
          citations — powered by the cloud reasoning tier (Kimi / Groq) when a key is set,
          extractive fallback otherwise. Corpus ingested via Firecrawl + bundled seed.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {SAMPLES.map((s) => (
          <button
            key={s}
            onClick={() => setQ(s)}
            className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs text-ink2 transition hover:border-crimson hover:text-crimson"
          >
            {s.length > 42 ? s.slice(0, 42) + "…" : s}
          </button>
        ))}
      </div>

      <div className="glass-card space-y-3 p-4">
        <textarea
          value={q}
          onChange={(e) => setQ(e.target.value)}
          rows={2}
          className="glass-input w-full p-3 text-sm"
        />
        <button onClick={ask} disabled={loading} className="btn-primary">
          {loading ? "Consulting advisories…" : "Ask"}
        </button>
      </div>

      {ans && (
        <div className="glass-card border-2 border-crimson/30 p-5">
          <p className="whitespace-pre-line text-[15px] leading-relaxed text-ink">{ans.answer}</p>
          {ans.sources.length > 0 && (
            <div className="mt-3 border-t border-white/10 pt-3">
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

      <div className="glass-card p-4">
        <div className="mb-2 text-xs font-semibold text-ink3">
          Ingested corpus ({sources.reduce((a, s) => a + s.chunks, 0)} chunks)
        </div>
        <ul className="space-y-1 text-xs text-ink2">
          {sources.map((s, i) => (
            <li key={i}>
              <span className="rounded bg-rosegold/15 px-1.5 text-rosegold">{s.authority}</span> {s.title}
              <span className="ml-1 text-ink3">· {s.origin} · {s.chunks} chunks</span>
            </li>
          ))}
          {sources.length === 0 && <li className="text-ink3">no corpus ingested</li>}
        </ul>
      </div>
    </div>
  );
}
