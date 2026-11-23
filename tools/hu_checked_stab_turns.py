"""Reproduce a called flop stab and compare the original GTO and locked turn decisions."""
import argparse
from dataclasses import dataclass
import base64
import gzip
import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import board_row, hcls
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey
from hu_trainer_route_gate import compatible

DATA = Path("data")
@dataclass(frozen=True)
class TurnStudy:
    batch: str
    rank: int
    model: str
    filename: str
    template: str
    template_sha: str
    spot: str
    family: str
    preflop_source: str
    root_pot: int
    root_stack: int
    ip_bet_pct: int
    root_branches: tuple
    label: str
    report_schema: str

    @property
    def bet(self):
        return (self.root_pot * self.ip_bet_pct + 50) // 100

    @property
    def pot(self):
        return self.root_pot + 2 * self.bet

    @property
    def stack(self):
        return self.root_stack - self.bet

    @property
    def flop_line(self):
        return f"x b{self.ip_bet_pct} c"

    @property
    def line(self):
        return self.flop_line + "/x"

    def archive_code(self, flop):
        return f"{self.batch}_R{self.rank}_{flop.upper()}"


def rendered_policy(study, source, reach, public, routes):
    game = source["subgame"]
    node, = (n for n in game["nodes"] if (n["line"], n["board"], n["player"]) == (study.line, public, 1))
    assert node["pot"] == study.pot and node["bets"] == [0, 0]
    actions = node["acts"]
    assert "x" in actions and "b50" in actions
    masks = base64.b64decode(reach["compatible_action_mask_b64"], validate=True)
    hands = game["hands"][1]
    result = {}
    for i, (hand, mask) in enumerate(zip(hands, masks, strict=True)):
        if not mask:
            continue
        hand = "".join(cardkey(hand))
        flop_class = hcls(hand, public[:6])
        turn_class = hcls(hand, public)
        label = routes[board_row(public)]["decisions"].get(turn_class)
        if not label or flop_class not in routes[board_row(public[:6])]["parents"]:
            continue
        weights = [max(0, node["strat"][j * len(hands) + i]) for j in range(len(actions))]
        total = sum(weights)
        assert total > 0
        result[hand] = (flop_class, turn_class, label, dict(
            action_order=actions, accepted_mask=mask,
            accepted_actions=[a for j, a in enumerate(actions) if mask & (1 << j)],
            strategy={a: round(w / total, 7) for a, w in zip(actions, weights, strict=True)}))
    return result


