"""Screen three new low two-suit roots for rank29's native half-pot lead and 75% barrels."""
import argparse
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

import hu_b703_rank29_highcards as source
from hu_b580_rank27_rivers import suit_isomorphism_class

CASES={'8s7s6d':['Js','Ts','Qs','Ks'],'6c5c4h':['Tc','Jc','Qc','Kc'], '5d4d2c':['Td','Jd','Qd','Kd']}
PINS={'tools/hu_b703_rank29_highcards.py':'1adbb4fe4bd2ad36643dd3e79bf5f41cd9580ac8',
      'tools/hu_b703_rank29_routes.cjs':'8ac70c349c5f60d35578e9f85fda0d2ec08d5384',
      'tools/hu_trainer_route_contract.cjs':'3b10524228c357552bb3f1eac88e17f9b2459b32',
      'nl2_cert_registry.js':'709f289d1c87e4b6f64cac5a4231b4c8d717991b'}
LIVE={'nl2_hu_model.js':'b4a308a0f65b707f43f41f0b354cec87c08d5af6','nl2.js':'15aee97e53a156fe073c96a120638a8a3679958f'}


def run(args):
    assert all(source.git_blob(name)==sha for name,sha in {**PINS,**LIVE}.items())
    assert len({suit_isomorphism_class(f) for f in CASES})==3
    historical=Path('data/nl2_hu_b582_rank29_reach.json');old=json.loads(historical.read_bytes())
    assert old['sampled_positive_flops']==0 and sorted(row['root_route_eligible_hands'] for row in old['flops'])==[1,10,11]
    assert {suit_isomorphism_class(f) for f in CASES}.isdisjoint({suit_isomorphism_class(row['flop']) for row in old['flops']})
    route=json.loads(subprocess.check_output(['node','tools/hu_b703_rank29_routes.cjs']))
    assert route['turn']==['mono:0'] and route['river']=={'mono:0':'下注 ¾'}
    with ZipFile(source.TEMPLATE) as z:manifest=json.loads(z.read('original-manifest.json'))
    assert source.sha(Path(source.TEMPLATE).read_bytes())==source.TEMPLATE_SHA
    witnesses=[];flop=args.flop;suit=flop[1];other={'s':'c','c':'d','d':'h'}[suit]
    for turn in CASES[flop]:
        hero='A'+suit+turn[0]+other
        river='3h' if flop=='8s7s6d' else '9s'
        villain='2h2d' if flop!='5d4d2c' else '7c7s'
        source.RANGE_WITNESSES={flop:(turn,river,hero,villain)}
        witnesses.append(source.static_witness(flop,manifest,route))
    source.RANGE_WITNESSES={flop:tuple(witnesses[0][k] for k in ('turn','river','hero','villain'))}
    source.CASES=CASES;source.APP_PINS=LIVE
    source.run(args)
    if args.preflight:return
    path=args.output/'proof.json';out=json.loads(path.read_bytes())
    assert out['schema']=='NL2_B703_R29_ORIGINAL_WORKER_V1'
    assert out['preregistered_flops']==list(CASES) and out['preregistered_turns']==CASES[flop]
    assert out['root_gate_threshold']=='MAX_FREQUENCY_OR_GE40PCT_AND_GE70PCT_OF_MAX_UNCHANGED'
    locked=[(p,row) for t in out['turns'] for p,row in t.get('nl2_rivers',{}).items()]
    assert len({p for p,row in locked})==len(locked)
    joint=[row for p,row in locked if row['strict_legal_combos']>0 and row['compatible_hole_card_pairs']>0]
    assert all(row['b50'] is not None for row in joint)
    out.update(schema='NL2_B717_R29_LOW_CONNECTED_ORIGINAL_V1',source_pins=PINS,
        wrapped_original_algorithm_blob=out['source_worker_blob'],source_worker_blob=source.git_blob('tools/hu_b717_rank29_low_connected.py'),
        preregistered_range_witnesses=witnesses,prior_b582_screen_sha256=source.sha(historical.read_bytes()),
        selection_mechanism='LOW_TWO_SUIT_FLOPS_WITH_FOUR_HIGH_SAME_SUIT_TURN_CARDS_FROM_POSITIVE_ROOT_B582_FINDING',
        native_locked_public_boards=len(locked),reachable_locked_public_boards=len(joint),half_pot_assessments=len(joint),
        nonpolarized_candidates=sum(bool(row['b50']['candidate']) for row in joint))
    path.write_bytes(source.json_bytes(out))
    print(json.dumps({k:out[k] for k in ('positive_distinct_flops','native_locked_public_boards','reachable_locked_public_boards','half_pot_assessments','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True);p.add_argument('--driver',type=Path);p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
