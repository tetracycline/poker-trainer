"""Replay BB's pot-size flop stab and both rendered turn barrel sizes against separate original policies."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import POOL
from hu_b509_limp_ip import observations
from hu_b518_rank220_native import measured_rates
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case

sys.path.insert(0, str(Path(__file__).parent / 'lines_pipeline'))
from run10_common import classes, hcls

VERSIONS = ('gto', 'exp_ip')
RANGES = {'gto':'8c254e05d84f79879a7d4c63ef6c46dc42f8ef1e28524f2d9c8e5e2178ae5361',
          'exp_ip':'cf8a0abdb28f1a7c99ca7d744d1b6eddeaba78e55c118a21ee458e18c9ef97e3'}
CASES = {'Ah8c5d':('3h',['Ad','5h']), 'KsJc7h':('9h',['Qs','5s']), 'Qd9h6c':('3h',['Ks','Kh']),
         'Js8d7c':('Ks',['Ad','2h']), 'KcTh4s':('Qd',['Ks','9h'])}
COLUMNS = ['TPG', 'TPW', 'MID', 'DRAW', 'WDRAW']
PARENT = 'x b100 c'
MENU = '33%,50%,75%,100%'


def board_row(board):
    ranks = board[::2]
    if max(Counter(board[1::2]).values()) >= 3:
        return 'mono'
    if len(set(ranks)) < len(ranks):
        return 'paired'
    for high, category in [('A','A_high'),('KQ','KQ_high'),('JT','mid_high')]:
        if set(ranks).intersection(high):
            return category
    return 'low'


def witnesses(hands, public, route):
    matches = []
    for cards in sorted(hands):
        hand = ''.join(cards)
        river_class, = classes(hand, public)
        for board, group, allowed in [(public[:6],hcls(hand,public[:6]),route['flop']),
                                       (public[:8],hcls(hand,public[:8]),route['turn']),
                                       (public,river_class,route['turn'])]:
            if group not in COLUMNS or f'{board_row(board)}:{COLUMNS.index(group)}' not in allowed:
                break
        else:
            matches.append(hand)
    return matches


def authenticate(directory, flop, turn, rivers, version):
    s = original(directory,flop,turn,version,batch='B527',spot='SB_BB',flop_line=PARENT,
                 flop_policy='checked-b100only',turn_policy='checked-b33-b50',turn_extracts=['x b33 c','x b50 c'],
                 root_pot=600,root_stack=9700,turn_mode='33-50-75-100',turn_menu=MENU)
    root,job,sub = s['root'],s['root_job'],s['subgame']
    assert sha(compact([job['oop'],job['ip']])) == RANGES[version]
    from hu_b483_locked_medium import PIPELINE, RANGES as RANGE_FILE
    assert (s['manifest']['solver_pin'],s['manifest']['solver_ranges_sha256']) == (PIPELINE,RANGE_FILE)
    if sub is not None:
        job = s['subgame_job']
        parent, = (n for n in root['nodes'] if n['line'] == PARENT+'/' and n['board'].endswith(turn))
        assert (parent['bets'],parent['pot'],sub['pot'],job['pot']) == ([600,600],1800,1800,1800)
        assert sub['rivers']==rivers and job['root_no_bet'] and job['stack']==sub['stack']==9100
        for seat,key in enumerate(('oop_w','ip_w')):
            assert job[key] == [[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
        if version!='gto':
            s['measured_lock_application']=s['actual_turn_job_lock_coverage']
    return s


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--downloads',type=Path,required=True)
    cli.add_argument('--run',type=int,required=True)
    args=cli.parse_args()
    data=Path('data')
    routes=json.loads(subprocess.check_output(['node','tools/hu_b527_checked_barrels.cjs']))
    registry=json.loads((data/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    groups={r:dict(rank=int(r),model_id=x['model'],boards=[],pins=[]) for r,x in routes.items()}
    medium={r:dict(references={},gto_references={}) for r in routes}
    attempts=[]
    for flop,(turn,rivers) in CASES.items():
        attempt=dict(flop=flop,turn=turn,decisions={})
        attempts.append(attempt)
        sources=[]
        for version in VERSIONS:
            m=args.downloads/f'NL2-B527-{flop}-{version}/trainer/evidence/{flop}-{version}.json'
            if m.is_file() and not json.loads(m.read_bytes())['failures']:
                sources.append(authenticate(args.downloads,flop,turn,rivers,version))
        if len(sources)!=2 or any(s['subgame'] is None for s in sources):
            attempt['status']='INCOMPLETE_OR_EMPTY_PAIR'
            continue
        g,e=sources
        if any(not 0<=s[k]['info']['gto_expl_pct']<=.5 for k in ('root','subgame') for s in sources) or any(
                not 0<=e[k]['info']['hero_gap_pct']<=.5 for k in ('root','subgame')):
            attempt['status']='CONVERGENCE_GATE'
            continue
        rates=measured_rates(e)
        assert e['subgame']['info']['lock_stats'] and rates
        blob=gzip.compress(compact(dict(run_id=args.run,flop=flop,turn=turn,source_arrays=sources)),mtime=0)
        code=f'B527_{flop.upper()}_{args.run}'
        for s in sources:
            s.update(run=args.run,archive_code=code,archive_sha256=sha(blob))
        for rank,pct in [('188',50),('191',33)]:
            route=routes[rank]
            model=registry[route['model']]
            assert model['frequency_rank']==int(rank) and model['solver_profile']=='SB_BB'
            line=f'{PARENT}/x b{pct} c/x'
            rows=[observations(s,line,10,s['root_sha256']) for s in sources]
            outcomes=attempt['decisions'][rank]={}
            for river in rivers:
                public=next((p for p in rows[0] if p.endswith(river)),None)
                if public is None or public not in rows[1]:
                    outcomes[river]={'status':'UNEXPORTED'}
                    continue
                gr,er=(v[public] for v in rows)
                details=outcomes[river]=dict(gto_pairs=gr['compatible_hole_card_pairs'],nl2_pairs=er['compatible_hole_card_pairs'])
                if min(details.values())==0:
                    continue
                shared=set.intersection(*(source_case(model,s,public,line,1)[1] for s in sources))
                hands=witnesses(shared,public,route)
                details['shared_rendered_hands']=hands
                if not hands:
                    continue
                b,p=emit_board(model,g,e,public,line,texture(flop))
                invest=1800*pct//100
                assert (b['actual_pot_bb'],b['actual_effective_stack_bb'])==((1800+2*invest)/100,(9100-invest)/100)
                p['shared_rendered_hands']=hands
                b['nl2_locked_variants'][0].update(measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
                    pool_sha256=POOL,applied_street_rates=rates,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
                groups[rank]['boards'].append(b)
                groups[rank]['pins'].append(p)
                gr['root_applied_rust_lock_nodes']=0
                er['root_applied_rust_lock_nodes']=sum(v['nodes'] for v in e['root']['info']['lock_stats'].values())
                for field,row in [('gto_references',gr),('references',er)]:
                    medium[rank][field][source_key(model['model_id'],row)]=row
                (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(blob)
                break
    refs=dict(schema='NL2_B527_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for rank,group in groups.items():
        assert len(group['boards'])==len({b['flop'] for b in group['boards']})<=5
        if len(group['boards'])>=3:
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
            for field in ('references','gto_references'):
                refs[field].update(medium[rank][field])
    if refs['references']:
        (data/'nl2_hu_b527_locked_medium.json').write_bytes(json_bytes(refs))
    (data/'nl2_hu_b527_checked_barrels.json').write_bytes(json_bytes(dict(run=args.run,models=groups,attempts=attempts)))


if __name__=='__main__':
    main()
