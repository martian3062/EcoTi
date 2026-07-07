"use client";

type FeedItem = {
  kind: string;
  data: Record<string, unknown>;
  at: number;
};

const KIND_STYLE: Record<string, string> = {
  event: "border-l-crimson",
  fused: "border-l-danger",
  toast: "border-l-warn",
  hello: "border-l-ink3",
};

export default function EventFeed({
  items,
  title = "Live fused-event feed",
  maxH = "max-h-[420px]",
}: {
  items: FeedItem[];
  title?: string;
  maxH?: string;
}) {
  return (
    <div className="glass-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-ink2">{title}</h2>
      <div className={`${maxH} space-y-2 overflow-y-auto`}>
        {items.map((it, i) => (
          <div key={i} className={`border-l-2 ${KIND_STYLE[it.kind] ?? "border-l-ink3"} rounded-r bg-white/50 px-3 py-2 text-xs`}>
            <div className="mb-1 flex justify-between">
              <span className="font-semibold uppercase tracking-wide text-ink2">{it.kind}</span>
              <span className="text-ink3">{new Date(it.at).toLocaleTimeString()}</span>
            </div>
            <Summary kind={it.kind} data={it.data} />
          </div>
        ))}
        {items.length === 0 && <div className="text-xs text-ink3">waiting for events…</div>}
      </div>
    </div>
  );
}

function Summary({ kind, data }: { kind: string; data: Record<string, unknown> }) {
  if (kind === "event") {
    const p = (data.payload as Record<string, unknown>) || {};
    const pattern = (p.matched_script as Record<string, unknown> | undefined)?.label;
    return (
      <div className="text-ink">
        <span className="font-mono text-crimson">{String(data.module)}</span>
        <span className="text-ink2"> / {String(data.signal)} </span>
        {data.identifier ? <span className="text-ink3">[{String(data.identifier)}]</span> : null}
        <span className="ml-1 text-ink2">conf {Number(data.confidence).toFixed(2)}</span>
        {p.verdict ? <span className="ml-2 rounded bg-crimson/10 px-1.5 text-crimson">{String(p.verdict)}</span> : null}
        {pattern ? <span className="ml-2 text-ink3">{String(pattern)}</span> : null}
        <span className="ml-1 text-[10px] text-ink3">({String(data.route)})</span>
      </div>
    );
  }
  if (kind === "fused") {
    return (
      <div className="font-medium text-danger">
        ⚠ FUSED TrustRisk on {String(data.identifier)} — score {Number(data.score).toFixed(2)} —
        modules: {(data.modules as string[])?.join(", ")}
      </div>
    );
  }
  if (kind === "toast") {
    return <div className="text-warn">{String(data.message)}</div>;
  }
  return <div className="text-ink3">{JSON.stringify(data)}</div>;
}
