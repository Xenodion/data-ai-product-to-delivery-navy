# 03 — User Feedback and Design Hypotheses

## Feedback exercise

The following feedback was developed through a classroom role-play exercise to explore the product concept. The participants and quotations are simulated; they are not interview findings or evidence of measured user outcomes.

### Simulated participant feedback

**Support agent handling payment questions:** “When there is no payment reference, I need to see why those transactions are candidates. I would rather ask the merchant than send a confident answer based on a guess.”

**Support team lead managing a shared inbox:** “A single queue count does not tell me what is stuck. Show me how long a ticket has been waiting and let me open the oldest one that needs a person.”

**Support agent reviewing AI-assisted replies:** “If I change the desk, I want the reply to be prepared again for the new team. Keep the earlier version visible so I can understand what changed before I send anything.”

### Design implications

- Show payment candidates with distinguishing facts and sources; require clarification when evidence is insufficient.
- Make waiting time visible and provide an oldest-first path to eligible human tasks.
- Preserve draft history and invalidate dependent preparation after a desk correction.
- Keep human review and send confirmation explicit for every reply.

## Design hypotheses

| Hypothesis | Product implication to test |
|---|---|
| When a ticket has no payment reference, agents need to compare verified candidates before selecting one. | Show distinguishing facts and sources; never preselect an uncertain match. |
| Combining qualification and final reply review makes it harder to resolve a case efficiently. | Separate qualification from final review while allowing standard cases to proceed directly to review. |
| Ticket count alone does not help an agent decide what to handle first. | Show time since receipt and time in the current step; use oldest-first as the default. |
| A confidence score does not explain which fact needs attention. | Show a concrete reason, source passage, and next action. |
| Requalification can invalidate a prepared reply. | Preserve draft versions and require re-preparation after a desk correction. |
| New tickets can interrupt an agent's current work. | Keep the selected case and unsaved work stable as new tickets arrive. |

These hypotheses are consistent with the role-play feedback and remain to be checked during prototype evaluation.

## Follow-up validation

If practitioner access becomes available, conduct three 20-minute conversations about recent support work. Ask about the last ambiguous ticket, the steps taken to identify a payment, the consequence of a wrong desk, how the case was recovered, and how urgent tickets were handled. Focus on past behavior rather than asking whether someone likes or would use the proposed product.

Record participant role and context accurately. Keep any future practitioner observations separate from this simulated exercise.

## Prototype tasks

For a future usability session, ask two participants to think aloud while attempting these tasks, without coaching:

1. Identify a payment in a ticket without a reference, or request clarification when evidence is insufficient.
2. Correct the desk, inspect what changes, and find the prior draft in the history.
3. Open a task from Overview and continue working when new tickets arrive.
4. Review and send an unchanged draft, then explain the confirmation; compare with an edited draft.

Record task completion, wrong choices, hesitation, requests for help, source inspection, and observed duration. These observations describe the sessions only; they do not estimate time saved against an unmeasured baseline.

## Questions to resolve

Test whether a collapsible context panel or third column is easier to use. Observe badge comprehension, wait-time legibility, return to qualification, “Send and next” scope, and confirmation fatigue. Update the design from recorded evidence and keep future observations separate from this role-play feedback.
