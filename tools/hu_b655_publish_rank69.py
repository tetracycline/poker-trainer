"""Authenticate a B655 source and retain every actual rendered rank69 witness."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b655_rank69_checks as study
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b550_rank69_originals import LINE, MID, published_actions, turn_job
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board

RUN = 45271606815
HEAD = "19b59d0dc6342d7f51019d7796bc1e0b2525306c"
ARTIFACT = 14865762105
DIGEST = "e2bc16dba63b34a94161ae43158a27b5baeb78f31b54a0b2869f616898fc0886"


def verify(archive, receipt, pipeline, pool, route, run, head, batch):
    workflow = receipt["workflow_run"]
    assert (workflow["repository_id"], workflow["id"], workflow["head_sha"]) == (1438346845,run,head)
    raw = archive.read_bytes()
    assert receipt["digest"] == "sha256:" + sha(raw)
    with ZipFile(archive) as z:
        claim = json.loads(z.read("proof.json"))
        flop = claim["flop"]
        assert receipt["name"] == batch + "-R69-" + flop
        assert (claim["rank"], claim["model_id"]) == (69,MID)
        assert json.loads(z.read("flop/job.json")) == study.root_job(flop)
        root_raw = z.read("flop/result.json")
        assert sha(root_raw) == claim["root_sha256"]
        root = json.loads(root_raw)
        assert (root["flop"],root["pot"],root["stack"]) == (flop,550,9750)
        assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
        positive = [t for t in claim["turns"] if t["rivers"]]
        assert positive
        chosen = positive[0]
        turn = chosen["turn"]
        assert turn in study.CASES[flop]
        public = chosen["rivers"][0]["public_board"]
        pair, rows, hands = {}, {}, {}
        root_sha = sha(compact(root))
        code = batch + "_R69_" + flop.upper()
        for version in ("gto","exp_ip"):
            job, locks, rivers, prefix = turn_job(root,flop,turn,version,pool,pipeline)
            assert public in [prefix+r for r in rivers]
            assert json.loads(z.read(turn+"-"+version+"/job.json")) == job
            body = z.read(turn+"-"+version+"/result.json")
            sub = json.loads(body)
            assert (sub["flop"],sub["pot"],sub["stack"]) == (flop,914,9568)
            assert 0 <= sub["info"]["gto_expl_pct"] <= .5
            sub.update(line0="b33 c",turn=turn,rivers=rivers)
            manifest = dict(spot="BTN_BB",pot_family="SRP",locks=locks)
            source = dict(root=root,subgame=sub,version=version,run=run,
                          source_sha256=sha(body),manifest=manifest,archive_code=code,archive_sha256=sha(raw))
            if version == "exp_ip":
                assert 0 <= sub["info"]["hero_gap_pct"] <= .5 and sub["info"]["lock_stats"]
                manifest.update(gto_parent_source_run_id=run,gto_parent_source_sha256=root_sha)
                source.update(verified_gto_parent=dict(run=run,sha256=root_sha),
                              applied_rust_rates=sub["info"]["lock_stats"],
                              measured_lock_application=audit_patterns(sub,job,manifest,pool,1))
            else:
                assert not sub["info"].get("lock_stats")
            row = audit_decision(source,public,LINE,1,root_sha)
            assert row["strict_legal_combos"] > 0
            pair[version], rows[version] = source,row
            hands[version] = published_actions(source,row,route)
        common = sorted(hands["gto"].keys() & hands["exp_ip"].keys())
        assert common == chosen["rivers"][0]["hands"] and common
        assert rows["exp_ip"]["b50"] == chosen["rivers"][0]["locked_medium"]
    return flop,public,code,raw,pair,rows,common


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver",type=Path,required=True)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    args = parser.parse_args()
    assert subprocess.check_output(["git","-C",args.solver,"rev-parse","HEAD"],text=True).strip() == study.SOLVER
    raw = (args.solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    sys.path.insert(0,str((args.solver/"postflop/py").resolve()))
    import pipeline
    pool = json.loads(raw)["NL2"]
    receipt = json.loads(args.receipt.read_bytes())
    assert receipt["id"] == ARTIFACT and sha(args.archive.read_bytes()) == DIGEST
    route = json.loads(subprocess.check_output(["node","tools/hu_b550_rank69_routes.cjs"]))
    data = Path("data")
    model = json.loads((data/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][MID]
    flop,public,code,raw,pair,rows,common = verify(args.archive,receipt,pipeline,pool,route,RUN,HEAD,"B655")
    source = data/"solver_evidence"
    (source/("NL2_"+code+".zip")).write_bytes(raw)
    board,pin = emit_board(model,pair["gto"],pair["exp_ip"],public,LINE,texture(flop),viewer_code=code)
    assert board and pin
    board.update(origin_solve_run_id=RUN,source_run_role="ORIGINAL_GITHUB_ACTIONS_NATIVE_SOLVE",
                 restricted_flop_bet_sizes_pct=[33],flop_sizing_assumption="One-third-pot flop menu for both positions")
    board["nl2_locked_variants"][0].update(
        variant_label="原始翻牌真解，轉河牌按 NL2 分街頻率鎖定 BB 回應",
        applied_street_rates=rates(pair["exp_ip"]),measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",pool_sha256=POOL)
    pin.update(shared_rendered_checks=common,worker_artifact_id=ARTIFACT,worker_artifact_sha256=DIGEST,worker_head_sha=HEAD)
    group = dict(rank=69,model_id=MID,boards=[board],pins=[pin])
    observations = dict(gto_references={},references={})
    for version,field in (("gto","gto_references"),("exp_ip","references")):
        observations[field][source_key(MID,rows[version])] = rows[version]
    old = model["remaining_exact_board_evidence"][0]
    assert old["flop"] == "As7h3d" and not route["A_high"]["turn"]
    prior = dict(public_board=old["public_board"],status="NO_RENDERED_TURN_CHECK_BRANCH",
                 original_source_run=old["source_run_id"],original_source_sha256=old["source_sha256"])
    report = dict(group=group,observations=observations,prior_raw_reference=prior)
    (data/"nl2_hu_b655_rank69_partial.json").write_bytes(json_bytes(report))
    print(flop,len(common),"shared checks; recorded as a one-flop partial")


if __name__ == "__main__":
    main()
