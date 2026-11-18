# Trace case: first wrong decision and regression check

Reproduction commands (run from `src/`):
```powershell
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`; report `E-seeded_regression-20261118-b546` (`src/reports/eval_seeded_regression.json`). |
| Triệu chứng | `trial_pass` fails (`status resolved != denied`). `DbFactKept` fails on an override and `RefundAmountCorrect` fails (`ledger=20000 != label=0`). Reply says 20,000đ was refunded; expected status is denied and expected refund is 0đ. |
| Bước sai đầu tiên | Event **3**, `model_override`, payload `{"delay_days": 5}`. |
| Vì sao là bước đầu tiên | Event 1 creates the expected read-only handoff. Event 2 reads order O-202 from the database with `delay_days=2`. Event 3 replaces that value with the ticket's five-day claim. Event 4 then quotes 20,000đ and the agent records the incorrect refund. |
| Failure mode | FM-03, `ticket_trust` — trusts the ticket over the database. |
| Đối chứng | `fixed C-002@11`; report `E-fixed-20261118-b546` (`src/reports/eval_fixed.json`). There is no `model_override`; event 3 quotes 0đ with `no_entitlement`, then the reply correctly denies the request. Ledger is 0đ and status is `denied`. |
| Regression test | `src/tests/test_lab9_graders.py::test_c002_seed11_regression_fails_and_fixed_passes`. The test asserts `DbFactKept` and `RefundAmountCorrect` fail on `seeded_regression` and pass on `fixed`. The targeted grader test file passed: 8 tests. |
| Chưa chắc chắn | This deterministic MockLLM trace demonstrates the seeded override path. It does not estimate how often a real model would make the same mistake or detect a quiet override with no `model_override` event. |

Read the ledger as well as the reply: a plausible customer-facing message does not prove the refund was correct.
