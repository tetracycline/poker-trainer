#!/usr/bin/env python3
"""Read-only GTO SHA-pinned BB-OOP flop b50 40/70 reach preflight.

Original root and parent GTO source are immutable. A flop action with zero
per-combo reach under the same highest-frequency / 40%-and-70%-of-max rule
cannot authorize any descendant b50 c/x b50 c/ actor river CERT, regardless
of the turn; this does not extrapolate to other flops or game trees.
"""
import argparse, gzip, hashlib, json, pathlib
from hu_sequential_cfr_reach import accepted

D = pathlib.Path(__file__).resolve().parents[1] / "data"
TOL = 1e-7

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load(path):
    return json.loads(path.read_text())

def original_preflight(batch, flop, run, artifact):
    pinfile = D / f"nl2_hu_{batch.lower()}_rank71_lmp_{flop}_gto_parent_pin.json"
    idxfile = D / f"solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.index.json"
    gzfile = D / f"solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.json.gz"
    p, idx = load(pinfile), load(idxfile)
    assert (p["source_run_id"], idx["run_id"]) == (run, run)
    assert (p["target_rank"], p["model_id"]) == (71, "ln-iso-lmp_r_model-vlgh2t")
    assert (p["spot"], p["flop"], p["flop_line"], p["turn_line"]) == (
        "LMP_CO_BB", flop, "b50 c", "x b50 c"
    )
    assert (idx["verified_cases"], idx["gto_cases"], idx["locked_cases"]) == (1, 1, 0)
    assert sha(gzfile) == idx["gzip_sha256"]
    assert hashlib.sha256(gzip.decompress(gzfile.read_bytes())).hexdigest() == idx["source_sha256"]
    assert p["assumed_limped_169class"] and not p["observed_preflop_ranges"]
    assert p["original_full_100bb_lmp_gto_not_recomputed"] and not p["direct_nl2_lock_source_present"]
    artifact = pathlib.Path(artifact)
    base = artifact / "solver/postflop/out/LMP_CO_BB/gto"
    rootfile = base / f"{flop}_multiboard.json"
    jobfile = base / f"{flop}_multiboard.job.json"
    manifestfile = artifact / f"evidence/LMP_CO_BB-gto-{flop}.json"
    for f, digest in ((rootfile, p["original_gto_root_sha256"]),
                      (jobfile, p["original_gto_job_sha256"]),
                      (manifestfile, p["original_gto_manifest_sha256"])):
        assert f.is_file() and sha(f) == digest, f"Authentic GTO SHA mismatch {f}"
    r, job, mf = load(rootfile), load(jobfile), load(manifestfile)
    assert (r["flop"], r["pot"], r["stack"]) == (flop, 250, 9900)
    assert (job["pot"], job["stack"], job["rake_rate"], job["rake_cap"]) == (250, 9900, .05, 1000)
    assert not job.get("hero") and not job.get("locks")
    assert (mf["flop"], mf["spot"], mf["version"], mf["selected_lines"], mf["turns"]) == (
        flop, "LMP_CO_BB", "gto", ["b50 c"], [p["turn"]]
    )
    assert mf["preflop_ranges"]["source"] == "ASSUMED_EXPLICIT_169CLASS"
    assert r["info"]["gto_expl_pct"] <= .5
    roots = [n for n in r["nodes"] if n["line"] == "" and n["player"] == 0 and len(n["board"]) == 6]
    assert len(roots) == 1
    n = roots[0]
    actions = n["acts"]
    assert "b50" in actions
    nh = len(r["hands"][0])
    assert len(n["w"][0]) == nh and len(n["strat"]) == nh * len(actions)
    b50 = actions.index("b50")
    allowed, best_hands, active = set(), 0, 0
    high = 0.0
    for j, hand in enumerate(r["hands"][0]):
        if float(n["w"][0][j]) <= 1e-4:
            continue
        raw = [max(0.0, float(n["strat"][k * nh + j])) for k in range(len(actions))]
        den = sum(raw)
        if den <= 0:
            continue
        frac = [z / den for z in raw]
        best = max(range(len(frac)), key=lambda k: frac[k])
        high = max(high, frac[b50])
        active += 1
        if best == b50:
            best_hands += 1
        if best == b50 or (frac[b50] >= .4 - TOL and frac[b50] >= .7 * frac[best] - TOL):
            allowed.add(tuple(sorted((hand[:2], hand[2:4]))))
    canonical = accepted(n, r["hands"], "b50")
    assert allowed == canonical, "Must agree with canonical sequential action gate"
    return dict(
        batch=batch, source_run_id=run, flop=flop, turn=p["turn"],
        source_gto_pin_sha256=sha(pinfile), source_gto_index_sha256=sha(idxfile),
        original_GTO_full_flop_root_sha256=sha(rootfile),
        original_gto_exploitability_pct=r["info"]["gto_expl_pct"],
        original_root_flop_100bb_pot=2.5,
        hero_actor="BB_OOP", previous_flop_action="b50",
        original_root_flop_active_combo_count=active,
        observed_original_root_max_b50_frequency_pct=round(high * 100, 5),
        max_frequency_b50_combo_count=best_hands,
        strict_40_70_b50_flop_combo_count=len(allowed),
        descendant_b50c_xb50c_river_cannot_have_strict_combos=(len(allowed) == 0),
        original_target_line="b50 c/x b50 c/",
        original_target_actor_OOP_strict_combos=p["target_exact_actor_OOP_strict_combos"],
        preflop_limp_169classes="ASSUMED_NOT_OBSERVED",
        not_observed_NL2_per_private_hand_action_rates=True,
        not_new_GTO_solve=True, not_new_actor_NL2_lock=True,
        never_generalize_to_other_flops_or_TurnTrees=True,
        model_CERT_promotion=0,
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", nargs=4, action="append", metavar=("BATCH", "FLOP", "RUN", "ARTIFACT"), required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    a = ap.parse_args()
    rows = [original_preflight(batch, flop, int(run), pathlib.Path(artifact))
            for batch, flop, run, artifact in a.case]
    assert len({x["flop"] for x in rows}) == len(rows), "No duplicate exact flop"
    result = dict(schema="NL2_HU_RANK71_SHA_PINNED_GTO_FLOP_B50_ROOT_40_70_PREFLIGHT_V1",
                  exact_original_board_results=rows,
                  no_generic_CERT_from_preflight=True,
                  no_privacy_sensitive_hand_frequency_data_claimed=True,
                  methodology="Canonical every-combo 40% and >=70% of highest action, plus max-frequency action always eligible; exact immutable 100bb GTO flop source only.",
                  PR2_Draft_NEVER_MERGE=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"proofs":len(rows), "source_b50_strict_flop_counts":[x["strict_40_70_b50_flop_combo_count"] for x in rows]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
