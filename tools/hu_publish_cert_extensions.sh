#!/usr/bin/env bash
# Regenerate against the live draft branch on each non-fast-forward retry.
set -euo pipefail
branch=fix/nl2-hu-lines-audit-20261118
test "${GITHUB_REF_NAME:-}" = "$branch"
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
    status=data/nl2_hu_multiboard_status_current.json
    python3 tools/hu_apply_cert_extensions.py --out "$status"
    node tools/hu_extension_runtime_test.cjs "$status"
    bash tools/hu_exact_batch_audit.sh "$status"
    git add "$status" data/nl2_hu_verified_extensions.json data/nl2_hu_model_history_crosswalk.json data/nl2_hu_model_source_references.json
    if ! git diff --cached --quiet; then
      git commit -m 'Record the cumulative exact-board registry and all source references'
    fi
  )
  if git -C "$check" push origin "HEAD:refs/heads/$branch"; then
    git worktree remove "$check"
    exit 0
  fi
  git worktree remove "$check"
done
exit 1
