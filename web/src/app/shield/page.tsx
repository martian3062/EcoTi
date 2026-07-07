import CitizenShieldTool from "../components/CitizenShieldTool";

export default function ShieldPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">Citizen <span className="text-gradient">Fraud Shield</span></h1>
        <p className="text-sm text-ink2">Also available inside the Command Centre → Citizen tools.</p>
      </div>
      <div className="glass-card p-4">
        <CitizenShieldTool />
      </div>
    </div>
  );
}
