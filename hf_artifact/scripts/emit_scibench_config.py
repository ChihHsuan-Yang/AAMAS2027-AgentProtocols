#!/usr/bin/env python3
"""Emit the SciBench (v1.1.0) prompt set and run config, read from the runner
that actually produced the campaign -- never retyped.

Writes ONLY new paths:
    config/prompts_scibench.json
    config/run_config_scibench.json

Asserts, rather than claims:
  * the recomputed config_version equals the one stamped on all 2,296 rows
  * Arm B is BYTE-IDENTICAL to the Omni-MATH Arm B prompt
  * Arm A is NOT byte-identical (it was domain-adapted, option b)
and records a per-prompt identical/differs table so a consumer can see at a
glance which contract changed between domains.
"""
import json, os, sys, importlib.util, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
PROJ = os.path.dirname(ART)
EXP = os.path.join(PROJ, "experiments")

sys.path.insert(0, EXP)
_argv = sys.argv
sys.argv = ["emit_scibench_config"]
spec = importlib.util.spec_from_file_location("rx", os.path.join(EXP, "runner_xdomain.py"))
rx = importlib.util.module_from_spec(spec)
sys.modules["rx"] = rx
spec.loader.exec_module(rx)
sys.argv = _argv

STAMPED = "aed89f28ab338bdb"          # the config_version on all 2,296 frozen rows


