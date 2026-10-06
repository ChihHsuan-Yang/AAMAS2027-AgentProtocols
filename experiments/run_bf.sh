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
# Optional: CONC=20 (per-actor and global concurrency), ONLY=omni|scibench|bridge
#           or a comma list such as ONLY=omni,scibench,
#           DRY=1 (zero API calls: the runner's --dry-run on its 2 stub problems),
#           WARM=0 (skip the warm-up probe), WARM_MIN=90 (warm-up limit, minutes)
set -u
D=${1:?usage: run_bf.sh <output dir>}
: "${AAMAS_AUTH_SCRIPT_DIR:?export AAMAS_AUTH_SCRIPT_DIR first}"
: "${AAMAS_PROBLEMS_PARQUET:?export AAMAS_PROBLEMS_PARQUET first}"
CONC=${CONC:-20}
ONLY=${ONLY:-all}
ACTOR=${ACTOR:-google/gemma-4-31B-it}   # e.g. openai/gpt-oss-120b, meta-llama/Llama-3.3-70B-Instruct
TAG=${TAG:-gemma4}                     # file-name tag; default keeps the gemma-4 file names
N_OMNI=${N_OMNI:-1600}                 # Llama-3.3's frozen cells are n=400
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
    if python3 experiments/bf_status.py "$out" --n "$n" --arm "$arm" --actor "${ACTOR##*/}" --quiet; then
      echo "[run_bf] $(date '+%F %T') $rid COMPLETE" | tee -a "$out.log"
      return 0
    fi
    echo "[run_bf] $(date '+%F %T') $rid incomplete after pass $pass; waiting" | tee -a "$out.log"
    sleep $((pass * 120))
  done
  echo "[run_bf] $(date '+%F %T') $rid NOT COMPLETE after 4 passes -- check $out.log" | tee -a "$out.log"
  return 1
}

want () { [ "$ONLY" = all ] || case ",$ONLY," in *",$1,"*) true ;; *) false ;; esac; }

# A cold model answers "503 not ready" for 15-30 min after the first request;
# wait for it here rather than letting the 4 passes run out (WARM=0 skips).
if [ "${DRY:-0}" != 1 ] && [ "${WARM:-1}" = 1 ]; then
  python3 experiments/bf_warm.py "$ACTOR" --minutes "${WARM_MIN:-90}" || \
    echo "[run_bf] $(date '+%F %T') $ACTOR did not answer during warm-up; starting anyway"
fi

want omni && \
  job runner.py "$N_OMNI" Bf "$D/bf_omnimath_${TAG}.jsonl" "bf-${TAG}-n${N_OMNI}"
want scibench && \
  job runner_xdomain.py 574 Bf "$D/bf_scibench_${TAG}.jsonl" "bf-${TAG}-scibench"
want bridge && \
  job runner.py 400 A "$D/bridgeA_omnimath_${TAG}_n400.jsonl" "bridgeA-${TAG}-n400"

echo "[run_bf] $(date '+%F %T') all jobs finished; sha256:"
shasum -a 256 "$D"/*.jsonl 2>/dev/null || sha256sum "$D"/*.jsonl
