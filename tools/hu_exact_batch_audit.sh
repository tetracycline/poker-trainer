#!/usr/bin/env bash
# Validate every certified board in the selected registry and every HU route.
set -euo pipefail
registry=${1:?expected current registry file}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
python3 tools/hu_cert_lock_medium_audit.py --source "$registry" --out "$tmpdir/locks.json"
node tools/hu_line_contract.js >"$tmpdir/contract.json"
node tools/link_audit.js --md "$tmpdir/link.md" --json "$tmpdir/link.json"
node tools/reach_verify.js --log "$tmpdir/reach.md" --json "$tmpdir/reach.json"
node tools/hu_model_path_audit.js "$tmpdir/path.json"
node --check nl2_hu_multiboard_ui.js
node --check nl2-multiboard.js
node tools/hu_b378_v47_loader_runtime_test.cjs
python3 - "$registry" "$tmpdir/locks.json" "$tmpdir/link.json" <<'PY'
import collections, json, sys
from pathlib import Path
registry, locks, links = (json.loads(Path(p).read_text()) for p in sys.argv[1:])
labels = collections.Counter(r["label"] for r in registry["records"].values())
assert len(registry["records"]) == registry["TOTAL"] == 392
assert labels["CERT-MULTIBOARD"] == len(locks["models"]) == registry["CERT_MULTIBOARD"]
assert labels["APPROX"] == registry["APPROX"] and registry["EST"] == 0
assert labels["APPROX"] + labels["CERT-MULTIBOARD"] == 392
assert locks["not_generalized_handclass_GTO"] and locks["not_actual_NL2_earnings"]
counts = links["counts"]
assert counts["continuing"] == counts["reachRiver"] == 2475 and counts["riverShare"] == 100
print(f'{labels["CERT-MULTIBOARD"]} CERT / {labels["APPROX"]} APPROX, 2475/2475 HU routes')
PY
git diff --check
