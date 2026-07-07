"use client";
import { useEffect, useMemo, useState } from "react";
import { GraphCanvas, GraphNode, GraphEdge, lightTheme } from "reagraph";
import { api } from "@/lib/api";

type ClusterNode = { id: string; type?: string; district?: string; risk?: number };
type ClusterEdge = { src: string; dst: string; rel?: string };
type Cluster = { nodes: ClusterNode[]; edges: ClusterEdge[]; districts?: string[] };

// Distinct, accessible district palette (mule accounts coloured by district).
const DISTRICT_COLORS = ["#6d28d9", "#0891b2", "#d97706", "#059669", "#db2777", "#2563eb"];
const HUB_COLOR = "#dc2626"; // the queried number / hub node

function districtPalette(districts: string[]) {
  const map: Record<string, string> = {};
  districts.forEach((d, i) => (map[d] = DISTRICT_COLORS[i % DISTRICT_COLORS.length]));
  return map;
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

  const palette = useMemo(() => districtPalette(cluster?.districts ?? []), [cluster]);

  const nodes: GraphNode[] = useMemo(
    () =>
      (cluster?.nodes ?? []).map((n) => {
        const isHub = n.type === "phone";
        return {
          id: n.id,
          label: isHub ? n.id : `${n.id.replace("mule_", "M")}`,
          subLabel: n.district,
          fill: isHub ? HUB_COLOR : palette[n.district ?? ""] ?? "#b76e79",
          size: isHub ? 26 : 12,
          data: n,
        };
      }),
    [cluster, palette]
  );

  const edges: GraphEdge[] = useMemo(
    () =>
      (cluster?.edges ?? []).map((e, i) => ({
        id: `e${i}`,
        source: e.src,
        target: e.dst,
      })),
    [cluster]
  );

  const theme = {
    ...lightTheme,
    canvas: { background: "transparent" },
    node: {
      ...lightTheme.node,
      label: { ...lightTheme.node.label, color: "#1c1917", stroke: "#ffffff", activeColor: "#dc2626" },
    },
    edge: { ...lightTheme.edge, fill: "#c4b5c0", activeFill: "#dc2626" },
  };

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
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-ink2">
          <span><b className="text-ink">{cluster.nodes.length}</b> accounts</span>
          <span><b className="text-ink">{cluster.edges.length}</b> transfers</span>
          {meta.method && <span className="rounded bg-crimson/10 px-1.5 text-crimson">{meta.method}{meta.route === "fallback" ? " · self-heal" : ""}</span>}
          {meta.risk !== undefined && <span>risk <b className="text-danger">{meta.risk}</b></span>}
          {/* legend */}
          <span className="ml-auto flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1"><i className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: HUB_COLOR }} /> queried number</span>
            {(cluster.districts ?? []).map((d) => (
              <span key={d} className="flex items-center gap-1">
                <i className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: palette[d] }} /> {d}
              </span>
            ))}
          </span>
        </div>
      )}

      <div className="relative h-[460px] w-full overflow-hidden rounded-xl border border-black/5 bg-gradient-to-br from-white/70 to-peach/40">
        {nodes.length > 0 ? (
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            theme={theme}
            layoutType="radialOut2d"
            labelType="nodes"
            edgeArrowPosition="end"
            draggable
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-ink3">
            {loading ? "loading network…" : "no linked cluster for this identifier"}
          </div>
        )}
      </div>
      <p className="text-xs text-ink3">
        Central crimson node = the queried number/UPI · mule accounts coloured by district · arrows = fund transfers · drag nodes to explore. Layout via Reagraph (WebGL).
      </p>
    </div>
  );
}
