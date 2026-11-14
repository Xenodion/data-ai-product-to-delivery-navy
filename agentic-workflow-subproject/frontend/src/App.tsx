import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import {
  getOverview, getQueue, getTicket, submitAction, submitSend, submitTicket,
  type OverviewData, type QueueName, type TicketSnapshot,
} from "./api.ts";
import { FlowGraph } from "./FlowGraph.tsx";
import { Mailbox } from "./Mailbox.tsx";

const VIEWS: { hash: string; label: string; icon: string }[] = [
  { hash: "#dashboard", label: "Dashboard", icon: "▦" },
  { hash: "#workspace", label: "Workspace", icon: "▤" },
];

const WORKSPACE_TABS: { hash: string; label: string; queue: QueueName; countKey: string }[] = [
  { hash: "#workspace/re-routing", label: "Re-routing", queue: "re-router", countKey: "re-router" },
  { hash: "#workspace/review", label: "Ticket review", queue: "validator", countKey: "validator" },
  { hash: "#workspace/errors", label: "Errors", queue: "errors", countKey: "errors" },
];

const STATUS_LABEL: Record<string, string> = {
  awaiting_validation: "Needs review", ready_to_send: "Ready to send", awaiting_reroute: "Needs routing",
  manual_handling: "Manual handling", sent_open: "Sent · left open", sent_closed: "Sent · closed", closed_manual: "Closed without reply",
  processing: "Processing", error: "Flow error",
};

function useHash(): string {
  const normalize = (value: string) => ({ "#overview": "#dashboard", "#re-router": "#workspace/re-routing", "#validator": "#workspace/review", "#errors": "#workspace/errors" }[value] ?? value);
  const [hash, setHash] = useState(normalize(location.hash || "#dashboard"));
  useEffect(() => {
    const update = () => setHash(normalize(location.hash || "#dashboard"));
    addEventListener("hashchange", update);
    return () => removeEventListener("hashchange", update);
  }, []);
  return hash;
}

export function App() {
  const hash = useHash();
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [apiReady, setApiReady] = useState<boolean | null>(null);
  useEffect(() => {
    let live = true;
    const check = () => fetch("/health/ready").then((response) => {
      if (live) setApiReady(response.ok);
    }).catch(() => { if (live) setApiReady(false); });
    void check();
    const timer = window.setInterval(check, 5000);
    return () => { live = false; window.clearInterval(timer); };
  }, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="nav-toggle" aria-label={navCollapsed ? "Expand main navigation" : "Collapse main navigation"} aria-expanded={!navCollapsed} onClick={() => setNavCollapsed((value) => !value)}>☰</button>
        <a className="brand" href="#dashboard"><span className="brand-mark">K</span><span>KEELPAY <small>SUPPORT OPERATIONS</small></span></a>
        <div className="topbar-context"><span className="environment-mark" />Local demo <span className="context-separator">/</span> Flow v2</div>
        <div className={`connection ${apiReady ? "online" : apiReady === false ? "offline" : "checking"}`} role="status">
          <i />{apiReady === null ? "Connecting" : apiReady ? "Flow online" : "Flow offline"}
        </div>
      </header>
      <div className={`app-layout${navCollapsed ? " nav-collapsed" : ""}`}>
        <aside className="primary-nav" aria-label="Primary navigation">
          <span className="primary-nav-label">OPERATIONS</span>
          {VIEWS.map((view) => <a key={view.hash} href={view.hash} className={hash.startsWith(view.hash) ? "active" : ""} aria-current={hash.startsWith(view.hash) ? "page" : undefined}>
            <span className="nav-icon" aria-hidden="true">{view.icon}</span><span className="nav-label">{view.label}</span>
          </a>)}
          <div className="nav-bottom"><span className="nav-dot" /><span>Human review is active</span></div>
        </aside>
        <main className="content-main">
          {hash.startsWith("#workspace")
            ? <WorkspacePage hash={hash} />
            : <OverviewPage />}
          <footer className="app-footer"><span>Keelpay Support Copilot</span><span>Human decisions stay with the support team.</span></footer>
        </main>
      </div>
    </div>
  );
}

