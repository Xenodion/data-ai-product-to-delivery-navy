**ASSIGNMENT 2 · TEAM PROJECT · AFTER SESSION 2**

**Is it worth it? Sizing and investment memo**

|  |  |
|----|----|
| **Due** | Before Session 3 — Friday 16 October 2026, start of class |
| **Team** | Same team, same agent as Assignment 1 |
| **Files** | 02_sizing.xlsx (from the template) · 02_investment_memo.md (one page) · governance.md (Session 2 lines) |
| **Rule** | The sheet and the memo use the same base case. Committed by at least two members. |

**Why this assignment**

“We should build this” is not a decision until it has a number, an alternative and a threshold. Sizing lets a product manager lose an argument with the CFO on facts rather than on enthusiasm. The three scenarios exist because a single number hides the tail where projects die (Zillow Offers, 2021). And the threshold is rarely “do nothing”: it is the other project that would use the same team.

**What to do**

1.  **Size the upside, bottom-up, in 02_sizing.xlsx — for your team’s own project.** Start with the “How to fill it” tab: it gives your company’s starting numbers and worked examples. Rename your categories (ticket types, requests, incidents…; set Include = 0 for one you leave out). Give every input a Low / Base / High value, a source type (measured, analogy, guess, decision, judgement) and a note saying where it comes from. Stage adoption by quarter — never 100 % in year 1. Not every agent removes tickets: time saved, revenue retained or penalties avoided are sized too — see the worked examples and the Other value rows.

2.  **Price the cost side:** the seven lines — tokens and inference, integration, evaluation, supervision (the human in the loop is a cost), monitoring and on-call, re-evaluation at model changes, and the cost of error priced as probability × cost. Recheck token prices on the day you fill them in.

3.  **Decide:** three scenarios with probabilities that sum to 1 → an expected value. Compare it with do-nothing (the current process improving on its own) and with your next-best project — name it: it is your hurdle.

4.  **Find your flip point:** read the sensitivity table at the bottom of the Decision tab. The deflection rate at which the reading changes is the number your memo must name and your Session 4 prototype must measure.

5.  **Build, buy or orchestrate:** score the three options on the ten questions of the Build or buy tab, weight what matters to your company, and check the break-even against per-resolution pricing.

6.  **Write the memo — one page.** Line one is the decision: GO, NO-GO or CONDITIONAL GO on \[condition\]. Then the four questions a CFO asks: How much? How sure? What if we’re wrong? Compared to what? End with one line on build, buy or orchestrate.

7.  **Update governance.md:** which cost-of-error line is a legal or reputational risk, not just money — and who in the company owns it.

**Before you commit — the six sizing failure modes**

The written exam asks you to spot these in a brief. Make sure yours has none of them.

| **\#** | **Failure mode** | **What to do instead** |
|----|----|----|
| 1 | Top-down TAM copied from an analyst report | Count your own work: tickets × share × deflection × value — a source per branch |
| 2 | 100 % adoption in year 1 | An adoption ramp by quarter, each step conditional on a guardrail holding |
| 3 | Per-unit value = price, not net value | Human cost avoided − AI cost − expected cost of a wrong answer |
| 4 | Marginal AI cost forgotten — or fixed | Tokens scale with success; size with a cost curve, not a point |
| 5 | Cost of error not priced | Error rate × cost of one wrong answer, per category — the tail, priced |
| 6 | Do-nothing assumed to be zero | The current process improves on its own; the real competitor is another project |

- [ ] Every input has a Low / Base / High value, a source type and a note

- [ ] Probabilities sum to 1; the Decision cell no longer asks you to fill anything in

- [ ] The next-best project is named, in the sheet and in the memo

- [ ] The memo’s first line is the decision, and a conditional go states its condition

- [ ] The memo and the sheet show the same base case

- [ ] One line on build, buy or orchestrate, with the condition that would change it

- [ ] governance.md has the Session 2 lines

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr>
<td><p><strong>Using AI to help — yes, and audit every number</strong></p>
<p>You may ask Claude, ChatGPT or any other assistant for a first bottom-up model: it will give you a complete, well-structured sheet in under a minute, with plausible parameters, some sourced and some invented. Your job is the assumption register: which numbers are measured, which are analogies (and from which case), and which are guesses. A confident number without a source is a guess — label it as one.</p></td>
</tr>
</tbody>
</table>

**How it counts**

This assignment is part of your Git deliverable (40 % of the project grade). It becomes three beats of your final pitch — the market, the business case and the alternatives. The sizing sets the baseline of your three business metrics in Session 5, and the flip assumption is what your Session 4 prototype tests.

**Resources:** Session 2 slides (bottom-up tree, seven cost lines, scenarios and hurdle, investment memo, build / buy / orchestrate) · the 02_sizing template and the Paylio class sheet (format only) · Kohavi, Tang & Xu, Trustworthy Online Controlled Experiments (2020), ch. 1 and 7 · Klarna press release (27 Feb 2024) and Bloomberg (8 May 2025) · Zillow Group, Form 8-K (2 Nov 2021) · Stanford HAI, AI Index Report 2025.
