"""Test three preregistered K-high flops against the original UTG-CO rank146 route."""
import argparse
import gzip
import json
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, NoLegalRiver, compact, export_board, extract, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b471_rank146_prior import ID, LINE, OUT as PRIOR


BOARDS = (("KdJh6c", "Th"), ("KcTh4d", "6c"), ("KhQd7c", "4s"))
VERSIONS = ("gto", "exp_oop")
REPORT = Path("data/nl2_hu_b479_rank146_k_high.json")
MODEL_SPR = 7.25


def prior_group():
    prior = json.loads(PRIOR.read_bytes())
    assert (prior["rank"], prior["model_id"], prior["line"]) == (146, ID, LINE)
    assert [b["flop"] for b in prior["boards"]] == [p["flop"] for p in prior["pins"]] == ["KsQh4d", "QsJh4d"]
    for b, p in zip(prior["boards"], prior["pins"]):
        for prefix in ("", "locked_"):
            archive = EVIDENCE / f'NL2_MULTIBOARD_{p[prefix + "viewer_archive_code"]}.json.gz'
            assert sha(archive.read_bytes()) == p[prefix + "viewer_sha256"]
        assert (b["actual_pot_bb"], b["actual_effective_stack_bb"], b["actual_exact_action_line"]) == (13, 94.25, LINE)
        assert min(p["GTO_compatible_hole_card_pairs"], p["NL2_compatible_hole_card_pairs"]) > 0
    return {k: prior[k] for k in ("rank", "model_id", "line", "spot", "actor", "boards", "pins")}


def native_rivers(s, *, gto_root=False):
    root, turn = s["root"], s["subgame"]
    assert (root["pot"], root["stack"]) == (650, 9750)
    for game in (root, turn):
        if game is None:
            continue
        if not 0 <= game["info"]["gto_expl_pct"] <= .5:
            return "GTO_GAP_OUTSIDE_THRESHOLD", set()
        if gto_root and game is root:
            assert not game["info"].get("lock_stats") and game["info"].get("hero_gap_pct") is None
        elif s["version"] == "exp_oop" and not 0 <= game["info"]["hero_gap_pct"] <= .5:
            return "HERO_GAP_OUTSIDE_THRESHOLD", set()
    if turn is None:
        return "NO_LEGAL_TURN_CASE", set()
    assert (turn["pot"], turn["stack"]) == (1300, 9425)
    for game, line, player, action, pot, bets in (
        (root, "", 0, "b50", 650, [0, 0]),
        (root, "b50", 1, "c", 975, [325, 0]),
        (turn, "b50 c/", 0, "x", 1300, [0, 0]),
        (turn, "b50 c/x", 1, "x", 1300, [0, 0]),
    ):
        nodes = [n for n in game["nodes"] if n["line"] == line and n["player"] == player]
        if not nodes or action not in nodes[0]["acts"]:
            return "NATIVE_ACTION_UNAVAILABLE", set()
        assert len(nodes) == 1 and (nodes[0]["pot"], nodes[0]["bets"]) == (pot, bets)
    nodes = [n for n in turn["nodes"] if (n["line"], n["player"], len(n["board"])) == (LINE, 0, 10)]
    assert all(n["pot"] == 1300 and n["bets"] == [0, 0] for n in nodes)
    return ("CHECK_LEGAL_DEALS" if nodes else "NO_EXACT_RIVER_NODE"), {n["board"] for n in nodes}


def read_available(downloads, flop, turn, batch="B479"):
    sources, missing = [], {}
    for version in VERSIONS:
        folder = downloads / f"NL2-{batch}-{flop}-{version}"
        path = folder / "trainer/evidence" / f"{flop}-{version}.json"
        if not path.is_file():
            missing[version] = "MISSING_MANIFEST"
            continue
        manifest = json.loads(path.read_bytes())
        if manifest["failures"]:
            missing[version] = dict(reason="SOLVER_FAILURE", manifest_sha256=sha(path.read_bytes()),
                                    errors=[e["reason"] for e in manifest["failures"]])
            continue
        sources.append(original(downloads, flop, turn, version, batch=batch, spot="UTG_CO", flop_line="b50 c",
                                flop_policy="oop-b50only", turn_policy="checkcheck", turn_extract="x x",
                                root_pot=650, root_stack=9750))
    return sources, missing


def classify(pair, pin):
    available = {}
    outcomes = {}
    for s in pair:
        result, boards = native_rivers(s)
        outcomes[s["version"]] = result
        available[s["version"]] = boards
    report = dict(source_gates=outcomes, compatible_deals_by_river={}, selected_public_board=None)
    for public in sorted(available["gto"] | available["exp_oop"]):
        counts = {}
        for s in pair:
            version = s["version"]
            counts[version] = 0
            if public in available[version]:
                try:
                    _, counts[version], _ = extract(s, LINE, MODEL_SPR, pin, public_board=public)
                except NoLegalRiver:
                    pass
        report["compatible_deals_by_river"][public] = counts
        if min(counts.values()) and report["selected_public_board"] is None:
            report["selected_public_board"] = public
    return report


def process(downloads, flop, turn, run, group, batch="B479", texture="HIGH"):
    sources, missing = read_available(downloads, flop, turn, batch)
    report = dict(flop=flop, turn=turn, missing_originals=missing, selected_public_board=None)
    if not sources:
        return report
    code = f"{batch}_R146_{flop.upper()}"
    pack = dict(run_id=run, solver=SOLVER, rust=RUST, flop=flop, turn=turn, source_arrays=sources)
    encoded = gzip.compress(compact(pack), compresslevel=6, mtime=0)
    (EVIDENCE / f"NL2_{code}.json.gz").write_bytes(encoded)
    pin = dict(flop=flop, turn=turn, source_run_id=run, archive_code=code, archive_sha256=sha(encoded))
    report.update(pin)
    if missing:
        return report
    gto, locked = sources
    for key in ("preflop_ranges", "solver_pin", "pool_source_sha256", "solver_ranges_sha256"):
        assert gto["manifest"][key] == locked["manifest"][key]
    report.update(classify(sources, pin))
    public = report["selected_public_board"]
    if public:
        parent = dict(public_board=public[:8], source_kind="PINNED_PREFLOP_CFR", assumed_preflop_ranges=False, flop_texture=texture)
        board, evidence = export_board(pin, parent, sources, 146, LINE, MODEL_SPR, False, archive_digest=pin["archive_sha256"],
                                       viewer_code=f"R146_{run}_{flop}", public_board=public)
        assert (board["actual_pot_bb"], board["actual_effective_stack_bb"], board["acting_seat"]) == (13, 94.25, 0)
        group["boards"].append(board)
        group["pins"].append(evidence)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    assert args.run_id > 0
    group = prior_group()
    outcomes = [process(args.downloads, flop, turn, args.run_id, group) for flop, turn in BOARDS]
    count = len(group["boards"])
    assert count == len({p["flop"] for p in group["pins"]}) == len(group["pins"])
    if count >= 3:
        assert count <= 5
        dest = EVIDENCE / "extensions"
        dest.mkdir(exist_ok=True)
        (dest / "rank146.json").write_bytes(json_bytes(group))
    REPORT.write_bytes(json_bytes(dict(rank=146, model_id=ID, line=LINE, run_id=args.run_id,
                                       prior_gate_sha256=sha(PRIOR.read_bytes()), attempts=outcomes,
                                       distinct_paired_flops=count)))
    print(f"rank146: {count} paired distinct flops")


if __name__ == "__main__":
    main()
