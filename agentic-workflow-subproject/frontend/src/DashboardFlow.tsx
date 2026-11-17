import { useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import type { OverviewData } from "./api.ts";

type Props = { data: OverviewData; stale: boolean };
type Point = { x: number; y: number };
type Connection = { id: string; path: string; kind: "automatic" | "human" | "error" | "return" | "outcome" };
type IconName = "inbox" | "route" | "evidence" | "draft" | "check" | "person" | "alert";

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, ReactNode> = {
    inbox: <><path d="M4 5h16v14H4zM4 13h5l2 3h2l2-3h5" /><path d="M9 5v4m6-4v4" /></>,
    route: <><path d="M5 18V8a3 3 0 0 1 3-3h10M14 2l4 3-4 3M5 13h10a3 3 0 0 1 3 3v3" /><circle cx="5" cy="19" r="2" /><path d="m15 17 3 3 3-3" /></>,
    evidence: <><ellipse cx="8" cy="5" rx="5" ry="2" /><path d="M3 5v11c0 3 10 3 10 0V5M3 10c0 3 10 3 10 0" /><path d="M16 8h5v13h-9v-2M17 12h2m-2 4h2" /></>,
    draft: <><path d="M13 4H4v17h15v-8M10 14l1-4 8-8 3 3-8 8-4 1Z" /></>,
    check: <><path d="m8 12 3 3 6-7" /><circle cx="12" cy="12" r="9" /></>,
    person: <><circle cx="12" cy="7" r="3" /><path d="M5 21v-4a7 7 0 0 1 14 0v4M9 17v4m6-4v4" /></>,
    alert: <><path d="m12 3 10 18H2L12 3Z" /><path d="M12 9v5m0 3v.5" /></>,
  };
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

/** Connections follow actual card geometry; aggregate activity never implies a ticket's location. */
export function DashboardFlow({ data, stale }: Props) {
  const boardRef = useRef<HTMLDivElement>(null);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [paused, setPaused] = useState(false);
  const id = useId().replace(/:/g, "");
  const processing = data.by_status.processing;
  const active = !stale && (processing ?? 0) > 0;
  const animate = active && !paused;

  useLayoutEffect(() => {
    const board = boardRef.current;
    if (!board) return;
    const measure = () => {
      const bounds = board.getBoundingClientRect();
      const anchor = (name: string, side: "left" | "right" | "top" | "bottom"): Point => {
        const rect = board.querySelector<HTMLElement>(`[data-flow-node="${name}"]`)!.getBoundingClientRect();
        return { x: (side === "left" ? rect.left : side === "right" ? rect.right : rect.left + rect.width / 2) - bounds.left,
          y: (side === "top" ? rect.top : side === "bottom" ? rect.bottom : rect.top + rect.height / 2) - bounds.top };
      };
      const connect = (from: string, to: string, kind: Connection["kind"], fromSide: "left" | "right" | "top" | "bottom", toSide: "left" | "right" | "top" | "bottom") => {
        const a = anchor(from, fromSide), b = anchor(to, toSide);
        const horizontal = fromSide === "left" || fromSide === "right";
        const middle = horizontal ? (a.x + b.x) / 2 : (a.y + b.y) / 2;
        const curve = horizontal ? `C ${middle} ${a.y}, ${middle} ${b.y}, ${b.x} ${b.y}` : `C ${a.x} ${middle}, ${b.x} ${middle}, ${b.x} ${b.y}`;
        return { id: `${from}-${to}`, path: `M ${a.x} ${a.y} ${curve}`, kind };
      };
      const next = [
        connect("intake", "routing", "automatic", "right", "left"),
        connect("routing", "evidence", "automatic", "right", "left"),
        connect("evidence", "draft", "automatic", "right", "left"),
        connect("intake", "errors", "error", "bottom", "top"),
        connect("routing", "reroute", "human", "bottom", "top"),
        connect("reroute", "evidence", "return", "right", "bottom"),
        connect("draft", "review", "human", "bottom", "top"),
        connect("review", "outcome", "outcome", "right", "bottom"),
      ];
      setConnections((previous) => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(board);
    board.querySelectorAll<HTMLElement>("[data-flow-node]").forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, []);

  const stages: { id: string; icon: IconName; number: string; title: string; description: string; chips?: string[] }[] = [
    { id: "intake", icon: "inbox", number: "01", title: "Receive", description: "Validate the incoming request" },
    { id: "routing", icon: "route", number: "02", title: "Qualify & route", description: "Identify intent, desk and priority" },
    { id: "evidence", icon: "evidence", number: "03", title: "Gather evidence", description: "Select the context needed", chips: ["SQL", "Text Search"] },
    { id: "draft", icon: "draft", number: "04", title: "Prepare reply", description: "Draft from evidence and check policy" },
    { id: "outcome", icon: "check", number: "05", title: "Resolve & record", description: "Final check, human send or manual close" },
  ];
  const queues = [
    { id: "errors", name: "Flow errors", description: "Inspect a stopped flow", count: data.queues.errors, href: "#workspace/errors", icon: "alert" as const, kind: "error" },
    { id: "reroute", name: "Re-routing", description: "Choose the desk or reply", count: data.queues["re-router"], href: "#workspace/re-routing", icon: "person" as const, kind: "human" },
    { id: "review", name: "Ticket review", description: "Review, edit and decide", count: data.queues.validator, href: "#workspace/review", icon: "person" as const, kind: "human" },
  ];

  return <div className={`ops-flow${stale ? " is-stale" : ""}${animate ? " is-running" : ""}`}>
    <div className="ops-flow-toolbar">
      <div className="ops-flow-status"><span className={`ops-status-dot${active ? " active" : ""}`} /><b>{stale ? "Last known state" : processing === undefined ? "Activity unavailable" : active ? `${processing} processing` : "Ready for incoming work"}</b><span>From request to human decision</span></div>
      <button type="button" className="ops-motion-toggle" aria-pressed={paused} disabled={!active} onClick={() => setPaused((value) => !value)}>{paused ? "Resume motion" : "Pause motion"}</button>
    </div>
    <div className="ops-flow-board" ref={boardRef} role="group" aria-label="Workflow: intake, routing, evidence, draft, human decision, then outcome">
      <svg className="ops-flow-connections" width="100%" height="100%" aria-hidden="true">
        <defs><marker id={`${id}-arrow`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="m2 1 7 4-7 4" fill="none" stroke="context-stroke" strokeWidth="1.6" /></marker></defs>
        {connections.map((connection) => <g key={connection.id} className={`ops-connection ${connection.kind}`}>
          <path className="ops-wire" d={connection.path} markerEnd={`url(#${id}-arrow)`} />
          {animate && connection.kind === "automatic" && <g className="ops-moving-ticket">
            <rect x="-7" y="-5" width="14" height="10" rx="3" /><path d="M-3 -1H3M-3 2H1" />
            <animateMotion dur="3.6s" repeatCount="indefinite" path={connection.path} />
          </g>}
        </g>)}
      </svg>
      <div className="ops-stage-row">
        {stages.map((stage) => <div key={stage.id} className={`ops-stage ${stage.id}`} data-flow-node={stage.id}>
          <div className="ops-stage-top"><span className="ops-node-icon"><Icon name={stage.icon} /></span><span className="ops-step-number">{stage.number}</span></div>
          <b>{stage.title}</b><p>{stage.description}</p>
          {stage.chips && <div className="ops-tool-chips">{stage.chips.map((chip) => <span key={chip}>{chip}</span>)}</div>}
          {stage.id === "outcome" && <span className="ops-outcome-note">Sends are simulated</span>}
        </div>)}
      </div>
      <div className="ops-queue-row">
        {queues.map((queue) => <a key={queue.id} data-flow-node={queue.id} className={`ops-queue ${queue.id} ${queue.kind}${(queue.count ?? 0) > 0 ? " has-work" : ""}`} href={queue.href}>
          <div className="ops-queue-top"><span className="ops-node-icon"><Icon name={queue.icon} /></span><span className="ops-queue-count">{queue.count ?? "—"}<small>{queue.count === 1 ? "ticket" : "tickets"}</small></span></div>
          <b>{queue.name}</b><p>{queue.description}</p><span className="ops-queue-action">{queue.count === 0 ? "Queue clear" : queue.count === undefined ? "View queue" : "Open queue"}<span aria-hidden="true">↗</span></span>
        </a>)}
        <div className="ops-handoff-note"><span />Human decisions stay with your team.<small>Re-route, review or close explicitly.</small></div>
      </div>
    </div>
    <div className="ops-flow-key"><div><span><i className="automatic" />Automated preparation</span><span><i className="human" />Human checkpoint</span><span><i className="outcome" />Recorded outcome</span></div><p>Motion shows illustrative activity, not individual tickets.</p></div>
  </div>;
}
