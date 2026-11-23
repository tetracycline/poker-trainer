"""Replay the BB caller's exact river rows after a half-pot flop call and turn stab."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b514_turn_stab import rates
from hu_b536_sb_barrels import COLUMNS
from hu_b568_caller_rivers import conditional_source, rendered
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

DATA = Path('data')
MODEL = 'ln-ipc-r_model-ugjjw9'
LINE = 'b50 c/x b50 c/x'


def root_job(flop, turns, pipeline):
    job = pipeline.make_job('SB_BB', 'gto', flop, 'result.json', iters=1700, target=.5, compress=True,
        extract=[dict(prefix=[], street=True)] + [dict(prefix=['b50','c',t], street=False, raw=True) for t in turns])
    job.update(flop_oop='50%', flop_ip='50%')
    return job


def load_root(spec, package, pipeline):
    flop = spec['flop']
    source = json.loads(package.read('root.json'))
    job = root_job(flop, spec['root_turns'], pipeline)
    assert job == json.loads(package.read('root.job.json'))
    if 'prior_root_package' in spec:
        prior = EVIDENCE / spec['prior_root_package']
        assert sha(prior.read_bytes()) == spec['prior_root_sha256']
        with ZipFile(prior) as old:
            assert old.read('flop.json') == package.read('root.json')
            assert json.loads(old.read('flop.job.json')) == job
    assert (source['flop'],source['pot'],source['stack']) == (flop,600,9700)
    assert 0 <= source['info']['gto_expl_pct'] <= .5 and not source['info'].get('lock_stats')
    return source


def make_jobs(root, spec, pool, pipeline):
    turn, rivers = spec['turn'],spec['river_extracts']
    assert turn in spec['root_turns'] and spec['river'] in rivers
    node, = (n for n in root['nodes'] if n['line']=='b50 c/' and n['board'][-2:]==turn)
    assert (node['pot'],node['bets'])==(1200,[300,300])
    assert not set(rivers) & {node['board'][i:i+2] for i in range(0,8,2)}
    job = pipeline.make_job('SB_BB','gto',root['flop'],'gto.json',iters=2000,target=.45,rank=.45,compress=False)
    job.update(pipeline.SUB)
    ip, oop = spec['turn_ip'], spec['turn_oop']
    assert (ip,oop) in [('50%','50%,100%'),('33%,50%,75%,100%','33%,50%,75%,100%')]
    job.update(oop='',ip='',turn=turn,pot=1200,stack=9400,line0=['b50','c','/'],root_no_bet=False,
        turn_ip=ip,turn_oop=oop,extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','b50','c',r],street=True) for r in rivers])
    for seat,key in enumerate(('oop_w','ip_w')):
        job[key] = [[h,w] for h,w in zip(root['hands'][seat],node['wr'][seat],strict=True) if w>1e-4]
    locked,meta = prepare_job(dict(source=dict(version='gto',manifest=dict(spot='SB_BB'),root=root),job=job),'exp_ip',pool,pipeline)
    return (job,locked),meta,node['board']+spec['river']


def observations(s, public, route, masks=None):
    game,root = s['subgame'],s['root']
    def node(line,seat,board):
        result,=(n for n in game['nodes'] if (n['line'],n['player'],n['board'])==(line,seat,board))
        return result
    for line,seat,board,pot,bets,action in [
        ('b50 c/',0,public[:8],1200,[0,0],'x'),
        ('b50 c/x',1,public[:8],1200,[0,0],'b50'),
        ('b50 c/x b50',0,public[:8],1800,[0,600],'c'),
        ('b50 c/x b50 c/',0,public,2400,[600,600],'x'),
        (LINE,1,public,2400,[600,600],'b50')]:
        target=node(line,seat,board)
        assert (target['pot'],target['bets'])==(pot,bets) and action in target['acts']
    if masks is None:
        masks = game_reach(root, game)[0]
    row = proof(root, game, target, masks)
    assert row['compatible_hole_card_pairs'] >= row['strict_legal_combos'] >= 0
    row.update(version=s['version'],spot='SB_BB',family='SRP',flop=root['flop'],turn=game['turn'],
        source_run_id=s['run'],source_sha256=s['source_sha256'],archive_sha256=s['archive_sha256'],
        root_sha256=sha(compact(root)),gto_gap_pct=game['info']['gto_expl_pct'],locked_hero_gap_pct=game['info'].get('hero_gap_pct'),
        lock_scope=lock_scope(game,s['manifest']['locks'],s['version']),root_applied_rust_lock_nodes=0,
        subgame_applied_rust_lock_nodes=sum(stat['nodes'] for stat in s['applied_rust_rates'].values()))
    return row,rendered(s,row,target,route)


def native_check(package, spec, driver):
    with tempfile.TemporaryDirectory() as tmp:
        dest=Path(tmp)
        cases=[('gto.job.json','gto.json',1),('native.job.json','native.json',1)]
        if 'prior_root_package' not in spec:
            cases.insert(0,('root.job.json','root.json',2))
        for name,output,threads in cases:
            job=json.loads(package.read(name))
            (dest/name).write_bytes(compact(job))
            subprocess.run([str(driver),name],cwd=dest,env=dict(os.environ,RAYON_NUM_THREADS=str(threads)),check=True)
            expected=json.loads(package.read(output)); observed=json.loads((dest/job['out']).read_bytes())
            for d in (expected,observed): del d['info']['secs']
            assert expected==observed,(spec['flop'],name)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--solver', type=Path, required=True)
    cli.add_argument('--run', type=int)
    cli.add_argument('--out', type=Path)
    cli.add_argument('--reproduce-flop')
    cli.add_argument('--search-flop')
    cli.add_argument('--search-results', type=Path)
    args = cli.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    inputs=json.loads((DATA/'nl2_hu_b620_rank127_inputs.json').read_bytes())
    if args.reproduce_flop:
        spec,=(s for s in inputs if s['flop']==args.reproduce_flop)
        archive=EVIDENCE/spec['archive']
        assert sha(archive.read_bytes())==spec['sha256']
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
        with ZipFile(archive) as pkg: native_check(pkg,spec,solver/'postflop/pfdriver/target/release/pfdriver')
        return
    py=solver/'postflop/py'
    assert sha((py/'pipeline.py').read_bytes())==PIPELINE and sha((py/'ranges.py').read_bytes())==RANGES
    sys.path.insert(0, str(py))
    import pipeline
    poolfile = (solver / 'inputs/pool_stats.json').read_bytes()
    assert sha(poolfile) == POOL
    pool=json.loads(poolfile)['NL2']
    view=json.loads(subprocess.check_output(['node','tools/hu_b620_rank127_routes.cjs']))['127']
    route={key:{t+':'+str(COLUMNS[c]):label for t,cells in stage.items() for c,label in cells.items()}
           for key,stage in zip(('flop','turn','river'),view['stages'],strict=True)}
    if args.search_flop:
        assert args.search_results is not None and args.run and args.run>0
        from hu_b620_rank127_search import search
        search(args.search_flop, args.search_results, solver, args.run, route, pool, pipeline)
        return
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],view['id'])==(127,'SB_BB',MODEL)
    assert abs((88/24)/model['assumed_model_node_spr']-1)<=.05 and view['spr']==model['assumed_model_node_spr']
    assert len({suit_isomorphism_class(s['flop']) for s in inputs})==len(inputs)
    group=dict(rank=127,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B620_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    checks=[]
    for spec in inputs:
        archive = EVIDENCE / spec['archive']
        assert sha(archive.read_bytes()) == spec['sha256']
        sources = []
        with ZipFile(archive) as pkg:
            root=load_root(spec,pkg,pipeline)
            jobs,meta,public=make_jobs(root,spec,pool,pipeline)
            for filename,job,mode in zip(('gto','native'),jobs,('gto','exp_ip'),strict=True):
                assert json.loads(pkg.read(filename+'.job.json'))==job
                source=conditional_source(root,pkg.read(filename+'.json'),job,meta if mode=='exp_ip' else [],
                    mode,args.run,pool,spec['river_extracts'])
                source.update(archive_code=archive.stem.removeprefix('NL2_'),archive_sha256=spec['sha256'])
                assert 0<=source['subgame']['info']['gto_expl_pct']<=.5
                if mode=='exp_ip':assert 0<=source['subgame']['info']['hero_gap_pct']<=.5
                sources.append(source)
        g,e=sources
        assert g['subgame']['hands']==e['subgame']['hands']
        gr, gh = observations(g, public, route)
        er, eh = observations(e, public, route)
        hands=[]
        for hole in sorted(gh.keys() & eh.keys()):
            left,right=gh[hole].copy(),eh[hole].copy()
            gpolicy,epolicy=left.pop('native'),right.pop('native')
            assert left==right
            hands.append(dict(left,gto=gpolicy,nl2=epolicy))
        assert hands
        checks.append(dict(flop=spec['flop'],public_board=public,common_hands=len(hands),
            compatible_deals=[gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs']],
            nonpolarized_candidates=[gr['b50']['candidate'],er['b50']['candidate']]))
        if not args.run:continue
        board,pin=emit_board(model,g,e,public,LINE,texture(spec['flop']),viewer_code=g['archive_code'])
        origin = spec.get('origin_solve_run_id')
        role = 'ORIGINAL_GITHUB_ACTIONS_NATIVE_SOLVE' if origin else 'VERIFICATION_OF_LOCAL_NATIVE_RESULTS'
        board.update(source_run_role=role,origin_solve_run_id=origin,
            restricted_flop_bet_sizes_pct=[50],turn_ip_bet_menu=spec['turn_ip'],turn_oop_bet_menu=spec['turn_oop'])
        lock=board['nl2_locked_variants'][0]
        lock.update(source_run_role=board['source_run_role'],origin_solve_run_id=origin,pool_sha256=POOL,
            variant_label='小盲翻牌半池獲跟；轉河牌按 NL2 分街小盲行動鎖頻',measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
            gto_parent_source_run_id=args.run,gto_parent_source_sha256=sha(compact(root)),applied_street_rates=rates(e),
            viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
        pin.update(rendered_decision_hands=hands,source_run_role=board['source_run_role'])
        group['boards'].append(board)
        group['pins'].append(pin)
        for key, row in [('gto_references', gr), ('references', er)]:
            medium[key][source_key(MODEL, row)] = row
    if args.out:
        args.out.write_bytes(json_bytes(checks))
    if args.run:
        assert args.run>0 and 3<=len(group['boards'])<=5
        (EVIDENCE/'reverified/rank127.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b620_locked_medium.json').write_bytes(json_bytes(medium))

if __name__=='__main__':
    main()
