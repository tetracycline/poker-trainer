"""Promote independently solved BB river histories only on three or more distinct positive flops."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from hu_b467_river_source_gate import NoLegalRiver, compact, export_board, json_bytes, publish_bytes
from hu_btn_bb_river_pairs import B460_ARCHIVE, FLOPS, MODELS, verify

DATA = Path("data/solver_evidence")
SOURCE = DATA / "b466"
RUNS = {"9s6h3d":45091990886, "Js9h4d":45092103725, "As7s2s":45095729336,
        "Ks7h2d":45095729336, "Qs9s5s":45095729336}
TEXTURE = {"9s6h3d":"LOW", "Js9h4d":"MID", "As7s2s":"MONOTONE", "Ks7h2d":"HIGH", "Qs9s5s":"MONOTONE"}


def normalize(pair, version):
    raw = pair[version]
    source = dict(version=version, root=raw["flop_root"], subgame=raw["turn_subgame"],
                  manifest=raw["manifest"], source_sha256=raw["subgame_sha256"])
    for key, expected in (("root", raw["root_sha256"]), ("subgame", raw["subgame_sha256"])):
        assert hashlib.sha256(compact(source[key])).hexdigest() == expected
    return source


def load_board(flop, run):
    stub = f"BTN_BB_{flop}_{run}"
    proof = json.loads((SOURCE / (stub+".proof.json")).read_bytes())
    path = DATA / proof["archive"] if flop == "9s6h3d" else SOURCE / (stub+".json.gz")
    assert path.name == proof["archive"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == proof["archive_sha256"]
    if flop == "9s6h3d":
        assert digest == B460_ARCHIVE
    pair = json.loads(gzip.decompress(path.read_bytes()))
    rebuilt = verify(pair, run)
    assert dict(rebuilt, archive=path.name, archive_sha256=digest) == proof
    assert proof["flop"] == flop and proof["turn"] == FLOPS[flop]
    return proof, [normalize(pair, ver) for ver in ("gto","exp_oop")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Replay assertions and compare all published outputs")
    args = parser.parse_args()
    groups = {rank:dict(model_id=model, rank=rank, boards=[], pins=[]) for rank,(model,_,_) in MODELS.items()}
    results = []
    for flop, run in RUNS.items():
        if not (SOURCE / f"BTN_BB_{flop}_{run}.proof.json").exists():
            results.append(dict(flop=flop, run=run, status="NO_VERIFIED_SOURCE"))
            continue
        proof, sources = load_board(flop, run)
        for rank, (model, line, spr) in MODELS.items():
            m = proof["models"][str(rank)]
            assert (m["model_id"], m["line"], m["model_spr"]) == (model, line, spr)
            # Both prespecified rivers are considered in canonical public-card order.
            # Each flop supplies at most one named board per model.
            selected = None
            for row in sorted(m["rivers"], key=lambda r:r["board"]):
                if min(row[v]["strict"] for v in ("gto","exp_oop")) == 0:
                    continue
                public = row["board"]
                pin = dict(flop=flop, turn=FLOPS[flop], archive_code=proof["archive"], source_run_id=run)
                parent = dict(public_board=public[:8], source_kind="PINNED_PREFLOP_CFR", assumed_preflop_ranges=False,
                              flop_texture=TEXTURE[flop])
                try:
                    selected = export_board(pin, parent, sources, rank, line, spr, args.verify,
                                            archive_digest=proof["archive_sha256"], viewer_code=f"R{rank}_{flop}_{run}",
                                            public_board=public)
                except NoLegalRiver:
                    continue
                break
            if selected:
                board, pin = selected
                groups[rank]["boards"].append(board)
                groups[rank]["pins"].append(pin)
            results.append(dict(rank=rank, flop=flop, run=run, paired=bool(selected),
                                public_board=selected[0]["public_board"] if selected else None))
    for rank, ext in groups.items():
        if len(ext["boards"]) >= 3:
            publish_bytes(DATA/"extensions"/f"rank{rank}.json", json_bytes(ext), args.verify)
    out = dict(source_runs=RUNS, models={str(k):len(e["boards"]) for k,e in groups.items()}, evidence=results)
    publish_bytes(Path("data/nl2_hu_b469_btn_bb_strict_rivers.json"), json_bytes(out), args.verify)
    print(out["models"])


if __name__ == "__main__":
    main()
