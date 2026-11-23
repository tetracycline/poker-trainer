"""Replay full three-street MID reach for BB's checked-to-river 3-bet-pot decision."""
import argparse
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns, original
from hu_b483_locked_medium import POOL, PIPELINE, RANGES
from hu_b502_rank120_native import PINS
from hu_b514_turn_stab import rates
from hu_b562_rank263_continuations import reached, LINE
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, prepare_job, replay_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach

DATA=Path('data')
MODEL='ln-3bp-3b_r_model-1nr3lqx'
HISTORICAL={'Ks7s2s':(14530206356,'9d','4d'), 'KsQh4d':(14592263783,'Tc','3h')}
NEW='Kh7h3h'
RAW_CODE='B570_R263_KH7H3H'
OLD_LOCK_RUN=45107345902


def unpack(path, directory):
    with ZipFile(path) as z:
        for name in z.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
        z.extractall(directory)


def old_pair(folder, flop, pipeline, ranges, pool):
    aid,turn,river=HISTORICAL[flop]
    pin=json.loads(PINS.read_bytes())[str(aid)]
    original_source=load_original(folder,aid,pin,'BB3_BTN',flop,turn,'gto',pot=2050,stack=9000,pipeline=pipeline,ranges=ranges)
    g=original_source['source'];root_sha=original_source['identity']['root_sha256']
    code=f'B502_R120_{flop.upper()}_{turn.upper()}_EXP_OOP'
    blob=EVIDENCE/f'NL2_{code}.json.gz'
    e=replay_native(original_source,'exp_oop',pool,pipeline,blob,OLD_LOCK_RUN,code)
    e['native_job'],_=prepare_job(original_source,'exp_oop',pool,pipeline)
    return g,e,original_source['public']+river,root_sha,original_source['identity']


def new_pair(folder, turn, frozen, run, pipeline, ranges, pool, digest):
    g=original(folder,NEW,turn,'gto',batch='B570',spot='BB3_BTN',flop_line='x x',flop_policy='checkcheck',
               turn_policy='checkcheck',turn_extract='x x',root_pot=2050,root_stack=9000,flop_profile='full',frozen_turns=frozen['turns'])
    m=g['manifest']
    assert (m['solver_pin'],m['solver_ranges_sha256'])==(PIPELINE,RANGES)
    original_job=g['subgame_job']
    assert [g['root_job'][k] for k in ('oop','ip')]==[ranges.to_str(s) for s in ranges.ranges('BB3_BTN','gto')]
    assert original_job['line0']==['x','x','/'] and not original_job['root_no_bet']
    root,sub=g['root'],g['subgame']
    parent,=(n for n in root['nodes'] if n['line']=='x x/' and n['board'].endswith(turn))
    assert parent['bets']==[0,0] and parent['pot']==2050 and sub['rivers']==frozen['rivers'][turn]
    for seat,k in enumerate(('oop_w','ip_w')):
        assert original_job[k]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    g.update(archive_code=RAW_CODE,archive_sha256=digest,run=run)
    job,locks=prepare_job(dict(source=g,job=original_job),'exp_oop',pool,pipeline)
    native=folder/f'NL2-B570-{NEW}-gto/native/{turn}'
    if not native.exists():
        return g,None,parent['board'],g['root_sha256']
    assert (native/'job.json').read_bytes()==compact(job) and (native/'locks.json').read_bytes()==compact(locks)
    raw=(native/'native.json').read_bytes();game=json.loads(raw)
    assert all(game[k]==sub[k] for k in ('hands','flop','stack','pot'))
    game.update({k:sub[k] for k in ('rivers','line0','turn')})
    manifest=dict(m,version='exp_oop',locks=locks,gto_parent_source_run_id=run,gto_parent_source_sha256=g['root_sha256'])
    coverage=audit_patterns(game,job,manifest,pool,hero_seat=0)
    e=dict(version='exp_oop',root=root,root_sha256=g['root_sha256'],subgame=game,manifest=manifest,
           run=run,source_sha256=sha(raw),archive_code=RAW_CODE,archive_sha256=digest,native_job=job,
           verified_gto_parent=dict(run=run,sha256=g['root_sha256']),applied_rust_rates=game['info']['lock_stats'],
           measured_lock_application=coverage)
    return g,e,parent['board'],g['root_sha256']


