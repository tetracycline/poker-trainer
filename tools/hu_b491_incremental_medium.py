"""Regress overlapping report rows using a real root-only applied lock and its original GTO."""
import json
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from hu_board_reach_corrections import APPLIED, UNRESOLVED, apply_updates, read_replays, source_key, summarize


def main():
    original = json.loads(Path("data/nl2_hu_b485_locked_medium.json").read_bytes())
    key, row = next((k, r) for k, r in original["references"].items()
                    if r["strict_legal_combos"] and r["subgame_applied_rust_lock_nodes"] == 0 and r["gto"])
    gto = row["gto"]
    gto_key = source_key(json.loads(key)[0], gto)
    earlier_row = {k: v for k, v in row.items() if k not in (*APPLIED, "gto")}
    with TemporaryDirectory() as tmp:
        directory = Path(tmp)

        def write(number, refs, gtos=None, unresolved=None):
            report = dict(schema=f"NL2_HU_B{number}_ORIGINAL_LOCKED_MEDIUM_V1", references=refs)
            if unresolved is not None:
                report["unresolved"] = unresolved
            if gtos is not None:
                report["gto_references"] = gtos
            (directory/f"nl2_hu_b{number}_locked_medium.json").write_text(json.dumps(report))

        write(483, {key: earlier_row})
        write(489, {key: row}, {gto_key: gto})
        files, locks, gtos, links = read_replays(directory)
        assert len(files) == 2 and len(locks) == len(gtos) == 1 and links[key] == gto_key
        assert summarize(locks[key])["subgame_applied_rust_lock_nodes"] == 0
        assert locks[key]["root_applied_rust_lock_nodes"] == row["root_applied_rust_lock_nodes"] > 0
        write(489, {key: row})
        assert set(read_replays(directory)[2]) == {gto_key}

        def rejects():
            try:
                read_replays(directory)
            except (AssertionError, ValueError):
                return
            raise AssertionError("Bad source evidence accepted")

        for number, schema in ((542, "NL2_B542_NATIVE_PAIRED_TURN_VERSION_V1"), (544, "NL2_HU_B544_CONDITIONAL_MEDIUM_V1")):
            path = directory/f"nl2_hu_b{number}_locked_medium.json"
            path.write_text(json.dumps({"schema": schema, "references": {key: row}}))
            assert read_replays(directory)[0][-1]["schema"] == schema
            path.rename(directory/"nl2_hu_b999_locked_medium.json")
            rejects()
            (directory/"nl2_hu_b999_locked_medium.json").unlink()

        bad = deepcopy(row)
        bad["compatible_hole_card_pairs"] += 1
        write(489, {key: bad})
        rejects()
        write(489, {gto_key: gto})
        rejects()
        write(489, {}, {key: row})
        rejects()
        write(489, {key: dict(row, root_applied_rust_lock_nodes=0)})
        rejects()
        reason = "ORIGINAL_RUST_SUBGAME_NOT_PUBLISHED"
        write(483, {})
        pending = {key: {"reason": reason, "version": row["version"]}}
        write(489, {}, unresolved=pending)
        observed = read_replays(directory)[1][key]
        assert observed["status"] == UNRESOLVED
        summary = summarize(observed)
        assert summary["unresolved_reason"] == reason and "strictly_reachable_combos" not in summary
        write(489, {key: row}, unresolved=pending)
        assert read_replays(directory)[1][key]["status"] == row["status"]

        # Suppress only the missing variant; another original warrants retaining the named board.
        other = {"run_id": 1, "sha256": "1"*64}
        named = dict(flop=row["flop"], public_board=row["public_board"], actual_exact_action_line=row["line"],
                     acting_seat=row["acting_seat"], source_run_id=gto["source_run_id"], source_sha256=gto["source_sha256"],
                     nl2_locked_variants=[other, {"run_id": summary["run_id"], "sha256": summary["sha256"]}])
        def apply(g, locks):
            registry = {"records": {"model": {"label": "CERT-MULTIBOARD", "certified_3_to_5_exact_flop_boards": [deepcopy(named)]}}}
            update = dict(public_board=row["public_board"], line=row["line"], seat=row["acting_seat"],
                          gto_sha256=named["source_sha256"], gto_run=named["source_run_id"], gto=g, locks=locks)
            apply_updates(registry, {"model": [update]})
            return registry["records"]["model"]["remaining_exact_board_evidence"]
        assert apply(None, [summary])[0]["nl2_locked_variants"] == [other]
        pending_gto = dict(sha256=gto["source_sha256"], run_id=gto["source_run_id"], unresolved_reason=reason)
        assert apply(pending_gto, []) == []
        assert apply(None, [summary, dict(other, unresolved_reason=reason)]) == []
    print("Verified incremental roles, overlapping source outcomes, nested GTO and root-only Rust locks.")


if __name__ == "__main__":
    main()
