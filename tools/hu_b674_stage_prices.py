"""Apply the isolated B674 price patch only to the authenticated source revision."""
from pathlib import Path
import argparse
import subprocess

PINS = {
    "nl2_hu_model.js": "905530800036ae6e57af5a64528223ba5553d634",
    "nl2.js": "09907bc4190c0c05bf7df87cc6ca2d2bbdf5d231",
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.parse_args()
    staged = {name: Path("tools/staged/hu_b674_"+name) for name in PINS}
    for name, pin in PINS.items():
        actual = subprocess.check_output(["git","hash-object",name], text=True).strip()
        assert actual == pin, (name, actual, pin)
        assert staged[name].is_file()
    for name in PINS:
        Path(name).write_bytes(staged[name].read_bytes())

if __name__ == "__main__":
    main()