function WorkspacePage({ hash }: { hash: string }) {
  const tab = WORKSPACE_TABS.find((item) => item.hash === hash) ?? WORKSPACE_TABS[1];
  const [overview, setOverview] = useState<OverviewData | null>(null);
  useEffect(() => {
    let live = true;
    const load = () => getOverview().then((data) => { if (live) setOverview(data); }).catch(() => undefined);
    void load(); const timer = window.setInterval(load, 8000);
    return () => { live = false; window.clearInterval(timer); };
  }, []);
  const title = tab.queue === "re-router" ? "Re-routing" : tab.queue === "errors" ? "Flow errors" : "Ticket review";
  const description = tab.queue === "re-router"
    ? "Resolve unclear assignments and route tickets to the right desk."
    : tab.queue === "errors" ? "Inspect tickets that need operational attention."
      : "Review the message, evidence and reply before taking action.";
  return <section className="page workspace-page">
    <PageHeading eyebrow="AGENT WORKSPACE" title="Ticket workspace" description={description} />
    <nav className="workspace-tabs" aria-label="Ticket queues">
      {WORKSPACE_TABS.map((item) => {
        const count = overview ? item.queue === "validator" ? overview.queues.validator : overview.queues[item.countKey] : null;
        return <a key={item.hash} href={item.hash} aria-current={tab.hash === item.hash ? "page" : undefined}>
          {item.label}<span className="tab-count">{count ?? "—"}</span>
        </a>;
      })}
    </nav>
    <QueueWorkspace key={tab.queue} name={tab.queue} title={title} />
  </section>;
}

