# Baseline results (B0 majority, B1 rules, B2 TF-IDF + logistic regression)

Run with `ml/qualifier/scripts/run_baselines.py --final` on the dataset committed in `data/dataset/` (train 1,922, val 293, test_natural 610, test_traps 380), following `docs/scoring_protocol.md`. B2's regularisation (C=10) was chosen on val only, by lowest error severity score. The test sets were scored once, after the dataset was final. The severity points are the relative assumption of the protocol (human triage 1, wrong desk 3, wrong reference 5, wrong desk on an urgent ticket 10).

Headline (test_natural): B2 reaches 91.6 % desk accuracy but **33.9 silent errors per 100 tickets** (a definite answer with a wrong desk or a wrong reference) and 6.6 % of urgent tickets in a wrong desk, at an error severity score of 1.666. B1 scores 0.608 points above B2 (interval 0.374 to 0.846) and B0 2.225 above (1.936 to 2.515). The reference fields (`transaction_id`, `amount`, `currency`) are extracted by the same regular expressions in B1 and B2, so the fine-tuned model has to beat B2 mostly there and on the trap types (per-trap numbers are counts: no interval below 20 tickets).

Columns: `silent_error_rate` and `needless_triage_rate` are shares of all tickets; `auto_routed_rate` is the share routed to a desk by the system; `severity_score` is the mean severity in points.

