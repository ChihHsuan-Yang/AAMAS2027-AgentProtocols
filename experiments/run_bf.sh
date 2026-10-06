#!/usr/bin/env bash
# run_bf.sh -- the overnight Bf campaign, in order, until every cell is complete.
#
#   1. Omni-MATH  Arm Bf   n=1600   (the headline control)
#   2. SciBench   Arm Bf   n=574    (the replication domain)
#   3. Omni-MATH  Arm A    n=400    (bridge: has the endpoint drifted since 9-30?
#                                   check only, never pooled into any table)
#
# Each cell: requeue infra failures -> run -> requeue -> completion check, up to
# 4 passes. Completion = bf_status.py exits 0 (n problems, no pending infra rows).
#
# Usage, from the worktree root, with the python3 that has pandas/pyarrow/httpx/globus-sdk:
#   export AAMAS_AUTH_SCRIPT_DIR=...  AAMAS_PROBLEMS_PARQUET=...
#   bash experiments/run_bf.sh /Users/lxy/AAMAS/AAMAS2027-AgentProtocols/experiments/results/bf
#
# Optional: CONC=20 (per-actor and global concurrency), ONLY=omni|scibench|bridge,
#           DRY=1 (zero API calls: the runner's --dry-run on its 2 stub problems)
set -u
D=${1:?usage: run_bf.sh <output dir>}
: "${AAMAS_AUTH_SCRIPT_DIR:?export AAMAS_AUTH_SCRIPT_DIR first}"
: "${AAMAS_PROBLEMS_PARQUET:?export AAMAS_PROBLEMS_PARQUET first}"
CONC=${CONC:-20}
ONLY=${ONLY:-all}
ACTOR=google/gemma-4-31B-it
EXTRA=""
[ "${DRY:-0}" = 1 ] && EXTRA="--dry-run"
mkdir -p "$D"
KEEP=""
command -v caffeinate >/dev/null 2>&1 && KEEP="caffeinate -i"

job () {  # runner n arm out run_id
  local runner=$1 n=$2 arm=$3 out=$4 rid=$5 pass
  [ "${DRY:-0}" = 1 ] && n=2
  for pass in 1 2 3 4; do
    python3 experiments/bf_requeue.py "$out"
    echo "[run_bf] $(date '+%F %T') $rid pass $pass start" | tee -a "$out.log"
    $KEEP python3 "experiments/$runner" --n "$n" --arms "$arm" --actors "$ACTOR" \
        --out "$out" --run-id "$rid" --concurrency "$CONC" --actor-concurrency "$CONC" $EXTRA \
        >> "$out.log" 2>&1
    python3 experiments/bf_requeue.py "$out"
    if python3 experiments/bf_status.py "$out" --n "$n" --arm "$arm" --quiet; then
      echo "[run_bf] $(date '+%F %T') $rid COMPLETE" | tee -a "$out.log"
      return 0
    fi
    echo "[run_bf] $(date '+%F %T') $rid incomplete after pass $pass; waiting" | tee -a "$out.log"
    sleep $((pass * 120))
  done
  echo "[run_bf] $(date '+%F %T') $rid NOT COMPLETE after 4 passes -- check $out.log" | tee -a "$out.log"
  return 1
}

[ "$ONLY" = all ] || [ "$ONLY" = omni ] && \
  job runner.py 1600 Bf "$D/bf_omnimath_gemma4.jsonl" bf-gemma4-n1600
[ "$ONLY" = all ] || [ "$ONLY" = scibench ] && \
  job runner_xdomain.py 574 Bf "$D/bf_scibench_gemma4.jsonl" bf-gemma4-scibench
[ "$ONLY" = all ] || [ "$ONLY" = bridge ] && \
  job runner.py 400 A "$D/bridgeA_omnimath_gemma4_n400.jsonl" bridgeA-gemma4-n400

echo "[run_bf] $(date '+%F %T') all jobs finished; sha256:"
shasum -a 256 "$D"/*.jsonl 2>/dev/null || sha256sum "$D"/*.jsonl