function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const load = useCallback(() => getOverview().then((value) => {
    setData(value); setError(""); setUpdatedAt(new Date());
  }).catch((reason: Error) => setError(reason.message)), []);
  useEffect(() => {
    void load();
    const timer = window.setInterval(() => { void load(); }, 8000);
    return () => window.clearInterval(timer);
  }, [load, refresh]);

  return <section className="page dashboard-page">
    <PageHeading eyebrow="OPERATIONS" title="Support flow" description="A live view of incoming work, agent queues and completed outcomes."
      action={<button className="button button-quiet" onClick={() => setRefresh((value) => value + 1)}>↻ <span>Refresh</span></button>} />
    {error && <Notice>{data ? "Showing the last successful update. " : ""}Could not refresh live data: {error}</Notice>}
    {!data ? <Loading label={error ? "Waiting for the flow API" : "Loading live flow metrics…"} /> : <>
      <section className="metric-row" aria-label="Key flow metrics">
        <Metric label="Tickets received" value={data.total} note="All tickets in this run" tone="blue" />
        <Metric label="Waiting for an agent" value={(data.queues["re-router"] ?? 0) + (data.queues.validator ?? 0)} note="Across review queues" tone="amber" />
        <Metric label="Oldest open ticket" value={duration(data.oldest_waiting_seconds)} note="Time since ticket creation" tone="purple" />
        <Metric label="Simulated sends" value={data.simulated_sends} note="Replies recorded as sent" tone="green" />
      </section>

      <section className="card flow-card">
        <div className="section-heading"><div><p className="eyebrow">LIVE CONTROL MAP</p><h2>Ticket flow</h2></div><div className="graph-live"><i className={!error && (data.by_status.processing ?? 0) ? "is-busy" : ""} />{error ? "Last known data" : (data.by_status.processing ?? 0) ? `${data.by_status.processing} processing` : "Flow idle"}<span>· {updatedAt ? `Updated ${updatedAt.toLocaleTimeString()}` : "Waiting for update"}</span></div></div>
        <div className={`flow-summary${!error && (data.by_status.processing ?? 0) > 0 ? " is-active" : ""}`} aria-label="Ticket flow overview">
          <div className="flow-step"><small>01 · INTAKE</small><b>Receive</b><span>Incoming tickets</span></div><span className="flow-connector" aria-hidden="true"><i /></span>
          <div className="flow-step"><small>02 · ROUTING</small><b>Qualify &amp; route</b><span>Rules and model</span></div><span className="flow-connector" aria-hidden="true"><i /></span>
          <div className="flow-step"><small>03 · PREPARATION</small><b>Gather &amp; draft</b><span>Evidence and reply</span></div><span className="flow-connector" aria-hidden="true"><i /></span>
          <div className="flow-step human"><small>04 · HUMAN REVIEW</small><b>Review &amp; decide</b><span>Agent control</span></div><span className="flow-connector" aria-hidden="true"><i /></span>
          <div className="flow-step"><small>05 · OUTCOME</small><b>Resolve</b><span>Send or close</span></div>
        </div>
        <div className="queue-shortcuts" aria-label="Human and error queues">
          <a href="#workspace/re-routing"><span><b>Re-routing</b><small>Unclear assignments</small></span><strong>{data.queues["re-router"] ?? 0}</strong><em>Open queue →</em></a>
          <a href="#workspace/review"><span><b>Ticket review</b><small>Human review</small></span><strong>{data.queues.validator ?? 0}</strong><em>Open queue →</em></a>
          <a className="errors" href="#workspace/errors"><span><b>Flow errors</b><small>Operational attention</small></span><strong>{data.queues.errors ?? 0}</strong><em>Investigate →</em></a>
        </div>
        <p className="flow-caption">Movement indicates overall processing activity; it does not represent individual tickets.</p>
        <details className="flow-details"><summary>View detailed workflow</summary><FlowGraph data={error ? {...data, by_status: {...data.by_status, processing: 0}} : data} /></details>
      </section>
      <details className="dashboard-details"><summary>More metrics and demo tools</summary>
      <section className="dashboard-bottom">
        <article className="card status-card">
          <div className="section-heading"><div><p className="eyebrow">WORKLOAD</p><h2>Tickets by status</h2></div><span className="subtle">{data.total} total</span></div>
          <div className="send-disposition-summary" aria-label="Ticket resolution outcomes">
            <span><b>{data.send_dispositions.leave_open}</b> sent · left open</span>
            <span><b>{data.send_dispositions.close}</b> sent · closed</span>
            <span><b>{data.send_dispositions.closed_without_reply}</b> closed without reply</span>
          </div>
          {Object.keys(data.by_status).length ? <ul className="status-list">
            {Object.entries(data.by_status).sort((a, b) => b[1] - a[1]).map(([status, count]) => <li key={status}>
              <span className={`status-dot dot-${status}`} /><span className="status-name">{STATUS_LABEL[status] ?? humanize(status)}</span><b>{count}</b>
              <span className="bar-track"><i style={{ width: `${data.total ? Math.max(2, (count / data.total) * 100) : 0}%` }} /></span>
            </li>)}
          </ul> : <EmptyState title="No tickets yet" detail="Incoming work will appear here." />}
        </article>
        <article className="card ratios-card">
          <div className="section-heading"><div><p className="eyebrow">WORKLOAD SIGNAL</p><h2>Human queue rate</h2></div></div>
          <ReviewRatio ratio={data.ratios.human_review_rate} />
          <p className="helper">Open tickets in agent and send queues, out of all tickets received. This is a workload indicator, not a model quality score.</p>
          <a className="inline-link" href="#workspace/review">Open ticket review <span aria-hidden="true">→</span></a>
        </article>
        <details className="card inject-card"><summary><span><b>Inject a synthetic ticket</b><small>For local flow demos</small></span><span className="expand-icon">＋</span></summary>
          <TicketForm onSubmitted={() => setRefresh((value) => value + 1)} />
        </details>
      </section>
      </details>
    </>}
  </section>;
}

