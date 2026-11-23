"""Replay the rank1 B19 lock and solve its existing turn job with street-specific pool buckets."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope, source_nodes

MODEL = "ln-iso-lmp_t_model-19hfq8v"
RUN = 44762388523
PIN = "abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST = "9d1509fe5077d019825f833eed04b16d342dfda1"
POOL = "c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a"
MANIFEST = "dd93cdace45b6aa9e3c56f771f87f6999402c1ada4ff09974444e2ec1c082be9"
JOB = "8e8b97a51056c9756c48e92d8bdd27d8107f034be087f55baf2cc8e150ff5474"
ROOT = "f8362b3a1214fe1be02a033dc846c26d1c8d0c9cc76ebd11995bed2c2de2583e"
LOCK = "04374eed1d73fbc9eab3f7b89e8f9671f95420660e61a9a47d48634ab9967978"
GTO = "be5a87e90c6a24464e98431229d2661061bf4f9f7c8005fde314ca9a1248b2f4"
DATA = Path("data")
DOC = Path("docs/NL2_HU_B472_RANK1_STREET_POOL_RATES.md")
HISTORY = DATA / "nl2_hu_b472_rank1_historical_pool_rates.json"
RESULT = DATA / "nl2_hu_b472_rank1_new_pool_lock.json"
PACK = DATA / "solver_evidence/NL2_B472_R1_STREET_LOCK.json.gz"
BUCKETS = {"≤33%": "b33", "34-55%": "b50", "56-80%": "b75", "81-110%": "b100"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path, expected=None):
    if expected:
        assert sha(path) == expected, path
    return json.loads(path.read_bytes())


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def measured(source, pool):
    match = re.fullmatch(r"NL2\.HU_facing_bet\[([123])\]\.(?:by_size\[([^\]]+)\]|(bettor_vs_raise))", source)
    if not match:
        return None
    street, bucket, _ = match.groups()
    table = pool["NL2"]["HU_facing_bet"][street]
    return (int(street), BUCKETS[bucket], table["by_size"][bucket]) if bucket else (int(street), "r", table["bettor_vs_raise"])


def prepare(original, pool_path):
    evidence = original / "evidence"
    assert (evidence/"poker-solver-pin.txt").read_text().strip() == PIN
    assert (evidence/"rust-pin.txt").read_text().strip() == RUST
    manifest = read(evidence/"LMP_CO_BB-4s4h2d-exp_oop.json", MANIFEST)
    folder = original / "solver/postflop/out/LMP_CO_BB/exp_oop"
    root = read(folder/"4s4h2d_multiboard.json", ROOT)
    old = read(folder/"4s4h2d_b50c_8s.json", LOCK)
    old_job = read(folder/"4s4h2d_b50c_8s.job.json", JOB)
    pool = read(pool_path, POOL)
    assert manifest["pool_source_sha256"] == POOL and manifest["file_flop_sha256"] == ROOT
    assert manifest["spot"] == "LMP_CO_BB" and manifest["version"] == "exp_oop"
    assert (old_job["flop"], old_job["turn"], old_job["hero"], old_job["line0"]) == ("4s4h2d", "8s", 0, ["b50", "c", "/"])
    registry = read(DATA/"nl2_hu_multiboard_status_v51_b453_rank32.json")
    record = registry["records"][MODEL]
    board, = [b for b in record["certified_3_to_5_exact_flop_boards"] if b["public_board"] == "2d4h4s8s"]
    assert (record["frequency_rank"], record["label"], board["source_run_id"], board["source_sha256"]) == (1, "CERT-MULTIBOARD", RUN, GTO)
    assert board["assumed_preflop_ranges"] and board["actual_exact_action_line"] == "b50 c/" and board["acting_seat"] == 0
    assert any(l["run_id"] == RUN and l["sha256"] == LOCK and l["version"] == "exp_oop" for l in board["nl2_locked_variants"])
    new_job, metadata = copy.deepcopy(old_job), copy.deepcopy(manifest["locks"])
    rows = []
    for lock, meta in zip(new_job["locks"], metadata, strict=True):
        assert lock["pat"] == meta["pat"]
        lookup = measured(meta["source"], pool)
        if lookup is None:
            continue
        street, token, rate = lookup
        assert meta["n"] == rate["n"] >= 500
        assert abs(lock["fold"]*100-rate["fold"]) < 1e-6 and abs(lock["raise"]*100-rate["raise"]) < 1e-6
        assert lock["pat"] == rf"(?:^|[ /]){token}$"
        prior = old["info"]["lock_stats"].get(lock["pat"])
        pattern = rf"^(?:[^/]*/){{{street-1}}}(?:[^/]+ )?{token}$"
        lock["pat"] = meta["pat"] = pattern
        # Test the exact original node strings and the Rust driver's street-separator convention.
        for node in old["nodes"]:
            line = node["line"]
            intended = line.count("/")+1 == street and re.split("[ /]", line)[-1] == token
            assert bool(re.search(pattern, line)) == intended
        if prior:
            rows.append(dict(street=street, token=token, n=rate["n"], fold=rate["fold"], call=rate["call"], raise_pct=rate["raise"],
                             prior_fold=round(100*prior["fold"],3), prior_raise=round(100*prior["agg"],3),
                             prior_all_streets_nodes=prior["nodes"], pattern=pattern))
    assert {(r["street"],r["token"]) for r in rows} == {(i,t) for i in (1,2,3) for t in ("b50","b100")}
    for r in rows:
        first = next(q for q in rows if q["token"] == r["token"] and q["street"] == 1)
        assert abs(r["prior_fold"]-first["fold"]) < .01 and abs(r["prior_raise"]-first["raise_pct"]) < .01
    history = dict(model=MODEL, flop="4s4h2d", turn="8s", board="2d4h4s8s", line="b50 c/", family="LMP",
                   actor="BB_OOP", assumed_preflop=True, original_run=RUN, GTO_sha256=GTO, lock_sha256=LOCK,
                   root_sha256=ROOT, job_sha256=JOB, pool_sha256=POOL, original_manifest_sha256=MANIFEST,
                   poker_solver_pin=PIN, rust_pin=RUST, rows=rows)
    return root, old, new_job, metadata, board, history


def write_document(history, outcome=None):
    lines = ["# Rank 1 · BB 的轉牌決策", "",
             "LMP_CO_BB，4s4h2d / 8s，翻牌 BB 下半池、CO 跟注，轉牌由 BB 先行。翻前範圍採 169 類假設。", "",
             "B19 的 CO 局部鎖按順序嘗試規則。三街面對同尺寸下注共用一個正規表示式，因此原始 Rust 結果的棄牌與加注率吻合翻牌樣本。下表列出各街在原始 NL2 玩家池中的實測值。樣本數是全池該街該尺寸的決策次數。", "",
             "| 街 | 面對尺寸 | 池樣本數 | 池棄／跟／加 % | B19 鎖後棄／加 % |", "|---|---:|---:|---:|---:|"]
    for r in history["rows"]:
        lines.append(f'| {["翻牌","轉牌","河牌"][r["street"]-1]} | {r["token"][1:]}% | {r["n"]:,} | {r["fold"]} / {r["call"]} / {r["raise_pct"]} | {r["prior_fold"]} / {r["prior_raise"]} |')
    lines.extend(["", "B19 的 b50 與 b100 分別匹配 145 個求解樹節點。兩者皆為跨街數字。過牌後對手下注率與尺寸拆分沿用原始來源所列假設。", "",
                  f'[原始 CFR Run](https://github.com/tetracycline/poker-trainer/actions/runs/{RUN}) · [釘定 NL2 玩家池](https://github.com/tetracycline/poker-solver/blob/{PIN}/inputs/pool_stats.json)'])
    if outcome:
        lines.extend(["", "## 同牌面逐街鎖頻重算", "",
                      f'獨立 Rust 重算在相同父節點、範圍、底池與尺寸下鎖定 CO；BB 有 {outcome["new_compatible_combos"]} 個可達組合。半池具備 {outcome["b50"]["eligible"]} 個合格組合。各動作的來源加權頻率為 '+ "、".join(f"{a} {v}%" for a,v in outcome["action_frequencies_pct"].items())+"。", "",
                      "| 街 | 面對尺寸 | 重算後棄／加 % | Rust 匹配節點 |", "|---|---:|---:|---:|"])
        for row in outcome["achieved"]:
            lines.append(f'| {["翻牌","轉牌","河牌"][row["street"]-1]} | {row["token"][1:]}% | {row["fold_pct"]} / {row["raise_pct"]} | {row["nodes"]} |')
        lines.extend(["", f'[獨立重算 Run](https://github.com/tetracycline/poker-trainer/actions/runs/{outcome["run"]}) · [原始 Rust 與逐組合證據](../{PACK})'])
    DOC.write_text("\n".join(lines)+"\n")


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--original", type=Path, required=True)
    cli.add_argument("--pool", type=Path, required=True)
    cli.add_argument("--driver",type=Path)
    cli.add_argument("--work",type=Path)
    cli.add_argument("--run",type=int)
    args=cli.parse_args()
    root,old,job,metadata,board,history=prepare(args.original,args.pool)
    if not args.driver:
        save(HISTORY,history)
        write_document(history)
        return
    assert read(HISTORY)==history and args.work and args.run and args.run>0
    args.work.mkdir(parents=True,exist_ok=True)
    out=(args.work/"street-locked.json").resolve()
    job["out"]=str(out)
    job_path=args.work/"street-locked.job.json"
    save(job_path,job)
    subprocess.run([str(args.driver.resolve()),str(job_path.resolve())],check=True)
    raw=read(out)
    assert raw["hands"]==old["hands"] and (raw["flop"],raw["pot"],raw["stack"])==(old["flop"],old["pot"],old["stack"])
    assert raw["info"]["gto_expl_pct"]<=.5 and raw["info"]["hero_gap_pct"]<=job["target_pct"]==.5
    new=dict(raw,turn=job["turn"],line0=old["line0"],rivers=old["rivers"])
    new_node, = (n for n in new["nodes"] if (n["board"],n["line"],n["player"])==(board["public_board"],board["actual_exact_action_line"],0))
    key="|".join((new_node["board"],new_node["line"],"0"))
    masks,_=game_reach(root,new)
    compat=compatible_node_reach(root,new,new_node,masks[key])
    node,=source_nodes(dict(new,nodes=[new_node]),{"nodes":{key:compat}})
    assert compat["count"]>0 and abs(node["node_spr"]-board["actual_spr"])<.0001
    achieved=[]
    for row in history["rows"]:
        if row["street"]==1:
            assert row["pattern"] not in raw["info"]["lock_stats"]
            continue
        actual=raw["info"]["lock_stats"][row["pattern"]]
        assert actual["nodes"]>0 and abs(100*actual["fold"]-row["fold"])<.2 and abs(100*actual["agg"]-row["raise_pct"])<.2
        achieved.append(dict(street=row["street"],token=row["token"],fold_pct=round(100*actual["fold"],3),
                             raise_pct=round(100*actual["agg"],3),nodes=actual["nodes"]))
    result=dict(run=args.run, model=MODEL, source_sha256=sha(out), original_source_sha256=LOCK,
                old_job_sha256=JOB, pool_sha256=POOL, achieved=achieved,new_compatible_combos=compat["count"],
                compatible_hole_card_pairs=compat["compatible_hole_card_pairs"],gto_expl_pct=raw["info"]["gto_expl_pct"],
                hero_gap_pct=raw["info"]["hero_gap_pct"],action_frequencies_pct=node["action_frequency_weighted_pct"],
                b50=node["medium_50pct_strict_evidence"],lock_scope=lock_scope(new,metadata,"exp_oop"))
    # Preserve original solver bytes so the source SHA is independently reproducible.
    import base64
    export=dict(schema="NL2_B472_STREET_SPECIFIC_NL2_OOP_V1", run=args.run, job=job, source_file_b64=base64.b64encode(out.read_bytes()).decode(),
                exact_node=node, exact_hands=new["hands"][0], source_sha256=sha(out), history=history)
    PACK.write_bytes(gzip.compress(json.dumps(export,separators=(",",":"),ensure_ascii=False).encode(),mtime=0))
    result["archive_sha256"]=sha(PACK)
    save(RESULT,result)
    write_document(history,result)
    print("Verified",compat["count"],"two-seat legal BB combos",achieved)


if __name__=="__main__":
    main()
