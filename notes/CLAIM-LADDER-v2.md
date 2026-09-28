# Claim ladder v2 — post-validation, post-novelty-audit (2026-09-28)

Conservative. Each level states the strongest claim **currently justified**.

## OBSERVATION — what the existing corpus supports now

> **O1.** Prompted PER roles are highly distinguishable from behaviour alone
> (0.896 balanced accuracy, function-only features, trajectory-grouped CV), but
> that separability rests on **output formatting and answer commitment**, not on
> the cognitive division the contract governs: restricted to computation
> behaviour it falls to **0.714**, against a length-only nuisance control of
> **0.768**.

> **O2.** Compliance with individual clauses of one contract ranges from
> **0.961** (decomposes) to **0.042** (abstains from computing), and the two
> "MUST NOT" clauses in the same prompt block diverge sharply
> (abstains-from-answering 0.540 vs abstains-from-computing 0.042).

> **O3.** Realized fidelity differs across actor models given **byte-identical
> prompts within a domain**: P1a gemma3 .266 / gemma_4 .111 / gpt_oss .042;
> E2v2 gemma_4 .243 / gemma3 .112 / gpt_oss .062. **All six pairwise
> differences significant** under frozen, human-validated metrics (κ 0.81/0.84).

> **O4.** The two fidelity components **order the actors differently**. There is
> no single "most faithful" actor. gpt_oss_120b is last on both.

**Not claimable:** that role labels fail to induce distinct behaviour (O1
refutes it); anything about domains (contracts differ by domain); role-fidelity
variation as *novel* (MAST FM-1.2; 2604.02770; 2604.03809).

## MECHANISM HYPOTHESIS — what remains plausible

> **M1.** The value of a role-based organization depends on whether the actor
> substrate realizes the intended division of labor, rather than on the role
> specification itself.

Supporting but **not** establishing: the organization × actor interaction is
real and large (paired on 828 common problems, **+0.1522 [+0.1135,+0.1896]**),
and the P1a ordering aligns with it. Against: the E2v2 ordering does not, and
only **2 of 3** actors have the coverage to enter the comparison at all.

> **M2 (the dissociating hypothesis).** What matters is **realized fidelity**,
> not model capability. On the one pair where both are measurable, they are
> **anti-correlated** (gpt_oss: capability .568, P1a .042; gemma3: .425, .266).
> A capability-equalizer account (2608.21747) and a fidelity account therefore
> make **opposite** predictions for gpt_oss.

**Mediation is not estimable** from existing data: 3 actors, 2 usable, and two
components that disagree.

## INTERVENTION CLAIM — what Arm C must show

> **I1 (manipulation check, prerequisite).** Arm C drives P1a to ≈1.0 with a
> **non-zero, logged** rejection/regeneration count. Zero rejections = the
> constraint never bound = every downstream result void.

> **I2.** A change in realized fidelity (P1a, E2v2) between A and C, per actor.

> **I3 (the claim).** An **actor × intervention interaction** on task outcome.
> A main effect alone is 2608.21747 transplanted and is not sufficient.

> **I4 (the discriminating result).** The benefit tracks **low realized
> fidelity** rather than **low capability**. Since these are anti-correlated in
> our panel, the design can falsify our framing — and we report it if it does.

## GENERALIZATION CLAIM — what the third actor buys

With **two** actors an interaction is a single difference-of-differences: one
number, indistinguishable from an idiosyncrasy of gemma3, and unable to separate
a capability ordering from a fidelity ordering (with 2 points every ordering is
monotone in everything).

With **three** actors we can state:

> **G1.** The intervention's effect is **ordered by realized fidelity across
> three substrates**, and that ordering is **not** the capability ordering.

That is the difference between "we found an interaction" and "we identified what
the interaction is ordered by" — and it is exactly the claim 2608.21747 cannot
make, because capability is the only axis it varies.

**Still not claimable even with three actors:** any causal claim about *why* a
given substrate realizes roles differently; a sign reversal (retracted —
gpt_oss is not significantly positive on the common problem set); and
generality beyond the two domains run.
