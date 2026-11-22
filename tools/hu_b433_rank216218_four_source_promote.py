#!/usr/bin/env python3
"""B433: promote ranks216/218 from four independent exact original GTO + actual NL2-IP source flops.
No solver reruns: authenticate immutable B2/B400/B393/B429 GTO and B2/B412/B421/B431 NL2-IP artifacts.
Only exact named CO-IP boards, exact line, matching SPR and positive sequential 40/70 combo reach.
"""
import argparse, copy, hashlib, importlib, json, pathlib

import hu_b427_rank216218_three_true_sources_promote as b427
import hu_b431_rank216218_one_new_texture_nl2_ip_pair as b431
from hu_b421_rank216_218_true_co_ip_pairs import check as source_check
from hu_multiboard_promote import texture
import hu_cert_lock_medium_audit as source_audit
import hu_cert_lock_medium_coverage_matrix as medium_matrix

D = pathlib.Path("data")
PARENT = D / "nl2_hu_multiboard_status_v50_b417_rank166.json"
TRIAGE = D / "nl2_hu_b370_first10_approx_source_triage.json"
B393 = D / "nl2_hu_b393_five_cobb_gto_first_three_flops.json"
B400 = D / "nl2_hu_b400_five_cobb_gto_second_three_flops.json"
B412 = D / "nl2_hu_b412_r216218_one_real_nl2_ip_original_pair.json"
B421 = D / "nl2_hu_b421_r216218_one_real_nl2_ip_original_pair.json"
B429 = D / "nl2_hu_b429_r216218_three_new_texture_gto_sources.json"
B431 = D / "nl2_hu_b431_r216218_one_new_texture_nl2_ip_pair.json"
PRE = D / "nl2_hu_b433_r216218_four_true_source_pre_cert_gate.json"
STATUS = D / "nl2_hu_multiboard_status_v52_b433_rank216_218.json"
MATRIX = D / "nl2_hu_cert_lock_medium_matrix_v52_b433.json"
AUDIT = D / "nl2_hu_cert_lock_medium_audit_v52_b433.json"
PROOF = D / "nl2_hu_b433_rank216218_four_true_source_cert_proof.json"
DOC = pathlib.Path("docs/NL2_HU_B433_R216218_FOUR_TRUE_SOURCE_CERT.md")
TARGET = {216: "ln-ipfr-r_model-7kv23r", 218: "ln-ipfr-r_model-h0c7q7"}
FLOPS = ("Js9h4d", "Td8h3c", "Js9h5d", "7c6h5d")
LINE = "x b50 c/x b50 c/x"
V52 = "NL2_HU_392_MULTIBOARD_CERT_STATUS_V52_B433_R216_R218"

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def attach_source_paths(verified):
    # The shared verifier consumes the source path as well as the SHA; recover it from
    # the authenticated manifest rather than assuming every historical adapter emits it.
    for case in verified["real_cases"]:
        matches = [
            row for row in verified["manifest"]["cases"]
            if row["source_sha256"] == case["source_sha256"]
            and row["turn"] == case["turn"]
            and row["line"] == case["line"]
        ]
        assert len(matches) == 1, (case["source_sha256"], case["turn"], len(matches))
        case["source_path"] = matches[0]["source_path"]
    return verified

def actual_combo_counts(pin, original, partial, groot, eroot):
    gc = next(c for c in original["real_cases"] if c["source_sha256"] == pin["original_GTO_source_sha256"] and c["turn"] == pin["turn"])
    ec = next(c for c in partial["real_cases"] if c["source_sha256"] == pin["NL2_IP_source_sha256"] and c["turn"] == pin["turn"])
    gm, em = original["manifest"], partial["manifest"]
    gd = read(groot / "solver/postflop" / gc["source_path"])
    ed = read(eroot / "solver/postflop" / ec["source_path"])
    gfr = read(groot / "solver/postflop" / gm["file_flop"])
    efr = read(eroot / "solver/postflop" / em["file_flop"])
    gmask, _ = b427.game_reach(gfr, gd)
    emask, _ = b427.game_reach(efr, ed)
    key = "|".join((pin["public_board"], LINE, "1"))
    return gmask[key]["count"], emask[key]["count"]