def policies(s,public,root_sha):
    root,sub=s['root'],s['subgame']
    assert (root['pot'],root['stack'],sub['pot'],sub['stack'])==(2050,9000,2050,9000)
    for game in (root,sub):
        assert 0<=game['info']['gto_expl_pct']<=.5
    if s['version']!='gto':
        assert 0<=sub['info']['hero_gap_pct']<=.5
    for game,board,line,seat in [(root,public[:6],'',0),(root,public[:6],'x',1),
                (sub,public[:8],'x x/',0),(sub,public[:8],'x x/x',1),(sub,public,LINE,0)]:
        n,=(n for n in game['nodes'] if (n['board'],n['line'],n['player'])==(board,line,seat))
        assert n['pot']==2050 and n['bets']==[0,0] and 'x' in n['acts']
    n,=(n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,LINE,0))
    assert 'b50' in n['acts']
    masks=game_reach(root,sub)[0]
    strict=reached(sub,root,public,masks)
    row=audit_decision(s,public,LINE,0,root_sha)
    assert row['compatible_hole_card_pairs']==strict['legal_deals']
    eligible=set(strict['eligible_hands']);hands=sub['hands'][0]
    bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    out={}
    for index,(hole,mask) in enumerate(zip(hands,bits,strict=True)):
        h=''.join(cardkey(hole))
        if h not in eligible:
            continue
        assert mask
        acts=n['acts'];weights=[max(0.,n['strat'][j*len(hands)+index]) for j in range(len(acts))]
        total=sum(weights);assert total>0
        out[h]=dict(accepted_mask=mask,action_order=acts,accepted_actions=[a for j,a in enumerate(acts) if mask&(1<<j)],
                    strategy={a:round(w/total,7) for a,w in zip(acts,weights,strict=True)})
    assert set(out)==eligible
    return row,out


def actual_locks(e,p,pool):
    sub=e['subgame'];masks=game_reach(e['root'],sub)[0]
    out=[]
    for b,line in [(p[:8],'x x/x'),(p,LINE+'b50'),(p,LINE+'x')]:
        n,=(n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(b,line,1))
        first=next(r for r in e['manifest']['locks'] if re.search(r['pat'],line))
        native=next(r for r in e['native_job']['locks'] if re.search(r['pat'],line))
        assert e['native_job']['hero']==0 and native['pat']==first['pat']
        stat=sub['info']['lock_stats'][native['pat']]
        assert stat['nodes']>0
        reach=compatible_node_reach(e['root'],sub,n,masks[f'{b}|{line}|1'])
        row=dict(line=line,source=first['source'],scope=first['scope'],n=first['n'],native_rule=native,
                 compatible_hole_card_pairs=reach['compatible_hole_card_pairs'],applied_pattern_nodes=stat['nodes'],
                 applied_pattern_fold=stat['fold'],applied_pattern_aggressive=stat['agg'])
        if line.endswith('b50'):
            assert n['bets']==[1025,0] and n['pot']==3075
            metric=pool['HU_facing_bet']['3']['by_size']['34-55%']
            assert first['source']=='NL2.HU_facing_bet[3].by_size[34-55%]' and first['n']==metric['n']
            assert native['fold']==metric['fold']/100 and native['raise']==metric['raise']/100
        else:
            assert first['n']==0 and first['scope']=='ASSUMED_HISTORY_RATE_OR_SIZE' and native['bet']==.45
        out.append(row)
    return out


