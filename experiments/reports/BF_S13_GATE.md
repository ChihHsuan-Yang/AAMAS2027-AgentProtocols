# Sec.13 gate — does bf_control.py reproduce the frozen paper numbers?

**VERDICT: PASS.** The gate is satisfied; analysis may proceed once the cells
are complete.

## The test

`analysis/scripts/bf_control.py`'s own docstring fixes the pass condition:

> The A-vs-B block must reproduce the paper (Omni-MATH gemma-4: recovery 70/316
> vs 16/316; paired 37 vs 3 on n=237). If it does not, stop.

## Result, on the full frozen cell

| quantity | expected | reproduced |
|---|---|---|
| Arm A marginal recovery | 70/316 | **70/316** (0.2215) |
| Arm B marginal recovery | 16/316 | **16/316** (0.0506) |
| paired discordant, only A | 37 | **37** |
| paired discordant, only B | 3 | **3** |
| paired n | 237 | **237** |

All four figures match exactly (paired exact McNemar p = 1.95e-08).

Method note: the check **imports** `bf_control.py` and calls its own
`load / actor / fp_wrong / final_correct / mcnemar_exact`. A reimplementation
would have tested my code against the paper, not the script the directive names.

## An invocation hazard found on the way

Running the script as `--frozen <frozen> --bf <partial Bf file>` printed
`A 41/195, B 9/194, paired n=141 16 vs 1` — which **fails** the docstring
condition and, read literally, triggers the Sec.13 STOP.

That was my invocation, not the data. `bf_control.py` restricts every statistic
to `common = A ∩ B ∩ Bf` (line ~158) and prints a NOTE saying so. With Bf at
1,148 of 1,600 rows, the frozen A and B cells were silently cut to those 1,148
problems. Restricting the frozen cells to the same 1,148 by hand reproduces the
script's output exactly — `41/195`, `9/194`, `n=141`, `16` vs `1` — so the
restriction is the entire explanation and the frozen data is untouched.

**Consequence for the real run:** the Sec.13 gate must be evaluated on the FULL
frozen cell, never through a partial-Bf invocation. The script is not at fault
and must not be changed (Sec.21); the discipline is on the caller.

## Completion-order bias (why no interim number may be read)

The 1,148 finished problems are the *fast* ones, and fast means easy:

| Arm A (frozen), split by Bf completion | first-pass-wrong | final correct | recovery |
|---|---|---|---|
| finished (1,148) | 195/1148 = 0.170 | 0.866 | 41/195 = 0.210 |
| remaining (452) | 121/452 = **0.268** | 0.796 | 29/121 = 0.240 |

The hard tail is still outstanding, so any interim Bf statistic is computed on
an easier subset and will drift as that tail lands. Sec.10 forbids reading
interim results regardless; this quantifies why doing so would mislead.

## Status

Gate PASSED. No Bf result is read or interpreted here, per Sec.10 and Sec.13.

---

# S.13 gate, SECOND DOMAIN: SciBench

S.17 forbids inferring SciBench from Omni, so the gate is re-run against the
frozen SciBench cell with its own published numbers. The condition is stated
independently of me in `experiments/BF_CONTROL.md:177` ("SciBench: paired
n = 99, 21 vs 2. If they do not, the wrong frozen file was loaded").

As with Omni, the check **imports** `bf_control.py` and calls its own
`load / actor / fp_wrong / final_correct / mcnemar_exact` — a reimplementation
would test my code, not the script the directive names.

## Result, on the full frozen SciBench cell

```
/tmp/frozen_sci/scibench_AB.jsonl   2296 rows
  arm A  574 uids      arm B  574 uids
```

| quantity | published | reproduced | source of the published figure |
|---|---|---|---|
| marginal recovery A | 0.254 (30/118) | **30/118 = 0.2542** | `figures/README.md:277`, `notes/XDOMAIN-RESULTS.md:76` |
| marginal recovery B | 0.051 (6/118) | **6/118 = 0.0508** | `figures/README.md:277` |
| paired n | 99 | **99** | `README.md:67`, `results.tex:276` |
| paired discordant, only A | 21 | **21** | `README.md:67` |
| paired discordant, only B | 2 | **2** | `README.md:67` |
| paired recovery A | 0.212 | **21/99 = 0.2121** | `README.md:36`, `results.tex:276` |
| paired recovery B | 0.020 | **2/99 = 0.0202** | `README.md:36` |
| exact McNemar p | 6.6e-5 | **6.6e-05** | `README.md:36`, `results.tex:276` |

All eight reproduce. **S.13 PASS for SciBench.**

Both the marginal (0.254/0.051, n=118) and paired (0.212/0.020, n=99) pairs
reproduce, which matters because `notes/XDOMAIN-INTEGRATION-DECISION.md:94`
records a previous confusion between exactly these two. The gate checks both so
the Bf comparison later cannot be read against the wrong denominator.

## Caller discipline carries over

The Omni hazard applies unchanged: `bf_control.py` restricts all statistics to
`A ∩ B ∩ Bf`, so invoking it with a **partial** Bf file silently shrinks the
frozen cells and produces numbers that fail this gate for a reason that has
nothing to do with the data. The SciBench Bf cell is now complete (574/574,
`bf_status` exit 0), so the real invocation will not hit this — but the gate
above was evaluated on the **full frozen cell**, with no Bf file involved,
exactly as the Omni gate was.

## Both domains, gate status

| domain | gate | status |
|---|---|---|
| Omni-MATH | 70/316 vs 16/316; paired 37 vs 3, n=237 | **PASS** |
| SciBench | 30/118 vs 6/118; paired 21 vs 2, n=99 | **PASS** |

`bf_control.py` is unmodified (S.21).
