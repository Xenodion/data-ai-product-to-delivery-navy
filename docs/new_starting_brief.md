# NAVY — starting brief for our adapted P2 (draft for team agreement)

**Status:** draft, 30 October 2026. Same level of detail as the P2 entry in the course proposals. It fixes the story and the starting numbers only: the flow, the guardrails, the sizing and the architecture come after we agree on this page.

**What we keep from P2:** a B2B payments fintech, an agent-assist copilot that drafts and never sends, a human who validates, L2.
**What we adapt:** the scale, the pain, the job, the metric, the trap. The numbers are our own orders of magnitude, not a rescaling of a course case; they are re-derived and sourced in the S2 sizing.

## Words we use (the course uses "agent" for two different things)

| Term | Means | Not to be confused with |
|---|---|---|
| **Support agent** | A Keelpay employee who handles tickets (the "agents" who "spend 40 % of their time reading" in the course) | an AI agent |
| **Copilot** | The system we specify: a model plus fixed rules plus a screen. It prepares the case and a draft and never sends. It is what the course's row "Agent's job" describes | a support agent; an AI agent |
| **Model** | The small fine-tuned language model inside the copilot: it reads the free-text message and returns a structured JSON | the copilot as a whole |
| **AI agent** (agentic) | A system that chooses its own steps and calls tools in a loop. We do not build one in the first version: the copilot follows fixed steps | support agent |
| **Desk** | One of the specialist teams a ticket is routed to (payments, disputes, technical, compliance) | the NAVY project team |
| **Merchant** | A Keelpay customer; the person who writes the ticket | |
| **NAVY team** | Us, the four students | |

## Keelpay · Agent-assist copilot for a B2B payments fintech

| | |
|---|---|
| **Company** | Keelpay: ~1,500 merchant customers (SMEs and mid-size, France and Belgium), ~20,000 tickets / month in French and English, mostly payment status, disputes, technical / API and compliance questions. |
| **Pain** | Tickets arrive as free text, mostly by email. Before a support agent can answer, they must work out what the message is about, find the payment it refers to, check what was said before and pass it to the right desk: about 45 % of handling time. Roughly 1 ticket in 7 first lands in the wrong desk and loses a hand-over. |
| **Copilot's job** | No customer-facing autonomy. Reads the message, structures the key facts (type of request, payment, amount, urgency), routes the ticket to a desk, pre-reads the matching transactions and drafts the reply. The support agent edits and sends. |
| **Trust level** | L2 throughout: a support agent validates every ticket and every reply. |
| **Primary metric** | Average handling time per ticket at constant quality (QA score). Counter-metric: share of urgent tickets that reach the wrong desk. |
| **The trap** | A misread message looks handled: an urgent ticket (dispute deadline, compliance hold) sits in the wrong desk, or a draft is built on the wrong payment. When unsure, the copilot must say so rather than guess. |
| **Innovative angle** | Anything the copilot cannot determine is marked `UNDEFINED` and left to the support agent, not guessed; the support agent can open any ticket and see what the copilot read. Our A/B alternates copilot-on and copilot-off weeks for the same support agents, not for tickets, because the ticket mix changes day to day. |

## Starting numbers

| Number | Value | Tag |
|---|---|---|
| Merchants | ~1,500 | assumption |
| Tickets a month | ~20,000 | assumption |
| Share of handling time spent understanding, finding the payment and routing, before the answer is written | ~45 % | assumption |
| Tickets first routed to the wrong desk | ~1 in 7 (≈ 15 %) | assumption |
| Languages | French, English | assumption |

Each number is an order of magnitude with a test (time a sample of tickets, count reassigned tickets in the helpdesk). Nothing is measured yet.

## To agree on before anything else

1. The glossary above.
2. The story: company, pain, job, trap, A/B angle.
3. The five starting numbers, or the ones you want to change.
4. Whether we keep the Keelpay name.
