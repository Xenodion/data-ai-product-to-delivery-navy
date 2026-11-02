# 03 — User research · Keelpay agent-assist copilot

> **Method.** We could not hold the three user conversations before the deadline. Instead of inventing them, we replaced them with **desk research**: published studies, surveys and industry figures on support agents, AI assistance and misrouted tickets, each with its source and how much it can be trusted. This does **not** meet the "three conversations" rule, and the desirability gate says so. The **usability test** of the prototype is run with real people (teammates in role, said explicitly).

## Sources used instead of interviews
| # | Source | Type | How much we trust it |
|---|---|---|---|
| 1 | Brynjolfsson, Li & Raymond, "Generative AI at Work", *QJE* 140(2), 2025, pp. 889–942 — 5,172 customer-support agents at one company, staggered rollout of an AI assistant | peer-reviewed field study | high |
| 2 | Dell'Acqua et al., "Navigating the Jagged Technological Frontier" — 758 BCG consultants, randomised (HBS Working Paper 24-013, 2023) | field experiment | high; version to confirm |
| 3 | Parasuraman & Manzey, "Complacency and Bias in Human Use of Automation", *Human Factors* 52(3), 2010, pp. 381–410 | peer-reviewed review | high (read at abstract level) |
| 4 | Microsoft, contact-centre trial of Copilot for Service (CX Today, November 2023) | vendor-reported | medium |
| 5 | Zendesk, CX Trends 2026 — survey of 6,000+ consumers and 5,000 CX leaders and agents, 22 countries | vendor survey | medium |
| 6 | Mastercard with Javelin, "What's the true cost of a chargeback in 2025?" | industry research | medium |
| 7 | Chargeback time-limit guides (Chargebacks911, Chargeback Gurus) | vendor guides | low to medium |
| 8 | Ticket reassignment figures (HappySignals, BoldDesk, Infosys BPM case study) | vendor blogs, one case study | low |

## What the evidence says
| # | Finding | Which part of our brief it confirms or contradicts |
|---|---|---|
| 1 | AI assistance raised issues resolved per hour by **15 %** on average; the gain is concentrated on less experienced agents, with small quality declines for the most experienced. Assisted agents with two months of tenure performed like unassisted agents with more than six. Customers were more courteous and asked for a manager less often. | **Confirms** that agent-assist works in support, and the persona choice (new agents gain most). **Contradicts our sizing:** +15 % throughput ≈ **−13 % time per issue**, below the sizing's 20 % base case (issue #17). **Supports** reporting results by agent seniority (governance S1, question 6). |
| 4 | Microsoft reports **−12 %** average handling time in its own contact-centre trial; it cites 12–16 % for early customers. | **Same direction, same size** as source 1, and below our 20 % base. Vendor figure: an upper bound rather than a benchmark. |
| 2 | On tasks inside what the AI does well, consultants were faster and better; on a task built to be outside it, AI users were **19 percentage points less likely to be correct** than those without AI. | **Confirms the trap**: a confident answer on a hard ticket is worse than none. **Supports** `UNDEFINED` instead of a guess, triage for low confidence, and a gold set where at least a third are hard cases. |
| 3 | Automation complacency appears under multiple-task load, in experts as well as novices, and is not removed by practice; imperfect aids lead to both omission and commission errors. | **Confirms** the automation-bias risk on a busy queue: supports hypothesis 4 (seeded wrong readings), the counter-metric "drafts on the wrong payment validated unread", and showing each extracted field with its source passage. |
| 5 | **74 %** of consumers are frustrated when forced to repeat information, and 81 % want agents to continue the conversation without backtracking. | **Adds a cost** to a misroute that the sizing does not price: the merchant re-explaining after a hand-over (the sizing counts €3 of queue delay only). **Supports** the case card travelling with the ticket on a reroute. |
| 6 | A chargeback costs the merchant about **$128** in fees and internal costs, on an average disputed amount of $84–120. | **Confirms** the order of magnitude of a missed dispute (sizing: €400 per uncaught serious error on disputes, which also counts the relationship). |
| 7 | The card schemes give about 30 days (Visa) to 45 days (Mastercard) to answer a chargeback, but acquirers often give merchants only **5–10 days**; a missed deadline usually means the dispute is lost. | **Confirms** that disputes are time-critical and that a dispute ticket in the wrong desk can lose its window: supports the criticality rule (a person confirms the desk). |
| 8 | Vendors report **15–40 %** of manually routed tickets reassigned; one case study found about half of self-service tickets reassigned, pushing lead time above 40 hours. | **Suggests our given 1 in 7 (≈ 14 %) is conservative.** Weak evidence (vendors, conflicting figures): not used in the sizing. |

