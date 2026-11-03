# Routing Node Decision Cases

These synthetic cases define behavior of the deterministic decision layer. They are not model-performance scores, source fixtures, or production policy approval. `Q` means Human Qualification; `HR` means mandatory Human Review before every simulated send.

| ID | Input condition | Desk / priority | Human step and dependency | Preparation / expected effect |
|---|---|---|---|---|
| DE-001 | Valid supported payment intent; exact canonical ID resolves within merchant; approved source found | payments / model priority | HR | Factual draft; retain decision/source versions |
| DE-002 | Valid supported dispute intent; urgency high; facts and source available | disputes / high | HR | Factual draft proceeds; urgent attention visible |
| DE-003 | Valid `intent=UNDEFINED`; urgency high from model | triage / high | Q for intent/desk | No desk-specific draft until qualification; priority still visible |
| DE-004 | Valid `intent=OTHER` | triage / model priority | Q for unsupported request | No automatic desk mapping unless versioned approved config provides one |
| DE-005 | Qualifier output invalid | triage / unknown or independently detected priority | Q for model/request result | Keep ticket; use manual path if safe extraction unavailable |
| DE-006 | Qualifier unavailable; trusted text parser detects approved deadline signal | triage / configured priority with provenance | Q for intent/desk | Qualification and priority proceed independently |
| DE-007 | Supported desk; `sub_intent=UNDEFINED`; generic documented response does not depend on sub-intent | mapped desk / model priority | HR | Documentary draft allowed; do not force global triage |
| DE-008 | Supported desk; `sub_intent=UNDEFINED`; requested procedure requires the sub-intent | mapped desk / model priority | Q for procedure only | Hold dependent procedure; safe clarification/manual path remains available |
| DE-009 | `sentiment=UNDEFINED`; otherwise supported and resolvable | mapped desk / model priority | HR | Continue with neutral tone |
| DE-010 | `urgency=UNDEFINED`; no independent signal | mapped desk / unknown | HR | Continue; show unknown priority |
| DE-011 | High priority and payment facts are exact/source-backed | mapped desk / high | HR | Draft proceeds; no pre-draft confirmation |
| DE-012 | Payment desk known; no transaction ID; request asks for payment-specific status | payments / model priority | Payment selection or clarification | Preserve payments desk; no payment claim before resolution |
| DE-013 | Payment desk known; no transaction ID; response only needs approved general documentation | payments / model priority | HR | Documentary draft allowed; don't claim a transaction lookup occurred |
| DE-014 | External payout/order reference is present but not a canonical transaction ID | mapped desk / model priority | Clarification if payment facts needed | Do not coerce the external reference into a transaction ID |
| DE-015 | Two same-amount candidates are returned under the same merchant | mapped desk / model priority | Payment selection or clarification | Show distinguishing fields; select none automatically |
| DE-016 | Lookup returns a transaction owned by another merchant | mapped desk / model priority | Manual handling or clarification | Mark wrong merchant; expose/use no foreign facts or candidate |
| DE-017 | Exact canonical ID lookup returns no record | mapped desk / model priority | Clarification/manual according to policy | No payment-specific assertion |
| DE-018 | Lookup facts conflict with ticket amount/currency | mapped desk / model priority | Human resolution of payment conflict | No factual payment draft; preserve conflict reason |
| DE-019 | Lookup or retrieval service unavailable | mapped desk / model priority | HR after safe fallback; otherwise manual | Never convert service error to “not found”; no unsupported factual draft |
| DE-020 | Required source set empty or Drafter Model fails | mapped desk / model priority | HR for clarification; manual if unsafe | Clarification or manual draft; preserve source/model error |
| DE-021 | Draft blocked by configured content policy | mapped desk / model priority | Manual handling | Block assisted draft; preserve exact policy version/reason |
| DE-022 | Support Agent changes desk for the first time | corrected desk / recomputed priority | HR after one re-preparation | Mark dependent draft stale; rerun affected lookup/retrieval/draft once |
| DE-023 | Support Agent changes desk for a second time | triage / preserved priority | Q/manual handling | Stop automatic loop; no stale draft can send |
| DE-024 | Payment selection changes, desk does not | same desk / preserved priority | HR after dependency refresh | Recompute payment-dependent output; do not increment desk-reroute count |
| DE-025 | Two equally strong intents are present | triage / independently derived | Q for intent/desk | Do not split automatically or issue two drafts |
| DE-026 | Every field and source is valid; output reaches review queue | mapped desk / applicable priority | HR | Routing decision cannot itself authorize/send a reply or write the ledger |

Every case must also assert stable reason codes, policy/contract version references, tenant scope, and a durable decision event. For cases without the required synthetic records, unit tests may inject typed lookup/retrieval results; that does not count as evidence that the fixtures exist or that generated facts are grounded.
