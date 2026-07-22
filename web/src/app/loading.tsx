import EcotiGem from "./components/EcotiGem";

export default function Loading() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
      <div className="gem-float">
        <EcotiGem size={72} />
      </div>
      <div className="splash-bar-track"><div className="splash-bar" /></div>
      <div className="text-xs text-ink3">Loading…</div>
    </div>
  );
}
