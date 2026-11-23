"""Rebuild BB's exact half-pot / third-pot limped-pot river proof from original CFR arrays."""

import argparse
import base64
import json
from io import BytesIO
from itertools import permutations
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import board_row
from hu_b532_limp_barrels import river_row
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach

sys.path.insert(0, str(Path(__file__).parent / "lines_pipeline"))
from run10_common import classes, hcls

DATA = Path("data")
PIN = DATA / "nl2_hu_b580_frozen.json"
MODEL = "ln-iso-lmp_r_model-1aov4pd"
LINE = "b50 c/b33 c/"
HIST = "7h6d4s"
CODE = "B580_R27_LMP"
ARCHIVE = EVIDENCE / f"NL2_{CODE}.zip"


def suit_isomorphism_class(flop):
    cards = [flop[i : i + 2] for i in range(0, 6, 2)]
    return min(
        tuple(sorted((card[0], pattern["cdhs".index(card[1])]) for card in cards))
        for pattern in permutations("cdhs")
    )


def authenticate_original(frozen, receipts):
    artifact = frozen["original_artifact_id"]
    receipt = json.loads((receipts / f"{artifact}.json").read_bytes())
    assert (
        receipt["id"] == artifact
        and receipt["workflow_run"]["id"] == frozen["original_run"]
    )
    assert receipt["workflow_run"]["repository_id"] == 1438346845
    assert receipt["name"] == "NL2-B532-7h6d4s-gto"
    raw = (receipts / f"{artifact}.zip").read_bytes()
    assert "sha256:" + sha(raw) == receipt["digest"]
    assert sha(raw) == frozen["original_artifact_sha256"]

    with ZipFile(BytesIO(raw)) as receipt_zip:
        manifest = receipt_zip.read("trainer/evidence/7h6d4s-gto.json")
        original = json.loads(manifest)
        root_path = "solver/postflop/" + original["file_flop"]
        (turn_case,) = (c for c in original["cases"] if c["turn"] == "9d")
        turn_path = "solver/postflop/" + turn_case["source_path"]
        return {
            "original-manifest.json": manifest,
            "original-flop.job.json": receipt_zip.read(
                root_path.replace(".json", ".job.json")
            ),
            "original-turn.job.json": receipt_zip.read(
                turn_path.replace(".json", ".job.json")
            ),
            HIST + "/root.json": receipt_zip.read(root_path),
        }


