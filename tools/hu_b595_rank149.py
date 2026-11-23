"""Recover UTG's exact check-through river policies, including both original B51 sources."""
import argparse
import gzip
import json
import re
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import board_row
from hu_b581_checked_rivers import RUST, SOLVER, policy_hands
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach, compatible_node_reach
from solve_hu_missing_branches import EXTRA_SPOTS

DATA = Path('data')
MODEL = 'ln-opfr-r_model-142idcm'
LINE = 'x x/x x/'
TURN_MENU = {'8c6d4h':['Ts','9c','3s','Jd'], '9d7s4h':['Tc','Jc','5s','8h'], 'Js8d4c':['Ts','6c','Qd','2h']}


def fresh_pair(spec, reference, old_job, pool, pipeline, run):
    flop, turn, river = (spec[k] for k in ('flop','turn','river'))
    file = EVIDENCE / spec['archive']
    assert sha(file.read_bytes()) == spec['sha256']
    with ZipFile(file) as z:
        root = json.loads(z.read('root.json'))
        root_job = dict(reference['root_job'],flop=flop,out='result.json',
                        extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',t],street=False,raw=True) for t in TURN_MENU[flop]])
        assert root_job == json.loads(z.read('root.job.json'))
        assert (root['flop'],root['pot'],root['stack']) == (flop,650,9750)
        assert 0 <= root['info']['gto_expl_pct'] <= .5 and not root['info'].get('lock_stats')
        root_sha = sha(compact(root))
        boundary, = (n for n in root['nodes'] if n['line']=='x x/' and n['board'].endswith(turn))
        assert boundary['pot']==650 and boundary['bets']==[0,0]
        gto = dict(old_job,flop=flop,turn=turn,iters=2200,target_pct=.4,rank_pct=.4,out='result.json',
                   extract=[dict(prefix=[],street=True),dict(prefix=['x','x',river],street=True)])
        for seat,key in enumerate(('oop_w','ip_w')):
            gto[key] = [[h,w] for h,w in zip(root['hands'][seat],boundary['wr'][seat],strict=True) if w>1e-4]
        assert gto['line0']==['x','x','/'] and (gto['pot'],gto['stack'])==(650,9750)
        base = dict(version='gto',root=root,manifest=dict(spot='UTG_CO',pot_family='SRP',locks=[]))
        locked,meta = prepare_job(dict(source=base,job=gto),'exp_oop',pool,pipeline)
        locked.update(iters=2200,target_pct=.4,rank_pct=.4,out='result.json')
        pair = []
        for mode,job in [('gto',gto),('exp_oop',locked)]:
            assert json.loads(z.read(mode+'.job.json'))==job
            raw=z.read(mode+'.json')
            sub=json.loads(raw)
            assert (sub['flop'],sub['pot'],sub['stack'])==(flop,650,9750)
            assert 0<=sub['info']['gto_expl_pct']<=.5
            sub.update(line0='x x',turn=turn,rivers=[river])
            s=dict(base,manifest=dict(base['manifest']),version=mode,root_sha256=root_sha,subgame=sub,native_job=job,
                   archive_code=file.stem.removeprefix('NL2_'),archive_sha256=spec['sha256'],source_sha256=sha(raw),run=run)
            if mode=='exp_oop':
                assert 0<=sub['info']['hero_gap_pct']<=.5 and sub['hands']==pair[0]['subgame']['hands']
                s['manifest'].update(locks=meta,gto_parent_source_run_id=run,gto_parent_source_sha256=root_sha)
                s['verified_gto_parent']=dict(run=run,sha256=root_sha)
                s['measured_lock_application']=audit_patterns(sub,job,s['manifest'],pool,hero_seat=0)
                s['applied_rust_rates']=sub['info']['lock_stats']
            else:
                assert not sub['info'].get('lock_stats')
            pair.append(s)
    return boundary['board']+river,pair


def witnesses(pair, public, route):
    rows = [audit_decision(s,public,LINE,0,s['root_sha256']) for s in pair]
    assert all(r and r['compatible_hole_card_pairs']>0 and r['b50'] is not None for r in rows)
    hands = [policy_hands(s,r,route) for s,r in zip(pair,rows,strict=True)]
    witnesses = []
    for hole in sorted(hands[0].keys()&hands[1].keys()):
        g,e=[h[hole] for h in hands]
        assert g['classes']==e['classes']
        f,t,r=g['classes']
        witnesses.append(dict(hand=hole,flop_class=f,turn_class=t,river_class=r,flop_texture=board_row(public[:6]),
                              turn_texture=board_row(public[:8]),river_texture=board_row(public),displayed_suggestion='過',
                              gto=g['policy'],nl2=e['policy']))
    return rows,witnesses


def half_pot_reply(s, public, pool):
    sub=s['subgame']
    line=LINE+'b50'
    n,=(n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,line,1))
    assert (n['pot'],n['bets'])==(975,[325,0])
    rule=next(r for r in s['native_job']['locks'] if re.search(r['pat'],line))
    meta=next(r for r in s['manifest']['locks'] if re.search(r['pat'],line))
    assert meta['pat']==rule['pat'] and sub['info']['lock_stats'][rule['pat']]['nodes']>0
    if s.get('verified_gto_parent'):
        original=pool['HU_facing_bet']['3']['by_size']['34-55%']
        assert meta['n']==original['n'] and rule['fold']==original['fold']/100 and rule['raise']==original['raise']/100
    mask=game_reach(s['root'],sub)[0][f'{public}|{line}|1']
    pairs=compatible_node_reach(s['root'],sub,n,mask)['compatible_hole_card_pairs']
    return dict(board=public,line=line,first_rule=rule,opponent_source=meta,compatible_hole_card_pairs=pairs)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--originals',type=Path,required=True)
    parser.add_argument('--run',type=int)
    args=parser.parse_args()
    assert args.run is None or args.run>0
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    assert sha((solver/'postflop/py/ranges.py').read_bytes())==RANGES and sha((solver/'postflop/py/pipeline.py').read_bytes())==PIPELINE
    raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw)==POOL
    pool=json.loads(raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pipeline.SPOTS.update(EXTRA_SPOTS)
    route=json.loads(subprocess.check_output(['node','tools/hu_b595_rank149_routes.cjs']))['149']
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(149,'UTG_CO',15)
    receipt=json.loads((DATA/'nl2_hu_b575_turn_inputs.json').read_bytes())['originals']
    old=[]
    for mode,aid in [('gto',14664258709),('exp_oop',14664239001)]:
        original=load_original(args.originals,aid,receipt[str(aid)],'UTG_CO','9s6h3d','Ts',mode,
                               pot=650,stack=9750,pipeline=pipeline,ranges=ranges)
        s=original['source']
        s.update(root_sha256=original['identity']['root_sha256'],native_job=original['job'])
        old.append(s)
    assert not witnesses(old,'3d6h9sTsJs',route)[1]
    boards=[('3d6h9sTs7c',old,False)]
    reference=json.loads(gzip.decompress((EVIDENCE/'NL2_B538_JH9S4C_QC_45119866932.json.gz').read_bytes()))['source_arrays'][0]
    assert tuple(reference['root_job'][k] for k in ('oop','ip'))==tuple(ranges.to_str(r) for r in ranges.ranges('UTG_CO','gto'))
    inputs=json.loads((DATA/'nl2_hu_b595_rank149_inputs.json').read_bytes())
    assert (inputs['solver'],inputs['rust'])==(SOLVER,RUST) and set(TURN_MENU)=={b['flop'] for b in inputs['boards']}
    for spec in inputs['boards']:
        public,pair=fresh_pair(spec,reference,old[0]['native_job'],pool,pipeline,args.run)
        boards.append((public,pair,True))
    group=dict(rank=149,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B595_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for public,pair,fresh in boards:
        g,e=pair
        (gr,er),hands=witnesses(pair,public,route)
        assert hands
        response=half_pot_reply(e,public,pool)
        if args.run is None:
            print(public,len(hands),response['compatible_hole_card_pairs'],er['b50']['candidate'])
            continue
        board,pin=emit_board(model,g,e,public,LINE,texture(g['root']['flop']),viewer_code='B595_R149_'+g['root']['flop'].upper())
        lock=board['nl2_locked_variants'][0]
        if fresh:
            board.update(source_run_role='VERIFICATION_OF_LOCAL_NATIVE_RESULTS',origin_solve_run_id=None,restricted_flop_bet_sizes_pct=[50])
            lock.update(source_run_role=board['source_run_role'],origin_solve_run_id=None,pool_sha256=POOL,
                        variant_label='翻牌 GTO 範圍，轉河牌依 NL2 下注頻率鎖定對手',gto_parent_source_run_id=args.run,
                        gto_parent_source_sha256=g['root_sha256'],applied_street_rates=rates(e),measurement_policy='STREET_SPECIFIC_POOL_MARGINALS')
            pin.update(source_run_role='GITHUB_ACTIONS_AUTHENTICATED_LOCAL_NATIVE_IMPORT')
        else:
            pin['original_artifact_ids']=[14664258709,14664239001]
            pin['replaced_named_river']=dict(public_board='3d6h9sTsJs',shared_rendered_hands=0)
        lock.update(viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
        agreement={k:sum(all('x' in h[v]['accepted_actions'] for v in modes) for h in hands)
                   for k,modes in [('gto',('gto',)),('nl2',('nl2',)),('both',('gto','nl2'))]}
        pin.update(rendered_decision_hands=hands,hands_accepting_displayed_suggestion=agreement,original_opponent_rules=[response])
        print(public,len(hands),agreement['both'],response['compatible_hole_card_pairs'],er['b50']['candidate'])
        group['boards'].append(board)
        group['pins'].append(pin)
        medium['gto_references'][source_key(MODEL,gr)]=gr
        medium['references'][source_key(MODEL,er)]=er
    if args.run is None:
        return
    assert len({b['flop'] for b in group['boards']})==4
    (EVIDENCE/'reverified/rank149.json').write_bytes(json_bytes(group))
    (DATA/'nl2_hu_b595_locked_medium.json').write_bytes(json_bytes(medium))


if __name__=='__main__':
    main()
