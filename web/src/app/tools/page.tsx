import CitizenShieldTool from "../components/CitizenShieldTool";
import NumberCheckTool from "../components/NumberCheckTool";

export default function ToolsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">
          Citizen <span className="text-gradient">Tools</span>
        </h1>
        <p className="text-sm text-ink2">
          On-device fraud checks for citizens — a scam-message shield and a mobile-number risk check.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="glass-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink">Citizen Shield</h3>
          <CitizenShieldTool />
        </div>
        <div className="glass-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink">Number Check</h3>
          <NumberCheckTool />
        </div>
      </div>
    </div>
  );
}
