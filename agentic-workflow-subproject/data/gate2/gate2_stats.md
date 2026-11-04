# Gate 2 statistics
- cards written: 100 | failed deterministic checks: 3 | reviewed: 97
- judge called on 43 tickets | rejected by judge: 22 | accepted: 75
- final pass rate: 75% of written tickets
- cost: 0.0735 USD (0.00074 per ticket; spec estimate for the full run: 5.8 USD / 3190 = 0.0018)
- deterministic reasons: {'surface_missing': 2, 'urgency_wording_on_low': 1}
- voter_a: 97 votes, 2 unusable, disagreeing fields {'urgency': 21, 'intent': 13, 'sub_intent': 14, 'sentiment': 10, 'amount': 1, 'transaction_id': 2, 'currency': 2}
- voter_b: 97 votes, 0 unusable, disagreeing fields {'intent': 10, 'sub_intent': 13, 'urgency': 10, 'currency': 2, 'sentiment': 4, 'amount': 1}

| trap | written | not accepted |
|---|---|---|
| (no trap) | 69 | 18 |
| id_lookalike | 3 | 0 |
| id_quoted_only | 3 | 2 |
| id_nohyphen | 3 | 0 |
| currency_lone_dollar | 3 | 1 |
| thanks_hiding_problem | 2 | 1 |
| furious_not_urgent | 2 | 1 |
| polite_but_urgent | 2 | 0 |
| id_subject_only | 2 | 1 |
| prompt_injection | 2 | 1 |
| id_bare_with_intro | 2 | 1 |
| amount_two_main | 2 | 1 |
| id_malformed | 2 | 0 |
| amount_k_suffix | 2 | 0 |
| id_spaced | 1 | 0 |
| amount_two_equal | 1 | 0 |
| id_two_main | 1 | 0 |
| id_bare_no_intro | 1 | 0 |
| amount_approx | 1 | 0 |