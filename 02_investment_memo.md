# 02 — Investment memo (one page)

**Recommendation:** **CONDITIONAL GO, in two stages.** Ship now the rules-only ticket-to-transaction attach (stage 1). Build the router and the drafter (stage 2) only if the S4 gold-set experiment clears these bars together: the router (the fine-tuned model if it beats the prompted one) is at least 90 % right on the first pass with at least half of the tickets routed automatically, total time saved reaches about 13.5 % of handling time, and incremental serious errors stay at or below 0.1 % of tickets.

> Line one is the decision. Everything below is evidence for that line. Same base case as `02_sizing.xlsx`; the company, scale and constraint come from the frozen brief in the README. **The margin is thin and the memo says so (section 2).**

| €/year, year 1 | Pessimistic | Base | Optimistic | Expected value |
|---|---|---|---|---|
| Net annual value | −92,927 | +115,257 | +458,239 | **+121,398** |
| Probability | 0.30 | 0.50 | 0.20 | — |
| Do-nothing (value of the current process improving on its own) | 51,840 | 92,988 | 181,440 | 92,988 (the sheet compares with Base) |
| Next-best project: rules-only ticket-to-transaction attach, no AI (the hurdle) | 11,656 | 100,183 | 236,274 | 100,183 |

Steady state (Q4 adoption held for a full year, base): **+229,011 a year**. Year 1 carries the ramp-up.

