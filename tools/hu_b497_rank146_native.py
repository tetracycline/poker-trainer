"""Reverify the original rank146 river pairs and test three distinct full-menu UTG-CO flops."""
import argparse
import gzip
import json
from pathlib import Path

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b471_rank146_prior import ARCHIVES, ID, LINE, OUT as PRIOR, checked, read
from hu_b479_rank146_k_high import native_rivers, prior_group, process
from hu_b483_locked_medium import proof
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

BOARDS = (("QhJs2c", "7s"), ("KhQs9h", "Js"), ("JhTd6s", "9s"))
VERSIONS = ("gto", "exp_oop")
# Both preflop hand-range strings are fixed by the version and original UTG_CO solver profile.
RANGES = {"gto": "a6f80629fff3bb619215321a01d4c19183dc80dc37919720c04d0947f1500d70",
          "exp_oop": "f888646780c7d4d583c1d75db5cb8805e62a44f6da30d4d7d6728b03061c6000"}
REPORT = Path("data/nl2_hu_b497_rank146_native_rivers.json")
MEDIUM = Path("data/nl2_hu_b497_locked_medium.json")


def observation(source, run, archive_sha, public):
    root, sub, job = source["root"], source["subgame"], source["subgame_job"]
    version, turn = source["version"], sub["turn"]
    assert (job["flop"],job["turn"],job["line0"],job["rake_rate"],job["rake_cap"]) == (
        root["flop"],turn,["b50","c","/"],.05,1000)
    parent, = (n for n in root["nodes"] if n["line"] == "b50 c/" and n["board"][-2:]==turn)
    assert (parent["pot"],root["stack"]-max(parent["bets"])) == (job["pot"],job["stack"]) == (1300,9425)
    for seat,k in enumerate(("oop_w","ip_w")):
        assert job[k] == [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat]) if w>1e-4]
    gate, rivers = native_rivers(source, gto_root=source.get("uses_original_gto_flop",False))
    assert gate == "CHECK_LEGAL_DEALS" and public in rivers
    node, = (n for n in sub["nodes"] if (n["board"],n["line"],n["player"]) == (public,LINE,0))
    if "b50" in node["acts"]:
        child, = (n for n in sub["nodes"] if (n["board"],n["line"],n["player"]) == (public,LINE+"b50",1))
        assert (child["pot"],child["bets"]) == (1950,[650,0])
    rec = proof(root,sub,node,game_reach(root,sub)[0])
    counts = [sum(v["nodes"] for v in g["info"].get("lock_stats",{}).values()) for g in (root,sub)]
    scope = lock_scope(sub,source["manifest"]["locks"],version)
    if version=="exp_oop":
        assert scope["observed_marginal_source_nodes"] > 0 and counts[1] > 0 and job["hero"] == 0
    return dict(rec,spot="UTG_CO",family="SRP",flop=root["flop"],turn=turn,version=version,
                source_run_id=run,source_sha256=source["source_sha256"],archive_sha256=archive_sha,
                root_applied_rust_lock_nodes=counts[0],subgame_applied_rust_lock_nodes=counts[1],
                gto_gap_pct=sub["info"]["gto_expl_pct"],locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),
                lock_scope={k:v for k,v in scope.items() if k not in ("matching_examples","caveat")})


