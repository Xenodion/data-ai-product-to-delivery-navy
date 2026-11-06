import type { ReactNode } from "react";
import { autoAssigned, decided, duration, pct, type Overview, type Stage } from "./overview.ts";

// Same layout as docs/design/keelpay_workflow_map.svg, with live counts in place of descriptions.
type Kind = "det" | "gen" | "hum";

const ICON: Record<Kind, ReactNode> = {
  det: <text x="10" y="15" textAnchor="middle" className="ic">{"{ }"}</text>,
  gen: <path d="M10 1L12.4 7.6L19 10L12.4 12.4L10 19L7.6 12.4L1 10L7.6 7.6z" />,
  hum: <path d="M10 2a4 4 0 1 1 0 8a4 4 0 0 1 0-8zM2 19C2 13 6 11.5 10 11.5S18 13 18 19z" />,
};

const W = 190;
const H = 126;

function Card(p: { x: number; y: number; kind: Kind; head: string; title: string; failed?: number; w?: number; h?: number; children: ReactNode }) {
  const { x, y, kind, head, title, failed = 0, w = W, h = H, children } = p;
  return (
    <g transform={`translate(${x} ${y})`} className={`card ${kind}`}>
      <rect className="box" width={w} height={h} rx="13" />
      <path className="strip" d={`M0 26V13A13 13 0 0 1 13 0H${w - 13}A13 13 0 0 1 ${w} 13V26z`} />
      <svg x="12" y="6" width="14" height="14" viewBox="0 0 20 20" className="glyph">{ICON[kind]}</svg>
      <text x="32" y="17.5" className="hd">{head}</text>
      {failed > 0 && <text x={w - 12} y="17.5" className="hd" textAnchor="end">{failed} failed</text>}
      <text x="14" y="47" className="t">{title}</text>
      {children}
    </g>
  );
}

function Counts({ s }: { s: Stage }) {
  return (
    <>
      <text x="14" y="80" className="num">{s.waiting}</text>
      <text x="14" y="95" className="sub">waiting</text>
      <text x="88" y="80" className="num">{s.working}</text>
      <text x="88" y="95" className="sub">in progress</text>
      <text x="14" y="115" className="sub">Avg wait {duration(s.avgWaitSeconds)}, work {duration(s.avgWorkSeconds)}</text>
    </>
  );
}

function Lane({ y, h, kind }: { y: number; h: number; kind: Kind }) {
  return <rect x="124" y={y} width="1070" height={h} rx="18" className={`lane ${kind}`} />;
}

function Key(p: { x: number; y: number; kind: Kind; name: string; l1: string; l2: string }) {
  return (
    <g transform={`translate(${p.x} ${p.y})`} className={`card ${p.kind}`}>
      <rect className="strip" width="28" height="28" rx="8" />
      <svg x="6" y="6" width="16" height="16" viewBox="0 0 20 20" className="glyph">{ICON[p.kind]}</svg>
      <text x="38" y="19" className="kt">{p.name}</text>
      <text x="0" y="48" className="kd">{p.l1}</text>
      <text x="0" y="65" className="kd">{p.l2}</text>
    </g>
  );
}

function Edge({ d, fix, later }: { d: string; fix?: boolean; later?: boolean }) {
  return <path d={d} className={fix ? "edge fix" : later ? "edge later" : "edge"} markerEnd={`url(#${fix ? "a-fix" : later ? "a-later" : "a"})`} />;
}

function Label({ x, y, lines, fix, anchor = "start" }: { x: number; y: number; lines: string[]; fix?: boolean; anchor?: "start" | "middle" | "end" }) {
  return (
    <text x={x} y={y} textAnchor={anchor} className={fix ? "lb fix" : "lb"}>
      {lines.map((l, i) => (
        <tspan key={l} x={x} dy={i ? 16 : 0}>{l}</tspan>
      ))}
    </text>
  );
}

function End({ x, y, title, sub }: { x: number; y: number; title: string; sub: string }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect className="end" width="96" height="66" rx="13" />
      <text x="48" y="28" className="t small" textAnchor="middle">{title}</text>
      <text x="48" y="48" className="sub" textAnchor="middle">{sub}</text>
    </g>
  );
}

function Tool({ x, title, l1, l2 }: { x: number; title: string; l1: string; l2: string }) {
  return (
    <Card x={x} y={56} kind="det" head="TOOL" title={title} w={232} h={116}>
      <text x="14" y="74" className="sub">{l1}</text>
      <text x="14" y="91" className="sub">{l2}</text>
    </Card>
  );
}