## 1. How much?
**Bottom-up, base case, year 1.**
- **Volume and time saved:** 36,900 tickets a month on average over the year. The copilot saves 14.5 % of handling time at full adoption: 5.4 % from routing (15 % of time × 55 % of tickets routed automatically × 65 % cut) and 9.1 % from drafting (45 % of time × 22 % cut × 92 % of tickets correctly routed). Adoption averages 44 % over the year (15 % in Q1 to 70 % in Q4).
- **Value:** that is 28,033 ticket-equivalents at €7 of agent time each, **€196.2k gross**. Hand-overs avoided add **€36.5k** (misrouted tickets fall from 1 in 7 to 8 % on handled tickets, at €3 of queue delay each).
- **Costs:** wrong replies **−€41.4k** (incremental, priced against today's human error rate), tokens and retries −€1.8k, fixed costs **−€74k** (integration, training and security review €28k amortised, evaluation €10k, quality owner €18k, monitoring €12k, re-evaluation €6k). Net **+€115k**.

**Where the numbers come from.**
- **Given by the scenario** (treated as the company's logs, as the course template says): 2,500 merchants, ~36,000 tickets, the 15 % and 45 % time slices, 1 ticket in 7 misrouted, the data constraint.
- **Analogies:**
  - €5–15 per human ticket and €0.02–0.20 per AI conversation (S2 slides).
  - About −13 % time per issue (Brynjolfsson, Li & Raymond, QJE 2025).
  - $128 per chargeback (Mastercard 2025).
  - A CPU service that scales to zero at near-zero cost (our Museum Guide demo on Cloud Run).
- **Guesses to test:** everything else, each with its test in the sizing. The one that matters: **total time saved**, tested in S4 and measured in the S6 A/B.

## 2. How sure? — the verdict hangs on a few numbers
**Scenarios.** Weighted 30 / 50 / 20, the expected value is **+€121k**. The pessimistic case is a slow rollout with higher error rates and loses **€93k**; the optimistic case gains **€458k** and supplies most of the expected value.

**Flip points (base case, varying total time saved).**

| Total time saved | 10 % | 15 % | 20 % | 25 % | 30 % |
|---|---|---|---|---|---|
| Net value, year 1 | +€55k | +€122k | +€190k | +€258k | +€326k |

- The base case breaks even at about **7 % time saved**.
- It beats the next-best project and do-nothing from about **13.5 %**. The base case is 14.5 %, one point above, and the only published benchmark we have (about 13 % per issue, Brynjolfsson et al.) is slightly below it. **Our base case sits a little above the literature; the S4 and S6 measurements decide.**

**What else flips the label to NO-GO** (each tested on the workbook, everything else unchanged):
- **Volume.** The expected value stops clearing do-nothing and the next-best project below about **26,500 tickets a month** (about 11 per merchant). The 36,000 is a scenario choice, not a measurement.
- **Scenario weights.** Moving about 6 points of probability from the optimistic to the base case gives a NO-GO. The weights are our judgement and nothing tests them.
- **Fixed costs.** About €20k a year more flips it. We already added a €25k one-off for agent training, change management and the security and data-protection review after the final review.

**What the S4 prototype tests.**
- **Router:** the fine-tuned model against rules, classical ML and the prompted model, on first-pass accuracy, share routed automatically and urgent tickets sent to the wrong desk.
- **Hypotheses 2 and 4:** urgent tickets stay out of the wrong desk; seeded wrong readings are caught by the support agent.
- **Time saved:** measured on a sample, then in the S6 A/B.

## 3. What if we're wrong?
**Cost lines that dominate.** Not the model. Integration (€28k a year, amortised), the quality owner (€18k) and monitoring (€12k) dominate; hosting and tokens are under €5k a year.

**Cost of error, priced as a tail.**
- **Basis:** a wrong reading that a support agent does not catch costs about €150 on a payment question, €400 on a dispute and €300 on a technical or compliance question (guesses).
- **At the rates assumed:** about 0.075 % of tickets with an uncaught serious error (0.05–0.12 % by category), incremental to today, costs **€41k in year 1**, or **€54k** in the pessimistic case.
- **Safety nets:** `UNDEFINED` goes to a human; critical tickets (amount, urgency, dispute or compliance, deadline) need a human to confirm the desk before any draft; a misrouted ticket is rerouted and redrafted once, then goes to triage.
- **Not priced:** the money spent before the S4 gate (prototype, stage-1 work) is not in the pessimistic case. A rollout stopped at the gate loses that spend, not a full year of stage-2 costs.

**Governance line.** A wrong status, amount or deadline told to a merchant on a dispute or compliance question, and an urgent ticket left in the wrong desk, are **legal and reputational** risks: the merchant acts on it and can complain to the regulator. Owner: **Head of Compliance**. The Head of Support owns the routing rules, the thresholds and the switch back to "reading only" (`governance.md`, Session 2).

## 4. Compared to what?
**Do-nothing is not zero.** Agents get about 3 % faster a year, worth **€93k** at year-1 volume and cost. Volume also grows with the merchant base, so the cost of reading, routing, looking up and writing grows with it (problem statement, §7). The template compares it as a rival; the 3 % happens in both worlds, so we also read the project against zero (Decision tab, rows 41–43).

**Next-best project.** The same engineers can ship the rules-only attach: each ticket gets the merchant's recent transactions, open disputes and last tickets by merchant ID, date and amount.
- **Value:** about **€100k net a year** in the base case (6 % of handling time saved, 70 % adoption, €30k a year to run). It sits next to do-nothing (€93k) because both rest on a few percent of a €3.1M handling cost. To test it, observe 20 tickets.
- **Nothing is lost:** it is also the copilot's lookup layer, so stage 2 starts from it.

**Stage 2 as an increment on stage 1.** Stage 2 is worth the copilot minus the attach: **+€15k in the base case, +€21k in expected value, −€105k in the pessimistic case.** Part of the integration is shared with stage 1, so stage 2's own fixed cost is below the €74k shown; the sizing does not split it. Stage 2 is therefore not a safe bet on the sizing alone, which is why it is conditional on measurement.

**Does the pessimistic case clear the hurdle?** No: it loses €93k, against €12k earned by the next-best project in its own pessimistic case. That is why the decision is conditional.

## 5. Build, buy or orchestrate?
**We orchestrate**, because the edge is our ledger, dispute history and desk rules, and tickets must stay in our cloud (the data constraint): managed components in our own cloud (model hosting, retrieval) around our routing table and review screen. Weighted scores from the `Build or buy` tab: **Build 3.54 · Buy 3.00 · Orchestrate 3.66**. Build and Orchestrate are within the template's 0.3 margin, so the data constraint and the run burden decide.

**What would change our mind:** a vendor copilot that reads our ledger, runs inside our cloud tenancy and does not train on our data. We would buy it: about €25k a year for 46 seats at ~€45 a month, roughly €21k a year less than our build-specific costs.

*Sources:*
- `01_problem_statement.md` and `02_sizing.xlsx` (Inputs, Flow and Read options tabs).
- S2 slides: cost per human ticket, cost per AI conversation, do-nothing.
- Brynjolfsson, Li & Raymond, "Generative AI at Work", *QJE* 140(2), 2025.
- Mastercard, "What's the true cost of a chargeback in 2025?".
- Cloud Run per-second pricing and our Museum Guide deployment notes (`deploy/README.md`, free tier).
- Job postings for customer advisers in France (France Travail, Michael Page, 2026) — to re-source on the day.
