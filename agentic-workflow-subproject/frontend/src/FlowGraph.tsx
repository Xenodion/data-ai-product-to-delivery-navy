import type { OverviewData } from "./api.ts";

type NodeKind = "rule" | "model" | "tool" | "human" | "system" | "error";

function FlowNode(props: {
  x: number; y: number; title: string; kind: NodeKind; label: string; detail: string;
  count?: number; countLabel?: string; href?: string; active?: boolean; planned?: boolean;
}) {
  const { x, y, title, kind, label, detail, count, countLabel, href, active, planned } = props;
  const body = <g className={`flow-node ${kind}${active ? " has-work" : ""}${planned ? " planned" : ""}`}>
    <rect className="node-card" x={x} y={y} width="150" height="78" rx="3" />
    <rect className="node-accent" x={x} y={y} width="4" height="78" />
    <text className="node-kind" x={x + 14} y={y + 18}>{label}</text>
    {count !== undefined && <g className="node-count"><title>{count} {countLabel ?? "items"}</title><rect x={x + 107} y={y + 7} width="34" height="19" rx="2" /><text x={x + 124} y={y + 21} textAnchor="middle">{count}</text></g>}
    <text className="node-title" x={x + 14} y={y + 43}>{title}</text>
    <text className="node-detail" x={x + 14} y={y + 62}>{detail}</text>
    {planned && <text className="node-planned" x={x + 136} y={y + 71} textAnchor="end">PLANNED</text>}
  </g>;
  return href
    ? <a className="flow-node-link" href={href} aria-label={`${title}${count !== undefined ? `, ${count} tickets` : ""}; open queue`}>{body}</a>
    : <g role="group" aria-label={`${title}: ${detail}`}>{body}</g>;
}

