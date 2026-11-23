"""Authenticate fresh BTN/BB turns following a half-pot BB lead, BTN call and BB check."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case
from solve_hu_multiboard_100bb import measured_caller_flop_lead

MID = "ln-ipfr-t_model-qcljc6"
LINE = "b50 c/x"
FLOPS = ("6s5h4d", "5h4h3s", "7d5c4c", "6d4c3h", "8h7h5c")
VERSIONS = ("gto", "exp_ip")


def open_source(folder, item, flop, version, run, head, pool, pipeline, ranges):
    aid = item["id"]
    pin = dict(name=item["name"], run=run, head=head, sha256=item["digest"].split(":")[1])
    assert pin["name"] == f"B524-R8-{flop}-{version}"
    context = item["workflow_run"]
    assert (context["id"], context["head_sha"], context["repository_id"]) == (run, head, 1438346845)
    file = folder / f"{aid}.zip"
    assert sha(file.read_bytes()) == pin["sha256"]
    record = dict(artifact_id=aid, sha256=pin["sha256"], name=pin["name"], turns=[], identity=[])
    passing = {}
    with ZipFile(file) as z:
        candidates = [n for n in z.namelist() if n.startswith("trainer/evidence/") and n.endswith(".json") and not n.endswith("pool_stats.json")]
        if not candidates:
            return passing, dict(record, status="WORKER_DID_NOT_EMIT_ORIGINAL_MANIFEST")
        mf, = candidates
        m = json.loads(z.read(mf))
        assert (m["spot"], m["version"], m["flop"], m["selected_lines"], m["turns"]) == ("BTN_BB",version,flop,["b50 c"],pipeline.turns_for(flop)[:2])
        assert (m["flop_size_profile"],m["flop_line_policy"],m["restricted_tree_assumption"],m["turn_line_policy"]) == ("full","oop-b50only",False,"checkcheck")
        record.update(skipped=m["skipped"],failures=m["failures"])
        if m["failures"] or not m["cases"]:
            return passing, dict(record,status="NO_COMPLETE_AUTHENTICATED_ORIGINAL")
        rule, metadata = measured_caller_flop_lead(pool)
        if version == "exp_ip":
            assert m["measured_bb_flop_lead"] == metadata
            first = next(r for r in m["locks"] if re.search(r["pat"], ""))
            assert (first["pat"],first["n"],first["source"],first["scope"]) == ("^$",metadata["n"],metadata["src"],metadata["scope"])
        for case in m["cases"]:
            turn = case["turn"]
            assert case["line"] == "b50 c" and turn in m["turns"]
            stages = []
            for path, checksum in ((m["file_flop"],m["file_flop_sha256"]),(case["source_path"],case["source_sha256"])):
                name = "solver/postflop/" + path
                raw = z.read(name)
                assert sha(raw) == checksum
                game, job = json.loads(raw), json.loads(z.read(name[:-5]+".job.json"))
                info = game["info"]
                stages.append((info["gto_expl_pct"], info.get("hero_gap_pct")))
                if version == "exp_ip":
                    observed = next(r for r in job["locks"] if re.search(r["pat"], ""))
                    assert observed == rule
                    audit_patterns(game,job,m,pool,hero_seat=1)
                    if path == m["file_flop"]:
                        stat = info["lock_stats"]["^$"]
                        assert stat["nodes"] == 1 and abs(stat["agg"] - rule["bet"]) < .001
                        record["flop_opening_lock"] = dict(scope=metadata["scope"],n=metadata["n"],opening_rule=rule,rust=stat)
            if any(not 0<=gap<=.5 or (version=="exp_ip" and not 0<=hero<=.5) for gap,hero in stages):
                record["turns"].append(dict(turn=turn,status="ORIGINAL_STAGE_EXCEEDS_HALF_PERCENT",stage_gaps=stages))
                continue
            original = load_original(folder,aid,pin,"BTN_BB",flop,turn,version,pot=550,stack=9750,
                                     flop_line="b50 c",pipeline=pipeline,ranges=ranges)
            src, ident = original["source"], original["identity"]
            assert ident["flop_oop_menu"] == ident["flop_ip_menu"] == "33%,50%,75%,100%"
            assert (src["subgame"]["pot"],src["subgame"]["stack"]) == (1100,9475)
            row = audit_decision(src,original["public"],LINE,1,ident["root_sha256"])
            if not row:
                record["turns"].append(dict(turn=turn,status="TARGET_NOT_EXPORTED"))
                continue
            record["turns"].append(row)
            if row["compatible_hole_card_pairs"] > 0:
                passing[row["public_board"]] = (src, ident, row)
    return passing, record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--originals",type=Path,required=True)
    ap.add_argument("--solver",type=Path,required=True)
    ap.add_argument("--run",type=int,required=True)
    ap.add_argument("--head",required=True)
    args = ap.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip()==SOLVER
    raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    # The displayed 2.736% is an occurrence-opportunity estimate. Pool frequencies refer to HU SRP donk opportunities.
    model = json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][MID]
    assert (model["frequency_rank"],model["solver_profile"],model["street"],model["assumed_model_node_spr"]) == (8,"BTN_BB",1,8.364)
    items = [json.loads(p.read_bytes()) for p in args.originals.glob("*.json")]
    catalog = {item["name"]:item for item in items}
    assert len(items) == len(catalog)
    group = dict(rank=8,model_id=MID,boards=[],pins=[])
    ledger = dict(schema="NL2_B524_COMPLETE_BB_LEAD_REACH",run=args.run,head=args.head,
                  estimated_opportunity_fraction=model["estimated_nl2_occurrence_opportunity_frac"],
                  observed_srp_donk=pool["postflop_HU"]["SRP_donk"],pool_sha256=POOL,
                  measured_half_pot_bucket_opportunity_frac=pool['postflop_HU']['SRP_donk']['pct'] * pool['postflop_HU']['SRP_donk']['sizes']['34-55%'] / 10000,exact_conditional_frequency=None,
                  native_spr=9475/1100,flops=[])
    checks = dict(schema="NL2_B524_NATIVE_PAIRED_TURN_VERSION_V1", references={}, gto_references={})
    for flop in FLOPS:
        tables, audit = [], dict(flop=flop,versions={},selected=None)
        for version in VERSIONS:
            item = catalog.get(f"B524-R8-{flop}-{version}")
            table, entry = open_source(args.originals,item,flop,version,args.run,args.head,pool,pipeline,ranges) if item else ({},dict(status="MISSING_ORIGINAL_ARTIFACT"))
            tables.append(table)
            audit["versions"][version] = entry
        ledger["flops"].append(audit)
        common = sorted(tables[0].keys() & tables[1].keys())
        if not common:
            continue
        # The rank8 low-flop calling row allows good top pair and middle or small pair.
        # Require an explicit hand witness in both independently replayed ranges.
        selected = None
        ranks = "23456789TJQKA"
        flop_ranks = set(flop[::2])
        assert len(flop_ranks) == 3 and all(ranks.index(r) <= ranks.index("9") for r in flop_ranks)
        top = max(flop_ranks, key=ranks.index)
        for public in common:
            (g,gi,gr),(e,ei,er) = (table[public] for table in tables)
            hands = [source_case(model, src, public, LINE, 1)[1] for src in (g,e)]
            witnesses = []
            for hand in sorted(hands[0] & hands[1]):
                hole = {c[0] for c in hand}
                matched = hole & flop_ranks
                if len(hole) == 2 and len(matched) == 1 and (top not in matched or "A" in hole):
                    witnesses.append("".join(hand))
            if witnesses:
                selected = public
                break
        if selected is None:
            audit["status"] = "NO_COMMON_FLOP_PAIR_IN_RENDERED_CALL_ROW"
            continue
        audit["shared_flop_pair_witnesses"] = witnesses
        for version,ident in zip(VERSIONS,(gi,ei),strict=True):
            path = args.originals/f"{ident['artifact_id']}.zip"
            shutil.copyfile(path,EVIDENCE/f"NL2_B524_R8_{flop.upper()}_{version.upper()}.zip")
        b,pin = emit_board(model,g,e,public,LINE,texture(flop))
        assert b["actual_pot_bb"] == 11 and b["actual_effective_stack_bb"] == 94.75
        assert (pin["GTO_compatible_hole_card_pairs"],pin["NL2_compatible_hole_card_pairs"]) == (gr["compatible_hole_card_pairs"],er["compatible_hole_card_pairs"])
        pin.update(original_gto_archive=gi,original_locked_archive=ei)
        b["nl2_locked_variants"][0].update(variant_label="BB 翻牌領打採用實測單加注底池頻率，轉河牌使用分街鎖頻",
                                           measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",pool_sha256=POOL)
        group["boards"].append(b)
        group["pins"].append(pin)
        checks["gto_references"][source_key(MID,gr)]=gr
        checks["references"][source_key(MID,er)]=er
        audit["selected"]=public
    assert len({b["flop"] for b in group["boards"]}) == len(group["boards"]) <= 5
    Path("data/nl2_hu_b524_rank8_attempts.json").write_bytes(json_bytes(ledger))
    if len(group["boards"]) >= 3:
        (EVIDENCE/"reverified/rank8.json").write_bytes(json_bytes(group))
        Path("data/nl2_hu_b524_locked_medium.json").write_bytes(json_bytes(checks))


if __name__ == "__main__":
    main()