def audit(flop,g,e,public,root_sha,identity,model,group,medium,pool,publish):
    gr,gh=policies(g,public,root_sha);er,eh=policies(e,public,root_sha)
    common=sorted(gh.keys() & eh.keys())
    first=actual_locks(e,public,pool)
    result=dict(flop=flop,public_board=public,gto_deals=gr['compatible_hole_card_pairs'],nl2_deals=er['compatible_hole_card_pairs'],
                gto_eligible_hands=len(gh),locked_eligible_hands=len(eh),shared_decision_hands=common,
                original_gto_sha256=g['source_sha256'],locked_native_sha256=e['source_sha256'],
                frozen_gto_root_sha256=root_sha,first_matching_opponent_rules=first)
    if not common or not publish:
        return result
    same_run=g['run']==e['run']
    code=f'B570_R263_{flop.upper()}' if same_run else None
    board,pin=emit_board(model,g,e,public,LINE,texture(flop),viewer_code=code)
    from hu_b546_rank70_conditional import current_texture
    witnesses=[dict(hand=h,flop_class='MID',turn_class='MID',river_class='MID',displayed_suggestion='x',
        flop_texture=current_texture(public[:6]),turn_texture=current_texture(public[:8]),river_texture=current_texture(public),
        gto=gh[h],nl2=eh[h]) for h in common]
    pin.update(rendered_decision_hands=witnesses,hands_accepting_displayed_suggestion={
        key:sum(all('x' in w[v]['accepted_actions'] for v in vs) for w in witnesses)
        for key,vs in [('gto',['gto']),('nl2',['nl2']),('both',['gto','nl2'])]},
        authenticated_flop_boundary=identity,original_opponent_rules=first)
    board.update(flop_bet_size_menu=identity['flop_oop_menu'])
    lock=board['nl2_locked_variants'][0]
    lock.update(variant_label='原始翻牌 GTO 範圍，轉河牌採 NL2 分街回應鎖頻',gto_parent_source_run_id=g['run'],
        gto_parent_source_sha256=root_sha,pool_sha256=POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
        applied_street_rates=rates(e),turn_checked_to_bet_assumption=dict(bet=.45,applied_subgame_nodes=first[0]['applied_pattern_nodes']),
        viewer_archive_code=pin.get('locked_viewer_archive_code',pin['viewer_archive_code']),
        viewer_sha256=pin.get('locked_viewer_sha256',pin['viewer_sha256']))
    group['boards'].append(board);group['pins'].append(pin)
    medium['references'][source_key(MODEL,er)]=er;medium['gto_references'][source_key(MODEL,gr)]=gr
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--solver',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--run',type=int,help='Actions import run authenticating the new original')
    args=ap.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline, ranges
    subprocess.run(['node','tools/hu_b570_rank263_rows.cjs'],check=True)
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(263,'BB3_BTN',4.39)
    frozen=json.loads((DATA/'nl2_hu_b570_frozen_flop.json').read_bytes())
    assert frozen['flop']==NEW and frozen['turns']==pipeline.turns_for(NEW)[:2]
    assert frozen['rivers']=={t:pipeline.rivers_for(NEW,t) for t in frozen['turns']}
    group=dict(rank=263,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B570_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    observations=[]
    with TemporaryDirectory() as temp:
        base=Path(temp)
        unpack(EVIDENCE/'NL2_B570_R263_B502_ORIGINALS.zip',base)
        for flop in HISTORICAL:
            g,e,p,root_sha,identity=old_pair(base,flop,pipeline,ranges,pool)
            o=audit(flop,g,e,p,root_sha,identity,model,group,medium,pool,args.run)
            assert o['shared_decision_hands']
            o['selected']=True
            observations.append(o)
        archive=EVIDENCE/f'NL2_{RAW_CODE}.zip'
        rawsha=sha(archive.read_bytes())
        unpack(archive,base/f'NL2-B570-{NEW}-gto')
        selected=False
        for turn in frozen['turns']:
            g,e,public,root_sha=new_pair(base,turn,frozen,args.run,pipeline,ranges,pool,rawsha)
            if e is None:
                assert selected, 'Missing original lock before any eligible named river'
                observations.append(dict(flop=NEW,turn=turn,status='FROZEN_GTO_ONLY_AFTER_PRIOR_SELECTION',
                                         archive_sha256=rawsha,source_sha256=g['source_sha256']))
                continue
            identity=dict(root_sha256=root_sha,full_gto_sha256=g['source_sha256'],raw_archive_sha256=rawsha,
                          flop_oop_menu=g['root_job']['flop_oop'],flop_ip_menu=g['root_job']['flop_ip'])
            for river in frozen['rivers'][turn]:
                o=audit(NEW,g,e,public+river,root_sha,identity,model,group,medium,pool,args.run and not selected)
                if not selected and o['shared_decision_hands']:
                    selected=True
                    o['selected']=True
                observations.append(o)
    selected_flops={o['flop'] for o in observations if o.get('selected')}
    if args.run and len(selected_flops)>=3:
        assert len(group['boards'])==len(selected_flops)==3
        (EVIDENCE/'reverified/rank263.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b570_locked_medium.json').write_bytes(json_bytes(medium))
    args.out.write_bytes(json_bytes(dict(schema='NL2_HU_B570_BB3_RIVER_MID_V1',source_import_run=args.run,
        sampled_distinct_flops=len(selected_flops),new_selection='FIRST_FROZEN_REACHABLE_RIVER',observations=observations)))


if __name__=='__main__':
    main()
