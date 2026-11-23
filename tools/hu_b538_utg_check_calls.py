"""Replay UTG's check-call at half pot against CO, and both players' turn checks."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b518_rank220_native import measured_rates
from hu_b527_checked_barrels import COLUMNS, board_row, classes, hcls
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case

DATA=Path('data')
VERSIONS=('gto','exp_oop')
RANGE_SHA={'gto':'a6f80629fff3bb619215321a01d4c19183dc80dc37919720c04d0947f1500d70',
           'exp_oop':'f888646780c7d4d583c1d75db5cb8805e62a44f6da30d4d7d6728b03061c6000'}
LINE='x b50 c'
LINES={'68':LINE+'/', '205':LINE+'/x x/'}
FLOPS={
    '6c6d3h':{'6s':['2d','2h'],'5d':['Ks','Ac'],'4s':['8s','7s']},
    '8h8d4c':{'9h':['Qc','Qd'],'5h':['Th','Ks'],'4s':['Jc','2s']},
    'Jh9s4c':{'Qc':['3h','8c'],'4h':['3s','Tc'],'Kd':['6s','9c']},
    'Qh7s3d':{'Qs':['4h','5d'],'7d':['8s','6c'],'4c':['Tc','Qs']},
    'Ac8d3h':{'Qc':['2s','6h'],'6h':['7s','5d'],'2c':['3c','Jh']},
}


def authenticate(folder,flop,turn,version):
    runouts=FLOPS[flop]
    s=original(folder,flop,turn,version,batch='B538',spot='UTG_CO',flop_line=LINE,
        flop_policy='checked-b50only',turn_policy='checkcheck',turn_extract='x x',root_pot=650,root_stack=9750,
        flop_profile='utg-50-only',frozen_turns=list(runouts))
    m,r,rj=s['manifest'],s['root'],s['root_job']
    assert (m['solver_pin'],m['solver_ranges_sha256'],m['allow_turn_lead'])==(PIPELINE,RANGES,True)
    assert sha(compact([rj['oop'],rj['ip']]))==RANGE_SHA[version]
    face,=(n for n in r['nodes'] if len(n['board'])==6 and n['line']=='x b50')
    assert (face['player'],face['bets'],face['pot'])==(0,[0,325],975) and 'c' in face['acts']
    sub=s['subgame']
    if sub is None:
        return s
    j=s['subgame_job']
    parent,=(n for n in r['nodes'] if n['line']==LINE+'/' and n['board'].endswith(turn))
    assert (parent['bets'],parent['pot'],sub['pot'],j['pot'])==([325,325],1300,1300,1300)
    assert (sub['stack'],j['stack'],j['root_no_bet'],sub['rivers'])==(9425,9425,False,runouts[turn])
    assert j['line0']==['x','b50','c','/']
    for seat,key in enumerate(('oop_w','ip_w')):
        assert j[key]==[[h,w] for h,w in zip(r['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    return s


def visible_hands(shared, public, rank, routes):
    result=[]
    for h in sorted(shared):
        hand=''.join(h)
        steps=[(public[:6],hcls(hand,public[:6]),'68'),
               (public[:8],hcls(hand,public[:8]),rank)]
        if rank=='205':
            cls,=classes(hand,public)
            steps.append((public,cls,'205'))
        for board,cls,stage in steps:
            if cls not in COLUMNS or f'{board_row(board)}:{COLUMNS.index(cls)}' not in routes[stage]['allowed']:
                break
        else:
            result.append(hand)
    return result


def assess(sources,model,rank,public,routes):
    line=LINES[rank]
    rows=[]
    for s in sources:
        target=[n for n in s['subgame']['nodes'] if (n['board'],n['line'],n['player'])==(public,line,0)]
        if not target:
            return None,dict(status='TARGET_ABSENT')
        n,=target
        assert n['pot']==1300 and n['bets']==[0,0] and 'x' in n['acts']
        if rank=='68':
            assert {'b50','b100'}<=set(n['acts'])
        if 'b50' in n['acts']:
            faced,=(b for b in s['subgame']['nodes'] if (b['board'],b['line'],b['player'])==(public,line+'b50',1))
            assert (faced['pot'],faced['bets'])==(1950,[650,0])
        rows.append(audit_decision(s,public,line,0,s['root_sha256']))
    audit=dict(gto_pairs=rows[0]['compatible_hole_card_pairs'],nl2_pairs=rows[1]['compatible_hole_card_pairs'])
    if not min(audit.values()):
        return None,dict(audit,status='ZERO_JOINT_REACH')
    shared=set.intersection(*(source_case(model,s,public,line,0)[1] for s in sources))
    hands=visible_hands(shared,public,rank,routes)
    audit.update(common_actor_hands=len(shared),shared_rendered_hands=hands)
    return (rows if hands else None),dict(audit,status='VERIFIED' if hands else 'NO_SHARED_RENDERED_HAND')


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--downloads',required=True,type=Path)
    cli.add_argument('--run',required=True,type=int)
    args=cli.parse_args()
    routes=json.loads(subprocess.check_output(['node','tools/hu_b538_utg_routes.cjs']))
    models=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    groups={rank:dict(rank=int(rank),model_id=route['model'],boards=[],pins=[]) for rank,route in routes.items()}
    refs={rank:dict(references={},gto_references={}) for rank in routes}
    attempts=[]
    for flop,runouts in FLOPS.items():
        selected=set()
        for turn,rivers in runouts.items():
            attempt=dict(flop=flop,turn=turn,gaps={},nodes={})
            attempts.append(attempt)
            sources=[]
            for v in VERSIONS:
                mf=args.downloads/f'NL2-B538-{flop}-{v}/trainer/evidence/{flop}-{v}.json'
                if not mf.is_file() or json.loads(mf.read_bytes())['failures']:
                    continue
                s=authenticate(args.downloads,flop,turn,v)
                if s['subgame'] is None:
                    continue
                gaps=[s[g]['info']['gto_expl_pct'] for g in ('root','subgame')]
                if v!='gto':
                    gaps.extend(s[g]['info']['hero_gap_pct'] for g in ('root','subgame'))
                attempt['gaps'][v]=gaps
                if all(0<=x<=.5 for x in gaps):
                    sources.append(s)
            if len(sources)!=2:
                attempt['status']='NO_CONVERGED_PAIR'
                continue
            g,e=sources
            rates=measured_rates(e)
            if not rates:
                attempt['status']='NO_VERIFIED_STREET_LOCK'
                continue
            raw=gzip.compress(compact(dict(run_id=args.run,source_arrays=sources)),mtime=0)
            code=f'B538_{flop.upper()}_{turn.upper()}_{args.run}'
            for s in sources:
                s.update(run=args.run,archive_code=code,archive_sha256=sha(raw))
            turnboard,=(n['board'] for n in g['subgame']['nodes'] if n['line']==LINES['68'] and n['player']==0)
            for rank,boards in [('68',[turnboard]),('205',[turnboard+r for r in rivers])]:
                group=groups[rank]; model=models[group['model_id']]
                assert (model['frequency_rank'],model['assumed_model_node_spr'])==(int(rank),7)
                for public in boards:
                    rows,audit=assess(sources,model,rank,public,routes)
                    attempt['nodes'][public]=audit
                    if rows is None or rank in selected:
                        continue
                    board,pin=emit_board(model,g,e,public,LINES[rank],texture(flop))
                    assert (board['actual_pot_bb'],board['actual_effective_stack_bb'])==(13,94.25)
                    pin['shared_rendered_route_hands']=audit['shared_rendered_hands']
                    board.update(restricted_flop_size_profile='UTG_CO_50PCT_ONLY',restricted_flop_bet_sizes_pct=[50],turn_root_allows_lead=True)
                    board['nl2_locked_variants'][0].update(measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',pool_sha256=POOL,
                        applied_street_rates=rates,variant_label='翻牌限半池，轉牌可領打半池或滿池，依 NL2 分街邊際頻率局部鎖頻')
                    group['boards'].append(board)
                    group['pins'].append(pin)
                    selected.add(rank)
                    for field,row in zip(('gto_references','references'),rows):
                        refs[rank][field][source_key(model['model_id'],row)]=row
                    (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(raw)
    medium=dict(schema='NL2_HU_B538_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for rank,group in groups.items():
        count=len(group['boards'])
        assert count==len({b['flop'] for b in group['boards']})<=5
        if count>=3:
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
            for field in ('gto_references','references'):
                medium[field].update(refs[rank][field])
    if medium['references']:
        (DATA/'nl2_hu_b538_locked_medium.json').write_bytes(json_bytes(medium))
    (DATA/'nl2_hu_b538_utg_check_calls.json').write_bytes(json_bytes(dict(run=args.run,models=groups,attempts=attempts)))


if __name__=='__main__':
    main()
