"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

// A human news-anchor that reads the bulletin with a real human voice
// (Sarvam Bulbul TTS, India-accented) and is AUDIO-REACTIVE — the portrait glows
// and a live waveform moves in sync with the actual voice. Falls back to the
// browser's most natural voice if the TTS API is unavailable.
// Portrait = royalty-free stock (Pexels); swap NEXT_PUBLIC_ANCHOR_IMG to change.
const ANCHOR_IMG =
  process.env.NEXT_PUBLIC_ANCHOR_IMG ||
  "https://images.pexels.com/photos/3760263/pexels-photo-3760263.jpeg?auto=compress&cs=tinysrgb&w=500";

export default function AiAnchor({
  script,
  size = 170,
  lang = "en",
}: {
  script: string;
  size?: number;
  lang?: string;
}) {
  const [speaking, setSpeaking] = useState(false);
  const [level, setLevel] = useState(0);
  const [imgOk, setImgOk] = useState(true);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const acRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const fakeRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const cleanup = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (fakeRef.current) clearInterval(fakeRef.current);
    rafRef.current = null; fakeRef.current = null;
  };
  const stop = () => {
    cleanup();
    try { audioRef.current?.pause(); } catch {}
    try { window.speechSynthesis?.cancel(); } catch {}
    setSpeaking(false); setLevel(0);
  };
  useEffect(() => () => stop(), []); // eslint-disable-line react-hooks/exhaustive-deps

  const playB64 = (b64: string) => {
    const audio = new Audio("data:audio/wav;base64," + b64);
    audioRef.current = audio;
    audio.crossOrigin = "anonymous";
    try {
      const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ac = new AC(); acRef.current = ac;
      const srcNode = ac.createMediaElementSource(audio);
      const an = ac.createAnalyser(); an.fftSize = 64;
      srcNode.connect(an); an.connect(ac.destination);
      const data = new Uint8Array(an.frequencyBinCount);
      const tick = () => {
        an.getByteFrequencyData(data);
        setLevel(data.reduce((a, b) => a + b, 0) / data.length / 255);
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch { /* analyser optional */ }
    audio.onended = stop;
    audio.onerror = () => fallback();
    audio.play().then(() => setSpeaking(true)).catch(() => fallback());
  };

  const fallback = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const u = new SpeechSynthesisUtterance(script);
    const vs = window.speechSynthesis.getVoices();
    u.voice =
      vs.find((v) => /natural|neural|online/i.test(v.name) && /^en/i.test(v.lang)) ||
      vs.find((v) => /en[-_]IN/i.test(v.lang)) ||
      vs.find((v) => /^en/i.test(v.lang)) || null;
    u.rate = 1; u.pitch = 1.05;
    u.onstart = () => {
      setSpeaking(true);
      fakeRef.current = setInterval(() => setLevel(0.25 + Math.random() * 0.5), 120);
    };
    u.onend = stop;
    window.speechSynthesis.speak(u);
  };

  const play = async () => {
    if (!script) return;
    stop();
    setSpeaking(true);
    try {
      const r = (await api.tts({ text: script, lang })) as { audio_b64?: string };
      if (r.audio_b64) { playB64(r.audio_b64); return; }
    } catch { /* fall through */ }
    fallback();
  };

  const ring = 0.25 + level * 0.9;
  const scale = 1 + level * 0.05;
  const bars = 22;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        {/* reactive glow */}
        <div className="pointer-events-none absolute inset-0 rounded-2xl"
          style={{ boxShadow: `0 0 ${18 + level * 40}px rgba(236,72,153,${speaking ? ring : 0.25})`,
                   transition: "box-shadow 80ms linear" }} />
        {/* portrait */}
        <div className="h-full w-full overflow-hidden rounded-2xl border border-crimson/40 bg-gradient-to-br from-[#2a0a1e] to-[#160610]"
          style={{ transform: `scale(${scale})`, transition: "transform 80ms linear" }}>
          {imgOk ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={ANCHOR_IMG} alt="EcoTi AI anchor" onError={() => setImgOk(false)}
              className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-5xl">🎙️</div>
          )}
        </div>
        {/* LIVE badge */}
        <div className="absolute left-2 top-2 flex items-center gap-1 rounded bg-crimson/90 px-1.5 py-0.5 text-[9px] font-bold text-white">
          <span className="aitv-live-dot" /> LIVE
        </div>
        {/* lower-third */}
        <div className="absolute inset-x-0 bottom-0 flex items-center gap-1.5 bg-black/55 px-2 py-1 text-[10px] font-bold text-pink-100">
          <span className="rounded bg-crimson px-1">EcoTi · AI TV</span>
          <span className="text-pink-200/70">{speaking ? "on air" : "anchor"}</span>
        </div>
        {/* waveform */}
        {speaking && (
          <div className="absolute inset-x-2 bottom-6 flex h-6 items-end justify-center gap-[2px]">
            {Array.from({ length: bars }).map((_, i) => {
              const h = 8 + Math.abs(Math.sin(i * 0.9 + level * 10)) * level * 100;
              return <span key={i} style={{ height: `${Math.min(100, h)}%` }}
                className="w-[3px] rounded-full bg-pink-300/80" />;
            })}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        {!speaking ? (
          <button onClick={play} className="rounded-full bg-crimson px-3 py-1 text-xs font-semibold text-white hover:opacity-90">
            ▶ Read bulletin
          </button>
        ) : (
          <button onClick={stop} className="rounded-full bg-ink/70 px-3 py-1 text-xs font-semibold text-white hover:opacity-90">
            ■ Stop
          </button>
        )}
      </div>
    </div>
  );
}
