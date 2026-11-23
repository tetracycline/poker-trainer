"""Refit cross-street opponent marginals once per identical original subgame and audit each named decision."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b485_locked_medium import check_job, read_game
from hu_b504_root_only_locks import REGISTRY, exact_observation, register, solve_or_replay, write
from hu_board_reach_corrections import read_replays, source_key
from hu_multiboard_promote import FAM_ROOT
from hu_sequential_cfr_reach import game_reach

PINS = Path('data/nl2_hu_b521_originals.json')
SCOPES = Path('data/nl2_hu_b475_verified_lock_scope.json')


def original(directory, pin, ranges):
    aid,flop,line,turn = (pin[k] for k in ('artifact_id','flop','line','turn'))
    p = directory/f'{aid}.zip'
    assert sha(p.read_bytes()) == pin['zip_sha256']
    with ZipFile(p) as archive:
        assert {SOLVER,RUST} <= {archive.read(n).decode().strip() for n in archive.namelist() if n.startswith('evidence/') and n.endswith('.txt')}
        mf, = (n for n in archive.namelist() if n.startswith('evidence/') and n.endswith('.json'))
        m = json.loads(archive.read(mf))
        assert (m['schema'],m['spot'],m['version'],m['flop'],m['pot_family']) == ('NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',pin['spot'],pin['version'],flop,'SRP')
        assert (m['solver_pin'],m['solver_ranges_sha256'],m['pool_source_sha256']) == (PIPELINE,RANGES,POOL)
        assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and not m['failures']
        c, = (c for c in m['cases'] if c['source_sha256']==pin['source_sha256'])
        assert (c['line'],c['turn'])==(line,turn)
        rootraw = archive.read('solver/postflop/'+m['file_flop'])
        root, rjob = read_game(archive,m['file_flop'],m['file_flop_sha256'])
        sub, job = read_game(archive,c['source_path'],c['source_sha256'])
    version,spot = pin['version'],pin['spot']
    assert (root['pot']/100,root['stack']/100)==FAM_ROOT[spot] and root['flop']==flop
    assert [rjob['oop'],rjob['ip']]==[ranges.to_str(w) for w in ranges.ranges(spot,version)]
    assert job['locks']==rjob['locks'] and [r['pat'] for r in job['locks']]==[r['pat'] for r in m['locks']]
    for g,j in ((root,rjob),(sub,job)):
        check_job(j,g,version,rjob['locks'])
        assert g['info']['lock_stats'] and 0<=g['info']['gto_expl_pct']<=.5
    assert (sub['line0'],sub['turn'],job['line0'])==(line,turn,[*line.split(),'/'])
    parent, = (n for n in root['nodes'] if n['line']==line+'/' and n['board'].endswith(turn))
    assert (parent['pot'],root['stack']-max(parent['bets']))==(sub['pot'],sub['stack'])
    for seat,weights in enumerate(('oop_w','ip_w')):
        assert job[weights]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    return dict(run=pin['run'],id=aid,archive_sha256=pin['zip_sha256'],source_sha256=c['source_sha256'],root_sha256=m['file_flop_sha256'],
                root=root,rootraw=rootraw,sub=sub,job=job,version=version,spot=spot,flop=flop,turn=turn,line=line)


def targets(pin,old,models,refs,gtos):
    masks = game_reach(old['root'],old['sub'])[0]
    matched = []
    for target in pin['targets']:
        model = models[target['model_id']]
        assert model['frequency_rank']==target['rank'] and model['label']=='CERT-MULTIBOARD'
        b, = (b for b in model['certified_3_to_5_exact_flop_boards'] if (b['public_board'],b['actual_exact_action_line'],b['acting_seat'])
              == (target['public_board'],target['line'],target['actor']))
        assert (b['flop'],b['turn'],b['exact_flop_action']) == (old['flop'],old['turn'],old['line'])
        assert ('exp_ip' if b['acting_seat'] else 'exp_oop')==old['version']
        v, = (v for v in b['nl2_locked_variants'] if (v['run_id'],v['sha256']) == (old['run'],old['source_sha256']))
        identity = dict(public_board=b['public_board'],line=b['actual_exact_action_line'],acting_seat=b['acting_seat'])
        previous = refs[source_key(model['model_id'],dict(identity,source_run_id=v['run_id'],source_sha256=v['sha256']))]
        g = gtos[source_key(model['model_id'],dict(identity,source_run_id=b['source_run_id'],source_sha256=b['source_sha256']))]
        obs = exact_observation(old['root'],old['sub'],b,masks)
        assert g['status']==obs['status']=='POSITIVE_JOINT_REACH' and g['source_actions']==obs['source_actions']
        assert all(previous[k]==value for k,value in obs.items())
        assert previous['archive_sha256']==old['archive_sha256']
        # The original B483 replay predates root digests in report rows. Bind its actual ZIP root again.
        supplement = dict(previous,root_sha256=old['root_sha256'],root_gto_stage_gap_pct=old['root']['info']['gto_expl_pct'],
                          root_locked_hero_gap_pct=old['root']['info']['hero_gap_pct'],
                          root_applied_rust_lock_nodes=sum(s['nodes'] for s in old['root']['info']['lock_stats'].values()),
                          subgame_applied_rust_lock_nodes=sum(s['nodes'] for s in old['sub']['info']['lock_stats'].values()))
        supplement.pop('gto',None)
        matched.append((model,b,supplement))
    return matched


def assumed_turn(old,source,archive,rates):
    if {r['street'] for r in rates}!={3} or not old['job']['root_no_bet'] or old['version']!='exp_oop':
        return None
    sub=source['subgame']
    candidates=[n for n in sub['nodes'] if n['line']==old['line']+'/x' and n['player']==1 and len(n['acts'])>1]
    if not candidates or not any(w>1e-4 for w in candidates[0]['w'][1]):
        return None
    first=next((r for r in archive['locks'] if re.search(r['pat'],candidates[0]['line'])),None)
    if not first or first['pat']!='.*/x$' or first['scope']!='ASSUMED_HISTORY_RATE_OR_SIZE' or first['n']!=0:
        return None
    rule,=(r for r in archive['job']['locks'] if r['pat']==first['pat'])
    actual=sub['info']['lock_stats'][first['pat']]
    assert rule['bet']==.45 and actual['nodes']>0
    return dict(pattern=rule['pat'],bet=rule['bet'],pool_decisions=0,applied_subgame_nodes=actual['nodes'],scope=first['scope'])


def main():
    import gzip
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals',required=True,type=Path)
    parser.add_argument('--solver',required=True,type=Path)
    parser.add_argument('--key')
    parser.add_argument('--run',type=int)
    parser.add_argument('--out',type=Path)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--driver',type=Path)
    mode.add_argument('--replay',type=Path)
    args=parser.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip()==SOLVER
    if args.driver:
        assert args.key and args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',str(solver/'postflop/postflop-solver'),'rev-parse','HEAD'],text=True).strip()==RUST
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL
    pool=json.loads(poolraw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    groups=json.loads(PINS.read_bytes())
    registry=json.loads(REGISTRY.read_bytes())['records']
    scopes=json.loads(SCOPES.read_bytes())['sources']
    _,refs,gtos,_=read_replays()
    reports,observations=[],{}
    if args.driver or args.replay:
        assert args.run>0 and args.out
        out=args.out/'data/solver_evidence'
        out.mkdir(parents=True,exist_ok=True)
    for key,pin in groups.items():
        if args.key and args.key!=key:
            continue
        old=original(args.originals,pin,ranges)
        scope=scopes[f"{old['run']}/{old['source_sha256']}"]
        assert scope['scope']=='CONFIRMED' and scope['evidence'] and pin['source_sha256'].startswith(key)
        selected=targets(pin,old,registry,refs,gtos)
        if not args.driver and not args.replay:
            print(key, len(selected))
            continue
        code='B521_'+key
        if args.replay and not (args.replay/'data/solver_evidence'/f'NL2_{code}.json.gz').exists():
            reports.append(dict(parent_source=key,status='MISSING_COMPLETED_OUTPUT'))
            continue
        source,path,rates=solve_or_replay(args,old,pipeline,pool,out,archive_code=code)
        if args.driver:
            return
        envelope=json.loads(gzip.decompress(path.read_bytes()))
        assumption=assumed_turn(old,source,envelope,rates)
        masks=game_reach(old['root'],source['subgame'])[0]
        for model,board,previous in selected:
            result=register(out,model,board,old,source,path,rates,observations,masks,batch='B521',source_suffix='_'+key,
                            river_only=assumption)
            result.update(parent_source=key,model_id=model['model_id'])
            reports.append(result)
            if result['status']=='REGISTERED':
                observations[source_key(model['model_id'],previous)]=previous
    if args.replay:
        write(args.out/'data/nl2_hu_b521_native_street_locks.json',dict(run=args.run,pool_sha256=POOL,records=reports))
        write(args.out/'data/nl2_hu_b521_locked_medium.json',dict(schema='NL2_HU_B521_ORIGINAL_LOCKED_MEDIUM_V1',references=observations))
    if args.key:
        assert args.key in groups


if __name__=='__main__':
    main()