export function FlowMap({ o }: { o: Overview }) {
  const s = o.stages;
  const auto = autoAssigned(o);
  const v = decided(o);
  return (
    <svg viewBox="0 0 1320 632" role="group" aria-label="Keelpay ticket flow with counts at each step">
      <defs>
        <linearGradient id="gen" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#7c3aed" />
          <stop offset="1" stopColor="#c026d3" />
        </linearGradient>
        {[["a", "edge-m"], ["a-fix", "edge-f"], ["a-later", "edge-l"]].map(([id, cls]) => (
          <marker key={id} id={id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto">
            <path d="M0 0L10 5L0 10z" className={cls} />
          </marker>
        ))}
      </defs>

      <Lane y={10} h={186} kind="det" />
      <Lane y={212} h={176} kind="gen" />
      <Lane y={404} h={218} kind="hum" />
      <Key x={140} y={28} kind="det" name="DETERMINISTIC" l1="Same input, same result." l2="Fully testable, free to run." />
      <Key x={1000} y={224} kind="gen" name="AGENTIC" l1="Probabilistic, it can be wrong." l2="Proposes, never decides alone." />
      <Key x={140} y={428} kind="hum" name="HUMAN, THE APP" l1="Slower and costly, but accountable." l2="Always has the last word." />

      <rect x="670" y="20" width="508" height="164" rx="15" className="tools" />
      <text x="686" y="43" className="kd strong">Tools the Drafter can call, read-only. Not in the first version.</text>

      <Edge d="M108 306H140" />
      <Edge d="M330 306H345Q360 306 360 291V108Q360 93 375 93H390" />
      <Edge d="M540 156V291Q540 306 555 306H670" />
      <Edge d="M860 306H1030Q1045 306 1045 321V432" />
      <Edge d="M860 476H950" />
      <Edge d="M1140 495H1220" />
      <Edge d="M730 243V174" later />
      <Edge d="M770 172V241" later />

      <Edge d="M440 156V432" fix />
      <Edge d="M530 432V411Q530 396 545 396H735Q750 396 750 381V369" fix />
      <Edge d="M580 495H670" fix />
      <Edge d="M950 530H860" fix />
      <Edge d="M1045 558V585Q1045 600 1030 600H500Q485 600 485 585V558" fix />

      <End x={12} y={273} title="Ticket" sub={`${o.received} received`} />
      <End x={1220} y={462} title="Reply sent" sub={`${o.sent} simulated`} />

      <Card x={140} y={243} kind="gen" head="LLM" title="Qualifier Model" failed={s.qualifier.failed}>
        <Counts s={s.qualifier} />
      </Card>
      <Card x={390} y={30} kind="det" head="RULES DECISION" title="Routing Node">
        <text x="14" y="80" className="num">{pct(auto, o.routing.decided)}</text>
        <text x="14" y="95" className="sub">desk set by rules</text>
        <text x="14" y="115" className="sub">{auto} of {o.routing.decided} tickets</text>
      </Card>
      <Card x={670} y={243} kind="gen" head="LLM" title="Drafter Model" failed={s.drafter.failed}>
        <Counts s={s.drafter} />
      </Card>
      <Tool x={682} title="SQL lookup" l1="Reads a fake transactions" l2="table, one merchant at a time." />
      <Tool x={926} title="RAG search" l1="Finds the right passage in a" l2="fake help centre, with its source." />
      <a href="#re-router" aria-label={`Open Re-router, ${s.reRouter.waiting} tickets waiting`}>
        <Card x={390} y={432} kind="hum" head="HUMAN DECISION" title="Re-router">
          <Counts s={s.reRouter} />
        </Card>
      </a>
      <a href="#validator" aria-label={`Open Validator, ${s.agentEdits.waiting} edits waiting`}>
        <Card x={670} y={432} kind="hum" head="HUMAN" title="Agent edits">
          <Counts s={s.agentEdits} />
        </Card>
      </a>
      <a href="#validator" aria-label={`Open Validator, ${s.validator.waiting} tickets waiting`}>
        <Card x={950} y={432} kind="hum" head="HUMAN DECISION" title="Validator">
          <Counts s={s.validator} />
        </Card>
      </a>

      <Label x={350} y={232} anchor="end" lines={[`${o.routing.decided} read`]} />
      <Label x={552} y={278} lines={["every routed", `ticket: ${o.routing.decided}`]} />
      <Label x={875} y={296} lines={[`${o.drafts.ready} drafts ready`]} />
      <Label x={905} y={466} anchor="middle" lines={[`${o.editsDone} ready`]} />
      <Label x={450} y={350} fix lines={["desk unknown", `${o.routing.unknown} of ${o.routing.decided}, ${pct(o.routing.unknown, o.routing.decided)}`]} />
      <Label x={565} y={370} fix lines={["1st desk change", `${o.reRouter.firstChanges} new drafts`]} />
      <Label x={625} y={484} anchor="middle" fix lines={["2nd change"]} />
      <Label x={625} y={514} anchor="middle" fix lines={[`${o.reRouter.secondChanges} ticket`]} />
      <Label x={905} y={504} anchor="middle" fix lines={[`fix it: ${o.validator.fixIt}`, pct(o.validator.fixIt, v)]} />
      <Label x={770} y={592} anchor="middle" fix lines={[`wrong desk: ${o.validator.wrongDesk} of ${v}, ${pct(o.validator.wrongDesk, v)}`]} />
    </svg>
  );
}
