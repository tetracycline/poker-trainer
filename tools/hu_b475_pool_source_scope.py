"""Identify only historically proven cross-street pool proxies in a frozen CERT registry."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re

BASE = "9442f067eef09ed757198f0880d33023b489cf34"
SOLVER = "abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST = "9d1509fe5077d019825f833eed04b16d342dfda1"
POOL = "c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a"
BUCKETS = {"b50": "34-55%", "b100": "81-110%"}


def samples(case, token, rates):
    pattern = rf"(?:^|[ /]){token}$"
    stats = (case.get("rust_source_lock_stats") or {}).get(pattern)
    if not stats or stats["nodes"] <= 0:
        return None
    rules = case.get("lock_patterns", [])
    candidates = [m for m in rules if m["pat"] == pattern]
    if len(candidates) != 3:
        return None
    for street, (rule, bucket) in enumerate(zip(candidates, rates), 1):
        source = f"NL2.HU_facing_bet[{street}].by_size[{BUCKETS[token]}]"
        if rule.get("source") != source or rule.get("n") != bucket["n"]:
            return None
    actual_fold, actual_raise = 100 * stats["fold"], 100 * stats["agg"]
    if abs(actual_fold-rates[0]["fold"]) > .2 or abs(actual_raise-rates[0]["raise"]) > .2:
        return None
    villain = 1 if case["version"] == "exp_oop" else 0
    hits = collections.Counter()
    for node in case["nodes"]:
        line = node["exact_node_line"]
        street = line.count("/") + 1
        if (street not in (2, 3) or node["acting_seat"] != villain or
                node["strictly_reachable_combos"] <= 0 or not re.search(pattern, line)):
            continue
        first = next((r for r in rules if re.search(r["pat"], line)), None)
        if first == candidates[0]:
            hits[str(street)] += 1
    if not hits:
        return None
    return dict(action=token, applied_fold_pct=round(actual_fold, 3), applied_raise_pct=round(actual_raise, 3),
                first_matching_source_street=1, first_matching_source_n=rates[0]["n"],
                observed_later_street_node_counts=dict(hits), rust_tree_nodes=stats["nodes"])


def build(directory, pool_path):
    assert hashlib.sha256(pool_path.read_bytes()).hexdigest() == POOL
    pool = json.loads(pool_path.read_bytes())["NL2"]["HU_facing_bet"]
    buckets = {t: [pool[str(st)]["by_size"][size] for st in (1,2,3)] for t,size in BUCKETS.items()}
    file = directory/"nl2_hu_multiboard_status_current.json"
    registry = json.loads(file.read_bytes())
    refs = collections.defaultdict(list)
    for mid, model in registry["records"].items():
        if model["label"] != "CERT-MULTIBOARD":
            continue
        for board in model["certified_3_to_5_exact_flop_boards"]:
            for lock in board["nl2_locked_variants"]:
                refs[(lock["run_id"],lock["sha256"])].append(dict(
                    model=mid, spot=model["solver_profile"], family=model["family"], flop=board["flop"],
                    turn=board["turn"], version=lock["version"], public_board=board["public_board"],
                    line=board["actual_exact_action_line"], seat=board["acting_seat"]))
    sources = {}
    for path in sorted((directory/"solver_evidence").glob("NL2_MULTIBOARD_*.json.gz")):
        archive = json.loads(gzip.decompress(path.read_bytes()))
        if (archive.get("schema") != "NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1" or
                archive.get("source_poker_solver_pin") != SOLVER or archive.get("authentic_rust_engine_pin") != RUST or
                archive.get("errors") != []):
            continue
        for artifact in archive["artifacts"]:
            for case in artifact["cases"]:
                key = (archive["source_run_id"], case["source_sha256"])
                if key not in refs or case.get("NL2_pool_source_sha256") != POOL:
                    continue
                assert case["run_id"] == key[0]
                rows = refs[key]
                for row in rows:
                    assert (row["spot"],row["family"],row["flop"],row["turn"],row["version"]) == (
                        case["spot"],case["pot_family"],case["flop"],case["turn"],case["version"])
                proofs = [q for token in BUCKETS if (q := samples(case,token,buckets[token]))]
                record = dict(spot=case["spot"],version=case["version"],flop=case["flop"],turn=case["turn"],
                              archive=path.name, source_archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                              scope="CONFIRMED" if proofs else "CHECKED_WITHOUT_CONFIRMATION", evidence=proofs)
                if key in sources:
                    assert (record["scope"],record["evidence"]) == (sources[key]["scope"],sources[key]["evidence"])
                else:
                    sources[key] = record
    confirmed = {k:v for k,v in sources.items() if v["scope"] == "CONFIRMED"}
    mapped = [r for k in confirmed for r in refs[k]]
    summary = dict(lock_sources=len(refs), checked=len(sources), confirmed=len(confirmed),
                   checked_without_confirmation=len(sources)-len(confirmed), unchecked=len(refs)-len(sources),
                   affected_references=len(mapped),affected_models=len({r["model"] for r in mapped}),
                   affected_named_boards=len({(r["model"],r["public_board"],r["line"],r["seat"]) for r in mapped}))
    return dict(schema="NL2_VERIFIED_ORIGINAL_POOL_SOURCE_SCOPE_V1", snapshot=BASE,
                registry_sha256=hashlib.sha256(file.read_bytes()).hexdigest(), pool_sha256=POOL,
                source_poker_solver_pin=SOLVER, source_rust_pin=RUST, pool_by_action_and_street=buckets, summary=summary,
                sources={f"{run}/{sha}":row for (run,sha),row in sorted(sources.items())})


if __name__ == "__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--pool",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=build(args.data,args.pool)
    args.out.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n")
    print(result["summary"])
