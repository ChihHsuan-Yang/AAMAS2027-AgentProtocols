# Manuscript terminology map — NOT COMPILED INTO THE PDF

**Binding on every worker touching reader-facing prose.**

The manuscript must not read like an internal experiment log. Internal arm
codes stay in code, filenames, analysis scripts, raw data columns and
provenance notes — they are stable identifiers and renaming them would break
reproducibility. They must not appear in prose a reviewer reads.

| internal code | manuscript wording (default in **bold**) |
|---|---|
| A | **role-structured** · "soft-role organization" where contrast with C is needed |
| B | **role-free** · "roles removed" |
| C | **structurally enforced** · "interface-enforced organization" |
| C′ | **context-restored enforcement control** — mention only if it answers a reviewer-relevant alternative explanation |

## Rules

1. **Never write "Arm A/B/C/C′" in `paper/sections/*.tex` or `main.tex`.**
2. Tables may carry a short header like `role-structured` / `role-free`;
   never a bare letter.
3. The dataset card explains the codes semantically; raw columns keep A/B/C/Cp.
4. Final gate before any freeze:
   `grep -n "Arm~\?[ABC]" paper/main.tex paper/sections/*.tex` must be empty.

## Why

A reader who meets "Arm B" has to hold an arbitrary mapping in working
memory for eight pages. A reader who meets "the role-free team" does not.
The science is identical; the cost of understanding it is not.
