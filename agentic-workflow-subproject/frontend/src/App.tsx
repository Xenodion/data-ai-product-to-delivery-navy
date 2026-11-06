import { useEffect, useState, type ReactNode } from "react";
import { FlowMap } from "./FlowMap.tsx";
import { SAMPLE, active, autoAssigned, count, decided, duration, pct, type Overview } from "./overview.ts";

const TABS = [
  { hash: "#overview", label: "Overview" },
  { hash: "#re-router", label: "Re-router" },
  { hash: "#validator", label: "Validator" },
];

function useHash(): string {
  const [hash, setHash] = useState(location.hash || "#overview");
  useEffect(() => {
    const update = () => setHash(location.hash || "#overview");
    addEventListener("hashchange", update);
    return () => removeEventListener("hashchange", update);
  }, []);
  return hash;
}

export function App() {
  const hash = useHash();
  const o = SAMPLE;
  return (
    <>
      <header className="top">
        <h1>Keelpay Support Copilot</h1>
        <nav aria-label="Workspaces">
          {TABS.map((t) => (
            <a key={t.hash} href={t.hash} aria-current={hash === t.hash ? "page" : undefined}>
              {t.label}
            </a>
          ))}
        </nav>
        <p className="sample" role="status">
          Sample numbers: the backend is not connected yet
        </p>
      </header>
      <main>
        {hash === "#re-router" && <Workspace title="Re-router" waiting={count(o.stages.reRouter)} />}
        {hash === "#validator" && <Workspace title="Validator" waiting={count(o.stages.validator)} />}
        {hash !== "#re-router" && hash !== "#validator" && <OverviewPage o={o} />}
      </main>
    </>
  );
}

function Workspace({ title, waiting }: { title: string; waiting: number }) {
  return (
    <section className="empty">
      <h2>{title}</h2>
      <p>This workspace is not built yet. {waiting} tickets are in this queue in the sample.</p>
      <a href="#overview">Back to Overview</a>
    </section>
  );
}

function Stat({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div className="stat">
      <dd>{value}</dd>
      <dt>{label}</dt>
    </div>
  );
}

function Bars({ rows, whole }: { rows: { label: string; value: number; human?: boolean }[]; whole: number }) {
  const max = Math.max(...rows.map((r) => r.value));
  return (
    <ul className="bars">
      {rows.map((r) => (
        <li key={r.label} title={`${r.label}: ${r.value} of ${whole}, ${pct(r.value, whole)}`}>
          <span>{r.label}</span>
          <span className="track">
            <i className={r.human ? "human" : undefined} style={{ width: `${(100 * r.value) / max}%` }} />
          </span>
          <b>{pct(r.value, whole)}</b>
          <span className="n">{r.value}</span>
        </li>
      ))}
    </ul>
  );
}

function OverviewPage({ o }: { o: Overview }) {
  const s = o.stages;
  const stageRows = [
    ["Qualifier Model", s.qualifier],
    ["Drafter Model", s.drafter],
    ["Re-router", s.reRouter],
    ["Validator", s.validator],
    ["Agent edits", s.agentEdits],
  ] as const;
  const changes = o.reRouter.firstChanges + o.reRouter.secondChanges;
  return (
    <>
      <section className="numbers" aria-label="Ticket counts">
        <div>
          <h2>Right now</h2>
          <dl>
            <Stat value={active(o)} label="Active tickets" />
            <Stat value={count(s.reRouter)} label="In Re-router" />
            <Stat value={count(s.validator)} label="In Validator" />
            <Stat value={`${o.oldestWaitingMinutes} min`} label="Oldest waiting" />
          </dl>
        </div>
        <div>
          <h2>
            Since {o.period.since}, with {o.period.seeded} seeded tickets
          </h2>
          <dl>
            <Stat value={o.received} label="Received" />
            <Stat value={o.sent} label="Sent, simulated" />
            <Stat value={o.failed} label="Failed" />
            <Stat value={pct(autoAssigned(o), o.routing.decided)} label="Desk set by rules" />
          </dl>
        </div>
      </section>

      <section className="map" aria-label="Ticket flow" tabIndex={0}>
        <FlowMap o={o} />
      </section>
      <p className="note">Cards show the tickets at each step now. Arrows count tickets since {o.period.since}.</p>

      <section className="panels">
        <article>
          <h2>Where the rules sent tickets</h2>
          <p className="base">{o.routing.decided} tickets with a routing decision</p>
          <Bars
            whole={o.routing.decided}
            rows={[
              ...o.routing.desks.map((d) => ({ label: d.name, value: d.tickets })),
              { label: "Unknown, a person picks", value: o.routing.unknown, human: true },
            ]}
          />
          <p className="base">
            People changed the desk {changes} times: {pct(changes, o.routing.decided)} of routed tickets. A low rate does
            not prove the routing is right.
          </p>
        </article>
        <article>
          <h2>What the Validator decided</h2>
          <p className="base">{decided(o)} decisions so far</p>
          <Bars
            whole={decided(o)}
            rows={[
              { label: "Approved as written", value: o.validator.approved },
              { label: "Sent to Agent edits", value: o.validator.fixIt, human: true },
              { label: "Wrong desk", value: o.validator.wrongDesk, human: true },
            ]}
          />
          <p className="base">{o.editsDone} more replies were sent after an edit.</p>
        </article>
        <article>
          <h2>High priority</h2>
          <dl>
            <Stat value={o.urgent.open} label="Open" />
            <Stat value={o.urgent.unclaimed} label="Not picked up" />
            <Stat value={`${o.urgent.oldestMinutes} min`} label="Oldest" />
          </dl>
          <p className="base">Priority never changes the path. It only shows the agent what to open first.</p>
        </article>
        <article>
          <h2>Failed tickets</h2>
          <ul className="incidents">
            {o.incidents.map((i) => (
              <li key={i.ticket}>
                <b>{i.ticket}</b> {i.step}: {i.problem}. <span>{i.next}.</span>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <details className="table">
        <summary>Show step times as a table</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">Step</th>
              <th scope="col">Waiting</th>
              <th scope="col">In progress</th>
              <th scope="col">Failed</th>
              <th scope="col">Avg wait</th>
              <th scope="col">Avg work</th>
            </tr>
          </thead>
          <tbody>
            {stageRows.map(([name, st]) => (
              <tr key={name}>
                <th scope="row">{name}</th>
                <td>{st.waiting}</td>
                <td>{st.working}</td>
                <td>{st.failed}</td>
                <td>{duration(st.avgWaitSeconds)}</td>
                <td>{duration(st.avgWorkSeconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  );
}
