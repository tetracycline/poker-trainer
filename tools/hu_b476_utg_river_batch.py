"""Certify four UTG decisions only where exact legal river pairs survive three independently solved flops."""
import argparse
import gzip
import json
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, NoLegalRiver, compact, export_board, extract, json_bytes, sha
from hu_b470_rank73_new_rivers import original


FLOP_LINES = ("x x", "b50 c")
SPEC = dict(batch="B476", spot="UTG_CO", root_pot=650, root_stack=9750,
            flop_policy="checkcheck-and-oop-b50", flop_lines=FLOP_LINES, turn_policy="default",
            turn_extracts=("b33 c","b50 c","b75 c","b100 c"), turn_mode="33-50-75-100", turn_menu="33%,50%,75%,100%")
BOARDS = (("KcQd6h","5s","HIGH"), ("QhJc6d","7d","HIGH"), ("Td9h5c","Kh","MID"))
TARGETS = {
    99: ("ln-opfr-r_model-dfs9l1", "ln-opfr-t_model-1hmsxaw", "b50 c", 50, 3.375, 26.0, 87.75),
    109: ("ln-opfr-r_model-1txz51y", "ln-opfr-t_model-1ocorr7", "x x", 75, 5.7, 16.25, 92.625),
    110: ("ln-opfr-r_model-bt63wt", "ln-opfr-t_model-1ocorr7", "x x", 50, 7.25, 13.0, 94.25),
    111: ("ln-opfr-r_model-psu0y9", "ln-opfr-t_model-1ocorr7", "x x", 33, 8.8, 10.833, 95.333),
}


def replay_tree(source, flop_line, size):
    root, sub = source["root"], source["subgame"]
    if sub is None:
        return "SKIPPED_NO_LEGAL_TURN_CASE"
    job = source["subgame_job"]
    assert job["root_no_bet"] is False and job["turn_donk"] == ""
    assert job["line0"] == flop_line.split() + ["/"]
    turn_root, = (n for n in sub["nodes"] if len(n["board"]) == 8 and n["line"] == flop_line+"/" and n["player"] == 0)
    flop_decision, = (n for n in root["nodes"] if len(n["board"]) == 6 and n["line"] == "" and n["player"] == 0)
    assert flop_line.split()[0] in flop_decision["acts"]
    if flop_line == "b50 c":
        reply, = (n for n in root["nodes"] if len(n["board"]) == 6 and n["line"] == "b50" and n["player"] == 1)
        assert "c" in reply["acts"] and abs(reply["bets"][0] - .5 * flop_decision["pot"]) <= 1
    else:
        reply, = (n for n in root["nodes"] if len(n["board"]) == 6 and n["line"] == "x" and n["player"] == 1)
        assert "x" in reply["acts"]
    assert (sub["pot"], sub["stack"]) == ((1300,9425) if flop_line == "b50 c" else (650,9750))
    action = f"b{size}"
    if action not in turn_root["acts"]:
        return "REQUESTED_TURN_SIZE_ABSENT_FROM_SOLVED_MENU"
    response, = (n for n in sub["nodes"] if len(n["board"]) == 8 and n["line"]==flop_line+"/"+action and n["player"] == 1)
    assert abs(response["bets"][0] - turn_root["pot"] * size / 100) <= 1
    if "c" not in response["acts"]:
        return "NO_CALL_ON_SOLVED_TURN"
    if root["info"]["gto_expl_pct"] > .5 or sub["info"]["gto_expl_pct"] > .5:
        return "GTO_GAP_ABOVE_THRESHOLD"
    if source["version"] == "exp_oop" and max(root["info"]["hero_gap_pct"],sub["info"]["hero_gap_pct"]) > .5:
        return "HERO_GAP_ABOVE_THRESHOLD"
    return "CHECK_RIVER_DEALS"


