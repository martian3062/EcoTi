"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Item = { title: string; source: string; link: string; ts: string };

export default function NewsTicker() {
  const [items, setItems] = useState<Item[]>([]);

  useEffect(() => {
    const load = () => api.news().then((r: { items: Item[] }) => setItems(r.items || [])).catch(() => {});
    load();
    const t = setInterval(load, 5 * 60 * 1000); // refresh every 5 min
    return () => clearInterval(t);
  }, []);

  if (!items.length) return null;
  // duplicate for a seamless marquee loop
  const loop = [...items, ...items];

  return (
    <div className="news-ticker">
      <div className="news-live">
        <span className="news-dot" /> LIVE · FRAUD WATCH
      </div>
      <div className="news-track-wrap">
        <div className="news-track">
          {loop.map((it, i) => (
            <a key={i} href={it.link} target="_blank" rel="noopener noreferrer" className="news-item">
              <span className="news-src">{it.source || "News"}</span>
              <span className="news-title">{it.title}</span>
              <span className="news-sep">◆</span>
            </a>
          ))}
        </div>
      </div>
      <div className="news-tag">EcoTi · AI TV</div>
    </div>
  );
}
