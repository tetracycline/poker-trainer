"""Solve the named B496 rank-71 river from the printed reach of each original policy."""

import argparse
import base64
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b472_street_lock import POOL
from hu_b496_rank71_baseline import LINE, MODEL, observations, qualified, read_source
from hu_sequential_cfr_reach import accepted, cardkey, mask_at_node
from verify_hu_multiboard_100bb import strict_medium_evidence

PUBLIC = "2c2d4h4c2s"
RUN = 45106332670
REFS = {
    "gto": (
        14787866823,
        "0bc9dd8ace0294bb1026442f6b9aa2a9ceea568104f267b5c22bea87c3f43ef0",
    ),
    "exp_oop": (
        14788570107,
        "e559b2877baa42099b6ae8da156f1e18143891a9938738d5729b8014cc247992",
    ),
}
PATCH = Path("tools/hu_b561_river_root.patch")
SOURCE = "NL2.HU_facing_bet[3].by_size[34-55%]"
PAT = "^b50 c/x b50 c/b50$"


def one(game, board, line):
    (node,) = (n for n in game["nodes"] if (n["board"], n["line"]) == (board, line))
    return node


def load(directory, version):
    artifact, digest = REFS[version]
    ref = {"id": artifact, "run": RUN, "zip_sha256": digest}
    src = read_source(directory, ref, version, PUBLIC[:6], False)[PUBLIC[6:8]]
    sub, root = src["subgame"], src["root"]
    original = observations(src)[PUBLIC]
    assert qualified(src, original) and original["source_actions"] == ["x"]
    with ZipFile(directory / f"{artifact}.zip") as z:
        path = "solver/postflop/" + src["provenance"]["original_subgame_path"]
        job_bytes = z.read(path.replace(".json", ".job.json"))
        pool_bytes = z.read("trainer/evidence/pool_stats.json")
    assert sha(pool_bytes) == POOL
    job = json.loads(job_bytes)
    assert (job["river_ip"], job["river_raise"], job.get("river_donk")) == (
        "50%,100%,a",
        "a",
        "",
    )
    stat = json.loads(pool_bytes)["NL2"]["HU_facing_bet"]["3"]["by_size"]["34-55%"]
    assert stat == {"n": 64272, "fold": 53.1, "call": 37.6, "raise": 9.3}
    if version == "exp_oop":
        (meta,) = (r for r in src["manifest"]["locks"] if r.get("source") == SOURCE)
        (rule,) = (r for r in job["locks"] if r["pat"] == meta["pat"])
        assert (rule["fold"], rule["raise"], meta["n"]) == (
            stat["fold"] / 100,
            stat["raise"] / 100,
            stat["n"],
        )

    # Start with the authenticated raw flop-to-turn ranges. Multiply each actor's own
    # printed turn strategy at check, half-pot bet, call; never feed joint w into Range.
    # The archive rounds strategy to 1e-4. Verify the resulting blocker-adjusted
    # marginal weights hand by hand against the independently printed original river.
    weights = [dict(job[k]) for k in ("oop_w", "ip_w")]
    live = [set(map(cardkey, seat)) for seat in sub["hands"]]
    for game, board, line, action in [
        (root, PUBLIC[:6], "", "b50"),
        (root, PUBLIC[:6], "b50", "c"),
        (sub, PUBLIC[:8], "b50 c/", "x"),
        (sub, PUBLIC[:8], "b50 c/x", "b50"),
        (sub, PUBLIC[:8], "b50 c/x b50", "c"),
    ]:
        node = one(game, board, line)
        seat = node["player"]
        live[seat] &= accepted(node, game["hands"], action)
        if game is root:
            continue
        hands = sub["hands"][seat]
        offset = len(hands) * node["acts"].index(action)
        for i, h in enumerate(hands):
            weights[seat][h] *= node["strat"][offset + i]
    old = one(sub, PUBLIC, LINE)
    ranges = []
    for seat in (0, 1):
        ranges.append(
            {
                h: w
                for h, w in weights[seat].items()
                if w > 0 and PUBLIC[-2:] not in cardkey(h)
            }
        )
        live[seat] &= {
            cardkey(h)
            for h, w in zip(sub["hands"][seat], old["w"][seat], strict=True)
            if w > 1e-4
        }
    return {
        "provenance": src["provenance"],
        "original_job_sha256": sha(job_bytes),
        "baseline": original,
        "hands": sub["hands"],
        "old_node": old,
        "ranges": ranges,
        "strict": live,
        "pool": stat,
    }


