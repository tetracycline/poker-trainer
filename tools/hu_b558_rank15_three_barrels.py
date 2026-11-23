"""Verify three independent rank-15 flops against each rendered 75/50/50 action."""

import argparse
import base64
import math
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, sha, json_bytes
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b519_sb_barrels import MODELS, observations
from hu_b552_measured_sb_rivers import (
    first_match_rates,
    priced_job as old_job,
)
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, prepare_job
from hu_multiboard_promote import texture
from hu_native_turn_result import replay, run_native
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey
from hu_b536_sb_barrels import tx, COLUMNS

sys.path.insert(0, str(Path(__file__).resolve().parent / "lines_pipeline"))
from run10_common import hcls, classes

B552_RUN = 45124508379
B552_ARTIFACT = 14794349288
B552_DIGEST = "6ca06379b721c25a769a7cbb03b207aa57207446806cc136f5105ad2ff8ada7f"
B552_HEAD = "2919897006a427e7a7c06eebfb3382cbbb629ece"
OLD = "AcTc3d"
FRESH = "AdJd5c"
NEW = {"AhJh4s": ("Td", "2c"), FRESH: ("Kc", "2h")}
DATA = Path("data")
PARENTS = DATA / "nl2_hu_b558_rank15_parents.json"
RANK = 15
MID, LINE, POT, STACK = MODELS[RANK]


def load_boundary(args, flop, pipeline, ranges):
    catalog = [json.loads(p.read_bytes()) for p in args.originals.glob("*.json")]
    spec = json.loads(PARENTS.read_bytes()).get(flop)
    if spec is None:
        (m,) = (m for m in catalog if m["name"] == f"B558-{flop}-gto")
        spec = dict(
            id=m["id"],
            name=m["name"],
            head=args.head,
            run=args.run,
            sha256=m["digest"][7:],
        )
    aid = spec["id"]
    turn = "4s" if flop == OLD else NEW[flop][0]
    root = load_original(
        args.originals,
        aid,
        spec,
        "SB_BB",
        flop,
        turn,
        "gto",
        pot=600,
        stack=9700,
        pipeline=pipeline,
        ranges=ranges,
        flop_line=LINE,
    )
    menu = "75%" if flop == FRESH else "33%,50%,75%,100%"
    assert root["identity"]["flop_oop_menu"] == root["identity"]["flop_ip_menu"] == menu
    assert (
        root["source"]["subgame"]["pot"] == 1500
        and root["source"]["subgame"]["stack"] == 9250
    )
    return root, args.originals / f"{aid}.zip"


def both_streets(root, v, pool, pipeline):
    flop = root["source"]["subgame"]["flop"]
    rv = NEW[flop][1]
    if v == "gto":
        job, meta = deepcopy(root["job"]), []
    else:
        job, meta = prepare_job(root, v, pool, pipeline)
    assert (
        job["turn_oop"] == job["turn_ip"] == "50%,100%"
        and job["river_oop"] == "50%,100%,a"
    )
    job.update(
        turn_oop="50%",
        river_oop="50%",
        out="turn.json",
        extract=[
            dict(prefix=[], street=True),
            dict(prefix=["b50", "c", rv], street=True),
        ],
    )
    return job, meta


def source_pair(args, root, pool, pipeline):
    flop = root["source"]["subgame"]["flop"]
    turn, river = NEW[flop]
    sources = []
    archives = []
    for v in ("gto", "exp_oop"):
        code = f"B558_R15_{flop}_{turn}_{river}_{v}".upper()
        name = "NL2_" + code + ".zip"
        folder = args.results / code
        if args.driver:
            job, meta = both_streets(root, v, pool, pipeline)
            run_native(folder, args.driver, root, job, meta, args.run, v, name)
        src = replay(
            root, v, pool, pipeline, folder / name, args.run, code, both_streets
        )
        src["subgame"]["rivers"] = [river]
        assert all(
            0 <= src["subgame"]["info"][k] <= 0.5
            for k in (
                ["gto_expl_pct"] if v == "gto" else ["gto_expl_pct", "hero_gap_pct"]
            )
        )
        sources.append(src)
        archives.append(folder / name)
    return sources, archives


