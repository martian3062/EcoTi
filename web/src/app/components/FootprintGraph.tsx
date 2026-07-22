"use client";
import { useMemo } from "react";
import { GraphCanvas, GraphNode, GraphEdge, lightTheme } from "reagraph";

type GNode = { id: string; label: string; type: string; risk?: number };
type GEdge = { src: string; dst: string; rel?: string };

const TYPE_COLOR: Record<string, string> = {
  email: "#dc2626", phone: "#dc2626", ip: "#dc2626", upi: "#dc2626", username: "#dc2626",
  breach: "#b91c1c", account: "#6d28d9", platform: "#0891b2", district: "#d97706", tor: "#7c3aed",
};

export default function FootprintGraph({ graph }: { graph: { nodes: GNode[]; edges: GEdge[] } }) {
  const nodes: GraphNode[] = useMemo(
    () =>
      (graph?.nodes ?? []).map((n) => ({
        id: n.id,
        label: n.label,
        fill: TYPE_COLOR[n.type] ?? "#b76e79",
        size: n.type === graph?.nodes?.[0]?.type && n.id === graph?.nodes?.[0]?.id ? 24 : 12,
        data: n,
      })),
    [graph]
  );
  const edges: GraphEdge[] = useMemo(
    () => (graph?.edges ?? []).map((e, i) => ({ id: `e${i}`, source: e.src, target: e.dst, label: e.rel })),
    [graph]
  );

  const theme = {
    ...lightTheme,
    canvas: { background: "transparent" },
    node: { ...lightTheme.node, label: { ...lightTheme.node.label, color: "#1c1917", stroke: "#ffffff", activeColor: "#dc2626" } },
    edge: { ...lightTheme.edge, fill: "#c4b5c0", activeFill: "#dc2626" },
  };

  if (!graph?.nodes?.length) return null;

  return (
    <div className="relative h-[380px] w-full overflow-hidden rounded-xl border border-black/5 bg-gradient-to-br from-white/70 to-peach/40">
      <GraphCanvas nodes={nodes} edges={edges} theme={theme} layoutType="radialOut2d" labelType="nodes" edgeArrowPosition="end" draggable />
    </div>
  );
}
