import assert from "node:assert/strict";
import { SAMPLE, duration, pct, reconcile } from "./overview.ts";

assert.deepEqual(reconcile(SAMPLE), []);
assert.match(reconcile({ ...SAMPLE, sent: 96 })[0], /^received/);
assert.equal(pct(14, 123), "11.4%");
assert.equal(pct(1, 0), "n/a");
assert.equal(duration(6.4), "6.4 s");
assert.equal(duration(130), "2 min");
console.log("overview checks passed");
