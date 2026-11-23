"""Restore and verify published B461/B466 original artifacts without rerunning any solver."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from hu_b469_btn_bb_promotion import RUNS, SOURCE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-pins", action="store_true")
    args = parser.parse_args()
    ledger = Path("data/nl2_hu_b469_original_archive_pins.json")
    if args.write_pins:
        pins = {}
        for flop, run in RUNS.items():
            if flop == "9s6h3d":
                continue
            path = SOURCE / f"BTN_BB_{flop}_{run}.json.gz"
            if path.is_file():
                pins[flop] = hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()
        ledger.write_text(json.dumps(pins, indent=2) + "\n")
        return
    pins = json.loads(ledger.read_bytes())
    for flop, digest in pins.items():
        run = RUNS[flop]
        stem = f"BTN_BB_{flop}_{run}"
        expected = json.loads((SOURCE/(stem+".proof.json")).read_bytes())
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for ver in ("gto","exp_oop"):
                name = f"nl2-multiboard-B461-R52-BTNB-B33-{ver}" if flop == "Js9h4d" else f"B466-{flop}-{ver}"
                subprocess.run(["gh","run","download",str(run),"-n",name,"-D",str(root/ver)], check=True)
            subprocess.run([sys.executable,"tools/hu_btn_bb_river_pairs.py","--download-dir",str(root),
                            "--flop",flop,"--run-id",str(run),"--out",str(SOURCE)],check=True)
        path = SOURCE/(stem+".json.gz")
        assert hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest() == digest
        actual = json.loads((SOURCE/(stem+".proof.json")).read_bytes())
        # Compression headers can vary across platforms. Both source byte digests and all strategy data are pinned above.
        for result in (actual, expected):
            result.pop("archive_sha256")
        assert actual == expected, flop


if __name__ == "__main__":
    main()
