"""Resolve rank73 from three fresh BTN_BB original Rust pairs at a checked 33% flop and pot-sized turn lead."""
import argparse
import gzip
import json
import re
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from solve_hu_multiboard_100bb import marginal_pattern
from hu_b467_river_source_gate import NoLegalRiver, EVIDENCE, compact, export_board, extract, json_bytes, sha


MODEL = "ln-bb-r_model-150oewe"
SPOT = "BTN_BB"
FLOP_LINE = "x b33 c"
LINE = "x b33 c/b100 c/"
SPR = 3.145
BOARDS = (("7s5h3d", "6c"), ("8s7h5d", "3d"), ("4s4h2d", "8s"))
ROOT = Path("data/nl2_hu_multiboard_status_v51_b453_rank32.json")


def audit_patterns(game, job, manifest, pool):
    records = manifest["locks"]
    rules = job["locks"]
    assert [r["pat"] for r in records] == [r["pat"] for r in rules]
    marginal = [r for r in records if r.get("street")]
    assert {r["street"] for r in marginal} == {1, 2, 3}
    assert len({r["pat"] for r in marginal}) == len(marginal)
    stats = game["info"]["lock_stats"]
    assert set(stats) <= {r["pat"] for r in rules}
    rules_by_pattern = {r["pat"]: r for r in rules}
    evidence = {}
    for record in marginal:
        street = record["street"]
        token = "r" if record["source"].endswith("bettor_vs_raise") else record["pat"].split(")?")[-1][:-1]
        assert record["pat"] == marginal_pattern(street, token, True)
        assert f"[{street}]" in record["source"] and record["n"] >= 500
        counts = pool["HU_facing_bet"][str(street)]
        if token == "r":
            target = counts["bettor_vs_raise"]
        else:
            bucket = {"b33":"≤33%", "b50":"34-55%", "b75":"56-80%", "b100":"81-110%"}[token]
            target = counts["by_size"][bucket]
        rule = rules_by_pattern[record["pat"]]
        assert record["n"] == target["n"] and rule["fold"] == target["fold"]/100 and rule["raise"] == target["raise"]/100
        evidence[record["pat"]] = dict(street=street, source=record["source"], n=target["n"],
                                       fold_target=rule["fold"], raise_target=rule["raise"])
        for i in range(1, 4):
            for suffix in (token, "x "+token):
                path = "x x/" * (i-1) + suffix
                assert bool(re.search(record["pat"], path)) == (i == street)
    matches = {}
    for node in game["nodes"]:
        if node["player"] != 1 or len(node["acts"]) < 2 or not any(w > 1e-4 for w in node["w"][1]):
            continue
        line = node["line"]
        record = next((r for r in records if re.search(r["pat"], line)), None)
        if record is None:
            continue
        if record.get("street"):
            assert record["street"] == 1 + line.count("/") == len(node["board"]) // 2 - 2
        assert stats.get(record["pat"], {}).get("nodes", 0) > 0
        matches[record["pat"]] = matches.get(record["pat"], 0) + 1
    return dict(marginal_targets=evidence, first_pattern_visible_nodes=matches, driver_tree_nodes={k:v["nodes"] for k,v in stats.items()})