**What the evidence changes for v2 (#12):** the base case of the time saved should be argued against the 12–15 % published range, not above it, or the gap justified; the cost of a misroute should mention the merchant repeating themselves; the evaluation should report by agent seniority and on hard tickets separately.

## Usability test — one task, think aloud, don't help
**Prototype link:** `prototype/copilot_panel/index.html` (see `03_prototype_link.md`) · **Task given:** "Ticket #K-24121 came in this morning. Check what the copilot understood, choose the payment the merchant means, and get a reply ready to send."
**Run with two people in role (teammates, said explicitly), 5 minutes each.** Write what you saw, not what they said they would do.

| Tester | Finished without help? (yes / no) | Where they hesitated | What they expected instead |
|---|---|---|---|
| ⟨teammate 1, in role⟩ | | | |
| ⟨teammate 2, in role⟩ | | | |

## Desirability gate — do they want it?
- [ ] 2 of 2 finished the task without help — *to fill after the test*
- [ ] They told us what they did last time, not what they would do — **not met: no user conversation; replaced by desk research**
- [ ] At least one said "I want this before…" — **not met: no user conversation**
- [ ] Our out-of-scope list grew; our success criterion did not move — *the success criterion did not move; the evidence questions the sizing's time-saved base case (#17)*

**Decision:** go to the S4 build. The desk research confirms the problem, the trap and the human-in-the-loop design; it questions the size of the gain. Real conversations with support agents remain the first thing to do before claiming user validation.

## Sources
- [Brynjolfsson, Li & Raymond, QJE 2025 (EconPapers record)](https://econpapers.repec.org/RePEc:oup:qjecon:v:140:y:2025:i:2:p:889-942.)
- [Dell'Acqua et al., jagged frontier (summary with figures)](https://businessdatasolutions.github.io/ai-wiki/sources/2026-04-28-dellacqua-jagged-technological-frontier)
- [Parasuraman & Manzey, Human Factors 2010 (PubMed)](https://pubmed.ncbi.nlm.nih.gov/21077562/)
- [CX Today, Copilot cuts average handling time by 12 percent](https://www.cxtoday.com/wfo/copilot-cuts-average-handling-time-by-12-percent-claims-microsoft/)
- [Zendesk CX Trends 2026, global report (PDF)](https://cxtrends.zendesk.com/uploads/pdfs/gb/CXTrends2026_Global_GB.pdf)
- [Mastercard, true cost of a chargeback in 2025](https://b2b.mastercard.com/news-and-insights/blog/what-s-the-true-cost-of-a-chargeback-in-2025)
- [Chargebacks911, chargeback response time limits](https://chargebacks911.com/chargeback-rules/chargeback-time-limits/chargeback-response-time-limit/) · [Chargeback Gurus, chargeback time limits](https://www.chargebackgurus.com/blog/dont-run-out-the-clock-understanding-chargeback-time-limits)
- [HappySignals, bounced ticket levels](https://www.happysignals.com/blog/how-to-solve-the-issue-of-high-it-service-desk-bounced-ticket-levels) · [BoldDesk, reducing ticket reassignments](https://www.bolddesk.com/blogs/reduce-ticket-reassignments-webinar/amp) · [Infosys BPM case study (PDF)](https://www.infosysbpm.com/offerings/functions/customer-service-outsourcing/case-studies/documents/the-helpdesk-is-crying-out-for-help.pdf)
