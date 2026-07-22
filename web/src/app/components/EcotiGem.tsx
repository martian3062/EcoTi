// Faceted "EcoTi" gem — a low-poly magenta/crimson crystal rendered as inline SVG.
// Pure (no hooks) so it can be used in server or client components.

const SHADES = [
  "#f9a8d4", "#f472b6", "#ec4899", "#db2777", "#e11d48",
  "#be185d", "#9d174d", "#c026d3", "#fb7185", "#d6218b",
];

function fmt(n: number) {
  return Math.round(n * 10) / 10;
}
function P([x, y]: [number, number]) {
  return `${fmt(x)},${fmt(y)}`;
}

export default function EcotiGem({ size = 120, glow = true }: { size?: number; glow?: boolean }) {
  const N = 14;
  const cx = 100, cy = 100, R = 90, ri = 42;
  const uid = "gem"; // static ids are fine — one gem per view is typical

  const pt = (r: number, a: number): [number, number] => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  const outer: [number, number][] = [];
  const inner: [number, number][] = [];
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2 - Math.PI / 2;
    outer.push(pt(R * (i % 2 ? 0.93 : 1), a));
    inner.push(pt(ri * (i % 2 ? 1 : 0.85), a + 0.14));
  }

  const tris: { pts: string; fill: string }[] = [];
  let k = 0;
  for (let i = 0; i < N; i++) {
    const j = (i + 1) % N;
    tris.push({ pts: `${P([cx, cy])} ${P(inner[i])} ${P(inner[j])}`, fill: SHADES[k++ % SHADES.length] });
    tris.push({ pts: `${P(inner[i])} ${P(outer[i])} ${P(outer[j])}`, fill: SHADES[k++ % SHADES.length] });
    tris.push({ pts: `${P(inner[i])} ${P(outer[j])} ${P(inner[j])}`, fill: SHADES[k++ % SHADES.length] });
  }

  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg"
      style={glow ? { filter: "drop-shadow(0 0 24px rgba(236,72,153,0.55))" } : undefined}>
      <defs>
        <radialGradient id={`${uid}-hl`} cx="38%" cy="32%" r="70%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.55" />
          <stop offset="35%" stopColor="#ffffff" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
        <radialGradient id={`${uid}-shade`} cx="65%" cy="72%" r="75%">
          <stop offset="0%" stopColor="#4c0519" stopOpacity="0" />
          <stop offset="100%" stopColor="#4c0519" stopOpacity="0.55" />
        </radialGradient>
        <clipPath id={`${uid}-clip`}><circle cx="100" cy="100" r="92" /></clipPath>
      </defs>

      <g clipPath={`url(#${uid}-clip)`}>
        {tris.map((t, i) => (
          <polygon key={i} points={t.pts} fill={t.fill} stroke="rgba(255,255,255,0.16)" strokeWidth="0.6" />
        ))}
        <circle cx="100" cy="100" r="92" fill={`url(#${uid}-shade)`} />
        <circle cx="100" cy="100" r="92" fill={`url(#${uid}-hl)`} />
      </g>
      <circle cx="100" cy="100" r="92" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="1.5" />
    </svg>
  );
}
