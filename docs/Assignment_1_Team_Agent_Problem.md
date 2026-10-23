**ASSIGNMENT 1 · TEAM PROJECT · AFTER SESSION 2**

**Your team, your agent, your problem**

|  |  |
|----|----|
| **Due** | Before Session 3 — Friday 16 October 2026, start of class |
| **Team** | 4–5 students — the same team as in Agentic Workflows |
| **Files** | In your team’s Git repository, created from project_repo_template.zip: README.md · 01_problem_statement.md · governance.md (+ 00_pitch.md if you bring your own idea) |
| **Rule** | Committed by at least two members, each with their own Git account |

**Why this assignment**

Most AI projects that fail, fail before any model is trained: the pain was mis-diagnosed, the do-nothing option was never priced, or AI was the answer to a question nobody had asked. This file is the foundation of everything you will defend at the oral — the sizing (Assignment 2), the MVP (Session 3), the metrics and the A/B test all start from it.

Same team, same agent as in Agentic Workflows: there, you build and test it; here, you decide whether it should ship, and how.

**What to do**

1.  **Form your team and choose your agent.** Start from one of the eight proposals in the project document, or bring your own idea and write 00_pitch.md (it must pass the seven-point checklist). Fill in README.md: team, company, the agent’s job in one sentence — “When \[trigger\], the agent \[does\], producing \[outcome\]” — trust level per step, one thing it must never do.

2.  **Write the problem in one sentence,** with at least one number: “\[Who\] experiences \[pain\] when \[situation\], costing \[quantified impact\]; today they \[do-nothing baseline\]. Success looks like \[measurable outcome\].” For every number, say whether it is measured, an analogy (with its source) or a guess.

3.  **Draw the problem tree:** symptom → problem → root cause (5 Whys). Then say what would fix the cause — and whether that fix is AI, a rule, a process change or a documentation fix.

4.  **Answer “Is AI the right tool?”** — the four questions from last week: is there a rule that solves 80 %? Prediction/generation or organisational decision? Do we have the data? What does one error cost? Choose the level (rule, classical ML, GenAI, agent) and say why not the level below.

5.  **Check your agent against the four selection questions:** high frequency, bounded decision space, measurable success, recoverable failure — one line each.

6.  **Work backwards:** a one-paragraph press release dated launch day (who it is for, what changed, one number, one customer quote), then three hypotheses that “would have to be true”, each with how and in which session you will test it.

7.  **Price the do-nothing baseline:** what happens in 12 months if nobody builds anything? It is not zero — the team gets faster, the documentation improves, volumes grow.

8.  **Create governance.md** with provisional answers to the six questions: EU AI Act risk tier · whose data, on what legal basis · who is accountable and where is the human · what it must never do · explainable to whom · what happens to the people it cannot serve. Mark what you still have to check.

**What good looks like**

| **Weak** | **Strong** |
|----|----|
| “Customers are frustrated with support.” | A pain expressed as a cost — hours, euros, SLA penalties, churn — with its source type. |
| “Tickets are exploding.” (a symptom) | The cause behind it, reached with the 5 Whys — and a fix aimed at the cause. |
| AI because it is the topic of the course. | AI justified against a rule and against doing nothing. Two of last week’s six scenarios did not need new AI. |
| Hypotheses that are wishes (“users will love it”). | Hypotheses you can test on 200 tickets in Session 4, or measure in Session 5. |
| Governance answers that fit any chatbot. | Answers specific to your agent: its data, its users, the error that would hurt most. |

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr>
<td><p><strong>Example — illustrative, not one of the eight proposals</strong></p>
<p><strong>Problem in one sentence:</strong> Tier-1 agents at TravelDesk, a B2B travel-booking SaaS (900 corporate customers, 18,000 fare-rule tickets a month), lose about 6 minutes per ticket looking up change and cancellation rules — about 1,800 agent-hours a month; today they search a 300-page policy wiki by hand. Success looks like a median handling time below 3 minutes on these tickets, at a constant quality score.</p>
<p><strong>Source types:</strong> 18,000 tickets — measured (ticket log). 6 minutes — guess, to be measured on a two-week sample.</p>
<p><strong>One hypothesis:</strong> at least 60 % of fare-rule questions can be answered from the policy wiki alone — guess, tested on 200 tickets with the Session 4 prototype.</p></td>
</tr>
</tbody>
</table>

**Before you commit**

- [ ] README.md says who is in the team, which agent, and its job in one sentence

- [ ] The problem sentence has at least one number, and every number has a source type

- [ ] The problem tree goes down to a cause, not a symptom

- [ ] The AI level is chosen and justified against the level below

- [ ] Three testable hypotheses, each with a session where it will be tested

- [ ] The do-nothing baseline is written down — and is not zero

- [ ] governance.md answers the six questions, provisionally — and at least two members have committed

**How it counts**

This assignment is not graded on its own: it is the first part of your Git deliverable (40 % of the project grade) and the first two beats of your final pitch — the problem and the solution. At the oral, one question is drawn from governance.md, and the individual question (10 %) is about a commit you signed — so everybody commits. Session 3 (MVP design) starts from this file.

**Resources:** Session 1 and 2 slides · the project document (eight proposals, bring-your-own checklist) · project_repo_template.zip · Colin Bryar & Bill Carr, Working Backwards (2021), ch. 4 — the press release and FAQ · Google PAIR, People + AI Guidebook, “User Needs + Defining Success” · Moffatt v. Air Canada, 2024 BCCRT 149.
