"use client";
import { useEffect, useRef, useState } from "react";
import { connectFeed } from "@/lib/ws";
import { api } from "@/lib/api";
import EventFeed from "../components/EventFeed";

type FeedItem = { kind: string; data: Record<string, unknown>; at: number };

export default function ArchivePage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const loaded = useRef(false);

  // 1) load persisted history
  useEffect(() => {
    api.events().then((r: { events?: Record<string, unknown>[]; fused?: Record<string, unknown>[] }) => {
      const hist: FeedItem[] = [];
      (r.events ?? []).forEach((e) =>
        hist.push({ kind: "event", data: e, at: Date.parse(String(e.ts)) || Date.now() })
      );
      (r.fused ?? []).forEach((f) =>
        hist.push({ kind: "fused", data: f, at: Date.parse(String(f.ts)) || Date.now() })
      );
      hist.sort((a, b) => b.at - a.at);
      setItems(hist.slice(0, 200));
      loaded.current = true;
    }).catch(() => {});
  }, []);

  // 2) append live events
  useEffect(() => {
    const off = connectFeed((m) => {
      if (m.kind === "hello") return;
      setItems((prev) => [{ kind: m.kind, data: m.data, at: Date.now() }, ...prev].slice(0, 300));
    });
    return off;
  }, []);

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">
          Event <span className="text-gradient">Archive</span>
        </h1>
        <p className="text-sm text-ink2">
          Full history of module signals and fused TrustRisk events (persisted), updating live.
          {items.length ? ` ${items.length} entries.` : ""}
        </p>
      </div>
      <EventFeed items={items} title="Signal & fusion history" maxH="max-h-[70vh]" />
    </div>
  );
}