def prepare(source, version):
    old = source["old_node"]
    assert (old["player"], old["pot"], old["bets"]) == (0, 1000, [250, 250])
    job = {
        "flop": PUBLIC[:6],
        "turn": PUBLIC[6:8],
        "river": PUBLIC[8:],
        "pot": 1000,
        "stack": 9525,
        "rake_rate": 0.05,
        "rake_cap": 1000,
        "oop_w": list(source["ranges"][0].items()),
        "ip_w": list(source["ranges"][1].items()),
        "line0": ["b50", "c", "/", "x", "b50", "c", "/"],
        "flop_oop": "",
        "flop_ip": "",
        "flop_raise": "",
        "turn_oop": "",
        "turn_ip": "",
        "turn_raise": "",
        "river_oop": "50%",
        "river_ip": "50%,100%,a",
        "river_raise": "a",
        "iters": 3000,
        "target_pct": 0.10,
        "extract": [{"prefix": [], "street": True, "raw": True}],
        "out": "river.json",
    }
    if version == "exp_oop":
        pool = source["pool"]
        job.update(
            hero=0,
            rank_pct=0.10,
            locks=[
                {"pat": PAT, "fold": pool["fold"] / 100, "raise": pool["raise"] / 100}
            ],
        )
    return job


def audit(folder, source, version, job):
    job_raw, game_raw = (
        (folder / "river.job.json").read_bytes(),
        (folder / "river.json").read_bytes(),
    )
    assert json.loads(job_raw) == json.loads(compact(job))
    game = json.loads(game_raw)
    node, reply = one(game, PUBLIC, LINE), one(game, PUBLIC, LINE + "b50")
    assert (node["player"], node["acts"], node["pot"], node["bets"]) == (
        0,
        ["x", "b50"],
        1000,
        [0, 0],
    )
    assert (reply["player"], reply["pot"], reply["bets"]) == (
        1,
        1500,
        [500, 0],
    ) and reply["acts"] == ["f", "c", "a"]
    info = game["info"]
    assert 0 <= info["gto_expl_pct"] <= 0.10 and len(set(game["hands"][0])) == len(
        game["hands"][0]
    )
    applied = None
    if version == "exp_oop":
        assert set(info["lock_stats"]) == {PAT} and 0 <= info["hero_gap_pct"] <= 0.10
        applied = info["lock_stats"][PAT]
        assert (
            applied["nodes"] == 1
            and abs(applied["fold"] - 0.531) < 0.00001
            and abs(applied["agg"] - 0.093) < 0.00001
        )
    errors = []
    live = []
    for seat in (0, 1):
        result = dict(zip(game["hands"][seat], node["w"][seat], strict=True))
        predicted = [result.get(h, 0) for h in source["hands"][seat]]
        actual = source["old_node"]["w"][seat]
        deviation = [abs(x - y) for x, y in zip(predicted, actual, strict=True)]
        scale = sum(deviation) / sum(actual)
        errors.append(
            {"max_weight_error": max(deviation), "total_relative_absolute_error": scale}
        )
        assert max(deviation) < 0.005 and scale < 0.0001, errors
        live.append(
            source["strict"][seat] & {cardkey(h) for h, w in result.items() if w > 1e-4}
        )
    mask = mask_at_node(node, game["hands"])
    rows = []
    opponent_ranges = [
        (i, cardkey(h)) for i, h in enumerate(game["hands"][1]) if cardkey(h) in live[1]
    ]
    reply_mass = [0.0] * len(reply["acts"])
    pairs_total = half_pairs = 0
    for i, h in enumerate(game["hands"][0]):
        cards = cardkey(h)
        opponents = (
            [j for j, v in opponent_ranges if set(cards).isdisjoint(v)]
            if cards in live[0]
            else []
        )
        pairs = len(opponents)
        if not pairs:
            mask[i] = 0
            continue
        assert mask[i]
        pairs_total += pairs
        if mask[i] & 2:
            half_pairs += pairs
            for j in opponents:
                # Marginal solver lock_stats and the response mix seen over the strictly reached
                # deals can differ. Weight each exact pair by both ranges and the hero bet.
                mass = (
                    node["wr"][0][i] * node["strat"][len(mask) + i] * node["wr"][1][j]
                )
                assert mass > 0 and reply["w"][1][j] > 0
                for k in range(len(reply_mass)):
                    reply_mass[k] += (
                        mass * reply["strat"][k * len(game["hands"][1]) + j]
                    )
        rows.append(
            {
                "hand": h,
                "compatible_pairs": pairs,
                "accepted_mask": mask[i],
                "frequencies": {
                    a: node["strat"][j * len(mask) + i]
                    for j, a in enumerate(node["acts"])
                },
            }
        )
    baseline = source["baseline"]
    assert (len(rows), pairs_total) == (
        baseline["strict_legal_combos"],
        baseline["compatible_hole_card_pairs"],
    )
    medium = strict_medium_evidence(node, game, base64.b64encode(mask).decode())
    assert medium["eligible"] == sum(
        bool(row["accepted_mask"] & 2) for row in rows
    ) and bool(half_pairs) == bool(medium["eligible"])
    assert sum(reply_mass) > 0
    return {
        "version": version,
        "original": source["provenance"],
        "original_job_sha256": source["original_job_sha256"],
        "input_sha256": sha(job_raw),
        "output_sha256": sha(game_raw),
        "gto_gap_pct": info["gto_expl_pct"],
        "hero_gap_pct": info.get("hero_gap_pct"),
        "source_rounding_errors": errors,
        "actions": node["acts"],
        "reply_actions": reply["acts"],
        "river_reply": applied,
        "strict_legal_combos": len(rows),
        "compatible_pairs": pairs_total,
        "half_pot_pairs": half_pairs,
        "strict_reply_frequencies": {
            a: x / sum(reply_mass)
            for a, x in zip(reply["acts"], reply_mass, strict=True)
        },
        "b50": medium,
        "hands": rows,
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--originals", type=Path, required=True)
    cli.add_argument("--work", type=Path, required=True)
    cli.add_argument("--driver", type=Path)
    cli.add_argument("--run", type=int, required=True)
    args = cli.parse_args()
    reports = {}
    for v in REFS:
        source = load(args.originals, v)
        job = prepare(source, v)
        folder = (args.work / v).resolve()
        folder.mkdir(exist_ok=True, parents=True)
        if args.driver:
            (folder / "river.job.json").write_bytes(compact(job))
            subprocess.run(
                [str(args.driver.resolve()), "river.job.json"],
                cwd=folder,
                timeout=90,
                check=True,
            )
        reports[v] = audit(folder, source, v, job)
    (old,) = (
        r
        for r in json.loads(Path("data/nl2_hu_b500_half_pot_leads.json").read_bytes())[
            "records"
        ]
        if r["public_board"] == PUBLIC
    )
    assert (
        old["status"] == "ZERO_JOINT_REACH"
        and old["exp_oop"]["compatible_hole_card_pairs"] == 0
    )
    for v, k in [("gto", "original_gto_sha256"), ("exp_oop", "original_lock_sha256")]:
        assert old[k] == reports[v]["original"]["original_source_sha256"]
    data = {
        "schema": "NL2_HU_B561_FROZEN_RIVER_V1",
        "model_id": MODEL,
        "rank": 71,
        "run": args.run,
        "solver": SOLVER,
        "engine": RUST,
        "driver_patch_sha256": sha(PATCH.read_bytes()),
        "scope": "CONDITIONAL_RIVER_WITH_ROUNDED_ORIGINAL_TURN_POLICIES",
        "public_board": PUBLIC,
        "line": LINE,
        "seat": 0,
        "pot_bb": 10,
        "stack_bb": 95.25,
        "original_run": RUN,
        "full_turn_alternative_run": old["source_run_id"],
        "full_turn_status": old["status"],
        "pool": dict(
            source=SOURCE,
            sha256=POOL,
            scope="STREET_AND_SIZE_MARGINAL",
            **source["pool"],
        ),
        "policies": reports,
    }
    (args.work / "report.json").write_bytes(compact(data) + b"\n")
    print(
        [
            (v, r["strict_legal_combos"], r["compatible_pairs"], r["b50"])
            for v, r in reports.items()
        ]
    )


if __name__ == "__main__":
    main()
