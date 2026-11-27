import assert from "node:assert/strict";
import { reconcileReply } from "./replyEditor.ts";

assert.deepEqual(reconcileReply({ text: "old", base: "old", conflict: false }, "new"), { text: "new", base: "new", conflict: false });
assert.deepEqual(reconcileReply({ text: "local", base: "old", conflict: false }, "new"), { text: "local", base: "new", conflict: true });
assert.deepEqual(reconcileReply({ text: "saved", base: "old", conflict: false }, "saved"), { text: "saved", base: "saved", conflict: false });
assert.deepEqual(reconcileReply({ text: "local", base: "new", conflict: true }, "new"), { text: "local", base: "new", conflict: true });
console.log("reply editor checks passed");
