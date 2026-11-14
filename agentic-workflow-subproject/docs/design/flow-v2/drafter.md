# Flow v2: Desk Drafter (node 9)

The Drafter uses the configured provider and model (`drafter_model`) through one shared implementation and one prompt (`navy/drafter` in Langfuse, with a local fallback in `flow/drafter.py`). It receives only the finalized `EvidenceDecision`, not raw tool responses. The model cannot select tools.

## Output contract

The code, not the prompt, owns the output format (`flow/draft_render.py`). The model answers with one JSON object:

```json
{"language": "fr", "segments": [{"text": "…", "source_ids": ["kb_…"]}]}
```

It writes the body only. The code then:

1. removes wrapping quotes, a greeting prefix and a closing sign-off written by the model;
2. checks the segments: no placeholder or bracket, at most four segments, no first person singular, every cited source is one supplied, every `TX-` or `M-` reference comes from the ticket or the evidence, and a factual reply cites at least one source;
3. builds the reply: greeting, body and closing in the ticket language (`drafter_greeting`, `drafter_closing` in `config.toml`; en, fr, es, de, it);
4. runs the shared policy check (node 10) on the final text, inside the repair loop.

A rejected answer is sent back to the model once with the reason. If the second answer is also rejected, a clarification becomes a question written by the code (`model = "template"`, `drafter_fallback_question`), and any other mode ends with no draft and the reason code `DRAFT_REJECTED`. A provider failure stays `DRAFTER_UNAVAILABLE`. `Draft.attempts` records how many model calls a draft needed.

## Evidence modes

| Evidence mode | Drafter behavior | Evidence supplied |
|---|---|---|
| `factual` | State ledger facts as of the record date; follow the approved guidance | Ledger facts and approved guidance |
| `documentary` | Say the next step the guidance gives for the merchant; never claim a document or result exists | Approved guidance |
| `clarification` | Ask one concise question about what is missing; state no fact | Approved guidance when found (Text Search only, never the ledger), and the reason codes |
| `no_draft` | Do not call the model | None |

Approved policies carry two parts: internal steps for the support team, and a `Reply to the merchant:` part that says what to ask and what never to promise. The Drafter writes from the second part.

## Tickets a person answers

A ticket gets no draft (`HUMAN_ONLY_TOPIC`) when its sub-intent is in `human_only_sub_intents` (for example `account_hold`) or its text contains a word of `human_only_keywords` (complaint, regulator, legal threat, fraud, data-protection request, frozen funds, in several languages). A false match only costs a review.

## Safeguards

The policy check blocks figures that the evidence does not support, claims about the state of an account, promises of a refund or a price, and claims that a document exists or will be delivered. Ticket text is delimited as untrusted input. Draft records retain their evidence mode, cited source IDs, source versions, model, prompt name and prompt version. A person reviews every draft before anything is sent.

A cited source id proves that the reply names an approved source, not that every sentence matches it: the human Validator remains the final check on meaning.
