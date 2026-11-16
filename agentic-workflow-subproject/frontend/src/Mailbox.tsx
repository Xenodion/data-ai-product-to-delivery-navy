import { useEffect, useState } from "react";
import { getMerchantThreads, getWorldThread, type MailboxThread, type WorldThread } from "./api.ts";

const STATE_LABEL: Record<string, string> = {
  closed: "Closed", open_awaiting_merchant: "Waiting for merchant", open_awaiting_agent: "Waiting for agent",
};

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

/** The merchant's earlier conversations, like a mailbox. Hidden when the world database is not configured. */
export function Mailbox({ merchantId, currentTicketId }: { merchantId: string; currentTicketId: string }) {
  const [threads, setThreads] = useState<MailboxThread[] | null>(null);
  const [openId, setOpenId] = useState("");
  const [thread, setThread] = useState<WorldThread | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let live = true;
    getMerchantThreads(merchantId)
      .then((result) => { if (live) setThreads(result.threads.filter((item) => item.ticket_id !== currentTicketId)); })
      .catch(() => { if (live) setThreads(null); });
    return () => { live = false; };
  }, [merchantId, currentTicketId]);

  useEffect(() => {
    if (!openId) { setThread(null); return; }
    let live = true;
    setFailed(false);
    getWorldThread(openId).then((result) => { if (live) setThread(result); }).catch(() => { if (live) { setThread(null); setFailed(true); } });
    return () => { live = false; };
  }, [openId]);

  if (!threads?.length) return null;
  return <section className="mailbox" aria-label="Merchant conversation history">
    <div className="mailbox-heading"><p className="eyebrow">MERCHANT MAILBOX</p><h3>Earlier conversations <span className="tab-count">{threads.length}</span></h3></div>
    <ul className="mailbox-list">
      {threads.map((item) => {
        const isOpen = item.ticket_id === openId;
        return <li key={item.ticket_id} className={isOpen ? "open" : ""}>
          <button className="mailbox-row" aria-expanded={isOpen} onClick={() => setOpenId(isOpen ? "" : item.ticket_id)}>
            <span className={`mailbox-dot ${item.last_author}`} aria-hidden="true" />
            <span className="mailbox-subject">{item.subject || "No subject"}</span>
            <span className="mailbox-state">{STATE_LABEL[item.thread_state] ?? item.thread_state}</span>
            <time>{formatDate(item.last_message_at)}</time>
            <span className="mailbox-preview">{item.last_author === "agent" ? "Support: " : ""}{item.preview}</span>
            <span className="mailbox-count">{item.message_count} message{item.message_count === 1 ? "" : "s"}</span>
          </button>
          {isOpen && <div className="mailbox-thread">
            {failed && <p className="helper">This conversation could not be loaded.</p>}
            {thread?.messages.map((message) => <article key={message.turn_index} className={`mail-message from-${message.author_kind}`}>
              <div className="message-byline"><b>{message.author_kind === "agent" ? "Keelpay Support" : "Merchant"}</b><time>{formatDate(message.sent_at)}</time></div>
              <p>{message.body}</p>
            </article>)}
          </div>}
        </li>;
      })}
    </ul>
  </section>;
}