function QueueWorkspace({ name, title }: { name: QueueName; title: string }) {
  const [items, setItems] = useState<TicketSnapshot[]>([]);
  const [pageCursors, setPageCursors] = useState<(string | null)[]>([null]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const load = useCallback(async () => {
    try {
      const pages = await Promise.all(pageCursors.map((cursor) => getQueue(name, cursor)));
      setItems(pages.flatMap((page) => page.items)); setNextCursor(pages.at(-1)?.next_cursor ?? null); setError("");
    } catch (reason) { setError((reason as Error).message); }
    finally { setLoading(false); }
  }, [name, pageCursors]);
  const loadMore = async () => {
    if (!nextCursor) return;
    try {
      const cursor = nextCursor;
      const page = await getQueue(name, cursor);
      setItems((previous) => [...previous, ...page.items]); setPageCursors((previous) => [...previous, cursor]);
      setNextCursor(page.next_cursor); setError("");
    } catch (reason) { setError((reason as Error).message); }
  };
  useEffect(() => {
    void load(); const timer = window.setInterval(() => { void load(); }, 5000);
    return () => window.clearInterval(timer);
  }, [load, refresh]);

  const selected = useMemo(() => items.find((item) => `${item.ticket_id}:${item.turn}` === selectedKey) ?? items[0] ?? null, [items, selectedKey]);
  const visibleItems = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    if (!term) return items;
    return items.filter((item) => [item.ticket_id, item.ticket.subject, item.ticket.body, item.status, item.desk, item.priority]
      .some((value) => value?.toLocaleLowerCase().includes(term)));
  }, [items, query]);

  useEffect(() => {
    if (!selected) return;
    let live = true;
    const update = () => getTicket(selected.ticket_id, selected.turn).then((snapshot) => {
      if (live) setItems((previous) => previous.map((item) => item.ticket_id === snapshot.ticket_id && item.turn === snapshot.turn ? snapshot : item));
    }).catch((reason: Error) => { if (live) setError(reason.message); });
    void update(); const timer = window.setInterval(update, 3000);
    return () => { live = false; window.clearInterval(timer); };
  }, [selected?.ticket_id, selected?.turn]);

  return <section className="queue-page">
    <div className="queue-toolbar"><span>{items.length} ticket{items.length === 1 ? "" : "s"} loaded{nextCursor ? " · more available" : ""}</span><button className="button button-quiet" onClick={() => setRefresh((value) => value + 1)}>↻ <span>Refresh</span></button></div>
    {error && <Notice>Could not load queue: {error}</Notice>}
    <div className="workbench">
      <aside className="inbox card" aria-label={`${title} tickets`}>
        <div className="inbox-heading"><div><h2>Waiting tickets</h2><span>{visibleItems.length}{visibleItems.length !== items.length ? ` of ${items.length}` : ""}</span></div><span className="auto-refresh" title="Updates automatically">●</span></div>
        <label className="search-box"><span className="sr-only">Search tickets</span><span aria-hidden="true">⌕</span><input type="search" placeholder="Search ID, subject, desk…" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
        <div className="inbox-items">
          {visibleItems.map((item) => {
            const key = `${item.ticket_id}:${item.turn}`;
            const isSelected = selected?.ticket_id === item.ticket_id && selected.turn === item.turn;
            return <button className={`inbox-item ${isSelected ? "selected" : ""}`} key={key} onClick={() => setSelectedKey(key)} aria-pressed={isSelected}>
              <div className="inbox-item-line"><b>{item.ticket_id}</b><StatusBadge status={item.status} /></div>
              <span className="inbox-subject">{item.ticket.subject || item.ticket.body.slice(0, 72) || "No subject"}</span>
              <span className="inbox-meta">{item.desk ? humanize(item.desk) : "Desk unassigned"}<span>·</span>{item.priority ? humanize(item.priority) : "Priority unknown"}</span>
            </button>;
          })}
          {!visibleItems.length && <EmptyState title={query ? "No matching tickets" : loading ? "Loading queue…" : "Queue is clear"} detail={query ? "Try another ticket ID, subject or desk." : loading ? "Fetching the latest work." : "No tickets currently need attention here."} />}
        </div>
        {nextCursor && <button className="button button-quiet load-more" onClick={() => void loadMore()}>Load more tickets</button>}
      </aside>
      {selected ? <TicketWorkbench key={`${selected.ticket_id}:${selected.turn}`} ticket={selected} onChanged={() => setRefresh((value) => value + 1)} />
        : <div className="ticket-empty card"><EmptyState title="Select a ticket" detail="Choose an item from the queue to review its message and flow context." /></div>}
    </div>
  </section>;
}

