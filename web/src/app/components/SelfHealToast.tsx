"use client";
import { useEffect, useState } from "react";

export type Toast = { id: number; message: string; level: string };

const LEVEL: Record<string, string> = {
  info: "bg-crimson text-white",
  warning: "bg-warn text-white",
  critical: "bg-danger text-white",
  error: "bg-danger text-white",
};

export default function SelfHealToast({ toasts }: { toasts: Toast[] }) {
  const [visible, setVisible] = useState<Toast[]>([]);

  useEffect(() => {
    setVisible(toasts.slice(-4));
    if (toasts.length) {
      const t = setTimeout(() => setVisible((v) => v.slice(1)), 6000);
      return () => clearTimeout(t);
    }
  }, [toasts]);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {visible.map((t) => (
        <div
          key={t.id}
          className={`max-w-sm rounded-2xl px-4 py-2.5 text-sm shadow-lg ${LEVEL[t.level] ?? "glass-card text-ink"}`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