```
val (293 tickets), B2 C=10.0
B0   n=293.000 valid_json_rate=1.000 desk_accuracy=0.215 urgent_wrong_desk=0.759 silent_error_rate=0.812 auto_routed_rate=1.000 needless_triage_rate=0.000 macro_f1_intent=0.059 exact_transaction_id=0.648 exact_amount=0.642 accuracy_urgency=0.471 recall_high_urgency=0.000 severity_score=3.925
B1   n=293.000 valid_json_rate=1.000 desk_accuracy=0.403 urgent_wrong_desk=0.392 silent_error_rate=0.468 auto_routed_rate=0.734 needless_triage_rate=0.208 macro_f1_intent=0.321 exact_transaction_id=0.894 exact_amount=0.829 accuracy_urgency=0.464 recall_high_urgency=0.203 severity_score=2.509
B2   n=293.000 valid_json_rate=1.000 desk_accuracy=0.949 urgent_wrong_desk=0.076 silent_error_rate=0.283 auto_routed_rate=0.863 needless_triage_rate=0.007 macro_f1_intent=0.927 exact_transaction_id=0.894 exact_amount=0.829 accuracy_urgency=0.952 recall_high_urgency=0.911 severity_score=1.478
test_natural (610 tickets)
B0   n=610.000 valid_json_rate=1.000 desk_accuracy=0.236 urgent_wrong_desk=0.778 silent_error_rate=0.785 auto_routed_rate=1.000 needless_triage_rate=0.000 macro_f1_intent=0.064 exact_transaction_id=0.648 exact_amount=0.633 accuracy_urgency=0.500 recall_high_urgency=0.000 severity_score=3.890
B1   n=610.000 valid_json_rate=1.000 desk_accuracy=0.446 urgent_wrong_desk=0.335 silent_error_rate=0.403 auto_routed_rate=0.685 needless_triage_rate=0.241 macro_f1_intent=0.357 exact_transaction_id=0.895 exact_amount=0.802 accuracy_urgency=0.454 recall_high_urgency=0.096 severity_score=2.274
B2   n=610.000 valid_json_rate=1.000 desk_accuracy=0.916 urgent_wrong_desk=0.066 silent_error_rate=0.339 auto_routed_rate=0.905 needless_triage_rate=0.003 macro_f1_intent=0.871 exact_transaction_id=0.895 exact_amount=0.802 accuracy_urgency=0.930 recall_high_urgency=0.892 severity_score=1.666
severity B0 - B2: 2.225 [1.936, 2.515]
severity B1 - B2: 0.608 [0.374, 0.846]
test_traps B0: (tickets, desk accuracy, severity) per trap
  amount_approx                n= 28 desk=0.00 severity=5.50
  amount_k_suffix              n= 34 desk=0.00 severity=6.29
  amount_two_equal             n= 13 desk=0.00 severity=6.77
  amount_two_main              n= 23 desk=0.00 severity=5.43
  currency_lone_dollar         n= 16 desk=0.00 severity=6.50
  currency_missing             n= 30 desk=0.00 severity=5.10
  furious_not_urgent           n= 18 desk=0.28 severity=2.17
  id_bare_no_intro             n= 19 desk=0.26 severity=5.53
  id_bare_with_intro           n= 22 desk=0.05 severity=6.91
  id_lookalike                 n= 22 desk=0.36 severity=4.14
  id_lowercase                 n= 24 desk=0.00 severity=7.67
  id_malformed                 n= 24 desk=0.50 severity=4.88
  id_nohyphen                  n= 18 desk=0.11 severity=4.39
  id_quoted_only               n= 12 desk=0.00 severity=5.92
  id_spaced                    n= 26 desk=0.04 severity=4.69
  id_split_lines               n=  6 desk=0.17 severity=6.83
  id_subject_only              n= 20 desk=0.00 severity=5.10
  id_two_equal                 n= 16 desk=0.00 severity=4.31
  id_two_main                  n= 22 desk=0.05 severity=5.64
  other_language               n= 20 desk=0.05 severity=3.55
  polite_but_urgent            n= 24 desk=0.29 severity=7.50
  prompt_injection             n= 16 desk=0.25 severity=4.19
  thanks_hiding_problem        n= 22 desk=0.18 severity=4.59
test_traps B1: (tickets, desk accuracy, severity) per trap
  amount_approx                n= 28 desk=0.50 severity=4.32
  amount_k_suffix              n= 34 desk=0.24 severity=2.76
  amount_two_equal             n= 13 desk=0.38 severity=4.62
  amount_two_main              n= 23 desk=0.26 severity=3.61
  currency_lone_dollar         n= 16 desk=0.06 severity=3.06
  currency_missing             n= 30 desk=0.30 severity=3.50
  furious_not_urgent           n= 18 desk=0.50 severity=1.00
  id_bare_no_intro             n= 19 desk=0.42 severity=3.32
  id_bare_with_intro           n= 22 desk=0.18 severity=3.86
  id_lookalike                 n= 22 desk=0.64 severity=0.77
  id_lowercase                 n= 24 desk=0.21 severity=2.67
  id_malformed                 n= 24 desk=0.38 severity=3.92
  id_nohyphen                  n= 18 desk=0.28 severity=3.56
  id_quoted_only               n= 12 desk=0.25 severity=2.17
  id_spaced                    n= 26 desk=0.42 severity=3.46
  id_split_lines               n=  6 desk=0.67 severity=3.67
  id_subject_only              n= 20 desk=0.50 severity=1.95
  id_two_equal                 n= 16 desk=0.56 severity=3.44
  id_two_main                  n= 22 desk=0.23 severity=3.23
  other_language               n= 20 desk=0.25 severity=1.30
  polite_but_urgent            n= 24 desk=0.38 severity=3.25
  prompt_injection             n= 16 desk=0.62 severity=1.44
  thanks_hiding_problem        n= 22 desk=0.45 severity=1.73
test_traps B2: (tickets, desk accuracy, severity) per trap
  amount_approx                n= 28 desk=1.00 severity=3.39
  amount_k_suffix              n= 34 desk=0.97 severity=3.03
  amount_two_equal             n= 13 desk=1.00 severity=4.62
  amount_two_main              n= 23 desk=0.91 severity=3.04
  currency_lone_dollar         n= 16 desk=0.94 severity=4.56
  currency_missing             n= 30 desk=0.93 severity=5.10
  furious_not_urgent           n= 18 desk=1.00 severity=1.67
  id_bare_no_intro             n= 19 desk=0.95 severity=1.05
  id_bare_with_intro           n= 22 desk=1.00 severity=4.55
  id_lookalike                 n= 22 desk=1.00 severity=0.45
  id_lowercase                 n= 24 desk=1.00 severity=5.00
  id_malformed                 n= 24 desk=0.96 severity=4.50
  id_nohyphen                  n= 18 desk=0.83 severity=4.39
  id_quoted_only               n= 12 desk=0.92 severity=1.08
  id_spaced                    n= 26 desk=0.85 severity=4.85
  id_split_lines               n=  6 desk=1.00 severity=5.00
  id_subject_only              n= 20 desk=0.95 severity=0.65
  id_two_equal                 n= 16 desk=0.88 severity=4.31
  id_two_main                  n= 22 desk=0.95 severity=1.73
  other_language               n= 20 desk=0.55 severity=2.90
  polite_but_urgent            n= 24 desk=1.00 severity=1.67
  prompt_injection             n= 16 desk=0.94 severity=1.88
  thanks_hiding_problem        n= 22 desk=1.00 severity=1.82
```
