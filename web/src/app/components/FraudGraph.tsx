"use client";
import { useEffect, useMemo, useState } from "react";
import { GraphCanvas, GraphNode, GraphEdge } from "reagraph";
import { api } from "@/lib/api";

type ClusterNode = { id: string; type?: string; district?: string; risk?: number };
type ClusterEdge = { src: string; dst: string; rel?: string };
type Cluster = { nodes: ClusterNode[]; edges: ClusterEdge[]; districts?: string[] };

function riskColor(r?: number) {
  if (r === undefined) return "#b76e79";
  return r >= 0.85 ? "#dc2626" : r >= 0.6 ? "#e11d48" : r >= 0.4 ? "#d97706" : "#059669";
}

export default function FraudGraph({ initial = "+919812345678" }: { initial?: string }) {
  const [identifier, setIdentifier] = useState(initial);
  const [cluster, setCluster] = useState<Cluster | null>(null);
  const [meta, setMeta] = useState<{ method?: string; route?: string; risk?: number }>({});
  const [loading, setLoading] = useState(false);

  const load = async (id: string) => {
    setLoading(true);
    try {
      const r = await api.fraudGraph({ identifier: id });
      const ev = (r as { event?: { payload?: { cluster?: Cluster; method?: string; risk?: number } } }).event;
      setCluster(ev?.payload?.cluster ?? null);
      setMeta({ method: ev?.payload?.method, route: (r as { route?: string }).route, risk: ev?.payload?.risk });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(initial); /* eslint-disable-next-line */ }, [initial]);

  const nodes: GraphNode[] = useMemo(
    () =>
      (cluster?.nodes ?? []).map((n) => ({
        id: n.id,
        label: `${n.id}${n.district ? " · " + n.district : ""}`,
        fill: riskColor(n.risk),
        size: n.type === "phone" ? 18 : 10,
        data: n,
      })),
    [cluster]
  );

  const edges: GraphEdge[] = useMemo(
    () =>
      (cluster?.edges ?? []).map((e, i) => ({
        id: `e${i}`,
        source: e.src,
        target: e.dst,
        label: e.rel,
      })),
    [cluster]
  );

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <input
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          className="glass-input flex-1 px-3 py-2 font-mono"
          onKeyDown={(e) => e.key === "Enter" && load(identifier)}
        />
        <button onClick={() => load(identifier)} disabled={loading} className="btn-primary">
          {loading ? "Loading…" : "Map network"}
        </button>
      </div>

      {cluster && (
        <div className="flex flex-wrap gap-4 text-xs text-ink2">
          <span><b>{cluster.nodes.length}</b> nodes</span>
          <span><b>{cluster.edges.length}</b> links</span>
          {cluster.districts?.length ? <span><b>{cluster.districts.length}</b> districts: {cluster.districts.join(", ")}</span> : null}
          {meta.method && <span className="rounded bg-crimson/10 px-1.5 text-crimson">{meta.method}{meta.route === "fallback" ? " (self-heal)" : ""}</span>}
          {meta.risk !== undefined && <span>risk {meta.risk}</span>}
        </div>
      )}

      <div className="relative h-[440px] w-full overflow-hidden rounded-xl border border-black/5 bg-white/40">
        {nodes.length > 0 ? (
          <GraphCanvas nodes={nodes} edges={edges} layoutType="forceDirected2d" labelType="all" edgeArrowPosition="end" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-ink3">
            {loading ? "loading network…" : "no linked cluster for this identifier"}
          </div>
        )}
      </div>
    </div>
  );
}
