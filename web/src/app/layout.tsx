import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "EcoTi — Economic Trust Intelligence",
  description: "Self-healing multi-agent swarm for India's financial frontline",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="glass-nav sticky top-0 z-50 flex items-center justify-between px-6 py-3">
          <Link href="/" className="font-bold tracking-tight text-ink">
            <span className="text-gradient text-lg font-extrabold">EcoTi</span>
            <span className="ml-2 text-xs text-ink3">Economic Trust Intelligence</span>
          </Link>
          <nav className="flex gap-1 text-sm font-medium">
            <Link href="/" className="rounded-full px-3 py-1.5 text-ink2 transition hover:bg-crimson/10 hover:text-crimson">Command Centre</Link>
            <Link href="/network" className="rounded-full px-3 py-1.5 text-ink2 transition hover:bg-crimson/10 hover:text-crimson">Fraud Network</Link>
            <Link href="/footprint" className="rounded-full px-3 py-1.5 text-ink2 transition hover:bg-crimson/10 hover:text-crimson">OSINT Footprint</Link>
            <Link href="/tor" className="rounded-full px-3 py-1.5 text-ink2 transition hover:bg-crimson/10 hover:text-crimson">Tor Intel</Link>
            <Link href="/report" className="rounded-full px-3 py-1.5 text-ink2 transition hover:bg-crimson/10 hover:text-crimson">Report Fraud</Link>
            <Link href="/archive" className="rounded-full px-3 py-1.5 text-ink2 transition hover:bg-crimson/10 hover:text-crimson">Archive</Link>
          </nav>
        </header>
        <main className="mx-auto max-w-[1400px] p-6">{children}</main>
      </body>
    </html>
  );
}
