# Flow v2: Desk Drafter (node 9)

The local Drafter uses the configured provider/model and one shared implementation with a fixed system instruction per desk. It receives only the finalized `EvidenceDecision`, not raw tool responses. The model cannot select tools.

| Evidence mode | Drafter behavior | Required output evidence |
|---|---|---|
| `factual` | Answer from the approved ledger and knowledge facts only | Citation `[source_id]` on every non-empty line; unknown citations or uncited lines fail the draft |
| `documentary` | Explain the approved desk procedure or policy only | Same citation check |
| `clarification` | Ask one concise question; do not imply a lookup succeeded or assert transaction/account facts | No factual source claim |
| `no_draft` | Do not call the model | Not applicable |

Prompts are desk-specific for payments, disputes, technical API, compliance and triage. Ticket text is delimited as untrusted input. Draft records retain their evidence mode, cited source IDs, source versions, model and prompt version. The existing policy check runs on the returned text; an LLM/provider/citation failure leaves the ticket at the Validator with its context and no draft.

The current tool tier returns `unavailable`, so factual and documentary generation has not been exercised by the local flow; only clarification drafts are reachable. Citation presence is checked deterministically, but citation correctness and semantic factuality still require reviewed evaluation cases and human review. This module does not establish a send authorization.