def replay(study, spec, template, pool, pipeline, run, route, model):
    flop, turn = spec["flop"], spec["turn"]
    code = study.archive_code(flop)
    path = EVIDENCE / ("NL2_" + code + ".zip")
    digest = sha(path.read_bytes())
    assert digest == spec["sha256"] and turn in spec["root_turns"]
    with ZipFile(path) as z:
        root_raw = z.read("root.json")
        root = json.loads(root_raw)
        extracts = [dict(prefix=[], street=True)]
        for branch in study.root_branches:
            extracts.extend(dict(prefix=branch.split()+[t], street=False, raw=True) for t in spec["root_turns"])
        root_job = dict(template["root_job"], flop=flop, out="root.json", flop_oop="50%",
                        flop_ip=f"{study.ip_bet_pct}%", target_pct=.45, extract=extracts)
        assert json.loads(z.read("root.job.json")) == root_job
        assert (root["flop"], root["pot"], root["stack"]) == (flop, study.root_pot, study.root_stack)
        assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
        parent, = (n for n in root["nodes"] if n["line"] == study.flop_line + "/" and n["board"][-2:] == turn)
        public = parent["board"]
        assert sorted(public[:6][i:i+2] for i in (0,2,4)) == sorted(flop[i:i+2] for i in (0,2,4))
        assert parent["pot"] == study.pot and parent["bets"] == [study.bet, study.bet]
        job = dict(template["subgame_job"], flop=flop, line0=study.flop_line.split()+["/"],
                   turn=turn, out="gto.json", pot=study.pot, stack=study.stack, root_no_bet=False,
                   turn_oop="33%,50%,75%", turn_ip="33%,50%,75%",
                   extract=[dict(prefix=[], street=True)], target_pct=.45, iters=2000)
        for i, key in enumerate(("oop_w", "ip_w")):
            job[key] = [[h,w] for h,w in zip(root["hands"][i], parent["wr"][i], strict=True) if w>1e-4]
        assert json.loads(z.read("gto.job.json")) == job
        manifest = dict(spot=study.spot, pot_family=study.family, locks=[], preflop_ranges=template["manifest"]["preflop_ranges"])
        gto = dict(version="gto", root=root, run=run, archive_code=code, archive_sha256=digest, manifest=manifest)
        lockjob, rules = prepare_job(dict(source=gto, job=job), "exp_ip", pool, pipeline)
        assert json.loads(z.read("lock.job.json")) == lockjob
        root_sha = sha(compact(root))
        locked = dict(gto, version="exp_ip", verified_gto_parent=dict(run=run,sha256=root_sha),
                      manifest=dict(manifest,locks=rules,gto_parent_source_run_id=run,gto_parent_source_sha256=root_sha))
        for source, filename in [(gto,"gto.json"), (locked,"native.json")]:
            raw = z.read(filename)
            sub = json.loads(raw)
            assert (sub["flop"],sub["pot"],sub["stack"]) == (flop,study.pot,study.stack)
            assert 0 <= sub["info"]["gto_expl_pct"] <= .5
            assert sub["nodes"][0]["board"] == public and set(sub["nodes"][0]["acts"]) >= {"x","b50"}
            sub.update(line0=study.flop_line, turn=turn, rivers=[])
            source.update(subgame=sub, source_sha256=sha(raw))
    assert gto["subgame"]["hands"] == locked["subgame"]["hands"]
    assert not gto["subgame"]["info"].get("lock_stats")
    info = locked["subgame"]["info"]
    assert 0 <= info["hero_gap_pct"] <= .5 and info["lock_stats"]
    locked.update(measured_lock_application=audit_patterns(locked["subgame"], lockjob, locked["manifest"], pool, hero_seat=1),
                  applied_rust_rates=info["lock_stats"])
    rows = [audit_decision(s, public, study.line, 1, root_sha) for s in (gto, locked)]
    assert all(r and r["compatible_hole_card_pairs"]>0 for r in rows)
    hands = [rendered_policy(study, s, r, public, route) for s,r in zip((gto, locked), rows, strict=True)]
    common = []
    for h in sorted(hands[0].keys() & hands[1].keys()):
        f,t,label,g = hands[0][h]
        assert (f,t,label) == hands[1][h][:3]
        common.append(dict(hand=h,flop_class=f,turn_class=t,displayed_suggestion=label,gto=g,nl2=hands[1][h][3]))
    assert abs(study.stack/study.pot / model["assumed_model_node_spr"]-1) <= .05
    return public, (gto, locked), rows, common, root_sha


def reproduce(study, spec, driver):
    """Run all three supplied native jobs and compare the complete strategies and gaps."""
    archive = EVIDENCE / ("NL2_" + study.archive_code(spec["flop"]) + ".zip")
    assert sha(archive.read_bytes()) == spec["sha256"]
    with ZipFile(archive) as z, tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        for name, output, threads in [("root.job.json","root.json",2), ("gto.job.json","gto.json",1),
                                      ("lock.job.json","native.json",1)]:
            job = json.loads(z.read(name))
            assert job["out"] == output
            (work / name).write_bytes(compact(job))
            subprocess.run([str(driver),name], cwd=work, check=True,
                           env=dict(os.environ,RAYON_NUM_THREADS=str(threads)))
            expected = json.loads(z.read(output))
            fresh = json.loads((work / output).read_bytes())
            for result in (expected, fresh):
                del result["info"]["secs"]
            assert fresh == expected, (spec["flop"], name)


