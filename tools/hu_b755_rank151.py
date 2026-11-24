"""Extract unreported x b50 c boundaries in three original 100bb LMP roots for CO's river."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_b714_rank255_rivers import DECK, cards
from hu_b723_rank115_limp_rivers import EVIDENCE, load_root
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible

CASES = {'7s5h3d':['2h','9c','Qd'], '7h6d4s':['2c','8d','Kc'], '7h6h4c':['2s','8d','Qc']}
MODEL = 'ln-iso-lmp_r_model-p8a79'
LINE = 'x b50 c/x x/x'
ROUTE = 'tools/hu_b753_rank151_routes.cjs'


def source(flop):
    root, template, pin = load_root(flop)
    name = 'original-flop.job.json' if flop in ('7s5h3d','7h6d4s') else flop+'/root.job.json'
    with ZipFile(EVIDENCE/pin['archive']) as archive:
        original = archive.read(name)
        manifest = json.loads(archive.read('original-manifest.json'))
    assert sha(original) == pin['root_job_sha256']
    job = json.loads(original)
    assert job['flop_oop'] == job['flop_ip'] == '50%'
    assert len(root['nodes']) == {'7s5h3d':11,'7h6d4s':13,'7h6h4c':11}[flop]
    assert all(node['line'] != 'x b50 c/' for node in root['nodes'])
    extracts = [dict(prefix=['x','b50','c',t],street=False,raw=True) for t in CASES[flop]]
    assert all(x['prefix'] != e['prefix'] for x in job['extract'] for e in extracts)
    return root, template, manifest, pin, dict(job,out='result.json',extract=job['extract']+extracts)


def routes(root, turn, route, parent=None):
    f, = {n['board'] for n in root['nodes'] if len(n['board'])==6}
    public = f + turn
    nodes = {n['line']:n for n in root['nodes'] if n['board']==f}
    x, b, c = [nodes[k] for k in ('','x','x b50')]
    assert [(n['player'],n['pot'],n['bets']) for n in (x,b,c)] == [(0,250,[0,0]),(1,250,[0,0]),(0,375,[0,125])]
    bb = accepted(x,root['hands'],'x') & accepted(c,root['hands'],'c')
    co = accepted(b,root['hands'],'b50')
    if parent is not None:
        assert (parent['line'],parent['board'],parent['player'],parent['pot'],parent['bets']) == ('x b50 c/',public,0,500,[125,125])
        live = [{cardkey(h) for h,w in zip(hands,weights,strict=True) if w>1e-4} for hands,weights in zip(root['hands'],parent['wr'],strict=True)]
        bb &= live[0]
        co &= live[1]
    bb = {v for v in bb if cards(public).isdisjoint(v)}
    co = {''.join(h) for h in co if cards(public).isdisjoint(h) and hand_cell(''.join(h),f)[0] in route['flop']
          and hand_cell(''.join(h),public)[0] in route['turn'] and any(set(h).isdisjoint(v) for v in bb)}
    eligible = {}
    for r in DECK:
        if r in cards(public):
            continue
        kept = [h for h in sorted(co) if r not in cards(h) and route['river'].get(hand_cell(h,public+r)[0])=='過'
                and any(cards(h+r).isdisjoint(v) for v in bb)]
        if kept:
            eligible[r]=kept
    options=list(eligible)
    rivers=options if len(options)<=12 else [options[round(i*(len(options)-1)/11)] for i in range(12)]
    examples={}
    for r in rivers:
        h=eligible[r][0]
        v=next(v for v in sorted(bb) if cards(h+r).isdisjoint(v))
        examples[r]=dict(co=h,bb=''.join(v),cells=[hand_cell(h,(public+r)[:length])[0] for length in (6,8,10)])
    return eligible,rivers,dict(two_street_displayed_co=len(co),bb_x_and_call=len(bb),eligible_rivers=len(eligible),
                                selected_rivers=rivers,examples=examples)


def compare_extraction(original, current, turns):
    assert all(current[k]==original[k] for k in ('flop','pot','stack','hands'))
    identity=lambda n:(n['board'],n['line'],n['player'])
    new={identity(n):n for n in current['nodes']}
    assert len(new)==len(current['nodes'])==len(original['nodes'])+len(turns)
    for node in original['nodes']:
        assert new.pop(identity(node))==node,identity(node)
    assert {n['line'] for n in new.values()}=={'x b50 c/'}
    boundaries={n['board'][-2:]:n for n in new.values()}
    assert set(boundaries)==set(turns)
    assert 0<=current['info']['gto_expl_pct']<=.5 and not current['info'].get('lock_stats')
    return boundaries


def observations(root, sub, turn, rivers, allowed, route, contract):
    sub.update(line0='x b50 c',turn=turn,rivers=rivers)
    masks=game_reach(root,sub)[0]
    rows={}
    for n in sub['nodes']:
        if n['line']!=LINE:
            continue
        public=n['board']
        assert (n['player'],n['pot'],n['bets'],public[6:8],cards(public[:6]))==(1,500,[0,0],turn,cards(root['flop']))
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
        row=proof(root,sub,n,masks)
        x=1<<n['acts'].index('x')
        kept=[]
        for h,bits in zip(sub['hands'][1],base64.b64decode(row['compatible_action_mask_b64'],validate=True),strict=True):
            hand=''.join(cardkey(h))
            if bits & x and hand in allowed[public[-2:]]:
                assert route['river'][hand_cell(hand,public)[0]]=='過'
                kept.append(hand)
        rows[public]=dict(reach=row,displayed_hands=sorted(kept))
    assert len(rows)==len(rivers) and {b[-2:] for b in rows}==set(rivers)
    return rows


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve()
    def head(path):
        return subprocess.check_output(['git','-C',path,'rev-parse','HEAD'],text=True).strip()
    assert head(solver)==SOLVER
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert head(solver/'postflop/postflop-solver')==RUST
    py=solver/'postflop/py'
    assert (sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(PIPELINE,RANGES)
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL
    sys.path.insert(0,str(py))
    import pipeline
    pool=json.loads(poolraw)['NL2']
    raw=a.routes.read_bytes()
    route=json.loads(raw)
    assert (route['model_id'],route['actor'],route['line'],route['model_spr'])==(MODEL,1,LINE,19.55)
    registry=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (registry['frequency_rank'],registry['solver_profile'],registry['assumed_model_node_spr'])==(151,'LMP_CO_BB',19.55)
    assert len({suit_isomorphism_class(f) for f in CASES})==3
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    old,template,manifest,pin,root_job=source(a.flop)
    turns=CASES[a.flop]
    static={t:routes(old,t,route)[2] for t in turns}
    assert all(t['examples'] for t in static.values())
    if a.preflight:
        print(json.dumps(dict(flop=a.flop,old_nodes=len(old['nodes']),native_half_pot_only=True,static=static)))
        return
    out=a.output
    if a.driver:
        assert not out.exists() or not any(out.iterdir())
    else:
        assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True)
    (out/'rendered-routes.json').write_bytes(raw)
    root=solve(out/'flop',root_job,a.driver)
    boundaries=compare_extraction(old,root,turns)
    report=dict(schema='NL2_B755_R151_REUSED_RESTRICTED_FLOP_ROOTS_V1',rank=151,model_id=MODEL,actor=1,line=LINE,flop=a.flop,
                source=pin,original_fully_compared_nodes=len(old['nodes']),original_nodes_sha256=sha(compact(old['nodes'])),
                flop_bet_menu='50% only for BB and CO',source_preflop='ASSUMED_EXPLICIT_169CLASS',model_and_native_spr=19.55,
                solver=SOLVER,rust=RUST,pool_sha256=POOL,solver_ranges_sha256=RANGES,solver_pipeline_sha256=PIPELINE,
                canonical_frozen_flop_sha256=sha(compact(root)),root_sha256=sha((out/'flop/result.json').read_bytes()),
                root_job_sha256=sha((out/'flop/job.json').read_bytes()),preregistered_flops=list(CASES),turns=[],
                locked_policy='exp_ip: CO hero against partial BB pool marginals',observed_private_combo_rates=False)
    for turn in turns:
        boundary=boundaries[turn]
        allowed,rivers,gate=routes(root,turn,route,boundary)
        item=dict(turn=turn,gate=gate,boundary_sha256=sha(compact(boundary)),policies={},common={})
        report['turns'].append(item)
        if not rivers:
            continue
        job=dict(template,flop=a.flop,turn=turn,line0=['x','b50','c','/'],root_no_bet=False,oop='',ip='',pot=500,stack=9775,
                 turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',
                 river_donk='50%,75%,100%',iters=2200,target_pct=.45,rank_pct=.45,compress=False,out='result.json',
                 extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
        for seat,k in enumerate(('oop_w','ip_w')):
            job[k]=[[h,w] for h,w in zip(root['hands'][seat],boundary['wr'][seat],strict=True) if w>1e-4]
        assert job['oop_w'] and job['ip_w'] and (job['rake_rate'],job['rake_cap'])==(.05,1000)
        for mode in ('gto','exp_ip'):
            applied=None
            if mode=='exp_ip':
                target,rules=prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=job),mode,pool,pipeline)
                target['out']='result.json'
                assert target['hero']==1 and target['locks']
            else:
                target=job
            folder=out/(turn+'-'+mode)
            game=solve(folder,target,a.driver)
            assert (game['flop'],game['pot'],game['stack'])==(a.flop,500,9775) and 0<=game['info']['gto_expl_pct']<=.5
            if mode=='exp_ip':
                assert 0<=game['info']['hero_gap_pct']<=.5
                applied=audit_patterns(game,target,dict(locks=rules),pool,hero_seat=1)
                assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
            else:
                assert not game['info'].get('lock_stats') and not target.get('locks')
            rows=observations(root,game,turn,rivers,allowed,route,contract)
            item['policies'][mode]=dict(source_sha256=sha((folder/'result.json').read_bytes()),job_sha256=sha((folder/'job.json').read_bytes()),
                                        measured_lock_application=applied,boards=rows)
            if mode=='gto' and not any(v['displayed_hands'] for v in rows.values()):
                break
        if 'exp_ip' in item['policies']:
            for public,g in item['policies']['gto']['boards'].items():
                e=item['policies']['exp_ip']['boards'][public]
                common=sorted(set(g['displayed_hands'])&set(e['displayed_hands']))
                if common:
                    item['common'][public]=common
        if item['common']:
            break
    report['positive_distinct_flops']=int(any(t['common'] for t in report['turns']))
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps(dict(flop=a.flop,positive=report['positive_distinct_flops'],root_old_nodes=len(old['nodes']))))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','routes','output'):
        cli.add_argument('--'+k,type=Path,required=True)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
