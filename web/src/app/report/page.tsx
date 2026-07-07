"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const CATEGORIES = [
  ["digital_arrest", "Digital arrest / fake officer"],
  ["kyc_otp", "KYC / OTP / bank fraud"],
  ["courier", "Courier / parcel seizure"],
  ["upi_refund", "UPI / refund / remote access"],
  ["investment", "Investment / job / lottery"],
  ["other", "Other"],
];

type Recent = {
  total: number;
  by_category: { category: string; n: number }[];
  recent: { number: string; category: string; description: string; amount_lost: string; created_at: string }[];
};

export default function ReportPage() {
  const [number, setNumber] = useState("");
  const [category, setCategory] = useState("digital_arrest");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [contact, setContact] = useState("");
  const [done, setDone] = useState<{ number: string; reports_for_number: number; verdict: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState<Recent | null>(null);

  const loadRecent = () => api.reportRecent().then(setRecent).catch(() => {});
  useEffect(() => { loadRecent(); }, []);

  const submit = async () => {
    if (!number.trim()) return;
    setLoading(true);
    try {
      const r = (await api.report({
        number, category, description,
        amount_lost: amount ? Number(amount) : null,
        reporter_contact: contact,
      })) as { number: string; reports_for_number: number; updated_check: { verdict: string } };
      setDone({ number: r.number, reports_for_number: r.reports_for_number, verdict: r.updated_check.verdict });
      setNumber(""); setDescription(""); setAmount("");
      loadRecent();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">Report <span className="text-gradient">Fraud</span></h1>
        <p className="text-sm text-ink2">
          Report a scam number. Every report feeds EcoTi's community watchlist and immediately
          raises the risk score for anyone who checks that number.
        </p>
      </div>

      <div className="glass-card space-y-3 p-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <input value={number} onChange={(e) => setNumber(e.target.value)} placeholder="Fraud number (+91…)" className="glass-input px-3 py-2 font-mono" />
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="glass-input px-3 py-2">
            {CATEGORIES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="What happened? (optional)" className="glass-input w-full p-3 text-sm" />
        <div className="grid gap-3 sm:grid-cols-2">
          <input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" placeholder="Amount lost ₹ (optional)" className="glass-input px-3 py-2" />
          <input value={contact} onChange={(e) => setContact(e.target.value)} placeholder="Your contact (optional)" className="glass-input px-3 py-2" />
        </div>
        <button onClick={submit} disabled={loading} className="btn-primary">
          {loading ? "Submitting…" : "Submit report"}
        </button>
      </div>

      {done && (
        <div className="glass-card border-2 border-ok/40 bg-ok/8 p-4 text-sm text-ink">
          ✓ Reported <span className="font-mono font-semibold">{done.number}</span> — now{" "}
          <b>{done.reports_for_number}</b> community report(s). It is also officially reportable on
          the <b>1930</b> helpline & Sanchar Saathi (Chakshu).
        </div>
      )}

      {recent && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="glass-card p-4">
            <div className="mb-2 text-xs font-semibold text-ink3">By category ({recent.total} total)</div>
            <ul className="space-y-1 text-sm text-ink2">
              {recent.by_category.map((c) => (
                <li key={c.category} className="flex justify-between">
                  <span>{CATEGORIES.find(([v]) => v === c.category)?.[1] || c.category}</span>
                  <span className="font-mono text-crimson">{c.n}</span>
                </li>
              ))}
              {recent.by_category.length === 0 && <li className="text-ink3">no reports yet</li>}
            </ul>
          </div>
          <div className="glass-card p-4">
            <div className="mb-2 text-xs font-semibold text-ink3">Recent reports</div>
            <ul className="max-h-52 space-y-1 overflow-y-auto text-xs text-ink2">
              {recent.recent.map((r, i) => (
                <li key={i} className="border-b border-black/5 py-1">
                  <span className="font-mono text-ink">{r.number}</span>
                  <span className="ml-1 rounded bg-crimson/10 px-1.5 text-crimson">{r.category}</span>
                  {r.amount_lost && <span className="ml-1 text-ink3">₹{r.amount_lost}</span>}
                </li>
              ))}
              {recent.recent.length === 0 && <li className="text-ink3">no reports yet</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
