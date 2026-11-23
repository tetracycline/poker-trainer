#!/usr/bin/env bash
# Build one audited commit and transfer it only across changes outside its verified inputs.
set -euo pipefail
branch=fix/nl2-hu-lines-audit-20261118
patch=tools/hu_b533_trainer_routes.patch
registry=data/nl2_hu_multiboard_status_current.json
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git fetch --quiet --no-tags origin d0fe026b3cd59b50450f99471bd27c55e7d4b522

disjoint() {
  python - "$1" "$2" "$3" <<'PY'
import os,re,subprocess,sys
base,tip,candidate=sys.argv[1:]
changed=subprocess.check_output(['git','diff','--no-renames','--name-only','-z',base,tip]).split(b'\0')
for path in (os.fsdecode(p) for p in changed if p):
    # An Actions workflow is never read by the trainer, generator, or native proof replay.
    if path.startswith('.github/workflows/') and path not in (
        '.github/workflows/nl2-hu-b549-current-registry.yml','.github/workflows/nl2-hu-full-batch-audit.yml'):
        continue
    added=subprocess.run(['git','cat-file','-e',base+':'+path],stderr=subprocess.DEVNULL).returncode!=0
    # Only additions of uniquely named future solver scripts or frozen input plans can be disjoint.
    # New medium reports, board manifests, source archives and all existing files force a fresh audit.
    script=re.fullmatch(r'tools/(hu_b[0-9]+_[a-z0-9_]+)\.(?:py|cjs)',path)
    plan=re.fullmatch(r'data/(nl2_hu_b[0-9]+_[a-z0-9_]*(?:flops|originals|artifacts))\.json',path)
    if added and (script or plan):
        name=(script or plan)[1]
        referenced=subprocess.run(['git','grep','-q','-F','-e',name,candidate,'--',
                                   'tools','*.js','*.cjs','*.py','*.html','*.sh']).returncode
        if referenced==1:
            continue
    print('Rebuilding for changed audit input:',path)
    sys.exit(1)
PY
}

for generation in 1 2 3 4 5 6; do
  git fetch --quiet --no-tags origin "$branch"
  base=$(git rev-parse FETCH_HEAD)
  git merge-base --is-ancestor "$GITHUB_SHA" "$base"
  live=$(mktemp -d "$RUNNER_TEMP/b549.XXXXXX")
  git worktree add --quiet --detach "$live" "$base"
  (
    cd "$live"
    if test -f "$patch"; then
      git apply --3way "$patch"
      git rm -- "$patch"
    fi
    test -f tools/hu_trainer_route_gate.py && test -f tools/hu_trainer_route_contract.cjs
    python tools/hu_apply_cert_extensions.py --out "$registry"
    python tools/hu_b549_rank8_sources.py
    python - <<'PY'
import json
from pathlib import Path
records=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
assert len(records)==392
for rank in (8,100):
    group=json.loads(Path(f'data/solver_evidence/reverified/rank{rank}.json').read_bytes())
    record=records[group['model_id']]
    assert record['label']=='CERT-MULTIBOARD' and len(group['boards'])>=3
    assert {b['public_board'] for b in group['boards']}=={b['public_board'] for b in record['certified_3_to_5_exact_flop_boards']}
PY
    node tools/hu_extension_runtime_test.cjs "$registry"
    bash tools/hu_exact_batch_audit.sh "$registry"
    python tools/hu_b491_incremental_medium.py
    node tools/hu_b491_incremental_medium.cjs
    node tools/hu_b483_lock_medium_ui.cjs
    node tools/hu_b485_medium_viewers.cjs
    node tools/hu_b492_medium_tree_ui.cjs
    if test -f data/nl2_hu_b530_locked_medium.json; then
      node tools/hu_b530_history_rates_ui.cjs
    fi
    python tools/hu_current_medium_coverage.py --out "$RUNNER_TEMP/current-medium-coverage.json"
    git add -- "$registry" data/nl2_hu_verified_extensions.json data/nl2_hu_model_history_crosswalk.json data/nl2_hu_model_source_references.json
    git diff --cached --check
    if ! git diff --cached --quiet; then
      git commit -m 'B549: publish trainer route validation and the audited current exact-board registry'
    fi
  )
  candidate=$(git -C "$live" rev-parse HEAD)
  for push_attempt in $(seq 1 24); do
    git fetch --quiet --no-tags origin "$branch"
    tip=$(git rev-parse FETCH_HEAD)
    git merge-base --is-ancestor "$base" "$tip"
    if test "$tip" != "$base" && ! disjoint "$base" "$tip" "$candidate"; then
      break
    fi
    if test "$candidate" = "$base"; then
      exit 0
    fi
    if test "$tip" != "$base"; then
      git -C "$live" switch --quiet --detach "$tip"
      git -C "$live" cherry-pick "$candidate"
    fi
    if git -C "$live" push origin "HEAD:refs/heads/$branch"; then
      exit 0
    fi
  done
  git worktree remove "$live"
done
exit 1
