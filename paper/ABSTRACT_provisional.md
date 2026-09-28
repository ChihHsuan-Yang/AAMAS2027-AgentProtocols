# Provisional abstract — AAMAS 2027 (Oct 1 registration)

**Status:** frames the question, claims no unrun result. Every number is already
measured in existing traces and is reproducible from `analysis/scripts/`.

---

## v2 (233 words) — RECOMMENDED

Multi-agent LLM systems are commonly organized by assigning agents roles —
Planner, Executor, Reviewer — and describing each role's function in natural
language. Whether those descriptions produce a functional division of labor, and
whether that depends on which model fills the roles, is rarely measured.

We separate two constructs that are usually conflated. **Role distinguishability**
asks whether an observer can recover an agent's role from its behavior alone;
**role fidelity** asks whether an agent performs the function its contract
assigns, scored clause-by-clause against the contract that agent actually
received. Across 145,411 role messages from matched Planner–Executor–Reviewer
trajectories, the two dissociate. Roles are highly distinguishable (0.90
balanced accuracy from behavioral features), but that separability rests on
output formatting and answer commitment rather than on the cognitive division
the contract specifies: restricted to computation behavior, role separability
falls to 0.71, barely above a message-length control. Fidelity to individual
clauses of one contract ranges from 0.96 to 0.04, and differs sharply across
actor models given byte-identical prompts. We validate these measures against
human annotation and report where automated proxies fail.

We then ask whether enforcing the division of labor **architecturally** — through
interfaces that make contract violation unrepresentable, rather than through
stronger prompting — changes the effectiveness of the same organization, and
whether that effect depends on the actor model.

---

## Notes

- Final paragraph is deliberately a question, not a result. If the experiment
  completes before Oct 8, replace with the outcome; if not, it still stands.
- Avoids the arXiv:2609.27822 boundary entirely: no confidence, routing,
  calibration, commitment, or speaker selection.
- Does **not** claim roles are cosmetic — our own data refutes that.
- Numbers used: 145,411 messages (r1); 0.896→0.90 balanced accuracy and
  0.714→0.71 computation-only AUC (r2); 0.961 / 0.042 clause range (r7).
