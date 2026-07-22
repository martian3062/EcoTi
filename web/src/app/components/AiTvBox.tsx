"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import AiAnchor from "./AiAnchor";

type Item = { title: string; source: string; link: string };

export default function AiTvBox() {
  const [items, setItems] = useState<Item[]>([]);
  const [script, setScript] = useState("");
  const [idx, setIdx] = useState(0);
  const [min, setMin] = useState(false);

  useEffect(() => {
    api.news().then((r: { items: Item[] }) => setItems(r.items || [])).catch(() => {});
    api.newsAnchor().then((r: { script: string }) => setScript(r.script || "")).catch(() => {});
    const t = setInterval(() => api.news().then((r: { items: Item[] }) => setItems(r.items || [])).catch(() => {}), 5 * 60 * 1000);
    return () => clearInterval(t);
  }, []);

  // rotate the shown headline
  useEffect(() => {
    if (items.length < 2) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % items.length), 5000);
    return () => clearInterval(t);
  }, [items]);

  if (!items.length) return null;
  const cur = items[idx];

  if (min) {
    return (
      <button onClick={() => setMin(false)} className="aitv-min">
        <span className="aitv-live-dot" /> AI TV
      </button>
    );
  }

  return (
    <div className="aitv-box">
      <div className="aitv-head">
        <span className="flex items-center gap-1.5"><span className="aitv-live-dot" /> LIVE · EcoTi AI TV</span>
        <span className="flex items-center gap-1">
          <Link href="/aitv" title="Open AI TV" className="aitv-btn">⤢</Link>
          <button onClick={() => setMin(true)} title="Minimise" className="aitv-btn">—</button>
        </span>
      </div>
      <div className="aitv-body">
        <AiAnchor script={script} size={92} />
        <div className="min-w-0 flex-1">
          <a href={cur.link} target="_blank" rel="noopener noreferrer" className="aitv-headline block">
            <div className="text-[10px] font-bold uppercase text-rose-300">{cur.source || "News"}</div>
            <div className="line-clamp-3 text-[13px] leading-snug text-pink-50">{cur.title}</div>
          </a>
          <div className="mt-1.5 flex gap-1">
            {items.slice(0, 6).map((_, i) => (
              <span key={i} className={`h-1 w-4 rounded-full ${i === idx ? "bg-crimson" : "bg-white/20"}`} />
            ))}
          </div>
          <Link href="/aitv" className="mt-2 inline-block text-[11px] text-rose-300 hover:text-white">Open full AI TV →</Link>
        </div>
      </div>
    </div>
  );
}
