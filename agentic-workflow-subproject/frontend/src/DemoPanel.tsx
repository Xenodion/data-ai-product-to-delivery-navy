import { useEffect, useState } from "react";

// Demo-only control: rendered when the API runs with NAVY_DEMO_MODE=1.
export function DemoPanel({ onInjected }: { onInjected: () => void }) {
  const [max, setMax] = useState(0);
  const [count, setCount] = useState(5);
  const [auto, setAuto] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/api/v1/demo").then((r) => r.json())
      .then((d: { enabled: boolean; max_count: number }) => setMax(d.enabled ? d.max_count : 0))
      .catch(() => setMax(0));
  }, []);
  if (!max) return null;

  const inject = async () => {
    setBusy(true); setMessage("");
    try {
      const response = await fetch("/api/v1/demo/inject", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count, auto_handle: auto }),
      });
      const body = await response.json();
      setMessage(response.ok ? `${body.injected.length} tickets injected` : `Failed: ${body.detail?.code ?? response.status}`);
      onInjected();
    } catch (reason) {
      setMessage(`Failed: ${(reason as Error).message}`);
    } finally { setBusy(false); }
  };

  return <div className="card demo-panel" style={{ display: "flex", gap: 12, alignItems: "center", padding: "10px 14px", flexWrap: "wrap" }}>
    <strong>Demo</strong>
    <label>Tickets <input type="number" min={1} max={max} value={count} style={{ width: 64 }}
      onChange={(e) => setCount(Math.min(max, Math.max(1, Number(e.target.value) || 1)))} /></label>
    <label><input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} /> Handle automatically</label>
    <button className="button button-quiet" disabled={busy} onClick={() => { void inject(); }}>Inject tickets</button>
    {message && <span>{message}</span>}
  </div>;
}