def original(directory, flop, turn, version, *, batch="B470", spot=SPOT, flop_line=FLOP_LINE,
             flop_policy="checked-b33only", turn_policy="b100only", turn_extract="b100 c",
             root_pot=550, root_stack=9750, flop_lines=None, turn_extracts=None,
             turn_mode="default", turn_menu="50%,100%"):
    expected_flop = [flop_line] if flop_lines is None else list(flop_lines)
    expected_turn = [turn_extract] if turn_extracts is None else list(turn_extracts)
    base = directory / f"NL2-{batch}-{flop}-{version}"
    evidence = base / "trainer/evidence"
    assert (evidence / "poker-solver-pin.txt").read_text().strip() == SOLVER
    assert (evidence / "rust-pin.txt").read_text().strip() == RUST
    pool_bytes = (evidence / "pool_stats.json").read_bytes()
    assert sha(pool_bytes) == "c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a"
    pool = json.loads(pool_bytes)["NL2"]
    m = json.loads((evidence / f"{flop}-{version}.json").read_bytes())
    assert (m["schema"], m["spot"], m["flop"], m["version"]) == ("NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1", spot, flop, version)
    assert m["preflop_ranges"]["source"] == "PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert m["flop_size_profile"] == "full" and not m["restricted_tree_assumption"]
    assert m["flop_line_policy"] == flop_policy and m["selected_lines"] == expected_flop
    assert m["turn_line_policy"] == turn_policy and m["selected_turn_lines"] == expected_turn
    assert m["turn_sizing_mode"] == turn_mode and m["turns"] == [turn] and not m["failures"]
    assert (m["root_pot_bb"], m["root_remaining_bb"]) == (root_pot/100, root_stack/100)
    assert m["marginal_lock_matching"] == "RUST_FIRST_MATCH_POOLED_FALLBACK_EXACT_STREET"
    assert m["pool_source_sha256"] == sha(pool_bytes) and m["solver_ranges_sha256"]
    pf = base / "solver/postflop"
    rootfile = pf / "out" / spot / version / f"{flop}_multiboard.json"
    assert m["file_flop"] == str(rootfile.relative_to(pf))
    root_raw = rootfile.read_bytes()
    assert sha(root_raw) == m["file_flop_sha256"]
    root = json.loads(root_raw)
    flop_job = json.loads(rootfile.with_suffix(".job.json").read_bytes())
    assert (root["flop"], root["pot"], root["stack"]) == (flop, root_pot, root_stack)
    assert flop_job["flop_oop"] == flop_job["flop_ip"] == "33%,50%,75%,100%"
    if version == "gto":
        assert flop_job.get("hero") is None and not flop_job.get("locks")
    else:
        assert flop_job["hero"] == 0 and flop_job["locks"] and any((p.get("n") or 0)>=500 for p in m["locks"])
    out = dict(version=version, manifest=m, root=root, root_sha256=sha(root_raw), root_job=flop_job,
               subgame=None, subgame_job=None, source_sha256=None)
    if version == "exp_oop":
        out["actual_flop_job_lock_coverage"] = audit_patterns(root, flop_job, m, pool)
    outcomes = m["cases"] + m["skipped"]
    assert len(outcomes) == len(expected_flop)
    assert {(c["line"], c["turn"]) for c in outcomes} == {(l, turn) for l in expected_flop}
    assert m["solved_cases"] == len(m["cases"])
    cases = [c for c in m["cases"] if c["line"] == flop_line]
    if not cases:
        skipped, = (s for s in m["skipped"] if s["line"] == flop_line)
        assert skipped["reason"] in ("NO_BOTH_PLAYER_REACH", "ZERO_LEGAL_PLAYER_RANGE_AFTER_TURN_CARD_BLOCKERS",
                                     "RUST_ENGINE_EXCLUDED_EMPTY_REACH_RANGE")
        return out
    c, = cases
    subfile = rootfile.parent / f"{flop}_{flop_line.replace(' ', '')}_{turn}.json"
    assert c["source_path"] == str(subfile.relative_to(pf))
    subraw = subfile.read_bytes()
    assert sha(subraw) == c["source_sha256"]
    sub = json.loads(subraw)
    job = json.loads(subfile.with_suffix(".job.json").read_bytes())
    assert (sub["flop"], sub["turn"], sub["line0"]) == (flop, turn, flop_line)
    assert sub["info"]["gto_expl_pct"] == c["gto_gap_pct"]
    assert job["turn_oop"] == job["turn_ip"] == turn_menu
    assert job["rake_rate"] == .05 and job["rake_cap"] == 1000
    if version == "gto":
        assert job.get("hero") is None and not job.get("locks") and c["hero_gap_pct"] is None
    else:
        assert job["hero"] == 0 and job["locks"] and sub["info"]["lock_stats"]
        assert c["hero_gap_pct"] == sub["info"]["hero_gap_pct"]
    if version == "exp_oop":
        out["actual_turn_job_lock_coverage"] = audit_patterns(sub, job, m, pool)
    out.update(subgame=sub, subgame_job=job, source_sha256=sha(subraw))
    return out


