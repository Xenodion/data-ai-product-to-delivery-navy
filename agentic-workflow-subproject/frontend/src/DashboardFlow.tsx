import type { OverviewData } from "./api.ts";

type Props = { data: OverviewData; stale: boolean };

/** The overview reports queue totals, not the position of individual tickets. */
export function DashboardFlow({ data, stale }: Props) {
  const busy = !stale && (data.by_status.processing ?? 0) > 0;
  const queues = [
    { name: "Re-routing", subtitle: "Assignment needs a person", count: data.queues["re-router"], href: "#workspace/re-routing", kind: "route" },
    { name: "Ticket review", subtitle: "Review and decide", count: data.queues.validator, href: "#workspace/review", kind: "review" },
    { name: "Flow errors", subtitle: "Investigate a flow issue", count: data.queues.errors, href: "#workspace/errors", kind: "error" },
  ];
  return <div className="journey" aria-label="Support ticket workflow">
    <div className="journey-canvas">
      <svg className="journey-lines" viewBox="0 0 1000 280" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <marker id="journey-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1 1 L9 5 L1 9" fill="none" stroke="currentColor" strokeWidth="1.5" /></marker>
          <path id="journey-motion" d="M132 85 H182 M344 85 H394 M556 85 H606 M768 85 H818" />
        </defs>
        <g fill="none" className="journey-paths" markerEnd="url(#journey-arrow)">
          <path d="M132 85 H182 M344 85 H394 M556 85 H606 M768 85 H818" />
          <path className="journey-branch" d="M263 119 V155 Q263 169 277 169 H500 V183" />
          <path className="journey-branch" d="M687 119 V155 Q687 169 701 169 H833 V183" />
          <path className="journey-error-path" d="M50 119 V155 Q50 169 64 169 H167 V183" />
        </g>
        {busy && <g className="journey-tickets"><rect width="10" height="7" rx="2"><animateMotion dur="9s" repeatCount="indefinite" path="M132 85 H182 M344 85 H394 M556 85 H606 M768 85 H818" /></rect></g>}
      </svg>
      <div className="journey-stages">
        <div className="journey-stage"><span className="journey-icon">↙</span><div><small>01 / INTAKE</small><b>Ticket received</b><p>Validate the request</p></div></div>
        <div className="journey-stage"><span className="journey-icon">✳</span><div><small>02 / ROUTING</small><b>Qualify &amp; route</b><p>Fields, desk and priority</p></div></div>
        <div className="journey-stage"><span className="journey-icon">⌘</span><div><small>03 / PREPARATION</small><b>Gather evidence</b><p>SQL and Text Search</p></div></div>
        <div className="journey-stage"><span className="journey-icon">✎</span><div><small>04 / DRAFT</small><b>Prepare reply</b><p>Draft and policy check</p></div></div>
        <div className="journey-stage"><span className="journey-icon outcome">✓</span><div><small>05 / OUTCOME</small><b>Resolve &amp; record</b><p>Final check and simulated send</p></div></div>
      </div>
      <div className="journey-queues">
        {queues.map((queue) => <a key={queue.kind} className={`journey-queue ${queue.kind}`} href={queue.href}>
          <span className="queue-symbol" aria-hidden="true">{queue.kind === "error" ? "!" : "↗"}</span>
          <span className="queue-copy"><small>{queue.kind === "error" ? "NEEDS ATTENTION" : "HUMAN CHECKPOINT"}</small><b>{queue.name}</b><span>{queue.subtitle}</span></span>
          <span className="queue-count">{queue.count ?? "—"}<small>{queue.count === 1 ? "ticket" : "tickets"}</small></span>
          <span className="queue-action">Open queue <span aria-hidden="true">→</span></span>
        </a>)}
      </div>
    </div>
    <div className="journey-footer"><span><i /> {stale ? "Last known data" : busy ? "Processing activity shown" : "No processing activity"}</span><span>Animation is indicative, not individual ticket tracking.</span></div>
  </div>;
}