def source_pair(
    z,
    flop,
    turn,
    rivers,
    frozen,
    origin,
    template,
    basis,
    pool,
    pipeline,
    run,
    archive_sha,
):
    raw = lambda name: z.read(f"{flop}/{name}.json")
    root_raw = raw("root")
    root = json.loads(root_raw)
    tmpl, subtmpl = template
    assert (root["flop"], root["pot"], root["stack"]) == (flop, 250, 9900)
    assert (
        not root["info"].get("lock_stats") and 0 <= root["info"]["gto_expl_pct"] <= 0.5
    )
    if flop == HIST:
        assert sha(root_raw) == origin["file_flop_sha256"] == basis["root_raw_sha256"]
        root_job = tmpl
    else:
        root_job = dict(
            tmpl,
            flop=flop,
            out="root.json",
            extract=[
                dict(prefix=[], street=True),
                *[
                    dict(prefix=["b50", "c", card], street=False, raw=True)
                    for card in frozen["root_turns"][flop]
                ],
            ],
        )
        assert json.loads(raw("root.job")) == root_job
    check_limp_source(dict(root_job=root_job, manifest=origin, subgame_job=None))
    (parent,) = (
        n for n in root["nodes"] if n["board"].endswith(turn) and n["line"] == "b50 c/"
    )
    public = parent["board"]
    assert sorted(public[i : i + 2] for i in (0, 2, 4)) == sorted(
        flop[i : i + 2] for i in (0, 2, 4)
    )
    assert parent["pot"] == 500 and parent["bets"] == [125, 125]
    for line, seat, price, bets, action in [
        ("", 0, 250, [0, 0], "b50"),
        ("b50", 1, 375, [125, 0], "c"),
    ]:
        (n,) = (
            n for n in root["nodes"] if n["board"] == public[:6] and n["line"] == line
        )
        assert (n["player"], n["pot"], n["bets"]) == (
            seat,
            price,
            bets,
        ) and action in n["acts"]
    j = dict(
        subtmpl,
        flop=flop,
        turn=turn,
        out="gto.json",
        turn_oop=frozen["turn_oop"],
        turn_ip=frozen["turn_ip"],
        iters=2000,
        target_pct=0.45,
        extract=[dict(prefix=[], street=True)]
        + [dict(prefix=["b33", "c", r], street=True) for r in rivers],
    )
    for seat, name in enumerate(("oop_w", "ip_w")):
        j[name] = [
            [h, w]
            for h, w in zip(root["hands"][seat], parent["wr"][seat], strict=True)
            if w > 1e-4
        ]
    assert (
        j == json.loads(raw("gto.job"))
        and j["line0"] == ["b50", "c", "/"]
        and not j["root_no_bet"]
    )
    assert (j["pot"], j["stack"], j["river_oop"], j["river_ip"]) == (
        500,
        9775,
        frozen["river_menu"],
        frozen["river_menu"],
    )
    root_sha = sha(compact(root))
    root_run = frozen["original_run"] if flop == HIST else run
    manifest = dict(
        spot="LMP_CO_BB",
        pot_family="LMP",
        locks=[],
        preflop_ranges=origin["preflop_ranges"],
    )
    g = dict(
        version="gto",
        root=root,
        root_sha256=root_sha,
        run=run,
        archive_code=CODE,
        archive_sha256=archive_sha,
        manifest=manifest,
    )
    lockjob, metadata = prepare_job(dict(source=g, job=j), "exp_oop", pool, pipeline)
    assert lockjob == json.loads(raw("native.job")) and metadata == json.loads(
        raw("locks")
    )
    e = dict(
        g,
        version="exp_oop",
        manifest=dict(
            manifest,
            locks=metadata,
            gto_parent_source_run_id=root_run,
            gto_parent_source_sha256=root_sha,
        ),
        verified_gto_parent=dict(run=root_run, sha256=root_sha),
        native_job=lockjob,
    )
    for s, filename in [(g, "gto"), (e, "native")]:
        payload = raw(filename)
        sub = json.loads(payload)
        assert (sub["pot"], sub["stack"], sub["flop"]) == (500, 9775, flop)
        assert 0 <= sub["info"]["gto_expl_pct"] <= 0.5
        assert sub["nodes"][0]["board"] == public
        sub.update(line0="b50 c", turn=turn, rivers=rivers)
        s.update(source_sha256=sha(payload), subgame=sub)
    assert g["subgame"]["hands"] == e["subgame"]["hands"]
    assert (
        not g["subgame"]["info"].get("lock_stats")
        and e["subgame"]["info"]["lock_stats"]
    )
    assert 0 <= e["subgame"]["info"]["hero_gap_pct"] <= 0.5
    e.update(
        applied_rust_rates=e["subgame"]["info"]["lock_stats"],
        measured_lock_application=audit_patterns(
            e["subgame"], lockjob, e["manifest"], pool, hero_seat=0
        ),
    )
    identity = dict(
        result_provenance="PINNED_LOCAL_RUST_OUTPUT_VERIFIED_BY_IMPORT",
        origin_solve_run_id=None,
        verification_run_id=run,
        root_raw_sha256=sha(root_raw),
        root_canonical_sha256=root_sha,
        root_job_sha256=sha(compact(root_job)),
        root_gto_gap_pct=root["info"]["gto_expl_pct"],
        gto_job_sha256=sha(raw("gto.job")),
        locked_job_sha256=sha(raw("native.job")),
        original_flop_source="B532_GITHUB_ACTIONS"
        if flop == HIST
        else "LOCAL_PINNED_RUST",
        root_preflop_ranges="ASSUMED_EXPLICIT_169CLASS",
        flop_menu="50%",
        conditional_turn_oop="33%",
        conditional_turn_ip="50%,100%",
        conditional_river_menu=frozen["river_menu"],
    )
    return g, e, public, identity


