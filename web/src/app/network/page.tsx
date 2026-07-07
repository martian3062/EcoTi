"use client";
import dynamic from "next/dynamic";

// reagraph is WebGL — load client-side only.
const FraudGraph = dynamic(() => import("../components/FraudGraph"), {
  ssr: false,
  loading: () => <div className="glass-card h-[440px] p-4 text-sm text-ink3">loading graph engine…</div>,
});

export default function NetworkPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">
          Fraud <span className="text-gradient">Network Graph</span>
        </h1>
        <p className="text-sm text-ink2">
          WebGL map of the mule-account cluster linked to a number/UPI, from the self-healing
          fraud-graph agent. The central node is the queried number; surrounding accounts are
          coloured by district and connected by fund-transfer edges.
        </p>
      </div>
      <div className="glass-card p-4">
        <FraudGraph />
      </div>
    </div>
  );
}