def pair_pin(x, proof_path):
    return dict(
        flop=x["flop"],
        public_board=x["exact_public_board"],
        turn=x["turn"],
        GTO_run_id=x["original_GTO_source_run"],
        NL2_hero_IP_run_id=x["new_NL2_IP_source_run"],
        original_GTO_source_sha256=x["original_GTO_sha256"],
        NL2_IP_source_sha256=x["new_NL2_IP_sha256"],
        GTO_legal_40_70_hero_IP_combos=x["GTO_strict_40_70_combos"],
        NL2_IP_legal_40_70_hero_IP_combos=x["actual_NL2_IP_strict_40_70_combos"],
        actual_spr=x["actual_SPR"],
        source_proof_sha256=sha(proof_path),
    )

def patch_ui_v52(path):
    # Reuse the independently-tested V50->V51 loader migration, then strengthen it to V52/four boards.
    b427.patch_ui(path)
    s = path.read_text(encoding="utf-8")
    replacements = [
        ("NL2_HU_392_MULTIBOARD_CERT_STATUS_V51_B427_R216_R218", V52),
        ("v51b427", "v52b433"),
        ("data/nl2_hu_multiboard_status_v51_b427_rank216_218.json",
         "data/nl2_hu_multiboard_status_v52_b433_rank216_218.json"),
        ("data/nl2_hu_cert_lock_medium_matrix_v51_b427.json",
         "data/nl2_hu_cert_lock_medium_matrix_v52_b433.json"),
        ("const q=d.B427_r216218_three_true_original_GTO_NL2_IP_flops;",
         "const q=d.B433_r216218_four_true_original_GTO_NL2_IP_flops;"),
        ("q.flops?.join(',')!=='Js9h4d,Td8h3c,Js9h5d'",
         "q.flops?.join(',')!=='Js9h4d,Td8h3c,Js9h5d,7c6h5d'"),
        ("x.pins?.length!==3", "x.pins?.length!==4"),
        ("r.proven_exact_board_count!==3", "r.proven_exact_board_count!==4"),
        ("r.certified_3_to_5_exact_flop_boards?.length!==3",
         "r.certified_3_to_5_exact_flop_boards?.length!==4"),
        ("new Set(r.certified_3_to_5_exact_flop_boards.map(x=>x.flop)).size!==3",
         "new Set(r.certified_3_to_5_exact_flop_boards.map(x=>x.flop)).size!==4"),
    ]
    for old, new in replacements:
        assert old in s, (path.name, "missing UI patch anchor", old)
        s = s.replace(old, new)
    path.write_text(s, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical-gto", required=True, type=pathlib.Path)
    ap.add_argument("--historical-exp", required=True, type=pathlib.Path)
    ap.add_argument("--td-gto", required=True, type=pathlib.Path)
    ap.add_argument("--td-exp", required=True, type=pathlib.Path)
    ap.add_argument("--js-gto", required=True, type=pathlib.Path)
    ap.add_argument("--js-exp", required=True, type=pathlib.Path)
    ap.add_argument("--low-gto", required=True, type=pathlib.Path)
    ap.add_argument("--low-exp", required=True, type=pathlib.Path)
    a = ap.parse_args()

    parent = read(PARENT)
    triage = read(TRIAGE)
    b393 = read(B393)
    b400 = read(B400)
    b412 = read(B412)
    b421 = read(B421)
    b429 = read(B429)
    b431proof = read(B431)

    assert (parent["CERT_MULTIBOARD"], parent["APPROX"], parent["EST"], parent["TOTAL"]) == (163, 229, 0, 392)
    assert b412["schema"] == "NL2_B412_RANK216_218_ONE_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIR_V1"
    assert b421["schema"] == "NL2_B421_RANK216_218_ONE_NEW_ACTUAL_RUST_GTO_NL2_IP_PAIR_V1"
    assert b429["schema"] == "NL2_B429_R216218_THREE_NEW_TEXTURE_GENUINE_GTO_FIRST_V1"
    assert b431proof["schema"] == "NL2_B431_RANK216_218_ONE_NEW_TEXTURE_ACTUAL_RUST_GTO_NL2_IP_PAIR_V1"
    assert (b412["original_GTO_run"], b412["new_NL2_IP_run"]) == (45028060598, 45029736915)
    assert (b421["original_GTO_run"], b421["new_NL2_IP_run"]) == (45026396521, 45052841553)
    assert b412["B400_frozen_original_GTO_source_sha256"] == sha(B400)
    assert b421["B393_frozen_original_GTO_source_sha256"] == sha(B393)
    assert b412["new_distinct_qualifying_flops_by_rank"] == {"216": ["Td8h3c"], "218": ["Td8h3c"]}
    assert b421["new_distinct_qualifying_flops_by_rank"] == {"216": ["Js9h5d"], "218": ["Js9h5d"]}
    assert b429["original_run_id"] == 45055601616
    assert b431proof["B429_original_GTO_source_sha256"] == sha(B429)
    assert (b431proof["original_GTO_run"], b431proof["new_NL2_IP_run"]) == (45055601616, 45056914556)
    assert b431proof["new_distinct_qualifying_flops_by_rank"] == {"216": ["7c6h5d"], "218": ["7c6h5d"]}
    low_gto_row = next(x for x in b429["real_original_GTO_only_solve_sources"] if x["flop"] == "7c6h5d")
    assert low_gto_row["source_status"] == "ORIGINAL_GTO_ANY_TARGET_POSITIVE"

    loaded = {}
    # Historical B2 source: authenticate the successful CO_BB target artifacts, not the unrelated SB3 job.
    for version, root in (("gto", a.historical_gto), ("exp_ip", a.historical_exp)):
        row = next(x for x in triage["source_blind_selected_ten"] if x["frequency_rank"] == 216)["strictly_measured_pairs"][0]
        expected = row["gto_source_sha256"] if version == "gto" else row["nl2_hero_lock_sha256"]
        loaded[("Js9h4d", version)] = attach_source_paths(b427.legacy_b2_check(root, "Js9h4d", version, expected))

    # B412/B421 are existing authentic original Rust GTO + actual NL2-IP source pairs.
    G412 = attach_source_paths(source_check(a.td_gto, "Td8h3c", "gto", None))
    E412 = attach_source_paths(source_check(a.td_exp, "Td8h3c", "exp_ip", None))
    G421 = attach_source_paths(source_check(a.js_gto, "Js9h5d", "gto", None))
    E421 = attach_source_paths(source_check(a.js_exp, "Js9h5d", "exp_ip", None))
    for z in (G412, E412, G421, E421):
        assert z and z["status"] == "GENUINE_RUST_EXACT_SOURCE"
    row412 = b412["source_evidence"][0]
    row421 = b421["source_evidence"][0]
    assert G412["manifest_sha256"] == row412["original_GTO"]["manifest_sha256"]
    assert G412["root_original_Rust_SHA256"] == row412["original_GTO"]["root_original_Rust_SHA256"]
    assert E412["manifest_sha256"] == row412["actual_partial_NL2_IP"]["manifest_sha256"]
    assert E412["root_original_Rust_SHA256"] == row412["actual_partial_NL2_IP"]["root_original_Rust_SHA256"]
    assert G421["manifest_sha256"] == row421["original_GTO"]["manifest_sha256"]
    assert G421["root_original_Rust_SHA256"] == row421["original_GTO"]["root_original_Rust_SHA256"]
    assert E421["manifest_sha256"] == row421["actual_partial_NL2_IP"]["manifest_sha256"]
    assert E421["root_original_Rust_SHA256"] == row421["actual_partial_NL2_IP"]["root_original_Rust_SHA256"]
    loaded[("Td8h3c", "gto")] = G412
    loaded[("Td8h3c", "exp_ip")] = E412
    loaded[("Js9h5d", "gto")] = G421
    loaded[("Js9h5d", "exp_ip")] = E421

    # B429/B431 add a fourth, distinct exact flop with both original GTO and real NL2-IP source.
    G429 = attach_source_paths(b431.check(a.low_gto, "gto", 45055601616))
    E431 = attach_source_paths(b431.check(a.low_exp, "exp_ip", 45056914556))
    assert G429["status"] == E431["status"] == "GENUINE_RUST_EXACT_SOURCE"
    low_source = b431proof["source_evidence"][0]
    assert G429["manifest_sha256"] == low_source["original_GTO"]["manifest_sha256"]
    assert G429["root_original_Rust_SHA256"] == low_source["original_GTO"]["root_original_Rust_SHA256"]
    assert E431["manifest_sha256"] == low_source["actual_partial_NL2_IP"]["manifest_sha256"]
    assert E431["root_original_Rust_SHA256"] == low_source["actual_partial_NL2_IP"]["root_original_Rust_SHA256"]
    loaded[("7c6h5d", "gto")] = G429
    loaded[("7c6h5d", "exp_ip")] = E431

    roots = {
        "Js9h4d": (a.historical_gto, a.historical_exp),
        "Td8h3c": (a.td_gto, a.td_exp),
        "Js9h5d": (a.js_gto, a.js_exp),
        "7c6h5d": (a.low_gto, a.low_exp),
    }
    pins_by_rank = {}
    for rank, mid in TARGET.items():
        old = parent["records"][mid]
        assert (old["label"], old["frequency_rank"], old["solver_profile"], old["family"], old["street"]) == (
            "APPROX", rank, "CO_BB", "SRP", 2)
        trow = next(x for x in triage["source_blind_selected_ten"] if x["frequency_rank"] == rank)
        assert trow["model_id"] == mid and trow["true_paired_measured_NL2_hero_lock_flops"] == 1
        h = trow["strictly_measured_pairs"][0]
        assert h["flop"] == "Js9h4d" and h["exact_line"] == LINE and h["strict_legal_combo_count"] == 6
        hist = dict(
            flop="Js9h4d",
            public_board=h["exact_public_board"],
            turn=h["exact_public_board"][6:8],
            GTO_run_id=h["gto_source_run_id"],
            NL2_hero_IP_run_id=h["nl2_hero_lock_run_id"],
            original_GTO_source_sha256=h["gto_source_sha256"],
            NL2_IP_source_sha256=h["nl2_hero_lock_sha256"],
            GTO_legal_40_70_hero_IP_combos=h["strict_legal_combo_count"],
            NL2_IP_legal_40_70_hero_IP_combos=loaded[("Js9h4d", "exp_ip")]["real_cases"][0]["actor_IP_target_nodes"][h["exact_public_board"]]["strict_40_70_IP_hero_combos"],
            actual_spr=h["actual_spr"],
            source_proof_sha256=sha(TRIAGE),
        )
        td = next(x for x in b412["positive_40_70_named_river_pairs_by_rank"][str(rank)] if x["flop"] == "Td8h3c")
        js = next(x for x in b421["positive_40_70_named_river_pairs_by_rank"][str(rank)] if x["flop"] == "Js9h5d")
        low = next(x for x in b431proof["positive_40_70_named_river_pairs_by_rank"][str(rank)] if x["flop"] == "7c6h5d")
        pins = [hist, pair_pin(td, B412), pair_pin(js, B421), pair_pin(low, B431)]
        assert [x["flop"] for x in pins] == list(FLOPS)
        assert len({texture(x["flop"]) for x in pins}) >= 2
        pins_by_rank[str(rank)] = dict(rank=rank, model_id=mid, pins=pins)

    # Freeze the source quadruple before any status-label promotion.
    pre = dict(
        schema="NL2_B433_R216218_FOUR_AUTHENTIC_GTO_NL2_IP_SOURCE_PRECERT_V1",
        source_V50_status_sha256=sha(PARENT),
        B370_source_triage_sha256=sha(TRIAGE),
        B393_original_GTO_source_sha256=sha(B393),
        B400_original_GTO_source_sha256=sha(B400),
        B412_actual_NL2_IP_pair_proof_sha256=sha(B412),
        B421_actual_NL2_IP_pair_proof_sha256=sha(B421),
        B429_original_GTO_source_sha256=sha(B429),
        B431_actual_NL2_IP_pair_proof_sha256=sha(B431),
        ranks_with_four_full_street_40_70_positive_flops=[216, 218],
        eligible_rank_source_quadruples=pins_by_rank,
        source_blind_first10_preregistered=True,
        exact_spot="CO_BB",
        actor="CO_IP",
        exact_line=LINE,
        distinct_flops=list(FLOPS),
        distinct_texture_count=len({texture(x) for x in FLOPS}),
        original_preflop_CFR_is_not_NL2_conditional_private_hand_frequency=True,
        no_texture_level_GTO_or_blanket_50pct_strategy=True,
        only_exact_named_public_boards=True,
        four_independent_original_GTO_and_NL2_IP_sources_required=True,
        baseline_CERT_MULTIBOARD=163,
        baseline_APPROX=229,
        baseline_EST=0,
        PR2_remains_draft_unmerged=True,
    )
    PRE.write_text(json.dumps(pre, ensure_ascii=False, indent=2) + "\n")

    new = copy.deepcopy(parent)
    authenticated = []
    for rank, mid in TARGET.items():
        old = parent["records"][mid]
        model = dict(
            family=old["family"],
            spot=old["solver_profile"],
            street=old["street"],
            preflop_text=old["preflop_text"],
            abstract_action_history=old["abstract_action_history"],
            assumed_model_node_spr=old["assumed_model_node_spr"],
        )
        selected, proofs = [], []
        for pinrow in pins_by_rank[str(rank)]["pins"]:
            g = loaded[(pinrow["flop"], "gto")]
            e = loaded[(pinrow["flop"], "exp_ip")]
            gr, er = roots[pinrow["flop"]]
            actual = actual_combo_counts(pinrow, g, e, gr, er)
            expected = (pinrow["GTO_legal_40_70_hero_IP_combos"], pinrow["NL2_IP_legal_40_70_hero_IP_combos"])
            assert actual == expected, ("B433 exact sequential combo mismatch", rank, pinrow["flop"], pinrow["public_board"], expected, actual)
            sample, proof = b427.verify_pin(model, pinrow, g, e, gr, er, rank)
            selected.append(sample)
            proofs.append(proof)
        assert [x["flop"] for x in selected] == list(FLOPS)
        assert len({texture(x["flop"]) for x in selected}) >= 2
        rec = copy.deepcopy(old)
        rec.update(
            label="CERT-MULTIBOARD",
            high_frequency_preregistered=True,
            original_top24_high_frequency_preregistered=False,
            source_blind_expansion_rank=rank,
            source_blind_expansion_preregistered=True,
            prereg_cohort="B370_FIRST10_ORIGINAL_GTO_NL2_CO_BB_FOUR_EXACT_SOURCE_FLOPS",
            certified_3_to_5_exact_flop_boards=selected,
            proven_exact_board_count=4,
            blocked_reason=None,
            source_credibility="GITHUB_ACTIONS_ORIGINAL_FULL100BB_SHA_AND_ACTUAL_NL2_IP_PARTIAL_LOCK_40_70_FOUR_FLOPS",
        )
        new["records"][mid] = rec
        authenticated.append(dict(rank=rank, model_id=mid, pins=proofs))

    new.update(
        schema=V52,
        CERT_MULTIBOARD=165,
        APPROX=227,
        EST=0,
        TOTAL=392,
        parent_V50_SHA256=sha(PARENT),
        B433_preregistered_four_flop_source_sha256=sha(PRE),
        supplementary_cert_count=parent["supplementary_cert_count"] + 2,
        source_blind_expansion_ranks=sorted(set(parent["source_blind_expansion_ranks"] + [216, 218])),
        original_top24_cutoff_unchanged=True,
        no_generic_texture_GTO=True,
        no_observed_private_card_NL2_rates=True,
        PR2_remains_draft_never_merge=True,
        B433_r216218_four_true_original_GTO_NL2_IP_flops=dict(
            ranks=[216, 218],
            spot="CO_BB",
            actor="CO_IP",
            line=LINE,
            flops=list(FLOPS),
            source_blind_first10_preregistered=True,
            source_pre_cert_sha256=sha(PRE),
            authenticated_sources_by_rank=authenticated,
            historical_B2_source_run=44666290556,
            B412_NL2_IP_run=45029736915,
            B421_NL2_IP_run=45052841553,
            B429_GTO_run=45055601616,
            B431_NL2_IP_run=45056914556,
            only_exact_named_public_boards_no_generic_texture=True,
        ),
    )
    STATUS.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n")

    audit_path = pathlib.Path("tools/hu_cert_lock_medium_audit.py")
    audit_text = audit_path.read_text(encoding="utf-8")
    old_allow = "'NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166')"
    assert audit_text.count(old_allow) == 1
    audit_path.write_text(
        audit_text.replace(old_allow, "'NL2_HU_392_MULTIBOARD_CERT_STATUS_V50_B417_R166','" + V52 + "')"),
        encoding="utf-8",
    )
    checked_module = importlib.reload(source_audit)
    medium_matrix.audit = checked_module.audit
    checked = checked_module.audit(new)
    assert (checked["cert_multiboard"], checked["approx"], checked["EST"]) == (165, 227, 0)
    assert (
        checked["aggregate"]["named_board_proofs"],
        checked["aggregate"]["paired_hero_locked_source_variants"],
    ) == (626, 718)
    matrix = medium_matrix.create(new)
    assert (len(matrix["models"]), len(matrix["boards"])) == (165, 626)
    unknown = sum(
        1
        for board in matrix["boards"]
        for lock in board["hero_lock_proofs"]
        if lock["node_rate_data_status"] == "HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN"
    )
    assert unknown == 0
    matrix.update(
        schema="NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V52_B433",
        V52_status_sha256=sha(STATUS),
        source_unknown_variants_after=0,
        true_40_70_full100bb_CO_IP_source_rank216_218=True,
        no_private_card_conditional_opponent_NL2_frequency_claim=True,
        exact_named_board_50pct_research_only=True,
        PR2_Draft_NEVER_MERGE=True,
    )
    MATRIX.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n")
    AUDIT.write_text(json.dumps(checked, ensure_ascii=False, indent=2) + "\n")
    PROOF.write_text(
        json.dumps(
            dict(
                schema="NL2_B433_R216_218_TWO_MODELS_EIGHT_ORIGINAL_GTO_NL2_IP_CERT_BOARDS_V1",
                parent_V50_status_SHA256=sha(PARENT),
                B433_source_pre_cert_SHA256=sha(PRE),
                model_source_pins=authenticated,
                source_blind_first10_preregistered=True,
                true_original_full100bb_CFR_source_and_40_70_check=True,
                same_exact_CO_IP_line_SPR_and_paired_NL2_IP_hero_lock=True,
                four_distinct_exact_flops_per_model=list(FLOPS),
                only_named_board_no_generic_texture_GTO=True,
                no_NL2_villain_private_hand_observations=True,
                CERT_before=163,
                CERT_after=165,
                APPROX_before=229,
                APPROX_after=227,
                EST=0,
                named_boards_before=618,
                named_boards_after=626,
                locked_hero_variants_before=710,
                locked_hero_variants_after=718,
                unknown_lock_denominators_after=0,
                V52_status_sha256=sha(STATUS),
                V52_matrix_sha256=sha(MATRIX),
                V52_audit_sha256=sha(AUDIT),
                b50_nonpolarized_marks_are_exact_named_board_research_only=True,
                PR2_draft_never_merge=True,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    for filename in ("nl2_hu_multiboard_ui.js", "nl2-multiboard.js"):
        patch_ui_v52(pathlib.Path(filename))
    for filename in ("nl2.html", "nl2-multiboard.html"):
        p = pathlib.Path(filename)
        s = p.read_text(encoding="utf-8")
        old = "task-hybrid-b417-v50-20261122"
        assert s.count(old) == 1
        s = s.replace(old, "task-hybrid-b427-v51-20261122")
        s = s.replace("task-hybrid-b427-v51-20261122", "task-hybrid-b433-v52-20261122")
        p.write_text(s, encoding="utf-8")
    test = pathlib.Path("tools/hu_b378_v47_loader_runtime_test.cjs")
    ts = test.read_text(encoding="utf-8")
    old = "414-persistent|417-v50"
    assert ts.count(old) == 1
    ts = ts.replace(old, "414-persistent|417-v50|427-v51")
    ts = ts.replace("|427-v51", "|433-v52")
    test.write_text(ts, encoding="utf-8")
    DOC.write_text(
        "# B433 ranks216/218: four exact original GTO + genuine NL2-IP paired source flops each\n\n"
        "Both source-blind first-ten CO_BB models are promoted only on the exact named flops "
        "Js9h4d, Td8h3c, Js9h5d and 7c6h5d. Each board has independently SHA-verified original "
        "full-100bb Rust GTO and actual NL2-IP partially locked source, the same exact CO-IP "
        "line, positive sequential 40/70 hero combo reach and <=5% SPR error. "
        "No solver jobs were rerun; immutable original artifacts from B2, B400, B393, B412, "
        "B421, B429 and B431 were authenticated. Observed NL2 values are pooled marginals, "
        "not villain private-card conditional actions. The 50% non-polarized flag remains a "
        "named-board research marker only, never a generic texture recommendation. "
        "**165 CERT /227 APPROX /0 EST**, 626 named boards, 718 paired NL2 source locks, UNKNOWN=0. "
        "Full HU2475, frontend and independent Actions audits required. PR #2 stays DRAFT and unmerged.\n"
    )
    print("PASS B433 four-flop paired GTO/NL2-IP rank216/218: 165 CERT /227 APPROX, 626 boards, 718 locks, UNKNOWN=0")

if __name__ == "__main__":
    main()