def current(s, public, route):
    sub = s["subgame"]
    for b, line, seat, price, bets, action in [
        (public[:8], "b50 c/", 0, 500, [0, 0], "b33"),
        (public[:8], "b50 c/b33", 1, 665, [165, 0], "c"),
        (public, LINE, 0, 830, [165, 165], "b50"),
    ]:
        (n,) = (
            n
            for n in sub["nodes"]
            if (n["board"], n["line"], n["player"]) == (b, line, seat)
        )
        assert (n["pot"], n["bets"]) == (price, bets) and action in n["acts"]
    row, _ = river_row(s, LINE, public[-2:], 165)
    assert row["public_board"] == public
    bits = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
    hands = sub["hands"][0]
    seen = {}
    for i, (h, mask) in enumerate(zip(hands, bits, strict=True)):
        if not mask:
            continue
        h = "".join(cardkey(h))
        types = (hcls(h, public[:6]), hcls(h, public[:8]), classes(h, public)[0])
        if not all(
            group in route.get(board_row(public[: 6 + 2 * j]), [[], [], []])[j]
            for j, group in enumerate(types)
        ):
            continue
        actions = n["acts"]
        weights = [
            max(0.0, n["strat"][a * len(hands) + i]) for a in range(len(actions))
        ]
        total = sum(weights)
        assert total > 0
        seen[h] = dict(
            accepted_mask=mask,
            action_order=actions,
            accepted_actions=[a for j, a in enumerate(actions) if mask & (1 << j)],
            strategy={
                a: round(w / total, 7) for a, w in zip(actions, weights, strict=True)
            },
        )
    return row, seen


