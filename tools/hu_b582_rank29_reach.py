"""Replay the exact rank29 flop and river screening decisions from their native arrays."""
import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import POOL
from hu_b527_checked_barrels import board_row
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, compatible_node_reach, game_reach

sys.path.insert(0, str(Path(__file__).parent / 'lines_pipeline'))
from run10_common import classes, hcls

DATA = Path('data')
EVIDENCE = DATA / 'solver_evidence'
SOLVER = 'abe310c3aad02dd4a7c77fb2831801fd490cf51b'
LINE = 'b50 c/b75 c/'
DECK = [r+s for r in '23456789TJQKA' for s in 'cdhs']
COLUMNS = ['TPG','TPW','MID','DRAW','WDRAW']

def cards(text):
    return set(text[i:i+2] for i in range(0,len(text),2))

def rendered(hand, public, stage, route):
    category = classes(hand,public)[0] if stage=='river' else hcls(hand,public)
    if category not in COLUMNS:
        return False
    return f'{board_row(public)}:{COLUMNS.index(category)}' in route[stage]

def candidates(root, route):
    lead, = [n for n in root['nodes'] if n['line']=='']
    call, = [n for n in root['nodes'] if n['line']=='b50']
    assert (lead['player'],lead['pot'],call['player'],call['pot']) == (0,250,1,375)
    public=lead['board']
    callers=accepted(call,root['hands'],'c')
    heroes=[''.join(h) for h in accepted(lead,root['hands'],'b50') if rendered(''.join(h),public,'flop',route)]
    priority=[]
    for n in root['nodes']:
        if n['line']!='b50 c/':
            continue
        turn=n['board'][-2:]
        assert n['board']==public+turn and (n['pot'],n['bets'])==(500,[125,125])
        legal=[h for h in heroes if turn not in cards(h) and rendered(h,n['board'],'turn',route)]
        runouts=[]
        if legal:
            for river in DECK:
                if river in cards(n['board']):
                    continue
                eligible={h for h in legal if river not in cards(h) and rendered(h,n['board']+river,'river',route)
                          and any(set(v).isdisjoint(cards(h)|{turn,river}) for v in callers)}
                if eligible:
                    runouts.append((len(eligible),river,eligible))
        if runouts:
            runouts.sort(key=lambda r:(r[0],r[1]),reverse=True)
            priority.append((runouts[0][0],turn,n,runouts[:7]))
    priority.sort(key=lambda r:-r[0])
    return len(heroes),priority

def verified_masks(root,subgame,seat,public):
    node,=(n for n in subgame['nodes'] if (n['board'],n['line'],n['player'])==(public,LINE,seat))
    assert (node['pot'],node['bets'])==(1250,[375,375]) and 'b75' in node['acts']
    masks=game_reach(root,subgame)[0]
    proof=compatible_node_reach(root,subgame,node,masks[f'{public}|{LINE}|{seat}'])
    bits=base64.b64decode(proof['mask'],validate=True)
    return {''.join(cardkey(h)):mask for h,mask in zip(subgame['hands'][seat],bits,strict=True) if mask}

def replay(spec,template,turn_template,origin,route,pool,pipeline):
    path=EVIDENCE/spec['archive']
    assert sha(path.read_bytes())==spec['sha256']
    with ZipFile(path) as z:
        read=lambda name:json.loads(z.read(name))
        root,job=read('root.json'),read('root.job.json')
        flop=spec['flop']
        assert (root['flop'],root['pot'],root['stack'])==(flop,250,9900)
        assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
        suit=next(s for s in 'cdhs' if flop[1::2].count(s)==2)
        turns=[r+suit for r in '23456789TJQKA' if r+suit not in cards(flop)]
        extracts=[dict(prefix=[],street=True)]+[dict(prefix=['b50','c',t],street=False,raw=True) for t in turns]
        assert job==dict(template,flop=flop,out='root.json',extract=extracts)
        check_limp_source(dict(manifest=origin,root_job=job,subgame_job=None))
        assert {n['board'][-2:] for n in root['nodes'] if n['line']=='b50 c/'}==set(turns)
        count,picks=candidates(root,route)
        result=dict(flop=flop,root_sha256=sha(z.read('root.json')),root_gap_pct=root['info']['gto_expl_pct'],
                    root_route_eligible_hands=count,raw_turns=len(turns),candidate_turns=[t for _,t,_,_ in picks],tested=[])
        for _,turn,n,rivers in picks[:3]:
            j=dict(turn_template,flop=flop,turn=turn,out='result.json',turn_oop='75%',turn_ip='50%,100%',
                   river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',target_pct=.45,iters=2000,
                   extract=[dict(prefix=[],street=True)]+[dict(prefix=['b75','c',r],street=True) for _,r,_ in rivers])
            for i,k in enumerate(('oop_w','ip_w')):
                j[k]=[[h,w] for h,w in zip(root['hands'][i],n['wr'][i],strict=True) if w>1e-4]
            l,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='LMP_CO_BB')),job=j),
                                'exp_oop',pool,pipeline)
            assert rules==read(turn+'-locks.json')
            policies={}
            paths={}
            for version,expected in (('gto',j),('exp_oop',l)):
                folder=turn+'-'+version+'/'
                assert expected==read(folder+'job.json')
                native=z.read(folder+expected['out']); sub=json.loads(native)
                assert (sub['flop'],sub['pot'],sub['stack'])==(flop,500,9775)
                assert 0<=sub['info']['gto_expl_pct']<=.5
                if version=='exp_oop':
                    assert 0<=sub['info']['hero_gap_pct']<=.5 and sub['info']['lock_stats']
                else:
                    assert not sub['info'].get('lock_stats')
                sub.update(line0='b50 c',turn=turn)
                paths[version]=dict(sha256=sha(native),gto_gap_pct=sub['info']['gto_expl_pct'],locked_gap_pct=sub['info'].get('hero_gap_pct'))
                policies[version]={r:set(verified_masks(root,sub,0,n['board']+r)) & legal for _,r,legal in rivers}
            result['tested'].append(dict(turn=turn,policy_sources=paths,
                rivers=[dict(public_board=n['board']+r,gto=len(policies['gto'][r]),nl2=len(policies['exp_oop'][r]),
                             shared_hands=sorted(policies['gto'][r]&policies['exp_oop'][r])) for _,r,_ in rivers]))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    a=parser.parse_args()
    solver=a.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    pins=json.loads((DATA/'nl2_hu_b582_rank29_inputs.json').read_bytes())
    basis=EVIDENCE/'NL2_B580_R27_LMP.zip'
    assert sha(basis.read_bytes())==pins['template_archive_sha256']
    with ZipFile(basis) as z:
        template,turn_template,origin=[json.loads(z.read(n)) for n in ('original-flop.job.json','original-turn.job.json','original-manifest.json')]
    route=json.loads(subprocess.check_output(['node','tools/hu_b582_rank29_route.cjs']))
    rows=[replay(spec,template,turn_template,origin,route,json.loads(poolraw)['NL2'],pipeline) for spec in pins['flops']]
    result=dict(rank=29,solver=SOLVER,execution='LOCAL_PINNED_RUST',target_line=LINE,acting_seat=0,
                flop_menu_pct=[50],turn_oop_menu_pct=[75],river_bet_menu='50%,75%,100%,a',
                sampled_positive_flops=sum(any(r['shared_hands'] for t in row['tested'] for r in t['rivers']) for row in rows),flops=rows)
    a.out.write_bytes(json_bytes(result))

if __name__=='__main__':
    main()
