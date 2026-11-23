"""Recover exact GTO and locked reach and half-pot decisions from seven historic runs."""
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from hu_b483_locked_medium import PIPELINE, RANGES, PIN, POOL, RUST, digest, encode, proof
from hu_multiboard_promote import FAM_ROOT
from hu_sequential_cfr_reach import game_reach
from solve_hu_missing_branches import EXTRA_SPOTS
from verify_hu_multiboard_100bb import lock_scope


REGISTRY = "data/nl2_hu_multiboard_status_current.json"
FREEZE = "d0fe026b3cd59b50450f99471bd27c55e7d4b522"
REGISTRY_SHA = "6beab66f04bd02129259444f00436dc84d940aaea391f90fb040fca99d73628b"
MANIFEST = Path("data/nl2_hu_b485_original_artifacts.json")
ORIGINS = json.loads(MANIFEST.read_bytes())
OUT = Path("data/nl2_hu_b485_locked_medium.json")
MULTIBOARD_DRIVER = "d9da3d979280666a87c9e8a97baaf6438339a077"


def git_bytes(spec):
    return subprocess.check_output(["git", "show", spec])


@lru_cache(maxsize=1)
def references():
    raw = git_bytes(f"{FREEZE}:{REGISTRY}")
    assert digest(raw) == REGISTRY_SHA
    index = defaultdict(lambda: defaultdict(dict))
    lock_to_gto = {}
    for mid, model in json.loads(raw)["records"].items():
        for b in model["certified_3_to_5_exact_flop_boards"]:
            prefix = [mid, b["public_board"], b["actual_exact_action_line"], b["acting_seat"]]
            run, sh = b["source_run_id"], b["source_sha256"]
            gkey = encode(prefix+[run, sh]).decode()
            if str(run) in ORIGINS:
                index[run][sh][gkey] = (model, b, "gto")
            for lock in b["nl2_locked_variants"]:
                run, sh = lock["run_id"], lock["sha256"]
                if str(run) not in ORIGINS:
                    continue
                lkey = encode(prefix+[run, sh]).decode()
                assert lkey not in lock_to_gto and lock["version"] == ("exp_ip" if b["acting_seat"] else "exp_oop")
                for_key = index[run][sh]
                for_key[lkey] = (model, b, lock["version"])
                lock_to_gto[lkey] = gkey
    return index, lock_to_gto


def legacy_rules(pipeline, spot, version, flop, sizes):
    rules, meta = pipeline.lock_list(spot, version, flop)
    profile = pipeline.SPOTS[spot]
    villain_is_pfr = (profile["pfr"] == "ip") != (version == "exp_ip")
    if version != "gto" and not villain_is_pfr and sizes == "33%,50%,75%":
        pos = profile["pfr"].upper()
        label = f'{profile["kind"]}_PFR_{pos}'
        bucket = pipeline.LK.PH[label]["vs_cbet_by_size"]["34-55%"]
        if bucket["n"] >= 500:
            pat = "^x b50$" if pos == "IP" else "^b50$"
            rules.append(dict(pat=pat, fold=bucket["fold"]/100, **{"raise":bucket["raise"]/100}))
            meta.append(dict(pat=pat, n=bucket["n"], src=label+".vs_cbet_by_size[34-55%]"))
    return rules, meta


