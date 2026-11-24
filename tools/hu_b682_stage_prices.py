"""Apply the pinned B674 prices once, or accept exactly the already repaired pair."""
import argparse
from pathlib import Path
import subprocess

PINS={
    'nl2_hu_model.js':('905530800036ae6e57af5a64528223ba5553d634','a98cb80d7762b464064874de39dcff6f4bf5707d'),
    'nl2.js':('09907bc4190c0c05bf7df87cc6ca2d2bbdf5d231','15aee97e53a156fe073c96a120638a8a3679958f'),
}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true',required=True);p.parse_args()
    states=[];staged={}
    for name,(before,after)in PINS.items():
        path=Path('tools/staged/hu_b674_'+name)
        staged[name]=path.read_bytes()
        digest=subprocess.check_output(['git','hash-object',str(path)],text=True).strip()
        assert digest==after,(name,'staged patch differs',digest)
        current=subprocess.check_output(['git','hash-object',name],text=True).strip()
        assert current in (before,after),(name,'unrecognized current source',current)
        states.append(current==after)
    assert len(set(states))==1,'Mixed baseline/repaired source files are not an authorized input'
    if all(states):
        print('Pinned 33-percent call prices already applied; no changes')
        return
    for name,raw in staged.items():Path(name).write_bytes(raw)
    print('Applied pinned 33-percent call prices')


if __name__=='__main__':main()
