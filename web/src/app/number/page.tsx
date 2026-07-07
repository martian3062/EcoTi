import NumberCheckTool from "../components/NumberCheckTool";

export default function NumberPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink">Is this <span className="text-gradient">number a scam?</span></h1>
        <p className="text-sm text-ink2">Also available inside the Command Centre → Citizen tools.</p>
      </div>
      <div className="glass-card p-4">
        <NumberCheckTool />
      </div>
    </div>
  );
}
