# Baseline results (B0 majority, B1 rules, B2 TF-IDF + logistic regression)

Run on 2026-11-01 with `scripts/run_baselines.py --final`, on the dataset committed in `data/dataset/` (train 1922, val 293, test_natural 610, test_traps 380), following `docs/scoring_protocol.md`. B2's regularisation (C=10) was chosen on val only. The test sets were scored once, after the dataset was final. Cost weights are the relative ASSUMPTION of the protocol (triage 1, wrong desk 3, wrong reference 5, wrong desk on an urgent ticket 10).

Headline (test_natural): B2 reaches 0.916 desk accuracy and 0.066 urgent tickets in the wrong desk, at 1.666 cost per ticket. B1 costs 0.608 more per ticket than B2 (interval 0.374 to 0.846) and B0 2.225 more (1.936 to 2.515). The reference fields (`transaction_id`, `amount`, `currency`) are extracted by the same regular expressions in B1 and B2, so the model D has to beat B2 mostly there and on the trap types (per-trap numbers are counts: no interval below 20 tickets).

```
val (293 tickets), B2 C=10.0
B0   n=293.000 valid_json_rate=1.000 desk_accuracy=0.215 urgent_wrong_desk=0.759 confident_and_wrong=0.785 abstention_rate=0.000 macro_f1_intent=0.059 exact_transaction_id=0.648 exact_amount=0.642 accuracy_urgency=0.471 recall_high_urgency=0.000 cost_per_ticket=3.925
B1   n=293.000 valid_json_rate=1.000 desk_accuracy=0.403 urgent_wrong_desk=0.392 confident_and_wrong=0.530 abstention_rate=0.266 macro_f1_intent=0.321 exact_transaction_id=0.894 exact_amount=0.829 accuracy_urgency=0.464 recall_high_urgency=0.203 cost_per_ticket=2.509
B2   n=293.000 valid_json_rate=1.000 desk_accuracy=0.949 urgent_wrong_desk=0.076 confident_and_wrong=0.051 abstention_rate=0.137 macro_f1_intent=0.927 exact_transaction_id=0.894 exact_amount=0.829 accuracy_urgency=0.952 recall_high_urgency=0.911 cost_per_ticket=1.478
test_natural (610 tickets)
B0   n=610.000 valid_json_rate=1.000 desk_accuracy=0.236 urgent_wrong_desk=0.778 confident_and_wrong=0.764 abstention_rate=0.000 macro_f1_intent=0.064 exact_transaction_id=0.648 exact_amount=0.633 accuracy_urgency=0.500 recall_high_urgency=0.000 cost_per_ticket=3.890
B1   n=610.000 valid_json_rate=1.000 desk_accuracy=0.446 urgent_wrong_desk=0.335 confident_and_wrong=0.457 abstention_rate=0.315 macro_f1_intent=0.357 exact_transaction_id=0.895 exact_amount=0.802 accuracy_urgency=0.454 recall_high_urgency=0.096 cost_per_ticket=2.274
B2   n=610.000 valid_json_rate=1.000 desk_accuracy=0.916 urgent_wrong_desk=0.066 confident_and_wrong=0.089 abstention_rate=0.095 macro_f1_intent=0.871 exact_transaction_id=0.895 exact_amount=0.802 accuracy_urgency=0.930 recall_high_urgency=0.892 cost_per_ticket=1.666
cost B0 - B2: 2.225 [1.936, 2.515]
cost B1 - B2: 0.608 [0.374, 0.846]
test_traps B0: (tickets, desk accuracy, cost) per trap
  amount_approx                n= 28 desk=0.00 cost=5.50
  amount_k_suffix              n= 34 desk=0.00 cost=6.29
  amount_two_equal             n= 13 desk=0.00 cost=6.77
  amount_two_main              n= 23 desk=0.00 cost=5.43
  currency_lone_dollar         n= 16 desk=0.00 cost=6.50
  currency_missing             n= 30 desk=0.00 cost=5.10
  furious_not_urgent           n= 18 desk=0.28 cost=2.17
  id_bare_no_intro             n= 19 desk=0.26 cost=5.53
  id_bare_with_intro           n= 22 desk=0.05 cost=6.91
  id_lookalike                 n= 22 desk=0.36 cost=4.14
  id_lowercase                 n= 24 desk=0.00 cost=7.67
  id_malformed                 n= 24 desk=0.50 cost=4.88
  id_nohyphen                  n= 18 desk=0.11 cost=4.39
  id_quoted_only               n= 12 desk=0.00 cost=5.92
  id_spaced                    n= 26 desk=0.04 cost=4.69
  id_split_lines               n=  6 desk=0.17 cost=6.83
  id_subject_only              n= 20 desk=0.00 cost=5.10
  id_two_equal                 n= 16 desk=0.00 cost=4.31
  id_two_main                  n= 22 desk=0.05 cost=5.64
  other_language               n= 20 desk=0.05 cost=3.55
  polite_but_urgent            n= 24 desk=0.29 cost=7.50
  prompt_injection             n= 16 desk=0.25 cost=4.19
  thanks_hiding_problem        n= 22 desk=0.18 cost=4.59
test_traps B1: (tickets, desk accuracy, cost) per trap
  amount_approx                n= 28 desk=0.50 cost=4.32
  amount_k_suffix              n= 34 desk=0.24 cost=2.76
  amount_two_equal             n= 13 desk=0.38 cost=4.62
  amount_two_main              n= 23 desk=0.26 cost=3.61
  currency_lone_dollar         n= 16 desk=0.06 cost=3.06
  currency_missing             n= 30 desk=0.30 cost=3.50
  furious_not_urgent           n= 18 desk=0.50 cost=1.00
  id_bare_no_intro             n= 19 desk=0.42 cost=3.32
  id_bare_with_intro           n= 22 desk=0.18 cost=3.86
  id_lookalike                 n= 22 desk=0.64 cost=0.77
  id_lowercase                 n= 24 desk=0.21 cost=2.67
  id_malformed                 n= 24 desk=0.38 cost=3.92
  id_nohyphen                  n= 18 desk=0.28 cost=3.56
  id_quoted_only               n= 12 desk=0.25 cost=2.17
  id_spaced                    n= 26 desk=0.42 cost=3.46
  id_split_lines               n=  6 desk=0.67 cost=3.67
  id_subject_only              n= 20 desk=0.50 cost=1.95
  id_two_equal                 n= 16 desk=0.56 cost=3.44
  id_two_main                  n= 22 desk=0.23 cost=3.23
  other_language               n= 20 desk=0.25 cost=1.30
  polite_but_urgent            n= 24 desk=0.38 cost=3.25
  prompt_injection             n= 16 desk=0.62 cost=1.44
  thanks_hiding_problem        n= 22 desk=0.45 cost=1.73
test_traps B2: (tickets, desk accuracy, cost) per trap
  amount_approx                n= 28 desk=1.00 cost=3.39
  amount_k_suffix              n= 34 desk=0.97 cost=3.03
  amount_two_equal             n= 13 desk=1.00 cost=4.62
  amount_two_main              n= 23 desk=0.91 cost=3.04
  currency_lone_dollar         n= 16 desk=0.94 cost=4.56
  currency_missing             n= 30 desk=0.93 cost=5.10
  furious_not_urgent           n= 18 desk=1.00 cost=1.67
  id_bare_no_intro             n= 19 desk=0.95 cost=1.05
  id_bare_with_intro           n= 22 desk=1.00 cost=4.55
  id_lookalike                 n= 22 desk=1.00 cost=0.45
  id_lowercase                 n= 24 desk=1.00 cost=5.00
  id_malformed                 n= 24 desk=0.96 cost=4.50
  id_nohyphen                  n= 18 desk=0.83 cost=4.39
  id_quoted_only               n= 12 desk=0.92 cost=1.08
  id_spaced                    n= 26 desk=0.85 cost=4.85
  id_split_lines               n=  6 desk=1.00 cost=5.00
  id_subject_only              n= 20 desk=0.95 cost=0.65
  id_two_equal                 n= 16 desk=0.88 cost=4.31
  id_two_main                  n= 22 desk=0.95 cost=1.73
  other_language               n= 20 desk=0.55 cost=2.90
  polite_but_urgent            n= 24 desk=1.00 cost=1.67
  prompt_injection             n= 16 desk=0.94 cost=1.88
  thanks_hiding_problem        n= 22 desk=1.00 cost=1.82
```