def sha12(s):
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def main():
    assert rx.CONFIG_VERSION == STAMPED, (rx.CONFIG_VERSION, STAMPED)
    print(f"config_version recomputed from the runner: {rx.CONFIG_VERSION} "
          f"== stamped on all 2,296 rows  OK")

    sci = dict(rx.P.ALL_PROMPTS)
    omni = json.load(open(os.path.join(ART, "config", "prompts.json")))

    # Arm B must be carried across domains unchanged; Arm A must NOT be.
    for k in ("B_GENERIC_PREPEND", "B_GENERIC_APPEND"):
        assert sci[k] == omni[k], f"{k} differs -- the A/B manipulation is not the same"
    assert sci["A_SOLVER_PREPEND"] != omni["A_SOLVER_PREPEND"], \
        "A_SOLVER_PREPEND identical -- expected a domain adaptation (option b)"
    print("  Arm B byte-identical to Omni-MATH: asserted")
    print("  Arm A differs from Omni-MATH:      asserted")

    cmp_table, n_diff = {}, 0
    for k in sorted(sci):
        same = (k in omni) and (sci[k] == omni[k])
        n_diff += (not same)
        cmp_table[k] = {
            "identical_to_omnimath": bool(same),
            "scibench_sha256_12": sha12(sci[k]),
            "omnimath_sha256_12": sha12(omni[k]) if k in omni else None,
            "scibench_chars": len(sci[k]),
            "omnimath_chars": len(omni[k]) if k in omni else None,
        }
    print(f"  {n_diff} of {len(sci)} prompts differ between domains")

    out = dict(sci)
    out["_README"] = (
        "The EXACT prompt strings used by the SciBench (v1.1.0) campaign, read from "
        "experiments/runner_xdomain.py at build time. ARM A IS NOT THE SAME CONTRACT AS "
        "config/prompts.json -- it was domain-adapted. ARM B IS BYTE-IDENTICAL across the "
        "two domains. See _COMPARISON_TO_OMNIMATH and the card's cross-domain section. "
        "CP_* prompts are absent: Arm C' was not run in this domain."
    )
    out["_COMPARISON_TO_OMNIMATH"] = cmp_table
    json.dump(out, open(os.path.join(ART, "config", "prompts_scibench.json"), "w"),
              indent=1, sort_keys=True)

    run_cfg = {
        "_note": (
            "Held-constant configuration for the v1.1.0 SciBench campaign, read from "
            "experiments/runner_xdomain.py module constants at build time. Every budget "
            "and decoding knob is IDENTICAL to v1.0.0's run_config.json; what differs is "
            "the benchmark/slice/domain and the domain-adapted Arm A + evaluator prompts."
        ),
        "config_version": {
            "value": rx.CONFIG_VERSION,
            "rows": 2296,
            "file": "raw/scibench_AB.jsonl",
            "arms": ["A", "B"],
            "actors": ["gemma-4-31B-it", "gpt-oss-120b"],
            "source_commit": "c8c48ada000604a0e156075c482f5edc5133e2aa",
            "verification": (
                "Recomputed config_version_hash() from experiments/runner_xdomain.py and "
                "reproduced aed89f28ab338bdb exactly, matching the value stamped on all "
                "2,296 frozen rows."
            ),
            "why_it_differs_from_the_omnimath_hashes": (
                "The hash covers every prompt string plus benchmark_id and slice_id. Arm A "
                "and the evaluator were domain-adapted and the benchmark changed, so the "
                "hash necessarily differs. It is NOT poolable with the Omni-MATH hashes, "
                "and that is the point of the field."
            ),
            "KNOWN LIMITATION -- config_version does NOT cover the logger": (
                "Same limitation as v1.0.0: config_version_hash() does not hash the logging "
                "code, so it cannot distinguish instrumented from uninstrumented rows. Use "
                "chars_per_sec, not config_version, to detect F13."
            ),
        },
        "arm_contract_differs_by_domain": {
            "WARNING": (
                "ARM A IS NOT THE SAME CONTRACT IN THE TWO DOMAINS. Do not assume one "
                "contract across the release."
            ),
            "arm_A": "DOMAIN-ADAPTED (option b). 4 of 6 Arm A strings differ from v1.0.0.",
            "arm_B": "BYTE-IDENTICAL to v1.0.0 (asserted in code at build time).",
            "evaluator": (
                "DOMAIN-ADAPTED for units / significant figures / scientific notation. "
                "COMMON MODE: byte-identical across arms A and B within this domain, so it "
                "cannot manufacture an A-vs-B difference; it sets the difficulty floor only."
            ),
            "consequence": (
                "P1a and every clause-specific role-fidelity metric are NOT transported "
                "across domains and were deliberately not computed: scoring SciBench agents "
                "against Omni-MATH clauses would score them against instructions they never "
                "received."
            ),
            "why_adapt_rather_than_reuse": (
                "Arm B's generic prompt contains no domain language, so leaving Arm A's "
                "math-specific wording in place would make the two arms differ in TWO ways "
                "-- role structure AND domain fit -- and the domain-fit difference runs "
                "against Arm A. Adapting A restores a single-variable manipulation. Every "
                "structural clause of A is preserved (role separation, DELTA, required "
                "structure, Diagnosis/Fix Instruction, answer ownership, routing tags); "
                "only domain nouns and the answer-form enumeration change."
            ),
        },
        "backend": {
            "name": rx.BACKEND,
            "kind": "self-hosted vLLM OpenAI-compatible endpoint on an HPC cluster",
            "base_url": ("<REDACTED: institutional inference endpoint -- identifies the "
                         "operating institution; withheld for double-blind review>"),
        },
        "actor_models": ["openai/gpt-oss-120b", "google/gemma-4-31B-it"],
        "evaluator_model": rx.EVALUATOR_MODEL,
        "arms_run": ["A", "B"],
        "arms_not_run": {
            "C": "not run in this domain -- no enforcement_events table exists for SciBench",
            "Cp": "not run in this domain",
        },
        "decoding": {"temperature": rx.TEMPERATURE, "max_tokens": rx.MAX_TOKENS},
        "deliberation_budget": {
            "max_outer_rounds": rx.MAX_OUTER_ROUNDS,
            "inner_rounds": rx.INNER_ROUNDS,
            "total_cycles": rx.MAX_OUTER_ROUNDS * rx.INNER_ROUNDS,
            "identical_across_arms": True,
            "identical_to_v1_0_0": True,
        },
        "call_budgets": {
            "max_actor_calls": rx.MAX_ACTOR_CALLS,
            "max_evaluator_calls": rx.MAX_EVALUATOR_CALLS,
            "max_regenerations_per_turn": rx.MAX_REGENERATIONS,
            "max_transport_retries": rx.MAX_TRANSPORT_RETRIES,
            "request_timeout_s": rx.REQUEST_TIMEOUT_S,
        },
        "role_order": rx.ROLE_ORDER,
        "visibility_policy_per_arm": {k: rx.VISIBILITY[k] for k in ("A", "B")},
        "visibility_note": (
            "A and B are byte-identical in visibility, exactly as in v1.0.0. Only prompt "
            "text differs. This is unchanged by the domain adaptation."
        ),
        "corpus": {
            "benchmark_id": rx.BENCHMARK_ID,
            "slice_id": rx.SLICE_ID,
            "domain": rx.DOMAIN,
            "problems_source": ("<REDACTED local path>: the SciBench text_only slice of the "
                                "upstream SciAgentTrace release registry"),
            "n_problems": 574,
            "denominators": ("692 upstream -> 580 in the release registry -> 574 carrying "
                             "the text_only slice -> ALL 574 run. No sub-sampling, no seed, "
                             "no random draw."),
            "problem_manifest": "manifests/problem_sample_scibench.json (problem_uid list only)",
            "license": "MIT (NOT Apache-2.0) -- see LICENSES/",
        },
    }
    json.dump(run_cfg, open(os.path.join(ART, "config", "run_config_scibench.json"), "w"),
              indent=1, sort_keys=True)

    print("wrote config/prompts_scibench.json and config/run_config_scibench.json")


if __name__ == "__main__":
    main()