export function FlowGraph({ data }: { data: OverviewData }) {
  const busy = data.by_status.processing ?? 0;
  const reroute = data.queues["re-router"] ?? 0;
  const review = data.queues.validator ?? 0;
  const errors = data.queues.errors ?? 0;
  const sent = data.simulated_sends ?? 0;

  return <div className="flow-graph-scroll" role="region" aria-label="Interactive ticket flow graph" tabIndex={0}>
    <svg className="flow-graph" viewBox="0 0 1980 700" role="group" aria-labelledby="flow-graph-title flow-graph-description">
      <title id="flow-graph-title">Keelpay support ticket workflow</title>
      <desc id="flow-graph-description">A directed graph from intake, through qualification and parallel SQL and knowledge searches, to drafting and human review. Re-routing, review, errors, and send stages show live API counts and link to their queues.</desc>
      <defs>
        <pattern id="flow-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#e8edf2" strokeWidth=".7" /></pattern>
        <marker id="arrow-ink" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#8e9bac" /></marker>
        <marker id="arrow-human" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#c17b15" /></marker>
        <marker id="arrow-error" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#b53b49" /></marker>
        <marker id="arrow-return" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#21815c" /></marker>
        <path id="main-motion-path" d="M190 139H220H370H400H550H580H730H760H835V254H835C940 254 1000 333 1185 333H1365H1545V589H1535" />
      </defs>

      <rect className="graph-board" width="1980" height="700" />
      <rect x="18" y="22" width="1944" height="463" className="graph-lane lane-automation" />
      <rect x="18" y="500" width="1944" height="178" className="graph-lane lane-human" />
      <text className="lane-heading" x="38" y="50">AUTOMATED FLOW</text>
      <text className="lane-caption" x="205" y="50">rules, local model and independent read-only tools</text>
      <text className="lane-heading lane-heading-human" x="38" y="528">HUMAN CONTROL &amp; OUTCOMES</text>
      <text className="lane-caption" x="285" y="528">your decision is explicit at every checkpoint</text>

      <g className="flow-edges" fill="none" markerEnd="url(#arrow-ink)">
        <path d="M190 139H220" className={busy > 0 ? "edge-live" : ""} />
        <path d="M370 139H400" className={busy > 0 ? "edge-live" : ""} />
        <path d="M550 139H580" className={busy > 0 ? "edge-live" : ""} />
        <path d="M730 139H760" className={busy > 0 ? "edge-live" : ""} />
        <path d="M835 178V254" />
        <path d="M835 178C900 210 1010 215 1010 254" />
        <path d="M910 293C960 293 1030 333 1110 333" />
        <path d="M1085 293C1095 293 1100 333 1110 333" />
        <path d="M1260 333H1290" />
        <path d="M1440 333H1470" />
        <path d="M1535 372V550" markerEnd="url(#arrow-human)" className={`edge-human${review ? " edge-live" : ""}`} />
        <path d="M295 178C350 285 490 448 665 550" markerEnd="url(#arrow-human)" className={`edge-human edge-branch${reroute ? " edge-live" : ""}`} />
        <path d="M655 178V380C655 460 660 490 665 550" markerEnd="url(#arrow-human)" className={`edge-human edge-branch${reroute ? " edge-live" : ""}`} />
        <path d="M115 178C115 320 105 430 105 550" markerEnd="url(#arrow-error)" className="edge-error" />
        <path d="M665 550V480H742V139H760" markerEnd="url(#arrow-return)" className="edge-return" />
        <path d="M1260 372C1250 455 1330 480 1535 550" markerEnd="url(#arrow-human)" className="edge-human edge-branch" />
        <path d="M1600 589H1630" markerEnd="url(#arrow-ink)" />
        <path d="M1780 589H1800" markerEnd="url(#arrow-ink)" />
      </g>

      {busy > 0 && <g className="flow-particles" aria-hidden="true">
        <circle r="4"><animateMotion dur="4.8s" repeatCount="indefinite"><mpath href="#main-motion-path" /></animateMotion></circle>
        <circle r="2.5" opacity=".65"><animateMotion begin="-2.4s" dur="4.8s" repeatCount="indefinite"><mpath href="#main-motion-path" /></animateMotion></circle>
      </g>}

      <g className="edge-labels">
        <text x="705" y="468" textAnchor="middle">desk unclear</text>
        <text x="755" y="481" textAnchor="middle">one correction → re-check context</text>
        <text x="1190" y="454" textAnchor="middle">no draft / clarification</text>
        <text x="1548" y="463">requires human approval</text>
      </g>

      <FlowNode x={40} y={100} kind="rule" label="RULE · INTAKE" title="Ticket received" detail="Validate envelope" />
      <FlowNode x={220} y={100} kind="model" label="LOCAL MODEL" title="Qualifier" detail="Extract ticket fields" />
      <FlowNode x={400} y={100} kind="rule" label="RULE · CHECK" title="Field check" detail="Verify references" />
      <FlowNode x={580} y={100} kind="rule" label="RULE · ROUTE" title="Routing" detail="Desk & priority" />
      <FlowNode x={760} y={100} kind="rule" label="RULE · PLAN" title="Context plan" detail="Select needed tools" />
      <FlowNode x={760} y={254} kind="tool" label="SQL · READ ONLY" title="Ledger lookup" detail="Payment facts" />
      <FlowNode x={935} y={254} kind="tool" label="TEXT SEARCH · READ ONLY" title="Text Search" detail="Approved documents" />
      <FlowNode x={1110} y={294} kind="rule" label="RULE · GATE" title="Evidence gate" detail="Factual or clarify" />
      <FlowNode x={1290} y={294} kind="model" label="DRAFTER MODEL" title="Draft reply" detail="Uses supplied evidence" />
      <FlowNode x={1470} y={294} kind="rule" label="QUALITY · POLICY" title="Policy check" detail="Block unsafe draft" />
      <FlowNode x={40} y={550} kind="error" label="ERROR QUEUE" title="Needs investigation" detail="API-reported errors" count={errors} countLabel="tickets" href="#workspace/errors" active={errors > 0} />
      <FlowNode x={590} y={550} kind="human" label="HUMAN · ROUTING" title="Re-routing" detail="Choose the right desk" count={reroute} countLabel="tickets" href="#workspace/re-routing" active={reroute > 0} />
      <FlowNode x={1460} y={550} kind="human" label="HUMAN · REVIEW" title="Validator" detail="Review, edit, approve" count={review} countLabel="tickets" href="#workspace/review" active={review > 0} />
      <FlowNode x={1630} y={550} kind="rule" label="FINAL GATE" title="Compliance check" detail="Re-check final reply" />
      <FlowNode x={1800} y={550} kind="system" label="SIMULATED" title="Send & audit" detail="Recorded, never emailed" count={sent} countLabel="sent" />
    </svg>
  </div>;
}
