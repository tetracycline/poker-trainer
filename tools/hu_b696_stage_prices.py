"""Stage only the two authenticated turn-call leaves and their exact route contract."""
import argparse
from pathlib import Path
import subprocess

UI="15aee97e53a156fe073c96a120638a8a3679958f"
PINS={
    "nl2_hu_model.js":("a98cb80d7762b464064874de39dcff6f4bf5707d","b4a308a0f65b707f43f41f0b354cec87c08d5af6","tools/staged/hu_b696_nl2_hu_model.js"),
    "tools/hu_trainer_route_contract.cjs":("31370c779d22b7d895e76f1030504909019dbe5a","3b10524228c357552bb3f1eac88e17f9b2459b32","tools/staged/hu_b696_trainer_route_contract.cjs"),
}


def digest(path):
    return subprocess.check_output(["git","hash-object",str(path)],text=True).strip()


def apply():
    assert digest("nl2.js")==UI,"The reviewed UI source has changed"
    states=[];staged={}
    for target,(old,new,source) in PINS.items():
        assert digest(source)==new,(source,"staged source SHA mismatch")
        actual=digest(target);assert actual in (old,new),(target,"unrecognized source SHA",actual)
        states.append(actual==new);staged[target]=Path(source).read_bytes()
    assert len(set(states))==1,"Mixed four-price/six-price source state is not accepted"
    if all(states):
        print("The two pinned turn-call prices and route contract are already active; no changes")
        return
    for target,raw in staged.items():Path(target).write_bytes(raw)
    print("Applied only the two pinned 50-percent turn-call leaves and their route contract")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument("--apply",action="store_true",required=True);cli.parse_args()
    apply()
