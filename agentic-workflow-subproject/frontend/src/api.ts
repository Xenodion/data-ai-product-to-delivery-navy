export type QueueName = "re-router" | "validator" | "errors";

export type Draft = {
  version: number;
  text: string;
  desk: string;
  stale: boolean;
  blocked: boolean;
  source_ids: string[];
};

export type TicketSnapshot = {
  ticket_id: string;
  turn: number;
  flow_id: string;
  version: number;
  status: string;
  desk: string | null;
  priority: string | null;
  created_at: string;
  updated_at: string;
  error_code: string | null;
  ticket: {
    merchant_id: string;
    body: string;
    subject: string | null;
    channel: string;
    created_at: string;
  };
  prior_turns?: {
    turn: number;
    status: string;
    desk: string | null;
    priority: string | null;
    created_at: string;
    updated_at: string;
    ticket: { merchant_id: string; body: string; subject: string | null; channel: string; created_at: string };
    run?: { final_text?: string | null; status?: string } | null;
  }[];
  current_node: string | null;
  allowed_actions: string[];
  reason_codes?: string[];
  drafts?: Draft[];
  final_text?: string | null;
  send_disposition?: "leave_open" | "close" | null;
  send_receipt?: { send_key: string; disposition: "leave_open" | "close"; created_at: string } | null;
  human_actions?: { action: string; actor: string; reason?: string | null; send_disposition?: "leave_open" | "close" | null; created_at: string }[];
  qualifier?: { status: string; label?: Record<string, string> | null };
  evidence?: {
    mode: string;
    source_ids: string[];
    facts: { field: string; value: string; source_id: string; source_version: string }[];
  } | null;
  policy_check?: { status: string; findings: string[] } | null;
  final_policy_check?: { status: string; findings: string[] } | null;
  events: { node_id: string; status: string; duration_ms?: number | null; safe_error_code?: string | null }[];
};

export type QueuePage = { items: TicketSnapshot[]; count: number; next_cursor: string | null };
export type OverviewData = {
  total: number;
  by_status: Record<string, number>;
  queues: Record<string, number>;
  simulated_sends: number;
  send_dispositions: { leave_open: number; close: number; closed_without_reply: number };
  oldest_waiting_seconds: number;
  ratios: Record<string, { numerator: number; denominator: number }>;
};

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: { code?: string }; error?: { code?: string } } | null;
    const code = body?.detail?.code ?? body?.error?.code ?? `HTTP_${response.status}`;
    throw new Error(code);
  }
  return response.json() as Promise<T>;
}

export const getOverview = () => request<OverviewData>("/api/v1/overview");

export const getTicket = (ticketId: string, turn: number) =>
  request<TicketSnapshot>(`/api/v1/tickets/${encodeURIComponent(ticketId)}/turns/${turn}`);

export function getQueue(name: QueueName, cursor?: string | null): Promise<QueuePage> {
  const params = new URLSearchParams({ limit: "50" });
  if (cursor) params.set("cursor", cursor);
  return request<QueuePage>(`/api/v1/queues/${name}?${params}`);
}

export function submitTicket(ticket: {
  ticket_id: string;
  merchant_id: string;
  subject: string | null;
  body: string;
  created_at: string;
  turn: number;
  channel: "formal_email";
  attachments: [];
}): Promise<{ ticket_id: string; turn: number; flow_id: string; status: string }> {
  return request("/api/v1/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify(ticket),
  });
}

export function submitAction(
  ticket: TicketSnapshot,
  action: Record<string, unknown>,
): Promise<{ status: string; version: number }> {
  return request(`/api/v1/tickets/${encodeURIComponent(ticket.ticket_id)}/turns/${ticket.turn}/actions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
      "If-Match": String(ticket.version),
    },
    body: JSON.stringify(action),
  });
}

export function submitSend(
  ticket: TicketSnapshot,
  actor: string,
  disposition: "leave_open" | "close",
): Promise<{ status: string; version: number }> {
  return request(`/api/v1/tickets/${encodeURIComponent(ticket.ticket_id)}/turns/${ticket.turn}/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
      "If-Match": String(ticket.version),
    },
    body: JSON.stringify({ actor, disposition }),
  });
}

export type MailboxThread = {
  ticket_id: string;
  opened_at: string;
  channel: string;
  language: string;
  role: string;
  thread_state: "open_awaiting_agent" | "open_awaiting_merchant" | "closed";
  desk: string | null;
  resolution: string | null;
  subject: string;
  message_count: number;
  last_message_at: string;
  last_author: "merchant" | "agent";
  preview: string;
};

export type ThreadMessage = { turn_index: number; author_kind: "merchant" | "agent"; sent_at: string; body: string };
export type WorldThread = { ticket_id: string; merchant_id: string; subject: string; thread_state: string; messages: ThreadMessage[] };

export const getMerchantThreads = (merchantId: string) =>
  request<{ threads: MailboxThread[] }>(`/api/v1/merchants/${encodeURIComponent(merchantId)}/threads`);

export const getWorldThread = (ticketId: string) =>
  request<WorldThread>(`/api/v1/world/tickets/${encodeURIComponent(ticketId)}/thread`);