@lru_cache(maxsize=1)
def historical_fallbacks():
    raw = git_bytes(MULTIBOARD_DRIVER)
    with tempfile.TemporaryDirectory() as temp:
        file = Path(temp) / "original_multiboard.py"
        file.write_bytes(raw)
        spec = importlib.util.spec_from_file_location("b485_original_multiboard", file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod.make_fallbacks


def check_job(job, game, version, rules):
    assert (job["pot"], job["stack"], job["rake_rate"], job["rake_cap"]) == (game["pot"],game["stack"],.05,1000)
    assert job.get("hero") == {"gto":None,"exp_ip":1,"exp_oop":0}[version]
    assert job.get("locks", []) == rules
    if version == "gto":
        assert not rules and 0 <= game["info"]["gto_expl_pct"] <= .5
    else:
        assert rules and 0 <= game["info"]["hero_gap_pct"] <= .5 and isinstance(game["info"]["lock_stats"], dict)
        assert set(game["info"]["lock_stats"]) <= {r["pat"] for r in rules}


def read_game(archive, rel, sha):
    file = "solver/postflop/" + rel
    raw = archive.read(file)
    assert digest(raw) == sha
    return json.loads(raw), json.loads(archive.read(file.replace(".json", ".job.json")))


def replay(archive, origin, run, wanted, solver, pipeline, ranges, pool):
    mf, = [f for f in archive.namelist() if f.startswith("evidence/") and f.endswith(".json")]
    m = json.loads(archive.read(mf))
    assert not m["failures"]
    modern = m["schema"] == "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
    assert modern or m["schema"] == "HU_MISSING_ACTION_HISTORY_CFR_V1"
    solverpin, rustpin = (("poker-solver-pinned-SHA.txt","rust-engine-pin-SHA.txt") if modern
                          else ("poker-solver-commit.txt","upstream-engine-commit.txt"))
    assert archive.read("evidence/"+solverpin).decode().strip() == PIN
    assert archive.read("evidence/"+rustpin).decode().strip() == RUST
    spot, version = m["spot"], m["version"]
    assert f"-{spot}-{version}-" in origin["name"]
    if modern:
        assert (m["solver_pin"],m["solver_ranges_sha256"],m["pool_source_sha256"]) == (PIPELINE,RANGES,POOL)
        assert m["preflop_ranges"]["source"] == "PINNED_POKER_SOLVER_PREFLOP_CFR"
        assert m["flop_action_sizes"] == ["33%","50%","75%","100%"]
    else:
        assert (m["source_pipeline_sha256"],m["source_ranges_sha256"]) == (PIPELINE,RANGES)
        if "source_preflop_tree_sha256" in m:
            assert m["source_preflop_tree_sha256"] == digest((solver/"preflop/pfsolve.py").read_bytes())
        if m.get("derived_spot_profile"):
            assert m["derived_spot_profile"] == json.loads(encode(EXTRA_SPOTS[spot]))
    roots, output = {}, {}
    for c in m["cases"]:
        sh = c.get("source_sha256") if modern else c["sub_sha256"]
        if sh not in wanted:
            continue
        flop = m["flop"] if modern else c["flop"]
        if flop not in roots:
            if modern:
                raw_rules, meta = historical_fallbacks()(spot,version,pool,pipeline.lock_list,flop)
                assert [p["pat"] for p in meta] == [p["pat"] for p in m["locks"]]
                meta = m["locks"]
            else:
                raw_rules, meta = legacy_rules(pipeline,spot,version,flop,m.get("flop_bet_sizes"))
                meta = [dict(p,source=p["src"]) for p in meta]
            rules = json.loads(encode(raw_rules))
            rootpath = m["file_flop"] if modern else c["flop_json"]
            rootsha = m["file_flop_sha256"] if modern else c["flop_sha256"]
            root, rootjob = read_game(archive,rootpath,rootsha)
            assert (root["pot"]/100,root["stack"]/100) == FAM_ROOT[spot] and root["flop"] == flop
            assert [rootjob["oop"], rootjob["ip"]] == [ranges.to_str(w) for w in ranges.ranges(spot, version)]
            check_job(rootjob,root,version,rules)
            roots[flop] = root,rootsha,rules,meta
        root,rootsha,rules,meta = roots[flop]
        if not modern:
            assert c["flop_sha256"] == rootsha
        sub, job = read_game(archive, c["source_path"] if modern else c["sub_json"], sh)
        check_job(job, sub, version, rules)
        line, turn = c["line"], c["turn"]
        assert (sub["flop"],sub["turn"],sub["line0"],job["line0"]) == (flop,turn,line,[*line.split(),"/"])
        parent, = [n for n in root["nodes"] if n["line"] == line+"/" and n["board"][-2:] == turn]
        assert (sub["pot"],sub["stack"]) == (parent["pot"],root["stack"]-parent["bets"][0])
        for seat, name in enumerate(("oop_w","ip_w")):
            assert job[name] == [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat]) if w > 1e-4]
        scope = lock_scope(sub,meta,version)
        scope.pop("matching_examples",None)
        scope.pop("caveat",None)
        root_applied = sum(v["nodes"] for v in root["info"].get("lock_stats", {}).values())
        sub_applied = sum(v["nodes"] for v in sub["info"].get("lock_stats", {}).values())
        source = dict(source_sha256=sh, source_run_id=run, archive_id=origin["id"], archive_sha256=origin["sha256"],
                      root_sha256=rootsha, root_applied_rust_lock_nodes=root_applied, subgame_applied_rust_lock_nodes=sub_applied,
                      root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],
                      root_locked_hero_gap_pct=root["info"].get("hero_gap_pct"),
                      spot=spot, family=ranges.SPOTS[spot]["kind"],version=version,flop=flop,turn=turn,
                      gto_gap_pct=sub["info"]["gto_expl_pct"],locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),
                      lock_scope=scope)
        masks = game_reach(root,sub)[0]
        nodes = {(n["board"],n["line"],n["player"]): n for n in sub["nodes"]}
        verified = {}
        for key,(model,b,ver) in wanted[sh].items():
            assert (model["solver_profile"],b["flop"],b["turn"],b["exact_flop_action"],ver) == (spot,flop,turn,line,version)
            where = b["public_board"],b["actual_exact_action_line"],b["acting_seat"]
            n = nodes[where]
            assert (n["pot"]/100,(sub["stack"]-max(n["bets"]))/100) == (b["actual_pot_bb"],b["actual_effective_stack_bb"])
            if version == "gto":
                assert b["exact_node_actions"] == n["acts"]
            if where not in verified:
                verified[where] = dict(source, **proof(root,sub,n,masks))
            assert key not in output
            output[key] = verified[where]
    return output


