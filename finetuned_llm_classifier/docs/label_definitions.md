# Label definitions

Reference for the labelling rules of the ticket reader. It feeds the generation prompt, the reviewer prompt and the scoring. The machine-checkable part lives in `src/dataset_build/schema.py` (`TicketLabel`); this file gives the meaning. If they disagree, fix the one that is wrong in the same commit.

## 1. Format

One JSON object, exactly seven keys, **every value a string** (no JSON `null`, no number).

| Convention | Meaning |
|---|---|
| lowercase `snake_case` | a real class (`payment_status`, `delayed_credit`, `high`) |
| `UNDEFINED` | the ticket does not allow a decision: ambiguous, too vague, malformed reference. Goes to a human |
| `OTHER` | understood, but no desk or listed sub-intent fits (`intent` and `sub_intent` only). Goes to a human |
| `""` (empty string) | absent from the ticket; only on `transaction_id`, `amount`, `currency` |

Validation rules (all checked by `TicketLabel`):

| Field | Allowed | `""` allowed |
|---|---|---|
| `intent` | `payment_status`, `dispute`, `technical_api`, `compliance`, `OTHER`, `UNDEFINED` | no |
| `sub_intent` | one of the sub-intents of the intent, `OTHER` or `UNDEFINED`; if `intent` is `OTHER` or `UNDEFINED`, `sub_intent` repeats it | no |
| `urgency` | `high`, `medium`, `low`, `UNDEFINED` | no |
| `sentiment` | `negative`, `neutral`, `positive`, `UNDEFINED` | no |
| `transaction_id` | `TX-` + 6 digits, or `UNDEFINED` | yes |
| `amount` | dot decimal with two decimals, no thousands separator (`12500.00`), or `UNDEFINED` | yes |
| `currency` | closed list in `schema.py` (`CURRENCIES`), or `UNDEFINED` | yes |

The model input is the ticket as received: `Subject: ...` then a blank line then the body (French or English, possibly a forwarded thread).

## 2. Intent and sub-intent

`intent` is the main request of the message. If two requests are equally strong and no main one stands out, `intent` is `UNDEFINED`. If the intent is clear but none of its sub-intents fits, `sub_intent` is `OTHER`; if it is clear but cannot be told apart, `UNDEFINED`.

| Intent (desk) | Sub-intent | The merchant... |
|---|---|---|
| `payment_status` | `delayed_credit` | says a payment or payout was sent but is not credited after the expected time |
| | `missing_payment` | expects a payment that never arrived or cannot be found |
| | `status_inquiry` | asks where a payment stands, without claiming a delay |
| | `refund_status` | asks about a refund |
| `dispute` | `unauthorised_fee` | contests a fee they never agreed to |
| | `chargeback` | reports or answers a card chargeback |
| | `duplicate_charge` | says the same amount was charged twice |
| | `amount_mismatch` | says the amount differs from what was expected |
| `technical_api` | `webhook_down` | says notifications are not delivered or the endpoint fails |
| | `api_error` | reports error codes or timeouts on API calls |
| | `auth_failure` | has an API key, token or login rejected |
| | `integration_question` | asks how to integrate or use a feature |
| `compliance` | `kyc_update` | submits or updates identity, ownership or company documents |
| | `account_hold` | says the account is restricted or frozen and asks why |
| | `document_request` | asks for a certificate, attestation or statement |
| | `regulatory_question` | asks about PSD2, strong authentication, AML |

`OTHER` (intent): understood, no desk: pricing, new feature request, a chat about unrelated topics, a thank-you with no request, spam.
`UNDEFINED` (intent): two equal requests, too vague or truncated to read, unintelligible.

## 3. Urgency and sentiment

| Urgency | Rule |
|---|---|
| `high` | an explicit deadline within 48 hours, **or** the merchant's activity is blocked, **or** funds or the account are frozen, **or** a regulatory deadline is stated |
| `medium` | a real problem that does not block the merchant's activity and has no deadline (operations continue, or a workaround exists) |
| `low` | informational, no impact, no time pressure |
| `UNDEFINED` | the message is too short or too vague to judge how urgent it is |

| Sentiment | Rule |
|---|---|
| `negative` | explicit frustration, anger, a complaint or a threat (to leave, to escalate) |
| `neutral` | factual or polite request, no emotion marker and no complaint wording |
| `positive` | a clear compliment or expression of satisfaction (more than a routine thank-you) |
| `UNDEFINED` | the text is unintelligible, so no tone can be read |

A real problem affecting the merchant (money late or missing, a charge contested, an API failing) is at least `medium`; `low` is for informational requests. A restricted or frozen account is always `high`. Anger or politeness does not change urgency.

Urgency and sentiment are judged on the text alone and are independent of the intent (an `OTHER` ticket can be `high`).

## 4. Extraction rules

**`transaction_id`**: the payment the request is about, always written in the canonical form `TX-######`.

- Normalise the writing: `tx 994 821`, `TX994821`, `tx-994821` all become `TX-994821`.
- A bare 6-digit number counts only when the ticket introduces it as the transaction or payment reference (`transaction 994821`, `payment ref: 994821`).
- Not an ID, so `""`: invoice or order numbers (`INV-…`, `ORD-…`), phone numbers, IBAN fragments, HTTP codes, dates, the merchant's own internal references, a bare number with no such introduction.
- Looks like a transaction ID but is malformed (`TX-12345`, `TX-9948210`): `UNDEFINED`.
- Several valid IDs: the one the request is about; if none stands out, `UNDEFINED`. An ID that only appears in a quoted earlier message counts only if the request is about it.

**`amount`**: the amount of the payment or charge the request is about.

- Write it `12500.00`: dot decimal, two decimals, no separator. `12 500,00 €`, `12,500.00` and `12.5k` all become `12500.00`. An approximate amount ("about 500 euros") is written as stated (`500.00`).
- Several amounts: same rule as for IDs; if none stands out, `UNDEFINED`. No amount: `""`.

**`currency`**: only what the ticket states. `€` is `EUR`, `£` is `GBP`, an ISO code or a currency name is taken as is. A lone `$` is ambiguous: `UNDEFINED`. An amount with no currency, or no currency at all: `""`. Never infer the currency from the merchant's country.

## 5. Examples

Input: `Subject: Virement non crédité (TX-994821)` + « Le virement de 12 500 € initié lundi n'est toujours pas crédité chez notre fournisseur. C'est urgent, notre chaîne logistique est bloquée. »

```json
{"intent": "payment_status", "sub_intent": "delayed_credit", "transaction_id": "TX-994821", "amount": "12500.00", "currency": "EUR", "urgency": "high", "sentiment": "negative"}
```

Input: « Coucou, c'est pour savoir si vous gérez les cryptos ou si on peut changer la couleur de l'interface. »

```json
{"intent": "OTHER", "sub_intent": "OTHER", "transaction_id": "", "amount": "", "currency": "", "urgency": "low", "sentiment": "neutral"}
```

Input: « Bonjour, je conteste les frais de 45 $ de la facture INV-204518, et en parallèle notre webhook ne répond plus depuis ce matin. »

```json
{"intent": "UNDEFINED", "sub_intent": "UNDEFINED", "transaction_id": "", "amount": "45.00", "currency": "UNDEFINED", "urgency": "medium", "sentiment": "negative"}
```

(Two equal requests, so `UNDEFINED`; `INV-204518` is an invoice, not a transaction, so `""`; a lone `$` is `UNDEFINED`.)
