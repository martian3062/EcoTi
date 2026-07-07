"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import VerdictCard, { ShieldResult } from "./VerdictCard";

const LANGS = ["en", "hi", "ta", "kn", "te", "ml", "mr", "gu", "bn", "pa", "or", "as"];
const SAMPLE =
  "Sir this is CBI. Your Aadhaar is linked to money laundering. This is a digital arrest, do not disconnect. Transfer to this RBI account to clear your name.";

export default function CitizenShieldTool() {
  const [message, setMessage] = useState(SAMPLE);
  const [identifier, setIdentifier] = useState("+919812345678");
  const [lang, setLang] = useState("en");
  const [offline, setOffline] = useState(true);
  const [result, setResult] = useState<ShieldResult | null>(null);
  const [loading, setLoading] = useState(false);

  const assess = async () => {
    setLoading(true);
    try {
      setResult((await api.shield({ message, identifier, lang, edge: true, offline })) as ShieldResult);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-sm text-ink2">
        Paste a suspicious message or call transcript. Verdict runs on-device for privacy;
        offline mode proves the Shield path does not need a cloud model.
      </p>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        rows={3}
        className="glass-input w-full p-3 text-sm"
      />
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <input value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="phone / UPI" className="glass-input px-3 py-2" />
        <select value={lang} onChange={(e) => setLang(e.target.value)} className="glass-input px-3 py-2">
          {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <label className="flex items-center gap-2 text-ink2">
          <input type="checkbox" checked={offline} onChange={(e) => setOffline(e.target.checked)} />
          Offline proof
        </label>
        <button onClick={assess} disabled={loading} className="btn-primary ml-auto">
          {loading ? "Assessing..." : "Assess"}
        </button>
      </div>
      {result && <VerdictCard result={result} />}
    </div>
  );
}
