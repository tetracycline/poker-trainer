"""Authenticate the CO half-pot/three-quarter-pot menus and the exact 75% flop line for rank62."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import POOL
from hu_b518_rank220_native import RANGES, measured_rates
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case

sys.path.insert(0,str(Path(__file__).resolve().parent/'lines_pipeline'))
from run10_common import hcls

MODEL='ln-ipfr-t_model-snfiz2'
LINE='x b75 c/x'
DATA=Path('data')
HISTORY=DATA/'nl2_hu_b518_rank220_attempts.json'
CASES={'AsKh6s': '9c', '4h4s2d': 'Ad', '6h6c3d': 'Jh', 'JcJh4s': '8h', 'As9c5h': '7c'}
POOLS={'PAIRED':{'TPG','TPW','MID','DRAW','WDRAW'}, 'ACE_HIGH':{'TPG','DRAW','WDRAW'}}


def open_source(directory, flop, turn, version, old):
    batch,turn_policy,extract=('B518','checked-b50only','x b50 c') if old else ('B534','checkcheck','x x')
    manifest=directory/f'NL2-{batch}-{flop}-{version}/trainer/evidence/{flop}-{version}.json'
    if not manifest.is_file() or json.loads(manifest.read_bytes())['failures']:
        return None
    s=original(directory,flop,turn,version,batch=batch,spot='CO_BB',flop_line='x b75 c',
               flop_policy='checked-b75only',turn_policy=turn_policy,turn_extract=extract)
    root,job,sub=s['root'],s['root_job'],s['subgame']
    assert sha(compact([job['oop'],job['ip']]))==RANGES[version]
    assert s['manifest']['solver_pin']=='f0a173b3d9331c4ff8697359a838094f76babb35f16133e37bbd0bfb203b5253'
    if sub is None:
        return None
    parent,=(n for n in root['nodes'] if n['line']=='x b75 c/' and n['board'].endswith(turn))
    job=s['subgame_job']
    assert parent['bets']==[413,413] and sub['pot']==job['pot']==parent['pot']==1376
    assert sub['stack']==job['stack']==root['stack']-413==9337 and job['root_no_bet']
    assert sub['line0']=='x b75 c' and job['line0']==['x','b75','c','/']
    for seat,key in enumerate(('oop_w','ip_w')):
        assert job[key]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    if old:
        expected=next(a for a in old['attempts'] if a['flop']==flop)['versions'][version]
        assert (s['root_sha256'],s['source_sha256'])==(expected['root_sha256'],expected['source_sha256'])
    return s


def bucket(public):
    cards=public[::2]
    if any(public[1::2].count(suit)>=3 for suit in 'cdhs'):
        return 'MONOTONE'
    if len(set(cards))<len(cards):
        return 'PAIRED'
    return 'ACE_HIGH' if 'A' in cards else 'OTHER'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',type=Path,required=True)
    parser.add_argument('--run',type=int,required=True)
    args=parser.parse_args()
    subprocess.run(['node','tools/hu_b534_routes.cjs'],check=True)
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['street'],model['assumed_model_node_spr'])==(62,'CO_BB',1,6.791)
    old=json.loads(HISTORY.read_bytes())
    assert old['run_id']==45111862577
    group=dict(rank=62,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B534_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    attempts=[]
    for flop,turn in CASES.items():
        historical=old if flop=='AsKh6s' else None
        run=old['run_id'] if historical else args.run
        row=dict(flop=flop,turn=turn,source_run=run,versions={})
        attempts.append(row)
        sources=[]
        for v in ('gto','exp_ip'):
            source=open_source(args.downloads,flop,turn,v,historical)
            if source is not None:
                sources.append(source)
                row['versions'][v]=dict(root=source['root_sha256'],subgame=source['source_sha256'])
        if len(sources)!=2:
            row['status']='NO_PAIRED_SUBGAME'
            continue
        g,e=sources
        if not all(0<=s[k]['info']['gto_expl_pct']<=.5 for s in sources for k in ('root','subgame')) or not all(
                0<=e[k]['info']['hero_gap_pct']<=.5 for k in ('root','subgame')):
            row['status']='CONVERGENCE_OUTSIDE_GATE'
            continue
        rates=measured_rates(e)
        if not rates or not any(rate['street']==2 for rate in rates):
            row['status']='NO_MEASURED_TURN_LOCK'
            continue
        code=f'B534_R62_{flop.upper()}_{run}'
        blob=gzip.compress(compact(dict(run_id=run,flop=flop,turn=turn,source_arrays=sources)),mtime=0)
        for s in sources:
            s.update(run=run,archive_code=code,archive_sha256=sha(blob))
        boards=[next((n['board'] for n in s['subgame']['nodes'] if n['line']==LINE and n['player']==1),None) for s in sources]
        if not all(boards):
            row['status']='TARGET_NOT_EXPORTED'
            continue
        public,=set(boards)
        assert len(public)==8 and public[-2:]==turn
        gr,er=[audit_decision(s,public,LINE,1,s['root_sha256']) for s in sources]
        row.update(public_board=public,gto_compatible_pairs=gr['compatible_hole_card_pairs'],nl2_compatible_pairs=er['compatible_hole_card_pairs'])
        if not min(gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs']):
            row['status']='NO_PAIRED_JOINT_REACH'
            continue
        shared=source_case(model,g,public,LINE,1)[1] & source_case(model,e,public,LINE,1)[1]
        hands=[''.join(h) for h in sorted(shared)]
        flop_classes=POOLS.get(bucket(public[:6]),set())
        turn_classes=POOLS.get(bucket(public),set())
        matched=[h for h in hands if hcls(h,public[:6]) in flop_classes and hcls(h,public) in turn_classes]
        row['shared_rendered_hands']=matched
        if not matched:
            row['status']='NO_COMMON_RENDERED_HAND'
            continue
        b,pin=emit_board(model,g,e,public,LINE,texture(flop))
        assert b['actual_pot_bb']==13.76 and b['actual_effective_stack_bb']==93.37 and b['acting_seat']==1
        pin['shared_rendered_route_hands']=matched
        b['nl2_locked_variants'][0].update(measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',pool_sha256=POOL,
            applied_street_rates=rates,variant_label='翻牌至河牌依 NL2 分街邊際頻率局部鎖頻')
        group['boards'].append(b)
        group['pins'].append(pin)
        medium['gto_references'][source_key(MODEL,gr)]=gr
        medium['references'][source_key(MODEL,er)]=er
        (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(blob)
        row['status']='VERIFIED'
    count=len(group['boards'])
    assert count==len({b['flop'] for b in group['boards']})<=5
    if count>=3:
        (EVIDENCE/'reverified/rank62.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b534_locked_medium.json').write_bytes(json_bytes(medium))
    (DATA/'nl2_hu_b534_rank62_attempts.json').write_bytes(json_bytes(dict(rank=62,model_id=MODEL,run=args.run,
        historical_report_sha256=sha(HISTORY.read_bytes()),qualified_distinct_flops=count,attempts=attempts,verified_pairs=group,locked_medium=medium)))


if __name__=='__main__':
    main()
