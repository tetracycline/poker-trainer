#!/usr/bin/env bash
set -euo pipefail
branch=fix/nl2-hu-lines-audit-20261118
test "${GITHUB_REF_NAME:-}" = "$branch"
test "${GITHUB_REPOSITORY:-}" = tetracycline/poker-trainer
receipts=${1:?expected authenticated receipt directory}
solver=${2:?expected pinned solver checkout}
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
for attempt in 1 2 3; do
  git fetch --no-tags origin "$branch"
  latest=$(git rev-parse FETCH_HEAD)
  git merge-base --is-ancestor "$GITHUB_SHA" "$latest"
  check=$(mktemp -d)
  git worktree add -q --detach "$check" "$latest"
  (
    cd "$check"
    registry=data/nl2_hu_multiboard_status_current.json
    cp "$registry" "$RUNNER_TEMP/b668-before.json"
    python tools/hu_b668_publish_rank35.py --receipts "$receipts" --solver "$solver"
    python tools/hu_apply_cert_extensions.py --out "$registry"
    python - "$RUNNER_TEMP/b668-before.json" "$registry" <<'PY'
import json,sys
before,after=(json.load(open(p))["records"] for p in sys.argv[1:])
target="ln-iso-lmp_r_model-pjewx6"
assert before.keys()==after.keys()
assert all(before[k]==after[k] for k in before if k!=target)
row=after[target]
assert row["label"]=="CERT-MULTIBOARD" and row["proven_exact_board_count"]==4
assert row["assumed_model_node_spr"]==19.55
assert all(b["strict_full_street_combo_reachable"]>0 for b in row["certified_3_to_5_exact_flop_boards"])
PY
    node tools/hu_extension_runtime_test.cjs "$registry"
    bash tools/hu_exact_batch_audit.sh "$registry"
    node tools/hu_b492_medium_tree_ui.cjs
    node tools/hu_b584_optional_river_ui.cjs
    git add "$registry" data/nl2_hu_verified_extensions.json       data/nl2_hu_model_history_crosswalk.json data/nl2_hu_model_source_references.json       data/nl2_hu_b642_locked_medium.json data/nl2_hu_b668_rank35_replay.json       data/solver_evidence/reverified/rank35.json       data/solver_evidence/NL2_B642_R35_*.zip       data/solver_evidence/NL2_MULTIBOARD_B642_R35_*.json.gz
    git diff --cached --check
    if ! git diff --cached --quiet; then
      git commit -m 'B668 certify rank35 on four native boards with measured river locks'
    fi
  )
  if git -C "$check" push origin "HEAD:refs/heads/$branch"; then
    (
      cd "$check"
      git rev-parse HEAD | tee "$RUNNER_TEMP/b668-published-sha.txt"
      registry=data/nl2_hu_multiboard_status_current.json
      python tools/hu_apply_cert_extensions.py --out "$RUNNER_TEMP/b668-replay.json"
      cmp "$registry" "$RUNNER_TEMP/b668-replay.json"
      git diff --exit-code -- data/nl2_hu_verified_extensions.json         data/nl2_hu_model_history_crosswalk.json data/nl2_hu_model_source_references.json
      node tools/hu_extension_runtime_test.cjs "$registry"
      bash tools/hu_exact_batch_audit.sh "$registry"
      git fetch --quiet --no-tags --depth=1 origin d0fe026b3cd59b50450f99471bd27c55e7d4b522
      python tools/hu_b491_incremental_medium.py
      node tools/hu_b491_incremental_medium.cjs
      node tools/hu_b483_lock_medium_ui.cjs
      node tools/hu_b485_medium_viewers.cjs
      node tools/hu_b492_medium_tree_ui.cjs
      node tools/hu_b584_optional_river_ui.cjs
      python tools/hu_current_medium_coverage.py --out "$RUNNER_TEMP/b668-coverage.json"
    )
    git worktree remove --force "$check"
    exit 0
  fi
  git worktree remove --force "$check"
done
exit 1
