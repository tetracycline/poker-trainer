"""Recover the checked branches of three pinned SB3_BTN originals and test rank230's displayed middle pairs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b727_rank229 as native
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b676_checked_rivers import MODELS
from hu_trainer_route_gate import compatible

MODEL=MODELS[230]
WORKER='tools/hu_b782_rank230_mid_pairs.py'
ROUTE='tools/hu_b676_checked_routes.cjs'
SPEC={'Th9h7c':(699,{'2s':29,'5d':29,'6c':23}),
      'Ts8s7h':(699,{'2d':25,'5c':25,'6h':23}),
      'Ts9s6h':(695,{'2d':23,'5c':23,'8h':20})}
WORKERS={695:'4c711486fb045c96cf1aa52dfbeafe605ea41ba7',699:'4697ff7892178c6f3ebd0f82e08c2d31b9e9023c'}
ROOTS={'Th9h7c':'4b73e863b8dc856562dde9e574eba0ba37c108c24713ee526b99ae239571d0d5','Ts8s7h':'08f09182e597e4312a22dc769f57aec4df7b788ab684f2a8a11cc04e31eb4432','Ts9s6h':'2c29976968bb83969345e439a789908ad6a0ada6c78ee4484b4c42b0db650617'}
MENU='33%,50%,75%'


def blob(path):
    return subprocess.check_output(['git','hash-object',path],text=True).strip()


def original(flop,ranges):
    batch,turns=SPEC[flop];workers=Path(f'data/nl2_hu_b{batch}_rank84_workers.json');assert blob(workers)==WORKERS[batch]
    pin,=[x for x in json.loads(workers.read_bytes()) if x['flop']==flop]
    path=Path('data/solver_evidence')/f'NL2_B{batch}_R84_{flop.upper()}.zip';assert sha(path.read_bytes())==pin['sha256']
    with ZipFile(path) as z:
        proof=json.loads(z.read('proof.json'));job_raw=z.read('flop/job.json');source_raw=z.read('flop/result.json')
        assert sha(job_raw)==proof['root_job_sha256'] and sha(source_raw)==proof['root_sha256']==ROOTS[flop]
        assert (proof['flop'],proof['solver'],proof['rust'])==(flop,native.SOLVER,native.RUST)
    root=json.loads(source_raw);job=json.loads(job_raw)
    assert (root['flop'],root['pot'],root['stack'])==(flop,2100,9000) and len(root['nodes'])==14
    assert root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    assert (job['flop_oop'],job['flop_ip'],job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==('33%','33%',2100,9000,.05,1000)
    assert (job['oop'],job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('SB3_BTN','gto')) and not job.get('locks')
    assert not any(n['line']=='x x/' for n in root['nodes'])
    extra=[dict(prefix=['x','x',turn],street=False,raw=True) for turn in turns]
    assert all(e['prefix']!=j['prefix'] for e in extra for j in job['extract'])
    return root,dict(job,extract=job['extract']+extra),dict(worker=pin,original_archive=path.name,root_result_sha256=ROOTS[flop],
        root_job_sha256=sha(job_raw),original_nodes_sha256=sha(compact(root['nodes'])),original_nodes=len(root['nodes']))


def root_hands(root,turn,route,boundary=None):
    nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6};pub=nodes['']['board']+turn
    assert native.public_cards(pub[:6])==native.public_cards(root['flop'])
    seats=[]
    for i,line in enumerate(('','x')):
        n=nodes[line];assert (n['player'],n['pot'],n['bets'])==(i,2100,[0,0])
        check={h for h in native.accepted(n,root['hands'],'x') if native.public_cards(pub).isdisjoint(h)}
        if boundary:
            assert (boundary['board'],boundary['line'],boundary['player'],boundary['pot'],boundary['bets'])==(pub,'x x/',0,2100,[0,0])
            live={native.cardkey(h) for h,w in zip(root['hands'][i],boundary['wr'][i],strict=True) if w>1e-4}
            check &= live
        seats.append(check)
    heroes={h for h in seats[0] if all(native.hand_cell(''.join(h),pub[:n])[0] in route[k] for n,k in ((6,'flop'),(8,'turn')))
            and any(set(h).isdisjoint(v) for v in seats[1])}
    return heroes,seats[1]


def exact_root(old,new,flop):
    assert (old['flop'],old['pot'],old['stack'],old['hands'])==(new['flop'],new['pot'],new['stack'],new['hands'])
    assert old['info']['gto_iters']==new['info']['gto_iters'] and old['info']['gto_expl_pct']==new['info']['gto_expl_pct']
    assert not new['info'].get('lock_stats')
    nodes={(n['board'],n['line'],n['player']):n for n in new['nodes']}
    assert len(nodes)==len(new['nodes'])==len(old['nodes'])+len(SPEC[flop][1])
    for n in old['nodes']:assert nodes.pop((n['board'],n['line'],n['player']))==n
    assert all(n['line']=='x x/' and n['player']==0 and len(n['wr'])==2 for n in nodes.values())
    out={n['board'][6:]:n for n in nodes.values()};assert set(out)==set(SPEC[flop][1])
    return out


def decisions(root,game,turn,rivers,route,heroes,foes,first):
    rows=native.observations(root,game,turn,rivers,route)
    tn={n['line']:n for n in game['nodes'] if len(n['board'])==8}
    sb=heroes & native.accepted(tn['x x/'],game['hands'],'x')
    btn=foes & native.accepted(tn['x x/x'],game['hands'],'x')
    paired={}
    for node in game['nodes']:
        if node['line']!=native.LINE:continue
        public=node['board'];row=rows[public];assert node['player']==0
        sb_live={native.cardkey(h) for h,w in zip(game['hands'][0],node['w'][0],strict=True) if w>1e-4}
        btn_live={native.cardkey(h) for h,w in zip(game['hands'][1],node['w'][1],strict=True) if w>1e-4}
        active=sb&sb_live&native.accepted(node,game['hands'],'x')
        ready={(''.join(h),''.join(v)) for h in active if ''.join(h) in row['displayed_check_hands'] for v in btn&btn_live
               if native.public_cards(public).isdisjoint(h) and native.public_cards(public+''.join(h)).isdisjoint(v)}
        if first is not None:ready &= first[public]
        selected=sorted({h for h,v in ready});paired[public]=ready
        row['displayed_check_hands']=selected
        row['compatible_btn_witnesses']={h:dict(example=min(v for c,v in ready if c==h),count=sum(c==h for c,v in ready)) for h in selected}
    assert set(paired)==set(rows)
    return rows,paired


def run(a):
    solver=a.solver.resolve();py=solver/'postflop/py'
    rev=lambda d:subprocess.check_output(['git','-C',d,'rev-parse','HEAD'],text=True).strip()
    assert sys.version_info[:2]==(3,11) and rev(solver)==native.SOLVER
    assert blob('tools/hu_b727_rank229.py')=='601385f1ead29779ca5bf30f40237f13abba2c43' and blob(ROUTE)=='522ea33d7326c38a7493507cbde96b5df4a6f3f7'
    assert sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    if a.driver:assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and rev(solver/'postflop/postflop-solver')==native.RUST
    sys.path.insert(0,str(py));import pipeline,ranges
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==native.POOL;pool=json.loads(pool_raw)['NL2']
    raw_route=subprocess.check_output(['node',ROUTE]);route=json.loads(raw_route)['230']
    assert route['model']==MODEL and route['flop']==route['turn']==route['river']=={'low:2':'過','mid_high:2':'過'}
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],contract['seat'],contract['streets'])==(230,'SB3_BTN',0,['x x','x x',''])
    assert abs(90/21/model['assumed_model_node_spr']-1)<.05 and len({suit_isomorphism_class(f) for f in SPEC})==3
    flop=a.flop;old,job,origin=original(flop,ranges);turns=SPEC[flop][1]
    counts={t:len(root_hands(old,t,route)[0]) for t in turns};assert counts==turns,(flop,counts)
    if a.preflight:print(json.dumps(dict(flop=flop,root_ui_hands=counts,original_nodes=origin['original_nodes'])));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True);(out/'rendered-routes.json').write_bytes(raw_route)
    root=native.solve(out/'flop',job,a.driver);assert (out/'flop/job.json').read_bytes()==compact(job)
    boundaries=exact_root(old,root,flop)
    proof=dict(schema='NL2_B782_R230_ORIGINAL_CHECKED_MIDDLE_PAIRS_V1',rank=230,model_id=MODEL,actor=0,spot='SB3_BTN',
               flop=flop,line=native.LINE,source_worker_blob=blob(WORKER),origin=origin,solver=native.SOLVER,rust=native.RUST,pool_sha256=native.POOL,
               root_job_sha256=sha(compact(job)),root_sha256=sha((out/'flop/result.json').read_bytes()),original_flop_reexports=1,
               unchanged_original_nodes=14,new_raw_boundaries={t:sha(compact(b)) for t,b in boundaries.items()},restricted_flop_sizes='33% both seats',
               root_price=[2100,9000],no_observed_per_private_hand_frequency=True,lock_scope='FROZEN_GTO_FLOP_AND_MEASURED_PARTIAL_TURN_RIVER_NL2_MARGINALS',
               preregistered_turns=list(turns),turns=[],selected=None)
    for turn in turns:
        boundary=boundaries[turn];heroes,btn=root_hands(root,turn,route,boundary)
        gate=native.available_rivers(root,turn,route,None);assert gate['compatible_hero_hands']==sorted(''.join(h) for h in heroes)
        rivers=gate['river_extracts'];item=dict(turn=turn,root_gate=gate,preregistered_rivers=rivers,policies={},common={});proof['turns'].append(item)
        if not rivers:continue
        gj=pipeline.make_job('SB3_BTN','gto',flop,'result.json',iters=2400,target=.4,compress=False)
        gj.update(pipeline.SUB);gj.update(oop='',ip='',line0=['x','x','/'],turn=turn,pot=2100,stack=9000,root_no_bet=False,
            turn_oop=MENU,turn_ip=MENU,river_oop='33%,50%,75%,100%,a',river_ip='33%,50%,75%,100%,a',
            extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
        for i,k in enumerate(('oop_w','ip_w')):gj[k]=[[h,w] for h,w in zip(root['hands'][i],boundary['wr'][i],strict=True) if w>1e-4]
        assert gj['oop_w'] and gj['ip_w'] and (gj['rake_rate'],gj['rake_cap'])==(.05,1000)
        before=None
        for ver in ('gto','exp_oop'):
            tar=gj;applied=None
            if ver=='exp_oop':
                tar,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='SB3_BTN')),job=gj),ver,pool,pipeline)
                tar['out']='result.json';assert tar['hero']==0 and tar['locks']
            dest=out/(turn+'-'+ver);game=native.solve(dest,tar,a.driver)
            assert (dest/'job.json').read_bytes()==compact(tar) and (game['flop'],game['pot'],game['stack'])==(flop,2100,9000) and 0<=game['info']['gto_expl_pct']<=.5
            if ver=='exp_oop':
                assert game['hands']==gto_hands and 0<=game['info']['hero_gap_pct']<=.5
                applied=native.audit_patterns(game,tar,dict(spot='SB3_BTN',locks=rules),pool,0)
                assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
            else:
                gto_hands=game['hands'];assert not game['info'].get('lock_stats')
            rows,witnesses=decisions(root,game,turn,rivers,route,heroes,btn,before)
            item['policies'][ver]=dict(source_sha256=sha((dest/'result.json').read_bytes()),job_sha256=sha(compact(tar)),measured_lock_application=applied,boards=rows)
            if ver=='gto':
                before=witnesses
                if not any(witnesses.values()):break
            else:
                item['common']={k:sorted({h for h,v in vs}) for k,vs in sorted(witnesses.items()) if vs}
        if item['common']:
            public=next(iter(item['common']));assert compatible(contract,dict(public_board=public,actual_exact_action_line=native.LINE,acting_seat=0))
            proof['selected']=dict(turn=turn,public_board=public);break
    locked=[b['reach'] for t in proof['turns'] for b in t['policies'].get('exp_oop',{}).get('boards',{}).values()]
    joint=[r for r in locked if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None]
    proof.update(positive_distinct_flops=int(bool(proof['selected'])),locked_named_boards=len(locked),joint_halfpot_assessed=len(joint),
                 nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    proof['native_file_sha256']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(proof))
    print(json.dumps({k:proof[k] for k in ('flop','selected','positive_distinct_flops','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--flop',required=True,choices=SPEC)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--preflight',action='store_true');run(p.parse_args())