def anchors(originals, group):
    pairs=[]
    for spec, stored, stored_pin in zip(ARCHIVES, group["boards"], group["pins"], strict=True):
        b,p = checked(originals,spec,True)
        assert (b,p)==(stored,stored_pin)
        flop,turn,gr,er,ga,ea,gzip_sha,ezip_sha=spec
        gd,ed=(originals/f"r30-{n}" for n in (ga,ea))
        gm,em=(read(next((d/"evidence").glob("*.json"))) for d in (gd,ed))
        root=read(gd/"solver/postflop"/gm["file_flop"])
        gc,=(c for c in gm["cases"] if (c["line"],c["turn"])==("b50 c",turn))
        ec,=em["cases"]
        pair=[]
        for version,run,d,m,rel,archive_sha in (
                ("gto",gr,gd,gm,gc["source_path"],gzip_sha),
                ("exp_oop",er,ed,em,ec["original_Rust_exp_subgame_path"],ezip_sha)):
            path=d/"solver/postflop"/rel
            source=dict(version=version,uses_original_gto_flop=True,root=root,subgame=read(path),subgame_job=read(path.with_suffix(".job.json")),
                        source_sha256=sha(path.read_bytes()),manifest=dict(locks=m.get("locks",[])))
            # Historical EXP solves lock the turn and river after their authenticated original GTO flop.
            pair.append(observation(source,run,archive_sha,b["public_board"]))
        assert all(row["status"]=="POSITIVE_JOINT_REACH" for row in pair)
        assert [row["compatible_hole_card_pairs"] for row in pair]==[p["GTO_compatible_hole_card_pairs"],p["NL2_compatible_hole_card_pairs"]]
        pairs.append(pair)
    return pairs


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--downloads",type=Path)
    parser.add_argument("--originals",type=Path,required=True)
    parser.add_argument("--run-id",type=int)
    parser.add_argument("--check-anchors",action="store_true")
    args=parser.parse_args()
    group=prior_group()
    pairs=anchors(args.originals,group)
    if args.check_anchors:
        for g,e in pairs:print(g["flop"],g["public_board"],g["compatible_hole_card_pairs"],e["compatible_hole_card_pairs"])
        return
    assert args.downloads and args.run_id and args.run_id>0
    model=read(Path("data/nl2_hu_multiboard_status_current.json"))["records"][ID]
    assert (model["frequency_rank"],model["solver_profile"],model["family"],model["assumed_model_node_spr"])==(146,"UTG_CO","SRP",7.25)
    # Rank sets alone distinguish every new root, including the simultaneous UTG_CO rank79 batch.
    prior_473 = read(Path("data/nl2_hu_b473_rank146_new_flop.json"))["flop"]
    prior_479 = read(Path("data/nl2_hu_b479_rank146_k_high.json"))["attempts"]
    prior_476 = read(Path("data/nl2_hu_b476_four_utg_river_results.json"))["models"]["99"]["attempts"]
    exclude = [p["flop"] for p in group["pins"] + prior_479 + prior_476] + [prior_473, "QcJh5s", "QdJc3s", "KhQs8d"]
    ranks = {tuple(sorted(f[::2])) for f, _ in BOARDS}
    assert len(ranks) == len(BOARDS) and ranks.isdisjoint(tuple(sorted(f[::2])) for f in exclude)
    attempts=[]
    for flop,turn in BOARDS:
        attempt=process(args.downloads,flop,turn,args.run_id,group,batch="B497",texture=texture(flop))
        attempts.append(attempt)
        if "archive_sha256" not in attempt:continue
        packed=(EVIDENCE/f'NL2_{attempt["archive_code"]}.json.gz').read_bytes()
        assert sha(packed)==attempt["archive_sha256"]
        sources=json.loads(gzip.decompress(packed))["source_arrays"]
        decisions = {}
        attempt["reachable_river_evidence"] = {}
        for source in sources:
            version = source["version"]
            assert sha(compact([source["root_job"][k] for k in ("oop","ip")])) == RANGES[version]
            gate, rivers = native_rivers(source)
            attempt.setdefault("source_gates", {})[version] = gate
            for public in sorted(rivers):
                row = observation(source, args.run_id, attempt["archive_sha256"], public)
                decisions[version, public] = row
                attempt["reachable_river_evidence"].setdefault(public,{})[version] = {
                    k:row[k] for k in ("status","source_sha256","strict_legal_combos","compatible_hole_card_pairs","b50")}
        public=attempt["selected_public_board"]
        if public:
            pair=[decisions[v,public] for v in VERSIONS]
            assert all(r["status"]=="POSITIVE_JOINT_REACH" for r in pair)
            pairs.append(pair)
    count=len(group["boards"])
    assert count==len(pairs)==len(group["pins"])==len({p["flop"] for p in group["pins"]})<=5
    if count>=3:
        path=EVIDENCE/"extensions"/"rank146.json"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(json_bytes(group))
        refs={source_key(ID,e):e for g,e in pairs}
        gtos={source_key(ID,g):g for g,e in pairs}
        MEDIUM.write_bytes(compact(dict(schema="NL2_HU_B497_ORIGINAL_LOCKED_MEDIUM_V1",references=refs,gto_references=gtos))+b"\n")
    report=dict(rank=146,model_id=ID,spot="UTG_CO",actor="UTG_OOP",line=LINE,run_id=args.run_id,
                two_original_anchor_zip_pairs=ARCHIVES,prior_gate_sha256=sha(PRIOR.read_bytes()),
                attempts=attempts,distinct_paired_flops=count)
    REPORT.write_bytes(json_bytes(report))
    print(f"rank146: {count} paired distinct flops")


if __name__=="__main__":
    main()
