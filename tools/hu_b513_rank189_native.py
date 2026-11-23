"""Reproduce the BB-IP river after a 33%-pot flop stab and a full-pot turn bet."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

MODEL='ln-ipc-r_model-1ua8hb7'
LINE='x b33 c/x b100 c/x'
ANCHOR=('As9h2d','Kd',14598935222,14598327356)
BOUNDARY=('As7h3d','Kd',14628913050)
FRESH={'Ac8d2h':'Tc','Ac6d3h':'9d','As7s2s':'5s'}
CODE='B513_R189_AS7H3D_EXP_IP'
PINS=Path('data/nl2_hu_b513_rank189_artifacts.json')
RANKS='23456789TJQKA'
STRAIGHTS=[set('A2345')]+[set(RANKS[i:i+5]) for i in range(9)]


def unpaired_draw(hand, turn_cards):
    ranks=[c[0] for c in (*turn_cards,*hand)]
    if len(set(ranks))<len(ranks):return False
    suits=Counter(c[1] for c in (*turn_cards,*hand))
    hand_suits={c[1] for c in hand}
    present=set(ranks)
    if max(suits.values())>=5 or any(run<=present for run in STRAIGHTS):return False
    return any(suits[s]==4 for s in hand_suits) or any(
        len(run & present)==4 and run.intersection(c[0] for c in hand) for run in STRAIGHTS)


def measure(s,public,identity):
    root,sub=s['root'],s['subgame']
    nodes={(n['board'],n['line'],n['player']):n for n in sub['nodes']}
    n=nodes[public,LINE,1]
    assert (n['pot'],n['bets'],sub['stack']-max(n['bets']))==(2988,[996,996],8506)
    reply=nodes[public,LINE+' b50',0]
    assert 'b50' in n['acts'] and reply['pot']==4482 and reply['bets']==[996,2490]
    r=proof(root,sub,n,game_reach(root,sub)[0])
    scope=lock_scope(sub,s['manifest']['locks'],s['version'])
    return dict(r,version=s['version'],source_run_id=s['run'],source_sha256=s['source_sha256'],archive_sha256=s['archive_sha256'],
        spot='SB_BB',family='SRP',flop=sub['flop'],turn=sub['turn'],root_sha256=identity['root_sha256'],
        gto_gap_pct=sub['info']['gto_expl_pct'],locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),lock_scope=scope,
        root_applied_rust_lock_nodes=sum(v['nodes'] for v in root['info'].get('lock_stats',{}).values()),
        subgame_applied_rust_lock_nodes=sum(v['nodes'] for v in sub['info'].get('lock_stats',{}).values()))


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--originals',type=Path,required=True)
    cli.add_argument('--solver',type=Path,required=True)
    cli.add_argument('--results',type=Path)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--run',type=int)
    cli.add_argument('--head')
    args=cli.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip()==SOLVER
    pool_bytes=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_bytes)==POOL
    pool=json.loads(pool_bytes)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline,ranges
    pins=json.loads(PINS.read_bytes())

    def original(aid,flop,turn,ver):
        src=load_original(args.originals,aid,pins[str(aid)],'SB_BB',flop,turn,ver,pot=600,stack=9700,pipeline=pipeline,ranges=ranges,flop_line='x b33 c')
        assert src['job']['turn_ip']=='50%,100%' and src['job']['river_ip']=='50%,100%,a'
        return src

    bflop,bturn,bid=BOUNDARY
    boundary=original(bid,bflop,bturn,'gto')
    if args.driver:
        path=solve_native(boundary,'exp_ip',pool,pipeline,args.results,args.driver,args.run,CODE)
        replay_native(boundary,'exp_ip',pool,pipeline,path,args.run,CODE)
        return
    registry=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    model=registry['records'][MODEL]
    assert (model['frequency_rank'],model['street'],model['solver_profile'],model['assumed_model_node_spr'])==(189,2,'SB_BB',2.833)
    flop,turn,gid,eid=ANCHOR
    pairs={flop:(original(gid,flop,turn,'gto'),original(eid,flop,turn,'exp_ip'))}
    attempts={}
    if args.results:
        gz=list(args.results.rglob(f'NL2_{CODE}.json.gz'))
        if gz:
            assert len(gz)==1
            dest=EVIDENCE/gz[0].name
            shutil.copyfile(gz[0],dest)
            e=replay_native(boundary,'exp_ip',pool,pipeline,dest,args.run,CODE)
            pairs[bflop]=(boundary,dict(source=e,identity=boundary['identity']))
        infos={i['name']:i for i in json.loads((args.originals/'run.json').read_bytes())['artifacts']}
        for flop,turn in FRESH.items():
            pair=[]
            assert pipeline.turns_for(flop,1)==[turn]
            for ver in ('gto','exp_ip'):
                info=infos.get(f'B513-{flop}-{ver}')
                if info is None:break
                aid=info['id'];meta=json.loads((args.originals/f'{aid}.json').read_bytes())
                assert meta['workflow_run']['id']==args.run and meta['workflow_run']['head_sha']==args.head
                pins[str(aid)]=dict(sha256=info['digest'].removeprefix('sha256:'),run=args.run,head=args.head,name=info['name'])
                with ZipFile(args.originals/f'{aid}.zip') as z:
                    assert sha((args.originals/f'{aid}.zip').read_bytes())==pins[str(aid)]['sha256']
                    mf=json.loads(z.read(f'trainer/evidence/{flop}-{ver}.json'))
                    if mf['failures'] or len(mf['cases'])!=1:break
                    assert mf['selected_lines']==['x b33 c'] and mf['turns']==[turn]
                    c,=mf['cases']
                    if c['gto_gap_pct']>.5 or (ver!='gto' and c['hero_gap_pct']>.5):break
                obj=original(aid,flop,turn,ver)
                if ver=='exp_ip':
                    audit_patterns(obj['source']['subgame'],obj['job'],obj['source']['manifest'],pool,hero_seat=1)
                pair.append(obj)
            if len(pair)==2:pairs[flop]=pair
            else:attempts[flop]='INCOMPLETE_OR_UNCONVERGED_ORIGINAL_PAIR'
    group=dict(rank=189,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B513_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for flop,(orig,locked) in pairs.items():
        g,e=orig['source'],locked['source']
        assert texture(flop) in ('ACE_HIGH','MONOTONE')
        gs,es=g['subgame'],e['subgame']
        assert gs['turn']==es['turn'] and gs['rivers']==es['rivers']
        attempts[flop]={}
        for river in gs['rivers']:
            public=orig['public']+river
            if not all(any((n['board'],n['line'],n['player'])==(public,LINE,1) for n in sub['nodes']) for sub in (gs,es)):continue
            gr=measure(g,public,orig['identity']);er=measure(e,public,locked['identity'])
            rec=attempts[flop][public]=dict(gto=gr,exp_ip=er)
            if not all(0<=n<=.5 for n in (gr['gto_gap_pct'],er['gto_gap_pct'],er['locked_hero_gap_pct'])):continue
            if min(gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs'])==0:continue
            assert er['subgame_applied_rust_lock_nodes']>0 and er['lock_scope']['observed_marginal_source_nodes']>0
            _,gh,_=source_case(model,g,public,LINE,1);_,eh,_=source_case(model,e,public,LINE,1)
            board4=[public[i:i+2] for i in range(0,8,2)]
            rec['shared_unpaired_turn_draws']=sorted(''.join(h) for h in gh.intersection(eh) if unpaired_draw(h,board4))
            if not rec['shared_unpaired_turn_draws']:continue
            if not args.results:break
            board,pin=emit_board(model,g,e,public,LINE,texture(flop))
            pin['original_gto_archive']=orig['identity']
            pin['shared_unpaired_turn_draws']=rec['shared_unpaired_turn_draws']
            if e.get('verified_gto_parent'):
                pin['conditional_gto_flop_root_sha256']=orig['identity']['root_sha256']
                board['nl2_locked_variants'][0].update(variant_label='原始 GTO 翻牌，轉河牌依分街 NL2 邊際頻率局部鎖頻',measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',pool_sha256=POOL)
            else:pin['original_locked_archive']=locked['identity']
            group['boards'].append(board);group['pins'].append(pin)
            medium['references'][source_key(MODEL,er)]=er
            medium['gto_references'][source_key(MODEL,gr)]=gr
            break
    if args.results:
        Path('data/nl2_hu_b513_rank189_attempts.json').write_bytes(json_bytes(dict(rank=189,line=LINE,attempts=attempts,model=group)))
        if len(group['boards'])>=3:
            assert len(group['boards'])==len({b['flop'] for b in group['boards']})<=5
            (EVIDENCE/'reverified/rank189.json').write_bytes(json_bytes(group))
            Path('data/nl2_hu_b513_locked_medium.json').write_bytes(json_bytes(medium))
    print([(f,sum(bool(n.get('shared_unpaired_turn_draws')) for n in obs.values())) for f,obs in attempts.items() if isinstance(obs,dict)])


if __name__=='__main__':
    main()