def reachable_river_policies(source, row, ancestors, labels):
    game = source["subgame"]
    public = row["public_board"]
    seat = row["acting_seat"]
    hands = game["hands"][seat]
    (node,) = (
        n
        for n in game["nodes"]
        if (n["board"], n["line"], n["player"]) == (public, LINE + "/b50 c/", seat)
    )
    assert (
        seat == 0
        and node["acts"] == row["source_actions"]
        and len(node["strat"]) == len(hands) * len(node["acts"])
    )
    masks = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
    policies = {}
    for i, (hand, mask) in enumerate(zip(hands, masks, strict=True)):
        if not mask:
            continue
        hand_classes = [
            hcls(hand, public[:6]),
            hcls(hand, public[:8]),
            classes(hand, public)[0],
        ]
        cells = [
            tx(public[:n]) + ":" + str(COLUMNS.get(cls, -1))
            for n, cls in zip((6, 8, 10), hand_classes)
        ]
        if (
            cells[0] not in ancestors[0]
            or cells[1] not in ancestors[1]
            or cells[2] not in labels
        ):
            continue
        frequencies = [
            node["strat"][a * len(hands) + i] for a in range(len(node["acts"]))
        ]
        assert (
            all(math.isfinite(f) and f >= 0 for f in frequencies)
            and abs(sum(frequencies) - 1) < 0.002
        )
        policies["".join(cardkey(hand))] = dict(
            cells=cells,
            heuristic={"下注 ½": "b50", "過": "x"}[labels[cells[2]]],
            policy=dict(
                mask=mask,
                actions=node["acts"],
                frequency_pct=[
                    round(100 * f / sum(frequencies), 5) for f in frequencies
                ],
            ),
        )
    return policies


def audit_pair(root, sources, public, anc, acts, checks):
    rows = [
        observations(s, LINE, POT, STACK, root["identity"]["root_sha256"])[public]
        for s in sources
    ]
    evidence = [
        reachable_river_policies(s, row, anc, acts)
        for s, row in zip(sources, rows, strict=True)
    ]
    common = {}
    for hand in sorted(evidence[0].keys() & evidence[1].keys()):
        g, e = (parts[hand] for parts in evidence)
        assert (g["cells"], g["heuristic"]) == (e["cells"], e["heuristic"])
        common[hand] = dict(
            cells=g["cells"],
            heuristic=g["heuristic"],
            gto=g["policy"],
            locked=e["policy"],
        )
    assert common and all(r["compatible_hole_card_pairs"] > 0 for r in rows)
    for k, row in zip(("gto_references", "references"), rows, strict=True):
        checks[k][source_key(MID, row)] = row
    return dict(
        public_board=public,
        gto_sha256=sources[0]["source_sha256"],
        locked_sha256=sources[1]["source_sha256"],
        hands=common,
    ), rows


def compare_displayed_actions(pin, common):
    rows = []
    counts = dict(gto=0, nl2=0, both=0)
    for hand, example in common["hands"].items():
        suggestion = example["heuristic"]
        row = dict(
            hand=hand, rendered_cells=example["cells"], displayed_suggestion=suggestion
        )
        for label, role in [("gto", "gto"), ("nl2", "locked")]:
            policy = example[role]
            actions = policy["actions"]
            mask = policy["mask"]
            selected = [a for i, a in enumerate(actions) if mask & (1 << i)]
            row[label] = dict(
                accepted_mask=mask,
                action_order=actions,
                accepted_actions=selected,
                strategy={
                    a: pct / 100
                    for a, pct in zip(actions, policy["frequency_pct"], strict=True)
                },
            )
            counts[label] += suggestion in selected
        counts["both"] += all(
            suggestion in row[role]["accepted_actions"] for role in ("gto", "nl2")
        )
        rows.append(row)
    pin["rendered_decision_hands"] = rows
    pin["hands_accepting_displayed_suggestion"] = counts


