"""Verify the two frozen BTN-open / BB-call river histories on original paired solves."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path

from hu_b460_rank48_first_board import GTO_PIN, RUST_PIN, run_sources
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from verify_hu_multiboard_100bb import lock_scope, locked_model_gain, strict_medium_evidence

MODELS = {
    48: ("ln-bb-r_model-16s8tm3", "x x/b75 c/", 6.791),
    52: ("ln-bb-r_model-rb27ni", "x x/b33 c/", 10.436),
}
FLOPS = {"9s6h3d": "Ts", "Js9h4d": "Ts", "As7s2s": "5s", "Ks7h2d": "9d", "Qs9s5s": "Ts"}
B460_ARCHIVE = "7a727c75e4e9fd557b50f689cff78a164ed3007ca0e46c7a118a27ffa55b69d1"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_version(raw, version, flop, turn):
    manifest = raw["manifest"]
    root, sub = raw["flop_root"], raw["turn_subgame"]
    assert manifest["version"] == version and manifest["spot"] == "BTN_BB"
    assert manifest["selected_lines"] == ["x x"] and manifest["turns"] == [turn]
    assert manifest["flop_action_sizes"] == ["33%", "50%", "75%", "100%"]
    assert manifest["preflop_ranges"]["full_sha256"] == "787f719c752165262807f79b91daec81e1db86a83d557a4ea645ef2649f532c7"
    assert manifest["pool_source_sha256"] == "c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a"
    assert manifest["file_flop_sha256"] == raw["root_sha256"]
    assert manifest["cases"][0]["source_sha256"] == raw["subgame_sha256"]
    assert (root["flop"], root["pot"], root["stack"]) == (flop, 550, 9750)
    assert (sub["flop"], sub["turn"], sub["line0"]) == (flop, turn, "x x")
    for job in [raw["flop_job"], raw["turn_job"]]:
        assert (job.get("hero"), bool(job.get("locks"))) == ((None, False) if version == "gto" else (0, True))
        assert abs(job["rake_rate"] - .05) < 1e-8 and job["rake_cap"] == 1000
    for game in (root, sub):
        assert 0 <= game["info"]["gto_expl_pct"] <= .5
        if version == "exp_oop":
            assert 0 <= game["info"]["hero_gap_pct"] <= .5
    return game_reach(root, sub)[0]


def legal_ip_hands(raw, board, line):
    """The BTN must check the flop and call the exact BB turn size."""
    bet, call = line.split("/")[1].split()
    root, sub = raw["flop_root"], raw["turn_subgame"]
    held = None
    for game, public, prefix, action in ((root, board[:6], "x", "x"),
                                         (sub, board[:8], "x x/" + bet, call)):
        node, = (n for n in game["nodes"] if (n["board"], n["line"], n["player"]) == (public, prefix, 1))
        allowed = accepted(node, game["hands"], action)
        held = allowed if held is None else held & allowed
    blocked = {board[i:i+2] for i in range(0, len(board), 2)}
    return {h for h in held if blocked.isdisjoint(h)}


def node_evidence(raw, masks, line, target_spr):
    sub = raw["turn_subgame"]
    rows = {}
    for node in sub["nodes"]:
        board = node["board"]
        if len(board) != 10 or node["line"] != line or node["player"] != 0:
            continue
        pot, remaining = node["pot"], sub["stack"] - max(node["bets"])
        spr = remaining / pot
        if abs(spr / target_spr - 1) > .05:
            continue
        mask = masks[f"{board}|{line}|0"]
        handlist = sub["hands"][0]
        mask_bytes = base64.b64decode(mask["mask"], validate=True)
        assert len(mask_bytes) == len(handlist)
        hands = {tuple(sorted((h[:2], h[2:]))) for h, allowed in zip(handlist, mask_bytes) if allowed}
        assert len(hands) == mask["count"] and board not in rows
        villain = legal_ip_hands(raw, board, line)
        public = {board[i:i+2] for i in range(0, len(board), 2)}
        joint = {h for h in hands if public.isdisjoint(h) and any(set(h).isdisjoint(v) for v in villain)}
        joint_mask = bytes(v if cardkey(h) in joint else 0 for h, v in zip(handlist, mask_bytes))
        medium = strict_medium_evidence(node, sub, base64.b64encode(joint_mask).decode())
        rows[board] = (joint, dict(strict=len(joint), actor_only=len(hands), opponent=len(villain), raw=sum(w > 1e-4 for w in node["w"][0]),
                    actions=node["acts"], pot_bb=pot / 100, remaining_bb=remaining / 100,
                    spr=spr, medium=medium))
    return rows


def verify(archive, run_id):
    flop = archive["gto"]["manifest"]["flop"]
    turn = FLOPS[flop]
    assert archive["solver_pin"] == GTO_PIN and archive["rust_pin"] == RUST_PIN
    assert run_id > 0
    masks = {v: check_version(archive[v], v, flop, turn) for v in ("gto", "exp_oop")}
    exp = archive["exp_oop"]
    lock = lock_scope(exp["turn_subgame"], exp["manifest"]["locks"], "exp_oop")
    assert lock["observed_marginal_source_nodes"] > 0 and lock["pattern_matched_nodes"] > 0
    result = dict(flop=flop, turn=turn, run_id=run_id, spot="BTN_BB", actor=0,
                  source_sha={v: archive[v]["subgame_sha256"] for v in masks},
                  root_sha={v: archive[v]["root_sha256"] for v in masks},
                  gto_gap=archive["gto"]["turn_subgame"]["info"]["gto_expl_pct"],
                  hero_gap=exp["turn_subgame"]["info"]["hero_gap_pct"],
                  gain_bb=locked_model_gain(exp["turn_subgame"], "exp_oop"), lock=lock, models={})
    for rank, (model, line, spr) in MODELS.items():
        gto, nl2 = (node_evidence(archive[v], masks[v], line, spr) for v in masks)
        rivers = []
        for board in sorted(gto.keys() & nl2.keys()):
            gh, g = gto[board]
            eh, e = nl2[board]
            assert g["actions"] == e["actions"] and abs(g["spr"] - e["spr"]) < 1e-8
            rivers.append(dict(board=board, gto=g, exp_oop=e, common_strict_hands=len(gh & eh)))
        result["models"][str(rank)] = dict(model_id=model, line=line, model_spr=spr, rivers=rivers,
                                           paired=any(r["gto"]["strict"] > 0 and r["exp_oop"]["strict"] > 0 for r in rivers))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--download-dir", type=Path)
    p.add_argument("--b460-archive", type=Path)
    p.add_argument("--flop", required=True, choices=FLOPS)
    p.add_argument("--run-id", required=True, type=int)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    a.out.mkdir(exist_ok=True, parents=True)
    if a.b460_archive:
        assert a.flop == "9s6h3d" and a.run_id == 45091990886
        assert sha256(a.b460_archive) == B460_ARCHIVE
        arc = json.loads(gzip.decompress(a.b460_archive.read_bytes()))
        arc_path = a.b460_archive
    else:
        assert a.download_dir is not None
        arc = dict(schema="NL2_BTN_BB_PAIRED_RIVER_SOURCE_V1", solver_pin=GTO_PIN, rust_pin=RUST_PIN,
                   **{v: run_sources(a.download_dir, v, a.flop, FLOPS[a.flop]) for v in ("gto", "exp_oop")})
        arc_path = a.out / f"BTN_BB_{a.flop}_{a.run_id}.json.gz"
        arc_path.write_bytes(gzip.compress(json.dumps(arc, separators=(",", ":")).encode(), compresslevel=9, mtime=0))
    record = verify(arc, a.run_id)
    assert record["flop"] == a.flop
    record.update(archive=arc_path.name, archive_sha256=sha256(arc_path))
    (a.out / f"BTN_BB_{a.flop}_{a.run_id}.proof.json").write_text(json.dumps(record, indent=2) + "\n")
    print(a.flop, {k: m["paired"] for k, m in record["models"].items()})


if __name__ == "__main__":
    main()
