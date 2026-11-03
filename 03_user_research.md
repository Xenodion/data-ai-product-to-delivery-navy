# 03 — Design Feedback and Support Agent Journey

## Design frictions retained

| Design feedback | Product implication |
|---|---|
| A ticket without a reference can match several payments of the same amount. | Compare date, recipient, status, and provenance; do not preselect; request clarification when evidence is insufficient. |
| One screen mixes qualification with final reply review. | Separate workspaces and allow standard cases to go directly to review. |
| Ticket count alone does not show what to work on first. | Show time since receipt and wait in the current step; sort oldest first and label any urgent-first mode. |
| An abstract confidence score does not identify which fact needs checking. | Show a concrete reason, source passage, and expected action; do not invent percentages. |
| An unchanged reply may be sent without careful reading. | Require targeted confirmation of facts/sources; do not force cosmetic edits. |
| Requalification may make an earlier draft wrong. | Preserve versions, invalidate stale context, prepare once again, and require manual handling after a second desk change. |
| A resetting mock-up does not show continuous work. | Receive synthetic tickets into persistent queues, preserve edits, and retain backend history. |
| A decorative diagram cannot explain actual processing. | Drive Overview from events; clicking a human node opens an available task. |

These points motivate design choices; they are not AHT, QA, or financial measurements. Relevant roles are frontline Support Agents, support managers, and the demo operator.

## Changes retained in the brief

Separate qualification and final review; test a left-list/right-dossier layout as the starting hypothesis; offer candidates without guessing; expose sources and attention items; preserve human work; show actual flow and queues. The move from the V0 baseline to one future V1 follows the design decisions in the [workflow](docs/design/copilot-workflow.md).

## Conversation and usage-observation guide

Ask about past practice: the last ambiguous ticket, actual steps taken, payment search, consequence of a wrong desk, case recovery, and urgent-ticket process. Do not ask only whether someone “likes” the product.

Collect notes from three 20-minute conversations, including roles and context, distinguishing practitioners from classmates role-playing. Retain useful observations and their effect on decisions. Do not invent timings or participants to fill the guide.

## Interface validation tasks

1. Identify the payment in a ticket without a reference, or request clarification if evidence is insufficient.
2. Correct the desk, check what changes in context, and find the earlier draft in history.
3. Open a task from Overview, then continue despite new arrivals without losing the edit.
4. Send an unchanged draft after checking it and understand the confirmation; then compare an edited case.

For the main task, two participants think aloud without coaching. Record success, wrong choices, hesitation, help needed, source inspection, and observed duration. Task success is not an estimate of time saved against an unmeasured baseline.

## Open interface questions

Test the starting layout against a collapsible context panel or third column, plus badge comprehension, wait-time legibility, return to qualification, “Send and next” scope, and confirmation fatigue. Observation notes can update these choices; no success rate is claimed here. Implement only the selected design in the single V1 successor.
