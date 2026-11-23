"""Bind the SB river viewer’s shared hands to both original native strategy vectors."""
import base64
import gzip
import json
import math
from pathlib import Path
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_sequential_cfr_reach import cardkey


def policy(game, node, viewer, accepted_actions, hand):
    actions = node["acts"]
    v, = viewer["nodes"]
    assert actions == v["source_actions"] and node["line"] == v["exact_node_line"]
    n = len(game["hands"][0])
    assert game["hands"][0] == viewer["hands_by_seat"][0] and len(node["strat"]) == len(actions) * n
    index, = (i for i, h in enumerate(game["hands"][0]) if "".join(cardkey(h)) == hand)
    masks = base64.b64decode(v["strictly_reachable_masks_b64"], validate=True)
    assert len(masks) == n and masks[index] and accepted_actions == [
        a for j, a in enumerate(actions) if masks[index] & (1 << j)]
    values = [node["strat"][j * n + index] for j in range(len(actions))]
    assert all(math.isfinite(x) and x >= 0 for x in values)
    total = sum(values)
    assert abs(total - 1) <= .001
    return dict(action_order=actions, accepted_mask=masks[index], accepted_actions=accepted_actions,
                strategy={a: x / total for a, x in zip(actions, values, strict=True)})


def read_native(archive, pin, expected, public, line, version):
    if version == "gto":
        name, = (p for p in archive.namelist() if p.endswith(f'/{pin["flop"]}_b50c_{pin["turn"]}.json'))
        raw = archive.read(name)
    else:
        raw, = (payload for p in ("native/output.json", "history/output.json") if p in archive.namelist()
                and sha(payload := archive.read(p)) == expected)
    assert sha(raw) == expected
    game = json.loads(raw)
    node, = (n for n in game["nodes"] if (n["board"], n["line"], n["player"]) == (public, line, 0))
    return game, node


def main():
    path = EVIDENCE / "reverified/rank17.json"
    group = json.loads(path.read_bytes())
    original = json.loads(Path("data/nl2_hu_b557_sb_river_actions.json").read_bytes())["ranks"]["17"]
    assert group["rank"] == 17 and original["verified_distinct_flops"] == len(group["boards"]) == 3
    for pin in group["pins"]:
        public = pin["public_board"]
        observed, = (r for r in original["named_river_nodes"] if r["public_board"] == public)
        board, = (b for b in group["boards"] if b["public_board"] == public)
        line = board["actual_exact_action_line"]
        assert line == "b50 c/b33 c/" and board["acting_seat"] == 0
        previous = observed["native_actions_by_reached_hand"]
        assert set(previous) == set(pin["shared_rendered_route_hands"]) and previous
        source_file = EVIDENCE / ("NL2_" + pin["raw_archive_code"] + ".zip")
        viewer_file = EVIDENCE / ("NL2_MULTIBOARD_" + pin["viewer_archive_code"] + ".json.gz")
        viewer_raw = viewer_file.read_bytes()
        assert sha(viewer_raw) == pin["viewer_sha256"]
        viewer = json.loads(gzip.decompress(viewer_raw))
        assert sha(source_file.read_bytes()) == pin["archive_sha256"] == viewer["original_archive_sha256"]
        rows = {h: dict(hand=h, displayed_suggestion=previous[h]["generic_action"]) for h in sorted(previous)}
        with ZipFile(source_file) as archive:
            cases = viewer["artifacts"][0]["cases"]
            assert len(cases) == 2
            for version, role, digest in [("gto", "gto", pin["original_GTO_SHA256"]),
                                          ("exp_oop", "nl2", pin["actual_NL2_SHA256"])]:
                case, = (c for c in cases if c["version"] == version)
                n, = case["nodes"]
                assert case["source_sha256"] == digest and n["public_board"] == public and n["acting_seat"] == 0
                game, native = read_native(archive, pin, digest, public, line, version)
                for hand, row in rows.items():
                    row[role] = policy(game, native, case, previous[hand][version], hand)
        pin["rendered_decision_hands"] = list(rows.values())
    path.write_bytes(json_bytes(group))


if __name__ == "__main__":
    main()
