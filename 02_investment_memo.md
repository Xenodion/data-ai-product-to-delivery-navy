> **STALE — do not use or cite.** This memo belongs to the superseded case (800 merchants, 12,000 tickets, LLM drafting only, NO-GO). It is rewritten from the frozen brief (see README) after the sizing is rebuilt bottom-up. Kept for its structure and reusable sources.

# 02 — Investment memo (one page)

**Recommendation:** **NO-GO** on building the LLM reply copilot at Keelpay's current scale. Ship the rule-only ticket-to-transaction auto-attach first. Reopen the copilot only if its unsized benefits can be shown to be worth about €100k a year.

> Line one is the decision. Everything below is evidence for that line. Same base case as `02_sizing.xlsx`.

| €/year, year 1 | Pessimistic | Base | Optimistic | Expected value |
|---|---|---|---|---|
| Net annual value | −142,507 | −55,389 | +31,780 | **−64,091** |
| Probability | 0.30 | 0.50 | 0.20 | — |
| Do-nothing (value of the current process improving on its own) | 25,272 | 33,840 | 45,540 | 33,840 (the sheet compares with Base) |
| Next-best project: rule-only ticket-to-transaction auto-attach, no AI (the hurdle) | 70,000 | 70,000 | 70,000 | 70,000 |

## 1. How much?
**Bottom-up, base case, year 1.**
- **Payout tickets:** 12,000 tickets a month × 45 % "where is my money" = 5,400. Of these, 70 % get a grounded draft (3,780 a month), and each draft saves 27 % of the handling time.
- **Other tickets:** account, KYC and fee questions add a little. Dispute tickets get no draft (§3).
- **Time saved:** 10.0 % of all handling time at full adoption, and 4.8 % in year 1 because adoption ramps up to 70 % by Q4.
- **Value:** at €4.7 of agent time per ticket, that is **€32k gross**. After wrong replies (€14k) and tokens (€2k), **€16k is left before fixed costs**.

**Where the numbers come from.**
- **Measured:** nothing. Keelpay is a case with no ticket log; the 12,000 tickets and the 40 % reading share are case figures.
- **Analogies:**
  - €45k per agent (Paylio, cross-checked with French job postings).
  - The time saved, anchored on −12 to −13 % time per issue (Brynjolfsson et al., QJE 2025: +15 % issues resolved per hour; Microsoft: −12 %).
  - The cost of a wrong dispute reply (Mastercard 2025: $128 per chargeback).
  - Token prices.
- **The one guess that matters:** the cost of running the copilot, **€71k a year** of fixed costs scaled down from Paylio. It is more than twice the gross value.

## 2. How sure?
**Scenarios.** Weighted 30 / 50 / 20, the expected value is **−€64k**. Only the optimistic case is positive (+€32k), and it is still below both do-nothing and the hurdle. Even at full adoption with no ramp, the base case is −€38k a year.

**No flip point within reach.** The sensitivity table varies the time saved on a drafted payout ticket:

| Time saved | 27 % | 40 % | 60 % | 80 % | 100 % |
|---|---|---|---|---|---|
| Net value, base case | −€55k | −€42k | −€22k | −€2k | +€19k |

Even at 100 %, the base case stays below do-nothing (€34k). The decision is set by **scale**, not by how good the model is: 18 agents leave a prize of about 1–2 FTE. To flip it, the unsized benefits (faster first reply, faster ramp-up of new agents) would have to be worth **€98k a year** to beat do-nothing, or **€134k** to reach the hurdle.

**What the S4 prototype tests.** It checks the assumptions behind this NO-GO:
- **Hypothesis 1:** the share of payout tickets that get a correct draft (bars: 60 % coverage, 95 % correct).
- **Hypothesis 3:** the share of seeded wrong drafts that agents catch (bar: 90 %).
- **The hurdle:** how much reading time the attach panel alone removes.

## 3. What if we're wrong?
**Cost lines that dominate.** These are not the model. Integration (€20k a year, amortised), evaluation (€20k), supervision (€14k), monitoring (€10k) and re-evaluation (€7.5k) dominate. Tokens cost about €2k a year, so the decision does not depend on the token-price curve.

**Cost of error, priced as a tail.**
- **Basis:** a wrong reply that reaches a merchant costs about €120 on a payout question and about €250 on a dispute.
- **At the bars:** with the bars from the problem statement (5 % of drafts wrong × 10 % not caught), about 25 wrong replies a month reach merchants at full adoption. That costs **€14k in year 1**, or **€23k** in the pessimistic case.
- **Disputes are left out:** dispute drafts would cost about €35k a year in errors, against €21k of time saved.

**Governance line.** A wrong status, amount or deadline told to a merchant on a dispute or a PSD2 / KYC question is a **legal and reputational** risk: the merchant acts on it and can complain to the regulator. Owner: **Head of Compliance**. The Head of Support owns the day-to-day quality of replies (`governance.md`, Session 2).

## 4. Compared to what?
**Do-nothing is not zero.** Agents get about 5 % faster a year, which is worth **€34k**. Meanwhile volume grows about 15 % a year, so the €270k a year spent on reading becomes about €295k (problem statement, §7).

**Next-best project.** The same engineers can ship the rule-only auto-attach: each ticket gets the merchant's recent transactions, open disputes and last tickets, matched by merchant ID, date and amount.
- **Effort and risk:** 6–8 weeks, no model risk.
- **Value:** about **€70k net a year**, if the problem statement's guess holds that it removes 30–50 % of the reading. To test it, observe 20 tickets.
- **Nothing is lost:** it is also the copilot's retrieval layer, so building it first loses nothing if the copilot is reopened later.

**Does the pessimistic case clear the hurdle?** No: −€143k against €70k. The base and optimistic cases don't either.

## 5. Build, buy or orchestrate?
**If the copilot is reopened, we orchestrate**, because the edge is our ledger, dispute history and PSD2 / KYC policy text, which a vendor copilot does not see. Weighted scores from the `Build or buy` tab: **Build 2.80 · Buy 3.25 · Orchestrate 3.50**.

**What would change our mind:** a vendor copilot that reads our ledger and keeps payment data in the EU under a no-training DPA. We would buy it: about €11k a year for 18 seats at $50 each, roughly €39k a year less than our build-specific costs.

*Sources:*
- `01_problem_statement.md` and `02_sizing.xlsx` (Inputs, row 70 onwards).
- S2 slides, p. 37, and the Paylio class sheet.
- Brynjolfsson, Li & Raymond, "Generative AI at Work", *QJE* 140(2), 2025.
- Microsoft Copilot for Service trial (CX Today, Nov 2023).
- Mastercard, "What's the true cost of a chargeback in 2025?".
- Claude API price list (cached 2026-10-06).
- Zendesk and Intercom copilot prices (third-party summaries, 2026-10-30).
- French job postings (France Travail, Michael Page).
