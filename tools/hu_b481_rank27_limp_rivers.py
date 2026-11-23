"""Audit three original BB vs CO limp river pairs at the native rank27 route."""
import argparse
import gzip
import json
import subprocess
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b476_utg_river_batch import paired_river_board
from solve_hu_assumed_pots import RULES, w_lmp_ip

MODEL = "ln-iso-lmp_r_model-1aov4pd"
PARENT = "ln-iso-lmp_t_model-19hfq8v"
SPOT = "LMP_CO_BB"
LINE = "b50 c/b33 c/"
BOARDS = (("KcJh8s","2d","HIGH"), ("8h7c5s","Tc","LOW"), ("9h9c4d","7c","PAIRED"))
ROOT = Path("data/nl2_hu_multiboard_status_v51_b453_rank32.json")


def check_limp_source(source):
    manifest, job = source["manifest"], source["root_job"]
    ranges = manifest["preflop_ranges"]
    assert manifest["pot_family"] == "LMP" and ranges["profile"] == RULES[SPOT]
    ranks = "AKQJT98765432"
    names = {a+b+suffix for i,a in enumerate(ranks) for b in ranks[i:] for suffix in (("",) if a==b else ("s","o"))}
    assert len(names) == 169 and set(ranges["oop_169"]) == set(ranges["ip_169"]) == names
    for seat, policy in (("oop",lambda _:1.), ("ip",w_lmp_ip)):
        expected = {hand:float(policy(hand)) for hand in names}
        actual = {hand:float(weight) for hand,weight in (entry.split(":") for entry in job[seat].split(","))}
        assert ranges[seat+"_169"] == expected
        assert actual == {h:w for h,w in expected.items() if w>=.005}
    assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"]) == (250,9900,.05,1000)
    if source["subgame_job"]:
        sub = source["subgame_job"]
        assert sub["river_oop"] == sub["river_ip"] == "50%,100%,a"
        assert sub["oop_w"] and sub["ip_w"]


def verify_pair(directory, flop, turn, texture, run):
    sources = [original(directory,flop,turn,version,batch="B481",spot=SPOT,flop_line="b50 c",
                        flop_policy="oop-b50only", turn_policy="default", turn_extracts=("b33 c","b50 c","b75 c","b100 c"),
                        root_pot=250,root_stack=9900,turn_mode="33-50-75-100",turn_menu="33%,50%,75%,100%",
                        preflop_source="ASSUMED_EXPLICIT_169CLASS") for version in ("gto","exp_oop")]
    for source in sources:
        check_limp_source(source)
    g,e = sources
    for key in ("preflop_ranges","pool_source_sha256","solver_ranges_sha256","solver_pin"):
        assert g["manifest"][key] == e["manifest"][key]
    code = "B481_R27_"+flop.upper()
    blob = gzip.compress(compact(dict(schema="NL2_B481_GENUINE_LMP_SOURCE_PAIR_V1",run_id=run,flop=flop,
            turn=turn,solver=SOLVER,rust=RUST,preflop_range_source="ASSUMED_EXPLICIT_169CLASS",source_arrays=sources)), mtime=0)
    (EVIDENCE/f"NL2_{code}.json.gz").write_bytes(blob)
    pin = dict(flop=flop,turn=turn,source_run_id=run,archive_code=code,archive_sha256=sha(blob))
    report = paired_river_board(27,sources,pin,texture,"b50 c",33,11.53,8.333,96.083,(500,9775),
                                "ASSUMED_PREFLOP_RANGES",True)
    if report.get("result") == "PAIRED_POSITIVE":
        board, pin = report["board"], report["pin"]
        path = EVIDENCE / f'NL2_MULTIBOARD_{pin["viewer_archive_code"]}.json.gz'
        viewer = path.read_bytes()
        assert sha(viewer) == pin["viewer_sha256"]
        cases = json.loads(gzip.decompress(viewer))["artifacts"][0]["cases"]
        locked, = (c for c in cases if c["version"] == "exp_oop" and c["source_sha256"] == e["source_sha256"])
        node, = locked["nodes"]
        assert (node["public_board"],node["exact_node_line"],node["acting_seat"]) == (board["public_board"],LINE,0)
        assert node["strictly_reachable_combos"] == pin["NL2_strict_combos"]
        for field in ("medium_50pct_eligible_combos","b50_nonpolarized_relative_equity_research_candidate"):
            board["nl2_locked_variants"][0][field] = node[field]
    return dict(archive_code=code,**report)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads",required=True,type=Path)
    parser.add_argument("--run-id",required=True,type=int)
    args=parser.parse_args()
    records=json.loads(ROOT.read_bytes())["records"]
    m=records[MODEL]
    assert args.run_id>0 and (m["frequency_rank"],m["source_model_id"],m["family"],m["solver_profile"],
                              m["assumed_model_node_spr"],m["street"]) == (27,PARENT,"LMP",SPOT,11.53,2)
    scope=json.loads(subprocess.check_output(["node","tools/hu_b481_lmp_trainer_route.cjs"]))
    group=dict(model_id=MODEL,rank=27,actor="BB_OOP",spot=SPOT,line=LINE,trainer_scope=scope,boards=[],pins=[])
    attempts=[]
    for flop,turn,texture in BOARDS:
        report=verify_pair(args.downloads,flop,turn,texture,args.run_id)
        if report.get("result") == "PAIRED_POSITIVE":
            group["boards"].append(report.pop("board"))
            group["pins"].append(report.pop("pin"))
        attempts.append(report)
    if len(group["boards"]) == 3:
        assert {b["flop"] for b in group["boards"]} == {f for f,_,_ in BOARDS}
        path=EVIDENCE/"extensions/rank27.json"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(json_bytes(group))
    Path("data/nl2_hu_b481_rank27_limp_river_results.json").write_bytes(json_bytes(dict(**group,attempts=attempts,run_id=args.run_id)))
    print(f'{len(group["boards"])} of 3 genuine paired rank27 river sources')


if __name__=="__main__":
    main()