def build(directory, run, solver):
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip() == PIN
    poolraw = (solver/"inputs/pool_stats.json").read_bytes()
    assert digest(poolraw) == POOL
    pool = json.loads(poolraw)["NL2"]
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    info = ORIGINS[str(run)]
    source_api = json.loads((directory/f"{run}.json").read_bytes())
    api = {row["id"]:row for row in (source_api["artifacts"] if isinstance(source_api,dict) else source_api)}
    wanted = references()[0][run]
    output = {}
    for origin in info["artifacts"]:
        a = api[origin["id"]]
        r = a["workflow_run"]
        assert (a["name"],a["digest"],r["id"],r["head_sha"],r["repository_id"],r["head_branch"]) == (
            origin["name"],"sha256:"+origin["sha256"],run,info["trainer_commit"],1438346845,"fix/nl2-hu-lines-audit-20261118")
        file = directory/f'{a["id"]}.zip'
        assert digest(file.read_bytes()) == origin["sha256"]
        with zipfile.ZipFile(file) as archive:
            rows = replay(archive,origin,run,wanted,solver,pipeline,ranges,pool)
        assert rows and not output.keys() & rows.keys()
        output.update(rows)
    assert output.keys() == {k for group in wanted.values() for k in group}
    return output


def assemble(shards):
    all_rows = {}
    for shard in shards:
        assert not all_rows.keys() & shard.keys()
        all_rows.update(shard)
    refs, links = references()
    assert all_rows.keys() == {k for run in refs.values() for group in run.values() for k in group}
    gto = {k:v for k,v in sorted(all_rows.items()) if v["version"] == "gto"}
    locks = {k:dict(all_rows[k],gto=gto.get(links[k])) for k in sorted(links)}
    totals = Counter()
    for kind,rows in (("lock",locks),("gto",gto)):
        for row in rows.values():
            totals[f'{kind}_positive' if row["strict_legal_combos"] else f'{kind}_zero'] += 1
    return dict(schema="NL2_HU_B485_ORIGINAL_LOCKED_MEDIUM_V1",registry=REGISTRY,registry_sha256=REGISTRY_SHA,
                trainer_commits={r:v["trainer_commit"] for r,v in ORIGINS.items()},original_artifacts_sha256=digest(MANIFEST.read_bytes()),
                poker_solver_pin=PIN,rust_engine_pin=RUST,pool_sha256=POOL,totals=dict(sorted(totals.items())),
                references=locks,gto_references=gto)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",type=int)
    p.add_argument("--list-artifacts",action="store_true")
    p.add_argument("--downloads",type=Path)
    p.add_argument("--solver",type=Path)
    p.add_argument("--assemble",type=Path,nargs="+")
    p.add_argument("--out",type=Path,default=OUT)
    a=p.parse_args()
    if a.list_artifacts:
        print(" ".join(str(item["id"]) for item in ORIGINS[str(a.run)]["artifacts"]))
        return
    result = (assemble([json.loads(s.read_bytes()) for s in a.assemble]) if a.assemble
              else build(a.downloads,a.run,a.solver.resolve()))
    a.out.write_bytes(encode(result)+b"\n")
    print(result.get("totals",{"verified":len(result)}))


if __name__=="__main__":
    main()