def measured(e, public, pool):
    sub = e["subgame"]
    root = e["root"]
    masks = game_reach(root, sub)[0]
    out = []
    for b, line, street, bucket in [
        (public[:8], "b50 c/b33", 2, "≤33%"),
        (public, LINE + "b50", 3, "34-55%"),
        (public, LINE + "x", 3, None),
    ]:
        (n,) = (
            n
            for n in sub["nodes"]
            if (n["board"], n["line"], n["player"]) == (b, line, 1)
        )
        record = next(r for r in e["manifest"]["locks"] if re.search(r["pat"], line))
        native = next(r for r in e["native_job"]["locks"] if re.search(r["pat"], line))
        assert native["pat"] == record["pat"]
        if bucket is None:
            assert (
                record["scope"] == "ASSUMED_HISTORY_RATE_OR_SIZE"
                and record["n"] == 0
                and native["bet"] == 0.45
            )
        else:
            assert record["source"] == f"NL2.HU_facing_bet[{street}].by_size[{bucket}]"
            target = pool["HU_facing_bet"][str(street)]["by_size"][bucket]
            assert record["n"] == target["n"] and (native["fold"], native["raise"]) == (
                target["fold"] / 100,
                target["raise"] / 100,
            )
        stat = e["applied_rust_rates"][native["pat"]]
        assert stat["nodes"] > 0
        joint = compatible_node_reach(root, sub, n, masks[f"{b}|{line}|1"])
        out.append(
            dict(
                line=line,
                price=n["pot"],
                bets=n["bets"],
                source=record["source"],
                scope=record["scope"],
                n=record["n"],
                native_rule=native,
                pattern_nodes=stat["nodes"],
                applied_fold=stat["fold"],
                applied_aggressive=stat["agg"],
                reached_deals=joint["compatible_hole_card_pairs"],
            )
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", type=Path, required=True)
    ap.add_argument(
        "--out", type=Path, default=DATA / "nl2_hu_b580_rank27_checkpoint.json"
    )
    ap.add_argument("--receipts", type=Path, required=True)
    ap.add_argument("--run", type=int)
    args = ap.parse_args()
    if args.run is not None:
        assert args.run > 0
    frozen = json.loads(PIN.read_bytes())
    assert frozen["rank"] == 27 and frozen["line"] == LINE
    records = json.loads((DATA / "nl2_hu_multiboard_status_current.json").read_bytes())[
        "records"
    ]
    model = records[MODEL]
    assert (model["frequency_rank"], model["assumed_model_node_spr"]) == (27, 11.53)
    rendered = json.loads(
        subprocess.check_output(["node", "tools/hu_b580_rank27_rows.cjs"])
    )
    routes = rendered["27"]["by_texture"]
    solver = args.solver.resolve()
    assert (
        subprocess.check_output(
            ["git", "-C", solver, "rev-parse", "HEAD"], text=True
        ).strip()
        == SOLVER
    )
    assert sha((solver / "postflop/py/ranges.py").read_bytes()) == RANGES
    assert sha((solver / "postflop/py/pipeline.py").read_bytes()) == PIPELINE
    original_members = authenticate_original(frozen, args.receipts)
    pool_raw = (solver / "inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)["NL2"]
    sys.path.insert(0, str(solver / "postflop/py"))
    import pipeline

    attempts = []
    group = dict(rank=27, model_id=MODEL, boards=[], pins=[])
    medium = dict(
        schema="NL2_HU_B580_ORIGINAL_LOCKED_MEDIUM_V1", references={}, gto_references={}
    )
    archive_sha = sha(ARCHIVE.read_bytes())
    with ZipFile(ARCHIVE) as z:
        assert all(z.read(member) == raw for member, raw in original_members.items())
        basis = json.loads(z.read("source-provenance.json"))
        assert (
            basis["poker_solver"],
            basis["rust"],
            basis["original_run"],
            basis["original_artifact_sha256"],
        ) == (SOLVER, RUST, frozen["original_run"], frozen["original_artifact_sha256"])
        assert (
            basis["original_artifact_id"] == frozen["original_artifact_id"]
            and basis["local_run_id"] is None
        )
        assert set(z.namelist()) == set(basis["source_files"]) | {
            "source-provenance.json"
        }
        assert all(
            sha(z.read(name)) == digest
            for name, digest in basis["source_files"].items()
        )
        original_raw = z.read("original-manifest.json")
        origin = json.loads(original_raw)
        assert sha(original_raw) == frozen["origin_member_sha256"]["manifest"]
        template = []
        for name, role in [
            ("original-flop.job.json", "root_job"),
            ("original-turn.job.json", "turn_job"),
        ]:
            raw = z.read(name)
            assert sha(raw) == frozen["origin_member_sha256"][role]
            template.append(json.loads(raw))
        assert (
            origin["flop"] == "7h6d4s"
            and origin["spot"] == "LMP_CO_BB"
            and origin["version"] == "gto"
        )
        assert (
            origin["solver_pin"],
            origin["solver_ranges_sha256"],
            origin["pool_source_sha256"],
        ) == (PIPELINE, RANGES, POOL)
        assert (
            set(basis["completed_flops"]) == set(frozen["runouts"])
            and not basis["pending_flops"]
        )
        assert (
            len({suit_isomorphism_class(f) for f in frozen["runouts"]})
            == len(frozen["runouts"])
            == 3
        )
        for flop, turns in frozen["runouts"].items():
            selected = False
            for turn, rivers in turns.items():
                g, e, p, identity = source_pair(
                    z,
                    flop,
                    turn,
                    rivers,
                    frozen,
                    origin,
                    template,
                    basis,
                    pool,
                    pipeline,
                    args.run,
                    archive_sha,
                )
                for river in rivers:
                    public = p + river
                    gr, gh = current(g, public, routes)
                    er, eh = current(e, public, routes)
                    common = sorted(gh.keys() & eh.keys())
                    first = measured(e, public, pool)
                    qualifies = bool(common) and first[0]["reached_deals"] > 0
                    if common:
                        assert qualifies
                    named = [
                        dict(
                            hand=h,
                            flop_class=hcls(h, p[:6]),
                            turn_class=hcls(h, p),
                            river_class=classes(h, public)[0],
                            flop_texture=board_row(p[:6]),
                            turn_texture=board_row(p),
                            river_texture=board_row(public),
                            displayed_suggestion="過",
                            gto=gh[h],
                            nl2=eh[h],
                        )
                        for h in common
                    ]
                    chosen = qualifies and not selected
                    attempts.append(
                        dict(
                            flop=flop,
                            turn=turn,
                            public_board=public,
                            boundary=identity,
                            actual_spr=(9775 - 165) / 830,
                            gto_source_sha256=g["source_sha256"],
                            locked_source_sha256=e["source_sha256"],
                            gto_deals=gr["compatible_hole_card_pairs"],
                            nl2_deals=er["compatible_hole_card_pairs"],
                            gto_eligible_hands=sorted(gh),
                            locked_eligible_hands=sorted(eh),
                            rendered_decision_hands=named,
                            gto_medium=gr["b50"],
                            nl2_medium=er["b50"],
                            first_matching_rules=first,
                            selected=chosen,
                        )
                    )
                    if not chosen:
                        continue
                    selected = True
                    if not args.run:
                        continue
                    board, pin = emit_board(
                        model,
                        g,
                        e,
                        public,
                        LINE,
                        texture(flop),
                        viewer_code=f"B580_R27_{flop.upper()}",
                    )
                    pin.update(
                        rendered_decision_hands=named,
                        authenticated_flop_boundary=identity,
                        original_opponent_rules=first,
                        hands_accepting_displayed_suggestion={
                            k: sum(
                                all("x" in w[v]["accepted_actions"] for v in versions)
                                for w in named
                            )
                            for k, versions in [
                                ("gto", ["gto"]),
                                ("nl2", ["nl2"]),
                                ("both", ["gto", "nl2"]),
                            ]
                        },
                    )
                    board["source_run_role"] = "VERIFICATION_OF_LOCAL_NATIVE_RESULTS"
                    board["origin_solve_run_id"] = None
                    board["flop_bet_size_menu"] = "50%"
                    board["restricted_flop_bet_sizes_pct"] = [50]
                    board["conditional_turn_oop_bet_sizes_pct"] = [33]
                    lock = board["nl2_locked_variants"][0]
                    lock.update(
                        variant_label="限半池翻牌，BB 轉牌限三分之一池；轉河牌分街 NL2 回應鎖頻",
                        gto_parent_source_run_id=e["verified_gto_parent"]["run"],
                        gto_parent_source_sha256=e["verified_gto_parent"]["sha256"],
                        source_run_role="VERIFICATION_OF_LOCAL_NATIVE_RESULTS",
                        origin_solve_run_id=None,
                        measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",
                        pool_sha256=POOL,
                        applied_street_rates=rates(e),
                        viewer_archive_code=pin["viewer_archive_code"],
                        viewer_sha256=pin["viewer_sha256"],
                    )
                    group["boards"].append(board)
                    group["pins"].append(pin)
                    medium["references"][source_key(MODEL, er)] = er
                    medium["gto_references"][source_key(MODEL, gr)] = gr
    positives = sum(row["selected"] for row in attempts)
    if args.run:
        assert len(group["boards"]) == positives == len(frozen["runouts"])
        (EVIDENCE / "reverified/rank27.json").write_bytes(json_bytes(group))
        (DATA / "nl2_hu_b580_locked_medium.json").write_bytes(json_bytes(medium))
    args.out.write_bytes(
        json_bytes(
            dict(
                rank=27,
                schema="NL2_HU_B580_LMP_TWO_PRICED_BARRELS_V1",
                import_run=args.run,
                original_artifact_sha256=frozen["original_artifact_sha256"],
                source_bundle_sha256=archive_sha,
                sampled_distinct_flops=positives,
                observations=attempts,
            )
        )
    )


if __name__ == "__main__":
    main()
