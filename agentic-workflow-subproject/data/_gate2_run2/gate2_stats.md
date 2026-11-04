# Gate 2 statistics
- cards written: 100 | failed deterministic checks: 2 | reviewed: 98
- judge called on 52 tickets | rejected by judge: 28 | accepted: 70
- final pass rate: 70% of written tickets
- cost: 0.0782 USD (0.00078 per ticket; spec estimate for the full run: 5.8 USD / 3190 = 0.0018)
- deterministic reasons: {'urgency_wording_on_low': 2}
- voter_a: 98 votes, 0 unusable, disagreeing fields {'intent': 7, 'sub_intent': 5, 'urgency': 26, 'sentiment': 26, 'amount': 2, 'currency': 7}
- voter_b: 98 votes, 0 unusable, disagreeing fields {'intent': 9, 'sub_intent': 7, 'sentiment': 18, 'urgency': 18, 'transaction_id': 1}

| trap | written | not accepted |
|---|---|---|
| (no trap) | 67 | 19 |
| currency_lone_dollar | 5 | 4 |
| id_two_main | 4 | 1 |
| id_spaced | 3 | 1 |
| id_lookalike | 3 | 2 |
| currency_missing | 3 | 1 |
| amount_approx | 3 | 0 |
| furious_not_urgent | 2 | 1 |
| amount_two_equal | 2 | 1 |
| thanks_hiding_problem | 2 | 0 |
| polite_but_urgent | 2 | 0 |
| id_bare_no_intro | 2 | 0 |
| amount_k_suffix | 2 | 0 |
| amount_two_main | 2 | 1 |
| id_malformed | 1 | 1 |
| other_language | 1 | 0 |
| prompt_injection | 1 | 0 |
| id_nohyphen | 1 | 0 |