function TicketWorkbench({ ticket, onChanged }: { ticket: TicketSnapshot; onChanged: () => void }) {
  const [actor, setActor] = useState("local-reviewer");
  const [text, setText] = useState(ticket.final_text ?? currentDraft(ticket)?.text ?? "");
  const [reason, setReason] = useState("");
  const [desk, setDesk] = useState(ticket.desk ?? "payments");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [sendDisposition, setSendDisposition] = useState<"leave_open" | "close" | null>(null);
  const actions = ticket.status === "error" ? [] : ticket.allowed_actions;
  const draft = currentDraft(ticket);
  const canWrite = actions.includes("edit_draft") || actions.includes("write_reply");
  const originalReply = ticket.final_text ?? draft?.text ?? "";
  const hasUnsavedEdit = canWrite && text !== originalReply;
  const runAction = async (action: Record<string, unknown>) => {
    setBusy(true); setMessage("");
    try { const result = await submitAction(ticket, { ...action, actor: actor.trim() }); setMessage(`Action accepted · ${STATUS_LABEL[result.status] ?? humanize(result.status)}`); onChanged(); }
    catch (reason) { setMessage(`Action failed: ${(reason as Error).message}`); }
    finally { setBusy(false); }
  };
  const send = async () => {
    if (!sendDisposition) return;
    setBusy(true); setMessage("");
    try { const result = await submitSend(ticket, actor.trim(), sendDisposition); setMessage(`Send accepted · ${STATUS_LABEL[result.status] ?? humanize(result.status)}`); onChanged(); }
    catch (reason) { setMessage(`Send failed: ${(reason as Error).message}`); }
    finally { setBusy(false); }
  };

  return <div className="ticket-columns">
    <article className="ticket-main card">
      <div className="ticket-heading"><div><div className="ticket-kicker">TICKET <span>·</span> TURN {ticket.turn}</div><h2>{ticket.ticket.subject || "Incoming support request"}</h2></div><StatusBadge status={ticket.status} /></div>
      {actions.length > 0 && <div className="action-required"><span className="action-required-icon" aria-hidden="true">!</span><div><b>Human action required</b><span>{ticket.status === "awaiting_validation" ? "Review the draft and choose how to proceed." : ticket.status === "awaiting_reroute" ? "Confirm the right desk or write a direct reply." : ticket.status === "ready_to_send" ? "The reply is approved. Confirm the simulated send." : "Review the case and choose an allowed next step."}</span></div><span className="human-owner">AGENT</span></div>}
      <Mailbox merchantId={ticket.ticket.merchant_id} currentTicketId={ticket.ticket_id} />
      <div className="message-block"><div className="message-byline"><b>{ticket.ticket.merchant_id}</b><span>{humanize(ticket.ticket.channel)}</span><time>{formatDate(ticket.ticket.created_at)}</time></div><p>{ticket.ticket.body}</p></div>
      {ticket.error_code && <Notice>Flow stopped: <b>{humanize(ticket.error_code)}</b></Notice>}
      <div className="draft-section">
        <div className="draft-heading"><div><p className="eyebrow">REPLY DRAFT</p><h3>{draft ? `Draft v${draft.version}` : ticket.final_text ? "Final reply" : "Write a reply"}</h3></div>
          {draft && <span className={`policy-pill ${draft.blocked ? "blocked" : "clear"}`}>{draft.blocked ? "Needs attention" : "Draft ready"}</span>}
        </div>
        {draft?.blocked && <Notice>This draft is blocked by a policy check. Review the findings in the ticket context before proceeding.</Notice>}
        {hasUnsavedEdit && actions.includes("approve") && <p className="unsaved-note">You have unsaved edits. Save them before approving this reply.</p>}
        <textarea aria-label="Reply draft" className="reply-editor" value={text} onChange={(event) => setText(event.target.value)} disabled={busy || !canWrite} placeholder={canWrite ? "Write a clear, helpful reply…" : "No reply is available for this ticket."} />
        {!canWrite && <p className="helper">The current status does not allow editing this reply.</p>}
        <div className="action-fields">
          {actions.includes("reroute") && <label>Assign to desk<select value={desk} onChange={(event) => setDesk(event.target.value)}><option value="payments">Payments</option><option value="disputes">Disputes</option><option value="technical_api">Technical API</option><option value="compliance">Compliance</option></select></label>}
          {(actions.includes("handoff_to_rerouter") || actions.includes("reroute") || actions.includes("close_manual")) && <label>Reason for action<input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Add a short reason…" /></label>}
          <label className="actor-field">Reviewed by<input value={actor} onChange={(event) => setActor(event.target.value)} /></label>
        </div>
        {actions.includes("send") && <fieldset className="send-disposition-choice">
          <legend>After sending, this ticket will</legend>
          <label className={sendDisposition === "leave_open" ? "is-selected" : ""}><input type="radio" name={`send-disposition-${ticket.ticket_id}-${ticket.turn}`} value="leave_open" checked={sendDisposition === "leave_open"} disabled={busy} onChange={() => setSendDisposition("leave_open")} /><span><b>Stay open</b><small>Keep the conversation active for a follow-up.</small></span></label>
          <label className={sendDisposition === "close" ? "is-selected" : ""}><input type="radio" name={`send-disposition-${ticket.ticket_id}-${ticket.turn}`} value="close" checked={sendDisposition === "close"} disabled={busy} onChange={() => setSendDisposition("close")} /><span><b>Close</b><small>Mark this ticket resolved after sending.</small></span></label>
        </fieldset>}
        <div className="action-buttons">
          {actions.includes("approve") && <button className="button button-approve" disabled={busy || !actor.trim() || hasUnsavedEdit} onClick={() => void runAction({ action: "approve" })}>Approve reply</button>}
          {actions.includes("edit_draft") && <button className="button button-primary" disabled={busy || !text.trim() || !draft || !actor.trim()} onClick={() => void runAction({ action: "edit_draft", text, draft_version: draft?.version })}>Save changes</button>}
          {actions.includes("write_reply") && <button className="button button-primary" disabled={busy || !text.trim() || !actor.trim()} onClick={() => void runAction({ action: "write_reply", text })}>Save reply</button>}
          {actions.includes("handoff_to_rerouter") && <button className="button button-human" disabled={busy || !reason.trim() || !actor.trim()} onClick={() => void runAction({ action: "handoff_to_rerouter", reason })}>Send to re-routing</button>}
          {actions.includes("reroute") && <button className="button button-human" disabled={busy || !reason.trim() || !actor.trim()} onClick={() => void runAction({ action: "reroute", desk, reason })}>Assign ticket</button>}
          {actions.includes("close_manual") && <button className="button button-quiet" disabled={busy || !reason.trim() || !actor.trim()} onClick={() => void runAction({ action: "close_manual", reason })}>Close manually</button>}
          {actions.includes("send") && <button className="button button-approve" disabled={busy || !actor.trim() || !sendDisposition} onClick={() => void send()}>{sendDisposition === "close" ? "Send & close" : sendDisposition === "leave_open" ? "Send & leave open" : "Choose ticket outcome"}</button>}
        </div>
        {message && <Notice role="status">{message}</Notice>}
        {!actions.length && !ticket.error_code && <p className="helper">There are no agent actions available for this ticket right now.</p>}
      </div>
    </article>
    <TicketContext ticket={ticket} />
  </div>;
}

function TicketContext({ ticket }: { ticket: TicketSnapshot }) {
  return <aside className="ticket-context">
    <section className="card context-card"><div className="section-heading"><div><p className="eyebrow">TICKET CONTEXT</p><h2>At a glance</h2></div></div>
      <dl className="context-grid"><ContextValue label="Merchant" value={ticket.ticket.merchant_id} /><ContextValue label="Desk" value={ticket.desk ? humanize(ticket.desk) : "Unassigned"} /><ContextValue label="Priority" value={ticket.priority ? humanize(ticket.priority) : "Unknown"} /><ContextValue label="Current step" value={ticket.current_node ? humanize(ticket.current_node) : "Agent review"} /><ContextValue label="Qualifier" value={ticket.qualifier?.status ? humanize(ticket.qualifier.status) : "Pending"} /><ContextValue label="Version" value={`v${ticket.version}`} /></dl>
      {ticket.reason_codes?.length ? <div className="context-subsection"><h3>Routing signals</h3><div className="chip-list">{ticket.reason_codes.map((code) => <span className="chip" key={code}>{humanize(code)}</span>)}</div></div> : null}
    </section>
    <section className="card context-card"><div className="section-heading"><div><p className="eyebrow">EVIDENCE</p><h2>Sources & checks</h2></div></div>
      {ticket.evidence ? <><div className="evidence-mode">{humanize(ticket.evidence.mode)} mode</div>
        {ticket.evidence.source_ids.length ? <ul className="source-list">{ticket.evidence.source_ids.map((source) => <li key={source}><span className="source-icon">↗</span><span>{source}</span></li>)}</ul> : <p className="helper">No source selected for this reply.</p>}
        {ticket.evidence.facts.map((fact) => <div className="fact-row" key={`${fact.source_id}:${fact.field}`}><b>{humanize(fact.field)}</b><span>{fact.value}</span><small>{fact.source_id} · {fact.source_version}</small></div>)}
      </> : <p className="helper">Evidence details will appear when the flow has prepared the ticket context.</p>}
      <PolicyCheck title="Draft quality & policy" check={ticket.policy_check} />
      <PolicyCheck title="Final reply check" check={ticket.final_policy_check} />
    </section>
    {ticket.prior_turns?.length ? <section className="card context-card"><div className="section-heading"><div><p className="eyebrow">CONVERSATION</p><h2>Previous turns</h2></div></div>
      <ol className="draft-history">{[...ticket.prior_turns].reverse().map((turn) => <li key={turn.turn}><span className="timeline-dot" /><div><b>Turn {turn.turn} · {humanize(turn.status)}</b><span>{turn.ticket.subject || turn.ticket.body.slice(0, 110)}</span>{turn.run?.final_text && <small>Reply: {turn.run.final_text.slice(0, 160)}{turn.run.final_text.length > 160 ? "…" : ""}</small>}</div></li>)}</ol>
    </section> : null}
    <section className="card context-card"><div className="section-heading"><div><p className="eyebrow">ACTIVITY</p><h2>Drafts & flow history</h2></div></div>
      {ticket.drafts?.length ? <ol className="draft-history">{[...ticket.drafts].reverse().map((draft) => <li key={draft.version}><span className="timeline-dot" /><div><b>Draft v{draft.version}</b><span>{draft.stale ? "Replaced" : "Current"}{draft.blocked ? " · blocked" : ""} · {humanize(draft.desk)}</span><small>{draft.source_ids.length ? `${draft.source_ids.length} evidence source${draft.source_ids.length === 1 ? "" : "s"}` : "No evidence source"}</small></div></li>)}</ol> : <p className="helper">No draft has been created yet.</p>}
      {ticket.human_actions?.length ? <><h3 className="activity-subheading">Human decisions</h3><ol className="draft-history">{[...ticket.human_actions].reverse().map((event, index) => <li key={`${event.action}:${event.created_at}:${index}`}><span className="timeline-dot" /><div><b>{event.action === "send" ? event.send_disposition === "close" ? "Sent · closed" : "Sent · left open" : event.action === "close" ? "Closed without reply" : humanize(event.action)}</b><span>{event.actor} · {formatDate(event.created_at)}</span>{event.reason && <small>{event.reason}</small>}</div></li>)}</ol></> : null}
      <details className="lifecycle"><summary>Node history <span>{ticket.events.length}</span></summary><ol>{ticket.events.map((event, index) => <li key={`${event.node_id}:${index}`}><b>{humanize(event.node_id)}</b><span>{humanize(event.status)}{event.duration_ms != null ? ` · ${event.duration_ms} ms` : ""}</span>{event.safe_error_code && <small>{humanize(event.safe_error_code)}</small>}</li>)}</ol></details>
    </section>
  </aside>;
}

function TicketForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [ticketId, setTicketId] = useState(""); const [merchantId, setMerchantId] = useState("");
  const [subject, setSubject] = useState(""); const [body, setBody] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    try {
      const result = await submitTicket({ ticket_id: ticketId.trim(), merchant_id: merchantId.trim(), subject: subject.trim() || null, body: body.trim(), created_at: new Date().toISOString(), turn: 1, channel: "formal_email", attachments: [] });
      setMessage(`Accepted ${result.ticket_id} · ${STATUS_LABEL[result.status] ?? humanize(result.status)}`); setTicketId(""); setSubject(""); setBody(""); onSubmitted();
    } catch (reason) { setMessage(`Could not submit: ${(reason as Error).message}`); }
    finally { setBusy(false); }
  }
  return <form className="ticket-form" onSubmit={submit}>
    <label>Ticket ID<input required value={ticketId} onChange={(event) => setTicketId(event.target.value)} /></label>
    <label>Merchant ID<input required value={merchantId} onChange={(event) => setMerchantId(event.target.value)} /></label>
    <label>Subject<input value={subject} onChange={(event) => setSubject(event.target.value)} /></label>
    <label>Message<textarea required rows={3} value={body} onChange={(event) => setBody(event.target.value)} /></label>
    <button className="button button-primary" disabled={busy || !ticketId.trim() || !merchantId.trim() || !body.trim()}>{busy ? "Submitting…" : "Submit ticket"}</button>
    {message && <p role="status">{message}</p>}
  </form>;
}

