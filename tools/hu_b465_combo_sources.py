"""Export per-combo source views of the four original rank218 actor decisions."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from hu_b465_rank218 import FLOPS, ID, LINE, STATUS, read
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope, source_nodes


def export(downloads):
    registry = read(STATUS)
    model = registry["records"][ID]
    pins = {p["flop"]: p for p in registry["B465_rank218_four_original_sources"]["pins"]}
    boards = {b["flop"]: b for b in model["certified_3_to_5_exact_flop_boards"]}
    assert model["label"] == "CERT-MULTIBOARD" and set(pins) == set(boards) == set(FLOPS)
    for flop, directory in zip(FLOPS, ("historical", "td", "js", "low")):
        pin, board = pins[flop], boards[flop]
        by_run = {}
        for version, folder in (("gto", "gto"), ("exp_ip", "exp")):
            gto = version == "gto"
            run = pin["original_GTO_run" if gto else "actual_NL2_IP_run"]
            digest = pin["original_GTO_SHA256" if gto else "actual_NL2_SHA256"]
            root = downloads / f"{directory}-{folder}"
            pf = root / "solver/postflop"
            manifests = [read(p) for p in (root / "evidence").glob("*.json")]
            m, = (m for m in manifests if m.get("flop") == flop and m.get("version") == version and m.get("spot") == model["solver_profile"])
            c, = (c for c in m["cases"] if c["source_sha256"] == digest and c["turn"] == pin["turn"] and c["line"] == board["exact_flop_action"])
            assert hashlib.sha256((pf / c["source_path"]).read_bytes()).hexdigest() == digest
            root_sha = pin["original_Rust_root_SHA256" if gto else "real_NL2_IP_root_SHA256"]
            assert hashlib.sha256((pf / m["file_flop"]).read_bytes()).hexdigest() == root_sha
            parent, sub = read(pf / m["file_flop"]), read(pf / c["source_path"])
            node, = (n for n in sub["nodes"] if (n["board"], n["line"], n["player"]) == (pin["public_board"], LINE, 1))
            key = "|".join((node["board"], LINE, "1"))
            masks, _ = game_reach(parent, sub)
            compatible = compatible_node_reach(parent, sub, node, masks[key])
            evidence, = source_nodes(dict(sub, nodes=[node]), {"nodes": {key: compatible}})
            assert evidence["strictly_reachable_combos"] == pin["GTO_strict_combos" if gto else "NL2_strict_combos"] > 0
            if gto:
                assert evidence["medium_50pct_eligible_combos"] == board["medium_50pct_eligible_combos"]
                assert evidence["b50_nonpolarized_relative_equity_research_candidate"] == board["b50_nonpolarized_relative_equity_research_candidate"]
            by_run.setdefault(run, []).append(dict(
                version=version, spot=model["solver_profile"], pot_family=model["family"],
                source_sha256=digest, flop=flop, turn=pin["turn"], flop_line=c["line"],
                hands_by_seat=sub["hands"], nodes=[evidence], gto_exploitability_pct=sub["info"]["gto_expl_pct"],
                locked_hero_gap_pct=sub["info"].get("hero_gap_pct"), villain_lock_scope=lock_scope(sub, m["locks"], version)))
        for run, cases in by_run.items():
            out = dict(schema="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1", source_run_id=run,
                       no_generic_texture_certification=True, errors=[], artifacts=[dict(cases=cases)])
            data = json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode()
            path = Path("data/solver_evidence") / f"NL2_MULTIBOARD_R218_{flop}_{run}.json.gz"
            path.write_bytes(gzip.compress(data, mtime=0))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", required=True, type=Path)
    export(parser.parse_args().downloads)
