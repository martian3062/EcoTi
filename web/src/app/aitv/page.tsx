"use client";
import { useEffect, useState } from "react";
import AiAnchor from "../components/AiAnchor";
import { api } from "@/lib/api";

type Item = { title: string; source: string; link: string; ts: string };

export default function AiTvPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [script, setScript] = useState("");
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    api.news().then((r: { items: Item[] }) => setItems(r.items || [])).catch(() => {});
    api.newsAnchor().then((r: { script: string }) => setScript(r.script || "")).catch(() => {});
  }, []);

  useEffect(() => {
    if (items.length < 2) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % items.length), 6000);
    return () => clearInterval(t);
  }, [items]);

  const cur = items[idx];

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">
          <span className="text-gradient">EcoTi · AI TV</span> — Fraud Watch
        </h1>
        <p className="text-sm text-ink2">
          A GenAI news anchor reads a live bulletin summarising India&apos;s latest fraud &amp; cyber-crime
          headlines (Google News), with a safety tip. Click <b>Read bulletin</b> to hear it.
        </p>
      </div>

      {/* studio */}
      <div className="overflow-hidden rounded-2xl border border-crimson/30 bg-gradient-to-br from-[#2a0a1e] to-[#160610] p-6 text-white shadow-lg">
        <div className="mb-3 flex items-center gap-2 text-xs font-extrabold tracking-wide">
          <span className="aitv-live-dot" /> <span className="text-rose-300">LIVE</span>
          <span className="text-pink-100/60">· AI-generated bulletin · updates every 10 min</span>
        </div>
        <div className="grid items-center gap-6 md:grid-cols-[auto_1fr]">
          <div className="flex justify-center">
            <AiAnchor script={script} size={200} />
          </div>
          <div>
            {cur && (
              <a href={cur.link} target="_blank" rel="noopener noreferrer" className="aitv-headline block">
                <div className="mb-1 inline-block rounded bg-crimson px-2 py-0.5 text-[10px] font-bold uppercase">{cur.source || "News"}</div>
                <div className="text-xl font-bold leading-snug text-pink-50">{cur.title}</div>
              </a>
            )}
            <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-3 text-sm leading-relaxed text-pink-100/80">
              <div className="mb-1 text-[10px] font-bold uppercase text-rose-300">Anchor script</div>
              {script || "Preparing bulletin…"}
            </div>
          </div>
        </div>
      </div>

      {/* headlines grid */}
      <div>
        <div className="mb-2 text-sm font-semibold text-ink2">Latest fraud &amp; cyber headlines</div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((it, i) => (
            <a key={i} href={it.link} target="_blank" rel="noopener noreferrer"
              className="glass-card block p-3 transition hover:border-crimson/40">
              <div className="mb-1 text-[10px] font-bold uppercase text-crimson">{it.source || "News"}</div>
              <div className="text-sm text-ink">{it.title}</div>
            </a>
          ))}
          {!items.length && <div className="text-sm text-ink3">loading headlines…</div>}
        </div>
      </div>
    </div>
  );
}
