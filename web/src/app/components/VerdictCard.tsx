"use client";

type ReportDraft = { portal: string; category: string; steps: string[] } | null;
type Runtime = { provider?: string; offline_ready?: boolean; ollama_model?: string };
type MatchedScript = { label?: string; score?: number; severity?: string } | null;

export type ShieldResult = {
  verdict: string;
  advisory: string;
  lang: string;
  report_draft: ReportDraft;
  matched_script?: MatchedScript;
  edge_runtime?: Runtime;
  route?: string;
};

const STYLE: Record<string, string> = {
  scam: "border-danger/40 bg-danger/8 text-danger",
  suspicious: "border-warn/40 bg-warn/8 text-warn",
  safe: "border-ok/40 bg-ok/8 text-ok",
};

export default function VerdictCard({ result }: { result: ShieldResult }) {
  return (
    <div className={`glass-card border-2 p-5 ${STYLE[result.verdict] ?? "border-black/10"}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-2xl font-extrabold uppercase tracking-tight">{result.verdict}</span>
        <span className="badge shrink-0 bg-white/70 text-ink2">
          {result.route === "fallback" ? "edge fallback" : "on-device"} · {result.lang}
        </span>
      </div>
      <p className="mt-3 text-base text-ink">{result.advisory}</p>
      <div className="mt-3 grid gap-2 text-xs text-ink2 sm:grid-cols-2">
        <div className="rounded-lg bg-white/60 p-2.5">
          <div className="text-ink3">Matched pattern</div>
          <div>{result.matched_script?.label || "No high-risk script"}</div>
        </div>
        <div className="rounded-lg bg-white/60 p-2.5">
          <div className="text-ink3">Runtime</div>
          <div>
            {result.edge_runtime?.provider || "stub"} /{" "}
            {result.edge_runtime?.offline_ready ? "offline-ready" : "cloud"}
          </div>
        </div>
      </div>
      {result.report_draft && (
        <div className="mt-4 rounded-xl bg-white/60 p-3 text-sm text-ink">
          <div className="mb-1 font-semibold">One-tap report · {result.report_draft.portal}</div>
          <div className="mb-2 text-xs text-ink3">{result.report_draft.category}</div>
          <ol className="list-decimal space-y-1 pl-5 text-xs text-ink2">
            {result.report_draft.steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