function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}
function Metric({ label, value, note, tone }: { label: string; value: string | number; note: string; tone: string }) {
  return <article className="metric card"><span className={`metric-icon ${tone}`} aria-hidden="true">{tone === "amber" ? "◷" : tone === "purple" ? "⌛" : tone === "green" ? "✓" : "▦"}</span><span className="metric-label">{label}</span><b className="metric-value">{value}</b><span className="metric-note">{note}</span></article>;
}
function ReviewRatio({ ratio }: { ratio?: { numerator: number; denominator: number } }) {
  const numerator = ratio?.numerator ?? 0; const denominator = ratio?.denominator ?? 0;
  const percent = denominator ? Math.round(100 * numerator / denominator) : 0;
  return <div className="ratio-display"><div className="ratio-number">{percent}<small>%</small></div><div><b>{numerator} of {denominator}</b><span>tickets awaiting a human decision</span></div><div className="ratio-track"><i style={{ width: `${percent}%` }} /></div></div>;
}
function StatusBadge({ status }: { status: string }) { return <span className={`status-badge status-${status}`}><i />{STATUS_LABEL[status] ?? humanize(status)}</span>; }
function ContextValue({ label, value }: { label: string; value: string }) { return <div><dt>{label}</dt><dd>{value}</dd></div>; }
function PolicyCheck({ title, check }: { title: string; check?: { status: string; findings: string[] } | null }) {
  return <div className="policy-check"><div><b>{title}</b>{check ? <span className={`policy-pill ${check.status}`}>{humanize(check.status)}</span> : <span className="policy-pill pending">Pending</span>}</div>
    {check?.findings.length ? <ul>{check.findings.map((finding) => <li key={finding}>{humanize(finding)}</li>)}</ul> : check ? <small>No findings recorded.</small> : null}</div>;
}
function EmptyState({ title, detail }: { title: string; detail: string }) { return <div className="empty-state"><span aria-hidden="true">◇</span><b>{title}</b><p>{detail}</p></div>; }
function Notice({ children, role = "alert" }: { children: React.ReactNode; role?: "alert" | "status" }) { return <p className="notice" role={role}>{children}</p>; }
function Loading({ label }: { label: string }) { return <div className="loading card"><span className="spinner" />{label}</div>; }
function currentDraft(ticket: TicketSnapshot) { return [...(ticket.drafts ?? [])].reverse().find((draft) => !draft.stale) ?? null; }
function humanize(value: string) { return value.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
function duration(seconds: number) { if (seconds < 60) return `${Math.round(seconds)} sec`; if (seconds < 3600) return `${Math.round(seconds / 60)} min`; return `${Math.floor(seconds / 3600)} h ${Math.round((seconds % 3600) / 60)} min`; }
function formatDate(value: string) { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date); }