def board_pair(rank, source_pair, archive_pin, texture):
    _, _, flop_line, size, spr, pot, stack = TARGETS[rank]
    line = f"{flop_line}/b{size} c/"
    report = dict(flop=archive_pin["flop"], turn=archive_pin["turn"], archive_sha256=archive_pin["archive_sha256"],
                  source_gates={s["version"]: replay_tree(s,flop_line,size) for s in source_pair}, rivers={})
    if any(r != "CHECK_RIVER_DEALS" for r in report["source_gates"].values()):
        return report
    available = []
    for s in source_pair:
        available.append({n["board"] for n in s["subgame"]["nodes"] if (n["player"],len(n["board"]),n["line"])==(0,10,line)})
    eligible = []
    for public in sorted(available[0] | available[1]):
        seats = {}
        for s, nodes in zip(source_pair,available):
            ver=s["version"]
            if public not in nodes:
                seats[ver] = dict(result="MISSING_EXACT_RIVER_NODE", compatible_deals=0)
                continue
            try:
                case, pairs, hands = extract(s, line, spr, archive_pin, public_board=public)
            except NoLegalRiver:
                seats[ver] = dict(result="NO_COMPATIBLE_PRIVATE_DEAL", compatible_deals=0)
                continue
            node, = case["nodes"]
            assert abs(node["pot_bb"] - pot) <= .1 and abs(node["remaining_bb"] - stack) <= .1
            seats[ver] = dict(result="REACHABLE", compatible_deals=pairs, actor_combos=len(hands))
        report["rivers"][public] = seats
        if all(v["compatible_deals"] for v in seats.values()):
            eligible.append(public)
    if not eligible:
        report["result"] = "NO_PAIRED_EXACT_RIVER"
        return report
    public = eligible[0]
    parent = dict(public_board=public[:8], source_kind="PINNED_PREFLOP_CFR", assumed_preflop_ranges=False, flop_texture=texture)
    code = f'R{rank}_{archive_pin["source_run_id"]}_{archive_pin["flop"]}'
    b,p = export_board(archive_pin, parent, source_pair, rank, line, spr, False,
                       archive_digest=archive_pin["archive_sha256"], viewer_code=code, public_board=public)
    report.update(result="PAIRED_POSITIVE", board=b, pin=p)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--downloads", required=True, type=Path)
    parser.add_argument("--run-id", required=True, type=int)
    args=parser.parse_args()
    assert args.run_id > 0
    records=json.loads(Path("data/nl2_hu_multiboard_status_v51_b453_rank32.json").read_bytes())["records"]
    groups = {}
    for rank,(mid,parent,flop_line,size,spr,_,_) in TARGETS.items():
        m=records[mid]
        assert (m["frequency_rank"],m["source_model_id"],m["street"],m["solver_profile"],m["assumed_model_node_spr"]) == (rank,parent,2,"UTG_CO",spr)
        groups[rank]=dict(rank=rank, model_id=mid, actor="UTG_OOP", line=f"{flop_line}/b{size} c/", boards=[], pins=[], attempts=[])
    for flop,turn,texture in BOARDS:
        pairs={line:[original(args.downloads,flop,turn,v,flop_line=line,**SPEC) for v in ("gto","exp_oop")] for line in FLOP_LINES}
        archives=[]
        for i in (0,1):
            first=pairs["x x"][i]
            other=pairs["b50 c"][i]
            assert first["root_sha256"] == other["root_sha256"] and first["manifest"] == other["manifest"]
            branches={line: {k:v for k,v in pair[i].items() if k in ("subgame","subgame_job","source_sha256","actual_turn_job_lock_coverage")}
                      for line,pair in pairs.items()}
            archives.append(dict(version=first["version"], manifest=first["manifest"], root=first["root"], root_job=first["root_job"],
                                 root_sha256=first["root_sha256"], actual_flop_job_lock_coverage=first.get("actual_flop_job_lock_coverage"), branches=branches))
        assert archives[0]["manifest"]["preflop_ranges"] == archives[1]["manifest"]["preflop_ranges"]
        for k in ("pool_source_sha256","solver_ranges_sha256","solver_pin"):
            assert archives[0]["manifest"][k] == archives[1]["manifest"][k]
        code="B476_UTG_"+flop.upper()
        raw=gzip.compress(compact(dict(schema="NL2_B476_ORIGINAL_RUST_PAIRS_V1", solver=SOLVER,rust=RUST,flop=flop,
                                       turn=turn,run_id=args.run_id,sources=archives)),mtime=0)
        (EVIDENCE/f"NL2_{code}.json.gz").write_bytes(raw)
        pin=dict(flop=flop,turn=turn,source_run_id=args.run_id,archive_code=code,archive_sha256=sha(raw))
        for rank, group in groups.items():
            report=board_pair(rank,pairs[TARGETS[rank][2]],pin,texture)
            if report.get("result") == "PAIRED_POSITIVE":
                group["boards"].append(report.pop("board"))
                group["pins"].append(report.pop("pin"))
            group["attempts"].append(report)
    out=EVIDENCE/"extensions"
    out.mkdir(exist_ok=True)
    for rank,group in groups.items():
        if len(group["boards"])==3:
            assert len({b["flop"] for b in group["boards"]})==3
            (out/f"rank{rank}.json").write_bytes(json_bytes({k:v for k,v in group.items() if k!="attempts"}))
    Path("data/nl2_hu_b476_four_utg_river_results.json").write_bytes(json_bytes(dict(run_id=args.run_id,models=groups)))
    print({r:len(g["boards"]) for r,g in groups.items()})


if __name__=="__main__":
    main()
