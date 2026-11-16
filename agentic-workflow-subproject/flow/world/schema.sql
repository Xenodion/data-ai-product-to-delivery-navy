-- Merchant world schema (design: docs/design/flow-v2/world-schema-and-generation-plan.md, section 5).
-- Portable SQL: it runs unchanged on SQLite and PostgreSQL. Timestamps are ISO-8601 UTC text,
-- dates are ISO-8601 text, amounts are integers in minor units. Foreign keys must be enabled by the
-- connection (SQLite: PRAGMA foreign_keys = ON). One enumeration per line so that the tests can
-- compare each CHECK list with the matching Literal type of models.py.

CREATE TABLE merchants (
    merchant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sector TEXT NOT NULL CHECK (sector IN ('retail', 'saas', 'marketplace', 'education', 'logistics', 'hospitality', 'travel')),
    preferred_language TEXT NOT NULL CHECK (length(preferred_language) = 2),
    country TEXT NOT NULL CHECK (length(country) = 2),
    settlement_currency TEXT NOT NULL CHECK (length(settlement_currency) = 3),
    volume_tier TEXT NOT NULL CHECK (volume_tier IN ('small', 'medium', 'large')),
    plan TEXT NOT NULL,
    fee_bps INTEGER NOT NULL CHECK (fee_bps >= 0),
    kyc_status TEXT NOT NULL CHECK (kyc_status IN ('verified', 'pending', 'under_review')),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    onboarded_at TEXT NOT NULL
);

CREATE TABLE merchant_currencies (
    merchant_id TEXT NOT NULL REFERENCES merchants (merchant_id),
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    PRIMARY KEY (merchant_id, currency)
);

CREATE TABLE contacts (
    contact_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants (merchant_id),
    persona TEXT NOT NULL CHECK (persona IN ('small_shop_owner', 'accountant', 'developer', 'operations_manager', 'founder', 'compliance_officer')),
    language TEXT NOT NULL CHECK (length(language) = 2)
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants (merchant_id),
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    status TEXT NOT NULL CHECK (status IN ('settled', 'processing', 'under_review', 'failed', 'refunded', 'disputed')),
    payment_method TEXT NOT NULL,
    created_at TEXT NOT NULL,
    settled_at TEXT
);

CREATE TABLE refunds (
    refund_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES transactions (transaction_id),
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TEXT NOT NULL
);

CREATE TABLE disputes (
    dispute_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES transactions (transaction_id),
    status TEXT NOT NULL CHECK (status IN ('open', 'under_review', 'won', 'lost')),
    reason TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    CHECK (due_at > opened_at)
);

CREATE TABLE payouts (
    payout_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants (merchant_id),
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    currency TEXT NOT NULL CHECK (length(currency) = 3),
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'paid', 'held', 'failed')),
    scheduled_at TEXT NOT NULL,
    paid_at TEXT,
    held_reason TEXT
);

CREATE TABLE tickets (
    ticket_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants (merchant_id),
    contact_id TEXT NOT NULL REFERENCES contacts (contact_id),
    opened_at TEXT NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('formal_email', 'short_email', 'forwarded_thread', 'chat_message')),
    language TEXT NOT NULL CHECK (length(language) = 2),
    role TEXT NOT NULL CHECK (role IN ('current', 'history', 'dev')),
    thread_state TEXT NOT NULL CHECK (thread_state IN ('open_awaiting_agent', 'open_awaiting_merchant', 'closed')),
    -- V1 rules: current and dev tickets wait for the agent; history tickets are closed or wait for the merchant.
    CHECK (role = 'history' OR thread_state = 'open_awaiting_agent'),
    CHECK (role <> 'history' OR thread_state IN ('closed', 'open_awaiting_merchant'))
);

CREATE TABLE ticket_outcomes (
    ticket_id TEXT PRIMARY KEY REFERENCES tickets (ticket_id),
    desk TEXT NOT NULL CHECK (desk IN ('payments', 'disputes', 'technical_api', 'compliance', 'triage')),
    resolution TEXT NOT NULL,
    closed_at TEXT NOT NULL
);

-- turn_index is the position of the message inside its ticket (1 is the unchanged deck text); the
-- generation log calls it message_index.
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets (ticket_id),
    turn_index INTEGER NOT NULL CHECK (turn_index >= 1),
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    sent_at TEXT NOT NULL,
    body TEXT NOT NULL,
    author_kind TEXT NOT NULL CHECK (author_kind IN ('merchant', 'agent')),
    UNIQUE (ticket_id, turn_index),
    CHECK ((direction = 'inbound' AND author_kind = 'merchant') OR (direction = 'outbound' AND author_kind = 'agent'))
);

CREATE TABLE policies (
    source_id TEXT NOT NULL,
    version TEXT NOT NULL,
    desk TEXT NOT NULL CHECK (desk IN ('payments', 'disputes', 'technical_api', 'compliance')),
    language TEXT NOT NULL CHECK (length(language) = 2),
    status TEXT NOT NULL CHECK (status IN ('approved', 'draft', 'retired')),
    valid_from TEXT NOT NULL,
    valid_until TEXT,
    owner TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (source_id, version)
);

CREATE TABLE policy_sub_intents (
    source_id TEXT NOT NULL,
    version TEXT NOT NULL,
    sub_intent TEXT NOT NULL,
    PRIMARY KEY (source_id, version, sub_intent),
    FOREIGN KEY (source_id, version) REFERENCES policies (source_id, version)
);

CREATE INDEX idx_contacts_merchant ON contacts (merchant_id);
CREATE INDEX idx_transactions_merchant ON transactions (merchant_id, created_at);
CREATE INDEX idx_refunds_transaction ON refunds (transaction_id);
CREATE INDEX idx_disputes_transaction ON disputes (transaction_id);
CREATE INDEX idx_payouts_merchant ON payouts (merchant_id, scheduled_at);
CREATE INDEX idx_tickets_merchant ON tickets (merchant_id, opened_at);
CREATE INDEX idx_messages_ticket ON messages (ticket_id);
CREATE INDEX idx_policy_sub_intents_lookup ON policy_sub_intents (sub_intent);
