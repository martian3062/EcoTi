const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function post(path: string, body: unknown) {
  const res = await fetch(`${API}/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

async function get(path: string) {
  const res = await fetch(`${API}/api${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  scamCall: (b: unknown) => post("/scam-call/analyze", b),
  counterfeit: (b: unknown) => post("/counterfeit/verify", b),
  fraudGraph: (b: unknown) => post("/fraud-graph/score", b),
  shield: (b: unknown) => post("/shield/assess", b),
  numberCheck: (b: unknown) => post("/number/check", b),
  footprint: (b: unknown) => post("/footprint", b),
  torSummary: () => get("/tor/summary"),
  torAnomalies: () => get("/tor/anomalies"),
  torCheckIp: (b: unknown) => post("/tor/check-ip", b),
  report: (b: unknown) => post("/report", b),
  reportRecent: () => get("/report/recent"),
  p1Core: (b: unknown) => post("/demo/p1-core", b),
  ragAsk: (b: unknown) => post("/rag/ask", b),
  ragSources: () => get("/rag/sources"),
  geo: () => get("/geo/hotspots"),
  agentsStatus: () => get("/agents/status"),
  events: () => get("/events"),
  evidence: () => get("/evidence"),
  providersHealth: () => get("/providers/health"),
};
