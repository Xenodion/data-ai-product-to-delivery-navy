# 03 — Prototype and Demo Target

## Original V0 mock-up

The original V0 is a clickable static mock-up of the Keelpay support workspace. It uses synthetic tickets to show the inbox, ticket context, qualification information, payment candidates, source details, and human review actions.

- [Open the V0 mock-up](prototype/copilot_panel/index.html)
- [View the V0 screenshot](assets/prototype_K-24121.png)

![Original V0 mock-up showing ticket K-24121 and its payment candidates](assets/prototype_K-24121.png)

### Prompt used for the V0 mock-up

> A Keelpay support agent (B2B payments fintech, ~36,000 merchant tickets a month in French and English) on one of four desks: payments, disputes, technical / API, compliance. Job: get each ticket to the right desk and answer it on the right payment, without decoding a free-text message and hunting for the transaction by hand. Build a clickable mock of their helpdesk with four synthetic tickets (fictional merchants), one per path: routed automatically; payment not identifiable (French, amount in words, no reference); critical (forwarded chargeback with a deadline); UNDEFINED (several requests in one message).
>
> Three columns: the ticket queue with a routing badge per ticket; the ticket with the passages the copilot used underlined; the copilot side panel with (1) what the copilot read, as the JSON fields (intent, sub_intent, transaction_id, amount, currency, urgency, sentiment), each highlighting its source passage on hover; (2) the path taken through the flow; (3) the case card: merchant, transactions, linked disputes, last tickets, read-only; (4) the cited draft, editable, with numbered sources; (5) a one-click reroute; (6) a log. The copilot never sends: only the agent has a Send button. A switch turns the copilot off for one ticket.
>
> A decision table routes clear, non-critical tickets automatically (L3, sampled audit). UNDEFINED or low-confidence tickets go to human triage, nothing guessed. Critical tickets (dispute, deadline, high urgency) wait for a person to confirm the desk before any draft. Lookups are L1 (read-only, this merchant only); the draft is L2 (the agent approves every reply). A rerouted ticket is drafted again once; a second reroute goes to human triage. Use blue for what the system did and amber for what a person does, as in our flow figure.

This mock-up illustrates the interface and a sample interaction. It does not run live AI, connect to a backend, maintain a real queue, or send a merchant message. The product behavior and safeguards are defined in the [product specification](spec.md).

## V1 demo target

The planned V1 is one functional successor that implements the agreed workflow:

1. **Overview** shows synthetic ticket events and operational counts from the backend.
2. **Qualification & Routing** lets a Support Agent resolve only decisions that block safe preparation.
3. **Replies to Review** presents the draft, supporting facts and sources, history, editing, and a human-controlled simulated send.

The target flow uses a Python Demo Injector, Qualifier Model, deterministic Python Routing Node, synthetic Lookup and Retrieval, a Drafter Model, persistent backend state, and correlated Langfuse traces. Ticket messages remain in their authored languages. External drafting and traces are limited to non-critical synthetic demo data.

V1 is not implemented or deployed. Its detailed runtime and hosting choices remain in the [delivery roadmap](specs/roadmap.md).