def main(study):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver", required=True, type=Path)
    cli.add_argument("--run", type=int)
    cli.add_argument("--reproduce-flop", metavar="FLOP")
    cli.add_argument("--out",type=Path)
    args = cli.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    inputs=json.loads((DATA/f"nl2_hu_{study.filename}_inputs.json").read_bytes())
    if args.reproduce_flop:
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
        spec,=(s for s in inputs if s["flop"]==args.reproduce_flop)
        reproduce(study,spec,solver/"postflop/pfdriver/target/release/pfdriver")
        return
    poolraw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(poolraw)==POOL
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    if study.preflop_source=="PINNED_POKER_SOLVER_PREFLOP_CFR":
        from solve_hu_missing_branches import EXTRA_SPOTS
        pipeline.SPOTS.update(EXTRA_SPOTS)
    pool=json.loads(poolraw)["NL2"]
    raw=(EVIDENCE/study.template).read_bytes()
    assert sha(raw)==study.template_sha
    doc=json.loads(gzip.decompress(raw))
    if study.family=="ISO":
        assert (doc["solver"],doc["rust"])==(SOLVER,RUST)
    template,=(src for src in doc["source_arrays"] if src["version"]=="gto")
    assert template["manifest"]["preflop_ranges"]["source"]==study.preflop_source
    assert template["manifest"]["spot"] == study.spot
    if study.family=="SRP":
        from hu_b483_locked_medium import PIPELINE, RANGES
        assert template["manifest"]["solver_pin"]==PIPELINE and template["manifest"]["solver_ranges_sha256"]==RANGES
        import ranges
        assert (template["root_job"]["oop"],template["root_job"]["ip"]) == tuple(ranges.to_str(v) for v in ranges.ranges(study.spot,"gto"))
    routes=json.loads(subprocess.check_output(["node","tools/hu_b592_iso_turn_routes.cjs",str(study.rank)]))[str(study.rank)]
    model=json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][study.model]
    registry_route=json.loads((DATA/"nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][study.model]
    group=dict(rank=study.rank,model_id=study.model,boards=[],pins=[])
    medium=dict(schema=study.report_schema,references={},gto_references={})
    result=[]
    assert 3<=len(inputs)==len({s["flop"] for s in inputs})<=5
    for spec in inputs:
        public,(g,e),rows,hands,root_sha=replay(study,spec,template,pool,pipeline,args.run,routes,model)
        assert compatible(registry_route,dict(public_board=public,actual_exact_action_line=study.line,acting_seat=1))
        result.append(dict(flop=spec["flop"],public_board=public,common_hands=len(hands),
                           strict_pairs=[r["compatible_hole_card_pairs"] for r in rows],
                           nonpolarized_candidates=[r["b50"]["candidate"] for r in rows]))
        if not args.run or not hands:
            continue
        assert args.run > 0
        board,pin=emit_board(model,g,e,public,study.line,texture(spec["flop"]),viewer_code=g["archive_code"])
        pin.update(rendered_decision_hands=hands,source_run_role="VERIFICATION_OF_LOCAL_NATIVE_RESULTS")
        board.update(source_run_role=pin["source_run_role"],origin_solve_run_id=None,flop_bet_size_menu=("50%" if study.ip_bet_pct==50 else "OOP 50%, IP 100%"),
                     restricted_flop_bet_sizes_pct=sorted({50,study.ip_bet_pct}),conditional_turn_oop_bet_sizes_pct=[33,50,75],
                     conditional_turn_ip_bet_sizes_pct=[33,50,75])
        board["nl2_locked_variants"][0].update(source_run_role=pin["source_run_role"],origin_solve_run_id=None,
            variant_label=study.label,pool_sha256=POOL,
            measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",gto_parent_source_run_id=args.run,
            gto_parent_source_sha256=root_sha,applied_street_rates=rates(e),
            viewer_archive_code=pin["viewer_archive_code"],viewer_sha256=pin["viewer_sha256"])
        group["boards"].append(board)
        group["pins"].append(pin)
        for key,r in zip(("gto_references","references"),rows,strict=True):
            medium[key][source_key(study.model,r)]=r
    if args.out:
        args.out.write_bytes(json_bytes(result))
    if args.run:
        assert 3<=len(group["boards"])<=5
        (EVIDENCE/f"reverified/rank{study.rank}.json").write_bytes(json_bytes(group))
        (DATA/f"nl2_hu_{study.batch.lower()}_locked_medium.json").write_bytes(json_bytes(medium))
