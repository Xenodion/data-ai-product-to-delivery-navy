// Reproduces dataset/model evidence and writes a financial reference snapshot.
// Workbook figures are re-imported and checked separately with the local
// .specify/workbench/verify-sizing-export.mjs review utility.
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const base = 'finetuned_llm_classifier/';
function csv(file) {
  const text = fs.readFileSync(path.join(root, file), 'utf8').replace(/^\uFEFF/, '');
  const rows = []; let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') { if (quoted && text[i + 1] === '"') { field += '"'; i++; } else quoted = !quoted; }
    else if (c === ',' && !quoted) { row.push(field); field = ''; }
    else if (c === '\n' && !quoted) { row.push(field.replace(/\r$/, '')); rows.push(row); row = []; field = ''; }
    else field += c;
  }
  if (field || row.length) { row.push(field.replace(/\r$/, '')); rows.push(row); }
  const header = rows.shift();
  return rows.filter(r => r.some(Boolean)).map(r => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ''])));
}
const taxonomy = {
  payment_status: ['delayed_credit', 'missing_payment', 'status_inquiry', 'refund_status'],
  dispute: ['unauthorised_fee', 'chargeback', 'duplicate_charge', 'amount_mismatch'],
  technical_api: ['webhook_down', 'api_error', 'auth_failure', 'integration_question'],
  compliance: ['kyc_update', 'account_hold', 'document_request', 'regulatory_question'],
};
const sentinels = ['OTHER', 'UNDEFINED'];
const keys = ['intent','sub_intent','transaction_id','amount','currency','urgency','sentiment'];
const currencies = ['EUR','USD','GBP','CHF','CAD','SEK','DKK','NOK','PLN'];
function valid(p) {
  if (!p || typeof p !== 'object' || Object.keys(p).length !== 7 || !keys.every(k => typeof p[k] === 'string')) return false;
  if (!(sentinels.includes(p.intent) ? p.sub_intent === p.intent : taxonomy[p.intent]?.concat(sentinels).includes(p.sub_intent))) return false;
  const nullable = (v, test) => v === '' || v === 'UNDEFINED' || test(v);
  return ['low','medium','high','UNDEFINED'].includes(p.urgency)
    && ['positive','neutral','negative','UNDEFINED'].includes(p.sentiment)
    && nullable(p.transaction_id, v => /^TX-\d{6}$/.test(v))
    && nullable(p.amount, v => /^\d+\.\d{2}$/.test(v))
    && nullable(p.currency, v => currencies.includes(v));
}
const counts = (rows, field) => rows.reduce((out, r) => { out[r[field]] = (out[r[field]] || 0) + 1; return out; }, {});
const all = {}; const hashes = new Map(); const overlap = [];
for (const split of ['train','val','test_natural','test_traps']) {
  const rows = csv(base + `data/dataset/${split}.csv`);
  const labels = rows.map(r => JSON.parse(r.target));
  for (const r of rows) {
    const h = crypto.createHash('sha256').update(r.ticket).digest('hex');
    if (hashes.has(h)) overlap.push([hashes.get(h), split]); else hashes.set(h, split);
  }
  all[split] = { n: rows.length, invalidTargets: labels.filter(p => !valid(p)).length,
    language: counts(rows,'language'), intent: counts(labels,'intent'), writer: counts(rows,'writer_model') };
}
const metrics = {};
for (const system of ['b0','b1','b2','d_gpu','d_q8','d_q4']) {
  const preds = csv(base + `docs/results/${system}_test_natural_predictions.csv`);
  const data = csv(base + 'data/dataset/test_natural.csv');
  if (preds.length !== data.length) throw Error('row count mismatch');
  let syntactic = 0, accepted = 0, routed = 0, deskCorrect = 0, silent = 0, urgent = 0, urgentWrong = 0;
  let sentinelDespiteDesk = 0, anySentinelPolicyAuto = 0, nonUrgentNoSentinelPolicyAuto = 0;
  const desk = p => p && taxonomy[p.intent] ? p.intent : 'triage';
  preds.forEach((r, i) => {
    if (r.user_input !== data[i].ticket && !r.user_input.includes(data[i].ticket)) throw Error(`alignment mismatch ${system} ${i}`);
    const t = JSON.parse(data[i].target); let p = null;
    try { p = JSON.parse(r.extracted_response); syntactic++; } catch {}
    if (!valid(p)) p = null; else accepted++;
    const auto = desk(p) !== 'triage';
    if (auto) routed++;
    if (desk(p) === desk(t)) deskCorrect++;
    if (auto && (desk(p) !== desk(t) || ['transaction_id','amount','currency'].some(f => p[f] !== t[f]))) silent++;
    if (t.urgency === 'high') { urgent++; if (auto && desk(p) !== desk(t)) urgentWrong++; }
    if (auto && Object.values(p).some(v => sentinels.includes(v))) sentinelDespiteDesk++;
    if (auto && !Object.values(p).some(v => sentinels.includes(v))) {
      anySentinelPolicyAuto++;
      if (p.urgency !== 'high') nonUrgentNoSentinelPolicyAuto++;
    }
  });
  metrics[system] = { n: preds.length, syntactic, accepted, routed, deskCorrect, silent, urgent, urgentWrong,
    sentinelDespiteDesk, anySentinelPolicyAuto, nonUrgentNoSentinelPolicyAuto };
}
const financial = {
  baseTimeSaved: .15 * .55 * .8 + .45 * .33 * .92,
  weightedSeriousError: .45 * .0005 + .2 * .0012 + .35 * .0008,
  pointRoutingValueYear1: 36900 * 12 * .4375 * .01 * 3,
  pointRoutingValueSteady: 36900 * 12 * .7 * .01 * 3,
  // Snapshot values from the verified workbook export; this script does not parse XLSX.
  baseAnnualizedNet: 194297.65191666677,
  weightedEV: 214308.0664964286,
  nextBestBaseHurdle: 100183.2,
  optimismToBaseNeeded: (214308.0664964286 - 100183.2) / (703462.1223333332 - 194297.65191666677),
  evAtZeroOptimism: .3 * -78443.94642857143 + .7 * 194297.65191666677,
  timeSavedHurdle: .1332179006200493,
  zeroErrorsUpper95At200: 1 - Math.pow(.05, 1 / 200),
  zeroErrorsSampleForUpperPoint001: Math.ceil(Math.log(.05) / Math.log(.999)),
};
const evidence = { dataset: all, exactTextOverlaps: overlap, metrics, financial };
fs.writeFileSync(path.join(root, 'audit/2026-11-03-evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence, null, 2));
