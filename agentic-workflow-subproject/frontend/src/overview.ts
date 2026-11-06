/** What the Overview shows. Shaped like the backend answer it will later poll. */

export type Stage = {
  waiting: number;
  working: number;
  failed: number;
  avgWaitSeconds: number;
  avgWorkSeconds: number;
};

export type Overview = {
  period: { since: string; seeded: number };
  received: number;
  sent: number;
  failed: number;
  oldestWaitingMinutes: number;
  stages: { qualifier: Stage; drafter: Stage; reRouter: Stage; validator: Stage; agentEdits: Stage };
  routing: {
    decided: number; // tickets with an initial assignment decision
    desks: { name: string; tickets: number }[];
    unknown: number;
  };
  reRouter: { firstChanges: number; secondChanges: number; wrongDeskFromValidator: number };
  drafts: { ready: number; supersededInQueue: number };
  validator: { approved: number; fixIt: number; wrongDesk: number };
  editsDone: number;
  urgent: { open: number; unclaimed: number; oldestMinutes: number };
  incidents: { ticket: string; step: string; problem: string; next: string }[];
};

const stage = (waiting: number, working: number, failed: number, avgWaitSeconds: number, avgWorkSeconds: number): Stage => ({
  waiting,
  working,
  failed,
  avgWaitSeconds,
  avgWorkSeconds,
});

// ponytail: sample numbers until spec 008 has a backend; replace with polling, keep the type.
export const SAMPLE: Overview = {
  period: { since: "09:00 today", seeded: 4 },
  received: 128,
  sent: 97,
  failed: 3,
  oldestWaitingMinutes: 14,
  stages: {
    qualifier: stage(3, 1, 1, 12, 6.4),
    drafter: stage(2, 2, 2, 8, 9),
    reRouter: stage(4, 1, 0, 240, 100),
    validator: stage(14, 2, 0, 360, 130),
    agentEdits: stage(3, 1, 0, 180, 200),
  },
  routing: {
    decided: 123,
    desks: [
      { name: "Payments", tickets: 53 },
      { name: "Disputes", tickets: 27 },
      { name: "Technical/API", tickets: 19 },
      { name: "Compliance", tickets: 10 },
    ],
    unknown: 14,
  },
  reRouter: { firstChanges: 15, secondChanges: 1, wrongDeskFromValidator: 7 },
  drafts: { ready: 132, supersededInQueue: 9 },
  validator: { approved: 86, fixIt: 14, wrongDesk: 7 },
  editsDone: 11,
  urgent: { open: 6, unclaimed: 4, oldestMinutes: 11 },
  incidents: [
    { ticket: "K-24187", step: "Qualifier Model", problem: "Output was not valid JSON", next: "Agent handles it by hand" },
    { ticket: "K-24192", step: "Drafter Model", problem: "LLM API timed out", next: "Agent writes the reply" },
    { ticket: "K-24203", step: "Drafter Model", problem: "LLM API timed out", next: "Agent writes the reply" },
  ],
};

export const count = (s: Stage): number => s.waiting + s.working;

export const active = ({ stages: s }: Overview): number =>
  // The Re-router works in parallel: its tickets are already in one of these steps.
  count(s.qualifier) + count(s.drafter) + count(s.validator) + count(s.agentEdits);

export const autoAssigned = (o: Overview): number => o.routing.desks.reduce((sum, d) => sum + d.tickets, 0);

export const decided = (o: Overview): number => o.validator.approved + o.validator.fixIt + o.validator.wrongDesk;

export const pct = (part: number, whole: number): string => (whole ? `${((100 * part) / whole).toFixed(1)}%` : "n/a");

export const duration = (seconds: number): string =>
  seconds < 60 ? `${seconds} s` : `${Math.round(seconds / 60)} min`;

/** Lists every count that disagrees with another one; empty means the page tells one story. */
export function reconcile(o: Overview): string[] {
  const s = o.stages;
  const redrafts = o.reRouter.firstChanges;
  const checks: [string, number, number][] = [
    ["received = sent + failed + active", o.received, o.sent + o.failed + active(o)],
    ["failed = failures by step", o.failed, s.qualifier.failed + s.drafter.failed],
    ["failed = incidents listed", o.failed, o.incidents.length],
    ["routed = received - Qualifier", o.routing.decided, o.received - count(s.qualifier) - s.qualifier.failed],
    ["routed = desk known + unknown", o.routing.decided, autoAssigned(o) + o.routing.unknown],
    ["drafts ready = attempts - in progress - failed", o.drafts.ready, o.routing.decided + redrafts - count(s.drafter) - s.drafter.failed],
    ["drafts ready = Validator entries", o.drafts.ready, count(s.validator) + o.drafts.supersededInQueue + decided(o)],
    ["Re-router entries", o.routing.unknown + o.validator.wrongDesk, count(s.reRouter) + redrafts + o.reRouter.secondChanges],
    ["wrong desk seen on both sides", o.validator.wrongDesk, o.reRouter.wrongDeskFromValidator],
    ["desk changes replace queued drafts", redrafts + o.reRouter.secondChanges, o.validator.wrongDesk + o.drafts.supersededInQueue],
    ["Agent edits entries", o.validator.fixIt + o.reRouter.secondChanges, count(s.agentEdits) + o.editsDone],
    ["sent = approved + edited", o.sent, o.validator.approved + o.editsDone],
  ];
  return checks.filter(([, a, b]) => a !== b).map(([name, a, b]) => `${name}: ${a} != ${b}`);
}
