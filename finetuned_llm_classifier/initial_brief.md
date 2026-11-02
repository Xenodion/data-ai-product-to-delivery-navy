# Brief: fine-tuning a small LLM to read Keelpay merchant tickets

> Consistent with the frozen NAVY brief in the root `README.md` (source of truth). If they disagree, the root README wins.

## 1. Context and goal
Keelpay is a B2B payments fintech (~2,500 merchants, ~36,000 tickets a month, French and English, mostly by email). Its support agents spend about 15 % of handling time reading and routing the free-text message, and about 1 ticket in 7 first lands in the wrong desk (scenario figures, see the README). The NAVY copilot prepares each ticket for the support agent and never sends anything.

This sub-project fine-tunes a small LLM (on Vertex AI, in Keelpay's own Google Cloud project: tickets never leave Keelpay's cloud) for the first step of that copilot: reading the raw merchant message and returning a structured JSON. It is only worth keeping if it beats cheaper options (keyword and ID rules, a classical text classifier, a prompted open-source model in our own cloud) on a held-out set labelled by someone who did not tune it.

## 2. Role of the fine-tuned model in the flow
The model does not write free text. It reads one message and **always returns one strict JSON object** with a closed set of values.

1. **Input:** a raw merchant message (payment status question, dispute, technical / API issue, compliance request, or something unclear or out of scope).
2. **Model:** returns the JSON with fixed keys `intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`.
3. **Safety net:** a field the model cannot determine is `"UNDEFINED"`; a request it understands but that fits no desk is `"OTHER"`; `transaction_id`, `amount` or `currency` absent from the ticket is `""`. All values are strings. The model never guesses.
4. **After the model (outside this folder):** a fixed decision tree on the JSON routes the ticket to a desk (payments, disputes, technical, compliance) and triggers the transaction lookup. Any `"UNDEFINED"` or `"OTHER"` goes to a support agent for manual qualification. Nothing is sent to a merchant.

Closed values (aligned with the desks): `intent` is `payment_status`, `dispute`, `technical_api` or `compliance`, plus the sentinels `OTHER` and `UNDEFINED`; `urgency` is `high`, `medium`, `low`; `sentiment` is `negative`, `neutral`, `positive`; `sub_intent` is a closed list of four per intent. The full contract is `src/dataset_build/schema.py` and the definitions are `docs/label_definitions.md` (they win over the examples below).

## 3. Examples (training data format)

### Example 1: delayed SEPA transfer (French, payment status)
* **Input:**
  > « Bonjour, le virement de 12 500 € initié lundi dernier (ref: TX-994821) n'est toujours pas crédité chez notre fournisseur. C'est urgent, notre chaîne logistique est bloquée. »
* **Output:**
```json
{
  "intent": "payment_status",
  "sub_intent": "delayed_credit",
  "transaction_id": "TX-994821",
  "amount": "12500.00",
  "currency": "EUR",
  "urgency": "high",
  "sentiment": "negative"
}
```

### Example 2: webhook down (English, technical / API)
* **Input:**
  > "Hi, our payment notification webhooks have stopped responding since 9am. We get 502 Gateway Timeout on our /v1/webhooks endpoint. Can someone take a look?"
* **Output:**
```json
{
  "intent": "technical_api",
  "sub_intent": "webhook_down",
  "transaction_id": "",
  "amount": "",
  "currency": "",
  "urgency": "high",
  "sentiment": "neutral"
}
```

### Example 3: unrecognised fee (French, dispute)
* **Input:**
  > « Bonjour, nous constatons des frais de 45 € sur notre relevé du 14 octobre que nous n'avons jamais autorisés. Nous demandons leur annulation. »
* **Output:**
```json
{
  "intent": "dispute",
  "sub_intent": "unauthorised_fee",
  "transaction_id": "",
  "amount": "45.00",
  "currency": "EUR",
  "urgency": "medium",
  "sentiment": "negative"
}
```

### Example 4: out of scope (fallback)
* **Input:**
  > « Coucou, c'est pour savoir si vous gérez les cryptos ou si on peut changer la couleur de l'interface. »
* **Output:**
```json
{
  "intent": "OTHER",
  "sub_intent": "OTHER",
  "transaction_id": "",
  "amount": "",
  "currency": "",
  "urgency": "low",
  "sentiment": "neutral"
}
```