def checkpoint(args, root, pool, pipeline, anc, acts, checks):
    metadata = json.loads((args.originals / "b552-meta.json").read_bytes())
    assert (metadata["id"], metadata["digest"]) == (
        B552_ARTIFACT,
        "sha256:" + B552_DIGEST,
    )
    packed = args.originals / "b552-results.zip"
    assert metadata["name"] == "B552-native-sb-checkpoints" and metadata[
        "digest"
    ] == "sha256:" + sha(packed.read_bytes())
    assert (
        metadata["workflow_run"]["id"],
        metadata["workflow_run"]["head_sha"],
        metadata["workflow_run"]["repository_id"],
    ) == (B552_RUN, B552_HEAD, 1438346845)
    with ZipFile(packed) as z:

        def read(name):
            (entry,) = (p for p in z.namelist() if Path(p).name == name)
            return z.read(entry)

        report = json.loads(read("nl2_hu_b552_sb_river_checkpoints.json"))
        assert report["run"] == B552_RUN
        group = report["groups"]["15"]
        (board,) = group["boards"]
        (pin,) = group["pins"]
        code = "B552_R15_ACTC3D_4S_JS_EXP_OOP"
        dest = EVIDENCE / ("NL2_" + code + ".zip")
        dest.write_bytes(read(dest.name))
        assert sha(dest.read_bytes()) == pin["locked_original_archive_sha256"]
        old = replay(root, "exp_oop", pool, pipeline, dest, B552_RUN, code, old_job)
        old["subgame"]["rivers"] = ["Js"]
        common, rows = audit_pair(
            root, (root["source"], old), root["public"] + "Js", anc, acts, checks
        )
        assert rows == [group["gto_observation"], group["locked_observation"]] and all(
            h in common["hands"] and common["hands"][h]["cells"] == claimed["cells"]
            for h, claimed in pin["shared_rendered_actions"].items()
        )
        compare_displayed_actions(pin, common)
        assert (
            board["public_board"] == root["public"] + "Js"
            and board["source_sha256"] == root["identity"]["source_sha256"]
        )
        assert (
            pin["original_gto_archive"]["root_sha256"]
            == root["identity"]["root_sha256"]
        )
        for key in ("", "locked_"):
            name = "NL2_MULTIBOARD_" + pin[key + "viewer_archive_code"] + ".json.gz"
            raw = read(name)
            assert sha(raw) == pin[key + "viewer_sha256"]
            (EVIDENCE / name).write_bytes(raw)
        name = pin["original_gto_archive"]["repository_file"]
        raw = read(name)
        assert sha(raw) == root["identity"]["artifact_sha256"]
        (EVIDENCE / name).write_bytes(raw)
    return board, pin


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("solver", "originals", "results"):
        p.add_argument("--" + n, type=Path, required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--run", required=True, type=int)
    p.add_argument("--driver", type=Path)
    args = p.parse_args()
    solver = args.solver.resolve()
    assert (
        args.run > 0
        and subprocess.check_output(
            ["git", "-C", solver, "rev-parse", "HEAD"], text=True
        ).strip()
        == SOLVER
    )
    if args.driver:
        assert (
            args.driver.resolve()
            == solver / "postflop/pfdriver/target/release/pfdriver"
            and subprocess.check_output(
                ["git", "-C", solver / "postflop/postflop-solver", "rev-parse", "HEAD"],
                text=True,
            ).strip()
            == RUST
        )
    raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(raw) == POOL
    pool = json.loads(raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline, ranges

    model = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())[
        "records"
    ][MID]
    assert (model["frequency_rank"], model["solver_profile"], model["street"]) == (
        15,
        "SB_BB",
        2,
    )
    anc = json.loads(
        subprocess.check_output(["node", "tools/hu_b536_sb_route_cells.cjs"])
    )["15"]
    acts = json.loads(
        subprocess.check_output(["node", "tools/hu_b552_river_action_cells.cjs"])
    )["15"]
    group = dict(rank=15, model_id=MID, boards=[], pins=[])
    checks = dict(
        schema="NL2_HU_B558_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={}
    )
    if not args.driver:
        root, archive = load_boundary(args, OLD, pipeline, ranges)
        board, pin = checkpoint(args, root, pool, pipeline, anc, acts, checks)
        group["boards"].append(board)
        group["pins"].append(pin)
    for flop, (turn, river) in NEW.items():
        root, archive = load_boundary(args, flop, pipeline, ranges)
        sources, archives = source_pair(args, root, pool, pipeline)
        if args.driver:
            continue
        public = root["public"] + river
        common, rows = audit_pair(root, sources, public, anc, acts, checks)
        board, pin = emit_board(
            model, *sources, public, LINE + "/b50 c/", texture(flop)
        )
        assert (board["actual_pot_bb"], board["actual_effective_stack_bb"]) == (30, 85)
        menu = root["identity"]["flop_oop_menu"]
        board.update(
            frozen_gto_flop=True,
            flop_bet_menu=menu,
            restricted_tree_assumption=True,
            gto_turn_oop_bet_menu="50%",
            gto_river_oop_bet_menu="50%",
        )
        pin.update(original_gto_archive=root["identity"])
        compare_displayed_actions(pin, common)
        variant = board["nl2_locked_variants"][0]
        variant.update(
            pool_sha256=POOL,
            variant_label=("翻牌下注限 ¾ 池" if menu == "75%" else "翻牌含四種下注尺寸")
            + "，SB 轉河下注限半池，BB 按 NL2 分街鎖頻",
            gto_parent_source_run_id=root["source"]["run"],
            gto_parent_source_sha256=root["identity"]["root_sha256"],
            turn_oop_bet_menu="50%",
            river_oop_bet_menu="50%",
            viewer_archive_code=pin["viewer_archive_code"],
            viewer_sha256=pin["viewer_sha256"],
            applied_street_rates=rates(sources[1]),
            first_matching_barrel_rates=first_match_rates(
                sources[1], archives[1], pool, LINE
            ),
        )
        for path in archives:
            shutil.copyfile(path, EVIDENCE / path.name)
        parent = f"NL2_B558_R15_{flop.upper()}_PARENT.zip"
        shutil.copyfile(archive, EVIDENCE / parent)
        pin["original_gto_archive"]["repository_file"] = parent
        group["boards"].append(board)
        group["pins"].append(pin)
    if not args.driver:
        assert len({b["flop"] for b in group["boards"]}) == 3
        (EVIDENCE / "reverified/rank15.json").write_bytes(json_bytes(group))
        (DATA / "nl2_hu_b558_locked_medium.json").write_bytes(json_bytes(checks))


if __name__ == "__main__":
    main()
