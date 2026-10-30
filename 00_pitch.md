# 00 — Pitch: Keelpay request router (half a page, plus the details behind it)

> Same frame as P2 — a B2B payments fintech, a human who sends every reply. We redefine the agent's job and the company's scale. The P2 drafting copilot was sized in S2 and got a NO-GO at 12,000 tickets (`02_investment_memo.md`); that work stays in the history and becomes our Stage 2. Every number is tagged **assumption** (our fictional case, with a test), **analogy** (with its source) or **measured** (none yet).

**The company:** Keelpay, a B2B payments platform for European merchants: SEPA and card payouts, API integration, disputes.
- **2,500 merchants**, mostly SMEs, writing in French and English (assumption).
- **30,000 requests a month**, about 12 per merchant (assumption; same order as Paylio's 40,000, S2 slides p. 37).
- **~45 support agents** (analogy: Paylio's ratio of ~667 tickets per agent-month). Among them is a **triage desk of ~5 agents**.

**How a request travels today:**
- Every email or dashboard ticket lands in one shared inbox.
- The triage desk reads each message, works out what it is, and moves it to one of four specialist queues: payments status, disputes, technical / API, compliance.
- Only then does the specialist in charge start the actual work: finding the merchant's account and the transaction, then deciding and replying.

**The pain, as a cost:**
- **Triage by hand:** 30,000 × 1.5 min ≈ 750 h a month ≈ 4.7 FTE ≈ **€211k a year**, at €45k per agent and 160 h a month. The 1.5 min is an assumption; test it by timing 20–30 tickets at the desk.
- **Misroutes:** 12 % of requests reach the wrong queue (assumption), and each costs ~4 min more (≈ 1.5 FTE ≈ **€68k a year**). Test: count reassigned tickets in the helpdesk.
- **Time-critical misses:** about 1 % of requests are time-critical (300 a month): disputes with a deadline, compliance holds. When one waits in the wrong queue, the deadline can pass. Cost ≈ €250–300 each (analogy: Mastercard 2025, $128 per chargeback plus the disputed amount).
- **Total:** routing costs **≈ €279k a year**, before the time-critical misses.

**Do-nothing baseline:**
- In 12 months, volume grows about 15 % and agents get about 5 % faster on their own (same assumptions as `01` §7).
- Routing then costs ≈ €279k × 1.15 × 0.95 ≈ **€305k a year**. The triage desk needs about 0.6 extra FTE just to keep up.
- Time-critical requests are still caught only when someone happens to read them in time.

**The agent's job:** When a merchant request arrives (email or dashboard), the agent reads it and fills a strict JSON. The fields are `queue`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency` and `confidence`; a field it cannot determine is `UNDEFINED`. A routing table in code then moves the request to the right queue. The agent also prepares a **case card** for the specialist in charge.

**It does not replace the person in charge.**
- **The specialist:** still owns the request, checks the case card, decides and replies.
- **The triage desk:** is moved to the specialist queues, where it absorbs the 15 % growth. Nobody is let go.
- **What the agent removes:** reading a message to work out what it is, and searching for the account and the transaction.

**Queues and sub-categories** (draft, to confirm):

| Queue (desk) | `sub_intent` examples |
|---|---|
| Payments status | payout delayed, payout missing, credit not received |
| Disputes (*litiges*) | chargeback, contested fee, unauthorised debit |
| Compliance | KYC blocking, account restriction, PSD2 / strong authentication |
| Technical / API | webhook, error code, integration |
| `UNDEFINED` → human triage | unclear, several requests in one message, low confidence |

**The case card:**
- the extracted fields, each with the passage of the message it comes from;
- the lookups already run: merchant account, transaction status, linked disputes, KYC status;
- what the specialist must check before deciding.

**Trust level per step:**

| Step | Who | Trust level |
|---|---|---|
| Read the request and fill the JSON | Router model | **L3**: acts on its scope, a human audits a sample; one-click reroute by any agent |
| Map the JSON to a queue | Routing table in code, not the model | L3 |
| `UNDEFINED`, or low confidence on a time-critical class | Human triage | Human only |
| Prepare the case card | Agent | **L1**: shows evidence, suggests nothing. For disputes and KYC blocking: evidence only, no next step |
| Draft the reply | Stage 2, closed in year 1 | (L2 if reopened) |
| Reply, refund, release a payout, lift a KYC block | Specialist | Human only: the agent has no tool for these |

**One thing it must never do:** decide or act in the place of the person in charge. It reads, classifies and prepares. It never contacts a merchant and never touches money or an account.

**Why it is a product decision:**
- **Who decides:** the Head of Support has to decide whether a model may route every request.
- **The risk:** a time-critical request silently sitting in the wrong queue. It is rare and expensive, so recall on the dispute and compliance classes counts, not overall accuracy. Risk owner: **Head of Compliance** (`governance.md`).
- **Data:** messages hold account numbers and transaction references. Training data is synthetic; the model runs in our EU cloud project, or under a no-training, EU-region contract.
- **Which rung to build:** we build the cheapest that passes a test written in advance:
  1. a mandatory form field or rules (regex and keywords);
  2. classical ML;
  3. a prompted LLM;
  4. a fine-tuned small LLM.
- **What the model must beat:** the fine-tuned model is kept only if it beats the best cheaper rung on a held-out set. It must win on extracted-key accuracy and on time-critical recall, with at least 99 % valid JSON (`proposal_redefined_use_case.md` §5).
- **What sizing must include:** an adoption ramp by quarter, never 100 % in year 1.

## Checklist (all seven must be ticked)
- [x] A named company type, a ticket volume and a team size
- [x] A pain expressed as a cost
- [x] A do-nothing baseline
- [x] One job in one sentence
- [x] A trust level per step, at least one below L4
- [x] One thing it must never do
- [x] A real decision: someone must decide whether to ship it
