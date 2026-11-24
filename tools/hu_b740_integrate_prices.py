"""Apply and audit the one half-pot / three-times raise-call ingress and its four descendants."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b467_river_source_gate import compact,json_bytes,sha
import hu_b739_rank108 as native

CODE={
    'nl2_hu_model.js':('b4a308a0f65b707f43f41f0b354cec87c08d5af6','b3dea42d0478e178aefda628e539ec7d95fbe6bd','hu_b740_nl2_hu_model.js'),
    'nl2_cert_registry.js':('709f289d1c87e4b6f64cac5a4231b4c8d717991b','bfa03b476e4997205ed713eda28c6dacc6817d3b','hu_b740_nl2_cert_registry.js'),
    'tools/hu_trainer_route_contract.cjs':('3b10524228c357552bb3f1eac88e17f9b2459b32','88f702e6d0a645e23b1f9359febfab658ec92f80','hu_b740_route_contract.cjs')}
UI='15aee97e53a156fe073c96a120638a8a3679958f'
TARGETS={
    native.MODEL:(108,'',10,95.25,9.525),
    'ln-iso-lmp_r_model-1n1ge2d':(222,'b75 c',25,87.75,3.51),
    'ln-iso-lmp_r_model-1otnixw':(223,'b33 c',16.6,91.95,5.539),
    'ln-iso-lmp_r_model-1wo1hx8':(224,'b50 c',20,90.25,4.513),
    'ln-iso-lmp_r_model-1iqsf2n':(234,'x x',10,95.25,9.525)}
STATUS='data/nl2_hu_multiboard_status_current.json'
EXT='data/nl2_hu_verified_extensions.json'
REF='data/nl2_hu_model_source_references.json'
QUEUE='data/nl2_hu_stage2_queue.json'
XWALK='data/nl2_hu_model_history_crosswalk.json'
REPORT='data/nl2_hu_b740_raise_call_prices.json'
ATOMIC=set(CODE)|{STATUS,EXT,REF,QUEUE,REPORT}
ROUTE='tools/hu_b739_rank108_routes.cjs'


def git(*args):return subprocess.check_output(['git',*args])
def read(path):return json.loads(Path(path).read_bytes())
def blob(path):return git('hash-object',str(path)).decode().strip()


def assert_queue(before,out):
    expected=deepcopy(before)
    expected['source_sha256']['nl2_hu_model.js']=sha(Path('nl2_hu_model.js').read_bytes())
    seen=set()
    assert len(before['records'])==392
    for r in expected['records']:
        k=r['model_id']
        if k in TARGETS:
            seen.add(k);_,_,r['approx_pot_bb'],r['approx_remaining_bb'],r['approx_spr']=TARGETS[k]
    assert seen==set(TARGETS) and expected==out
    for name,digest in out['source_sha256'].items():assert sha(Path(name).read_bytes())==digest


def integrate(a):
    assert blob('nl2.js')==UI
    before={p:read(p) for p in (STATUS,EXT,REF,QUEUE)}
    old=before[STATUS];rs=old['records'];base_count=old['CERT_MULTIBOARD']
    assert len(rs)==392 and base_count>=153 and rs['ln-3bp-3b_r_model-4k40h1']['label']=='CERT-MULTIBOARD'
    children={k for k,v in rs.items() if v['source_model_id']==native.MODEL}
    assert children==set(TARGETS)-{native.MODEL}
    assert all(rs[k]['frequency_rank']==v[0] and rs[k]['label']=='APPROX' for k,v in TARGETS.items())
    original_cross=Path(XWALK).read_bytes();old_route=json.loads(subprocess.check_output(['node',ROUTE]))
    assert old_route['registry_spr']==10.695 and len(old_route['flop'])==len(set(old_route['flop']))==24
    roots=[]
    for flop,turns in native.TURNS.items():
        root,rj,tj,manifest,pin=native.original(flop)
        legal=native.preflight(root,old_route,turns)
        priced={n['line']:n for n in root['nodes'] if len(n['board'])==6}
        first,facing,raised=(priced[k] for k in ('','b50','b50 r'))
        assert rj['flop_raise']=='3x,a' and raised['bets']==[125,375] and raised['pot']==750
        assert raised['pot']+raised['bets'][1]-raised['bets'][0]==1000 and root['stack']-raised['bets'][1]==9525
        roots.append(dict(flop=flop,source=pin,original_nodes=len(root['nodes']),native_flop_raise_menu=rj['flop_raise'],
            opening_pot=first['pot'],facing_pot=facing['pot'],facing_bets=facing['bets'],raised_pot=raised['pot'],raised_bets=raised['bets'],
            opening_node_sha256=sha(compact(first)),facing_node_sha256=sha(compact(facing)),raised_node_sha256=sha(compact(raised)),
            playable_two_seat_upper_bounds={t:len(h) for t,h in legal.items()}))
    for dest,(previous,reviewed,stage) in CODE.items():
        p=Path('tools/staged')/stage;assert blob(dest)==previous and blob(p)==reviewed
        shutil.copyfile(p,dest)
    route=json.loads(subprocess.check_output(['node',ROUTE]));assert route==dict(old_route,registry_spr=9.525)
    subprocess.run([sys.executable,'tools/hu_apply_cert_extensions.py','--out',STATUS],check=True)
    subprocess.run(['node','tools/hu_cert_inventory.js',QUEUE],check=True)
    for p in (STATUS,EXT,REF):
        expected=deepcopy(before[p])
        for k,(rank,turn,pot,stack,spr) in TARGETS.items():
            if p==STATUS:expected['records'][k]['assumed_model_node_spr']=spr
            elif p==REF:expected['items'][k]['model_node_spr']=spr
            else:
                rr=expected['trainer_route_contract']['routes'][k]
                assert rr['seat']==0 and rr['streets']==(['bet raise c',''] if rank==108 else ['bet raise c',turn,''])
                assert 'priced_model_spr' not in rr
                rr['streets'][0]='b50 r c';rr['priced_model_spr']=spr
        assert expected==read(p),p
    assert_queue(before[QUEUE],read(QUEUE))
    assert Path(XWALK).read_bytes()==original_cross
    after=read(STATUS)
    assert (after['CERT_MULTIBOARD'],after['APPROX'],after['TOTAL'])==(base_count,392-base_count,392)
    report=dict(schema='NL2_B740_EXACT_BB_HALF_POT_CO_TRIPLE_RAISE_CALL_V1',
        source_originals=roots,rendered_flop_call_ingress=route['flop'],rendered_turn_cells=route['turn'],
        root_pot_chips=250,initial_stack_chips=9900,bb_bet_chips=125,co_raise_to_total_chips=375,bb_additional_call_chips=250,
        settled_pot_chips=1000,settled_stack_chips=9525,settled_spr=9.525,source_route_blob=blob(ROUTE),
        outcomes={k:dict(rank=v[0],turn=v[1],pot_bb=v[2],stack_bb=v[3],spr=v[4],previous_spr=rs[k]['assumed_model_node_spr']) for k,v in TARGETS.items()},
        ui_source_unchanged=UI,source_code_blobs={k:v[1] for k,v in CODE.items()},all_other_records_preserved=387,
        prior_certificates_preserved=base_count,original_certified_data_changed=0,rank233_preserved=True,CERT_MULTIBOARD=base_count,APPROX=392-base_count,
        new_native_solve_count=0,new_node_locked_public_boards=0,new_medium_assessments=0)
    Path(REPORT).write_bytes(json_bytes(report));a.paths.write_text('\n'.join(sorted(ATOMIC))+'\n')
    print(json.dumps({k:report[k] for k in ('all_other_records_preserved','prior_certificates_preserved','CERT_MULTIBOARD','APPROX')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--paths',type=Path,required=True)
    integrate(p.parse_args())

