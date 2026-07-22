import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import Splash from "./components/Splash";
import EcotiGem from "./components/EcotiGem";
import AiTvBox from "./components/AiTvBox";

const FAVICON =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='46' fill='%23ec4899'/%3E%3Cpath d='M50 6 L74 26 L66 62 L34 62 L26 26 Z' fill='%23be185d'/%3E%3Ccircle cx='40' cy='36' r='14' fill='%23f9a8d4' opacity='.6'/%3E%3C/svg%3E";

export const metadata: Metadata = {
  title: "EcoTi — Economic Trust Intelligence",
  description: "Self-healing multi-agent swarm for India's financial frontline",
  icons: { icon: FAVICON },
};

const NAV = [
  ["/", "Command Centre"],
  ["/network", "Fraud Network"],
  ["/footprint", "OSINT Footprint"],
  ["/tor", "Tor Intel"],
  ["/report", "Report Fraud"],
  ["/aitv", "AI TV"],
  ["/archive", "Archive"],
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Splash />
        <header className="glass-nav sticky top-0 z-50 flex flex-wrap items-center justify-between gap-2 px-6 py-3">
          <Link href="/" className="flex items-center gap-2 font-bold tracking-tight text-ink">
            <EcotiGem size={30} />
            <span className="text-gradient text-lg font-extrabold">EcoTi</span>
            <span className="ml-1 hidden text-xs text-ink3 sm:inline">Economic Trust Intelligence</span>
          </Link>
          <nav className="flex flex-wrap gap-1 text-sm font-medium">
            {NAV.map(([href, label]) => (
              <Link key={href} href={href} className="rounded-full px-3 py-1.5 text-ink2 transition hover:bg-crimson/10 hover:text-crimson">
                {label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-[1400px] p-6">{children}</main>
        <AiTvBox />
      </body>
    </html>
  );
}