def pair(directory, flop, turn, run):
    sources = [original(directory, flop, turn, version) for version in ("gto", "exp_oop")]
    g, e = sources
    assert g["manifest"]["preflop_ranges"] == e["manifest"]["preflop_ranges"]
    for k in ("pool_source_sha256", "solver_ranges_sha256", "solver_pin"):
        assert g["manifest"][k] == e["manifest"][k]
    code = f"B470_R73_{flop.upper()}"
    packed = gzip.compress(compact(dict(run_id=run, flop=flop, turn=turn, solver=SOLVER, rust=RUST,
                                        source_arrays=sources)), mtime=0)
    (EVIDENCE / f"NL2_{code}.json.gz").write_bytes(packed)
    pin = dict(flop=flop, turn=turn, source_run_id=run, archive_code=code, archive_sha256=sha(packed))
    report = dict(pin, public_rivers={}, result="NO_PAIRED_TARGET")
    if any(s["subgame"] is None for s in sources):
        report["result"] = "NO_LEGAL_TURN_CASE"
        return None, None, report
    if any(s["root"]["info"]["gto_expl_pct"] > .5 or s["subgame"]["info"]["gto_expl_pct"] > .5 for s in sources) or e["subgame"]["info"]["hero_gap_pct"] > .5 or e["root"]["info"]["hero_gap_pct"] > .5:
        report["result"] = "GAP_ABOVE_THRESHOLD"
        return None, None, report
    def boards(s):
        return {n["board"] for n in s["subgame"]["nodes"] if (n["line"], n["player"], len(n["board"])) == (LINE, 0, 10)}
    eligible = []
    for public in sorted(boards(g) & boards(e)):
        result = []
        for s in sources:
            try:
                item = extract(s, LINE, SPR, pin, public_board=public)
            except NoLegalRiver:
                item = (None, 0, set())
            result.append(item)
        report["public_rivers"][public] = {s["version"]: dict(compatible_deals=r[1], actor_combos=len(r[2])) for s,r in zip(sources,result)}
        if all(r[1] for r in result):
            eligible.append(public)
    if not eligible:
        return None, None, report
    public = eligible[0]
    parent = dict(public_board=public[:8], source_kind="PINNED_PREFLOP_CFR", assumed_preflop_ranges=False,
                  flop_texture="PAIRED" if flop=="4s4h2d" else "LOW")
    b, p = export_board(pin, parent, sources, 73, LINE, SPR, False, archive_digest=pin["archive_sha256"],
                        public_board=public, viewer_code=f"R73_{run}_{flop}")
    # Both the exact betting investment and pot must match the real generated trainer route.
    assert abs(b["actual_pot_bb"]-27.501) <= .1 and abs(b["actual_effective_stack_bb"]-86.5) <= .1
    report.update(result="PAIRED_POSITIVE", selected=public)
    return b, p, report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--downloads", type=Path, required=True)
    p.add_argument("--run-id", type=int, required=True)
    args = p.parse_args()
    model = json.loads(ROOT.read_bytes())["records"][MODEL]
    assert args.run_id>0 and (model["frequency_rank"], model["family"], model["solver_profile"], model["assumed_model_node_spr"]) == (73,"SRP",SPOT,SPR)
    success, pins, reports = [], [], []
    for flop, turn in BOARDS:
        missing = [version for version in ("gto", "exp_oop")
                   if not (args.downloads / f"NL2-B470-{flop}-{version}").is_dir()]
        if missing:
            reports.append(dict(flop=flop, turn=turn, missing_original_versions=missing))
            continue
        board, pin, report = pair(args.downloads, flop, turn, args.run_id)
        reports.append(report)
        if board:
            success.append(board)
            pins.append(pin)
    result = dict(rank=73, model_id=MODEL, boards=success, pins=pins, raw_sources=reports,
                  minimum_distinct_flops=3, exact_only=True)
    Path("data/nl2_hu_b470_rank73_river_sources.json").write_bytes(json_bytes(result))
    if len(success) == 3:
        assert {b["flop"] for b in success} == {f for f,_ in BOARDS}
        ext = EVIDENCE / "extensions/rank73.json"
        ext.parent.mkdir(exist_ok=True)
        ext.write_bytes(json_bytes(dict(model_id=MODEL, rank=73, boards=success, pins=pins)))
    print(f"Verified {len(success)} of 3 distinct positive paired flops for rank73")


if __name__ == "__main__":
    main()
