"""Continue Ts7h6s on four unexported heart turns using its unchanged native flop solution."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b766_rank75_chance_turns as chance
import hu_b789_rank230_seven_draws as previous
import hu_b791_collect as receipt
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_trainer_route_gate import compatible

base,native=previous.base,previous.native
FLOP='Ts7h6s'
OLD=tuple(previous.CASES[FLOP][1])
TURNS=('5h','4h','Jh','2h')
HERO,VILLAIN='6h9h','3c3d'
ROOT_SHA='045ae9b24569f2d91ea9d81d9b15e94c7d6703f86500aff3bdb2302a5dcb1a45'
WORKER='tools/hu_b793_rank230_heart_turns.py'
PINS={'B789-R230-Ts7h6s':(14899757576,'96f5c12c90c1dffd186dfd3d779d9720baf81cda2fdceebc64a76c2458b5c586'),
      'B789-root-R230-Ts7h6s':(14900021613,'fed136d8ad0acfba8d84835da7762e84e8c311df6bf242eba650badfe6803b73')}


def checked_input():
    manifest=Path('data/nl2_hu_b791_source_receipts.json');assert base.blob(manifest)=='306b3088a0af1075a5b129637497be26daa5bc16'
    auth=receipt.validate(json.loads(manifest.read_bytes()));paths=[]
    for name,(aid,digest) in PINS.items():
        item,=[a for a in auth['artifacts'] if a['name']==name]
        assert (item['id'],item['digest'])==(aid,'sha256:'+digest)
        path=Path('data/solver_evidence')/('NL2_'+receipt.SOURCES[name]+'.zip')
        assert sha(path.read_bytes())==digest;paths.append(path)
    with ZipFile(paths[0]) as src,ZipFile(paths[1]) as checkpoint:
        claim=json.loads(src.read('proof.json'));assert claim['flop']==FLOP and not claim['selected']
        files={k:src.read(k) for k in ('flop/job.json','flop/result.json','root-checkpoint.json')}
        assert all(checkpoint.read(k)==raw for k,raw in files.items()) and sha(files['flop/result.json'])==claim['root_sha256']==ROOT_SHA
        assert all(sha(src.read(k))==v for k,v in claim['native_file_sha256'].items())
        assert claim['source_worker_blob']==base.blob(previous.WORKER)==receipt.PINS[previous.WORKER]
        assert [r['turn'] for r in claim['turns']]==list(OLD) and set(OLD).isdisjoint(TURNS)
        jobs={t:src.read(t+'-gto/job.json') for t in OLD}
        old_pair={v:json.loads(src.read('3h-'+v+'/result.json')) for v in ('gto','exp_oop')}
    return claim,files,jobs,old_pair


def range_view(root,observed,turn,weights):
    anchor=observed[OLD[0]]
    assert (anchor['line'],anchor['player'],anchor['pot'],anchor['bets'])==('x x/',0,2100,[0,0])
    boundary=dict(line='x x/',board=anchor['board'][:6]+turn,player=0,pot=2100,bets=[0,0],wr=weights)
    return dict(root,nodes=root['nodes']+[boundary]),boundary


def plans(root,old_pair,claim,jobs,route,pipeline):
    observed={n['board'][6:]:n for n in root['nodes'] if n['line']=='x x/'}
    assert set(observed)==set(OLD) and (root['pot'],root['stack'],root['flop'])==(2100,9000,FLOP)
    masks={t:chance.blocked(root['hands'],t) for t in OLD+TURNS};held={}
    for t in OLD:
        rebuilt=chance.reconstruct(root,observed,masks,[x for x in OLD if x!=t],t)
        assert all(chance.weight_bytes(x)==chance.weight_bytes(y) for x,y in zip(rebuilt,observed[t]['wr'],strict=True))
        record,=[r for r in claim['turns'] if r['turn']==t]
        job=previous.turn_job(root,t,dict(wr=rebuilt),record['preregistered_rivers'],pipeline)
        assert compact(job)==jobs[t]
        held[t]=dict(binary64_seat_sha256=[sha(chance.weight_bytes(x)) for x in rebuilt],original_full_gto_job_sha256=sha(jobs[t]))
    old_masks={}
    for ver,sub in old_pair.items():
        board=observed['3h']['board'];sb,=[n for n in sub['nodes'] if (n['board'],n['line'])==(board,'x x/')]
        i,=[i for i,h in enumerate(sub['hands'][0]) if ''.join(native.cardkey(h))==HERO]
        n=len(sub['hands'][0]);weights=[max(0,sb['strat'][j*n+i]) for j in range(len(sb['acts']))]
        check=weights[sb['acts'].index('x')]/sum(weights)
        eligible=native.cardkey(HERO) in native.accepted(sb,sub['hands'],'x')
        assert eligible==(ver=='gto') and (check>.99 if ver=='gto' else .21<check<.23)
        old_masks[ver]=dict(original_3h_sb_check_fraction=check,accepted=eligible)
    result={}
    for turn in TURNS:
        weights=chance.reconstruct(root,observed,masks,OLD,turn);view,edge=range_view(root,observed,turn,weights)
        heroes,foes=base.root_hands(view,turn,route,edge)
        assert native.cardkey(HERO) in heroes and native.cardkey(VILLAIN) in foes
        assert len(native.public_cards(FLOP+turn+HERO+VILLAIN))==8
        gate=native.available_rivers(view,turn,route,None);rivers=gate['river_extracts']
        named=[r for r in rivers if len(native.public_cards(FLOP+turn+r+HERO+VILLAIN))==9 and
            all(route[s].get(native.hand_cell(HERO,(FLOP+turn+r)[:n])[0])=='過' for s,n in (('flop',6),('turn',8),('river',10)))]
        assert named and HERO in gate['compatible_hero_hands']
        gate.update(physical_sb=HERO,compatible_btn=VILLAIN,prior_pair_unblocked_ui_rivers=named,
                    derived_binary64_seat_sha256=[sha(chance.weight_bytes(x)) for x in weights])
        result[turn]=(view,edge,heroes,foes,gate,rivers,previous.turn_job(root,turn,edge,rivers,pipeline))
    return held,old_masks,result


def run(a):
    solver=a.solver.resolve();rust=a.rust_source or solver/'postflop/postflop-solver';py=solver/'postflop/py'
    assert sys.version_info[:2]==(3,11) and previous.git_head(solver)==native.SOLVER and a.flop==FLOP
    assert base.blob('tools/hu_b766_rank75_chance_turns.py')=='2624730b49abd405db6aa82b2f87c5e8bf728c64'
    assert all(base.blob(rust/path)==h for path,h in chance.RUST_FILES.items()) and base.blob(solver/'postflop/pfdriver/src/main.rs')==chance.DRIVER_SOURCE
    if a.driver:assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and previous.git_head(rust)==native.RUST
    assert sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    sys.path.insert(0,str(py));import pipeline,ranges
    raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(raw)==native.POOL;pool=json.loads(raw)['NL2']
    route_bytes=subprocess.check_output(['node',base.ROUTE]);route=json.loads(route_bytes)['230']
    assert route['model']==base.MODEL and route['flop']==route['turn']==route['river']=={'low:2':'過','mid_high:2':'過'}
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][base.MODEL]
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][base.MODEL]
    assert (model['frequency_rank'],model['solver_profile'],contract['seat'],contract['streets'])==(230,'SB3_BTN',0,['x x','x x',''])
    assert abs(90/21/model['assumed_model_node_spr']-1)<.05
    claim,files,jobs,old_pair=checked_input();root=json.loads(files['flop/result.json']);parent_job=json.loads(files['flop/job.json'])
    assert (parent_job['oop'],parent_job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('SB3_BTN','gto'))
    assert (parent_job['flop_oop'],parent_job['flop_ip'],parent_job['pot'],parent_job['stack'],parent_job['rake_rate'],parent_job['rake_cap'])==('33%','33%',2100,9000,.05,1000)
    held,masks,proposals=plans(root,old_pair,claim,jobs,route,pipeline)
    if a.preflight:print(json.dumps(dict(flop=FLOP,old_gto_jobs_verified=len(held),old_3h=masks,new_physical_rivers={t:p[4]['prior_pair_unblocked_ui_rivers'] for t,p in proposals.items()})));return
    out=a.output.resolve()
    if a.driver:assert not out.exists() or not any(out.iterdir())
    out.mkdir(parents=True,exist_ok=True)
    for name,b in files.items():
        dest=out/name;dest.parent.mkdir(exist_ok=True,parents=True)
        if a.driver:dest.write_bytes(b)
        else:assert dest.read_bytes()==b
    assert native.solve(out/'flop',parent_job,None)==root
    (out/'rendered-routes.json').write_bytes(route_bytes)
    origin=dict(run=receipt.RUN,head=receipt.HEAD,job=receipt.JOBS[FLOP],artifacts=PINS,original_root_result_sha256=ROOT_SHA,
        original_root_job_sha256=sha(files['flop/job.json']),original_checkpoint_sha256=sha(files['root-checkpoint.json']),
        original_five_held_out_jobs=held,original_3h_6h9h=masks,rust_source=chance.RUST_FILES,driver_source=chance.DRIVER_SOURCE)
    proof=dict(schema='NL2_B793_R230_HELD_OUT_HEART_TURNS_V1',rank=230,model_id=base.MODEL,actor=0,spot='SB3_BTN',flop=FLOP,line=native.LINE,
        source_worker_blob=base.blob(WORKER),origin=origin,solver=native.SOLVER,rust=native.RUST,pool_sha256=native.POOL,
        root_job_sha256=origin['original_root_job_sha256'],root_sha256=ROOT_SHA,root_native_solves_repeated=0,original_flop_reexports=0,
        restricted_flop_sizes='33% both seats',root_price=[2100,9000],no_observed_per_private_hand_frequency=True,
        lock_scope='FROZEN_GTO_FLOP_AND_MEASURED_PARTIAL_TURN_RIVER_NL2_MARGINALS',preregistered_turns=list(TURNS),turns=[],selected=None)
    for turn,(view,edge,heroes,btn,gate,rivers,gj) in proposals.items():
        item=dict(turn=turn,root_gate=gate,preregistered_rivers=rivers,policies={},common={});proof['turns'].append(item);before=None
        for ver in ('gto','exp_oop'):
            target=gj;applied=None
            if ver=='exp_oop':
                target,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='SB3_BTN')),job=gj),ver,pool,pipeline)
                target['out']='result.json';assert target['hero']==0 and target['locks']
            leaf=out/(turn+'-'+ver);game=native.solve(leaf,target,a.driver)
            assert (leaf/'job.json').read_bytes()==compact(target) and (game['flop'],game['pot'],game['stack'])==(FLOP,2100,9000)
            assert 0<=game['info']['gto_expl_pct']<=.5
            if ver=='gto':gto_hands=game['hands'];assert not game['info'].get('lock_stats')
            else:
                assert game['hands']==gto_hands and 0<=game['info']['hero_gap_pct']<=.5
                applied=native.audit_patterns(game,target,dict(spot='SB3_BTN',locks=rules),pool,0)
                assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
            rows,witnesses=base.decisions(root,game,turn,rivers,route,heroes,btn,before)
            item['policies'][ver]=dict(source_sha256=sha((leaf/'result.json').read_bytes()),job_sha256=sha(compact(target)),measured_lock_application=applied,boards=rows)
            if ver=='gto':
                before=witnesses
                if not any(witnesses.values()):break
            else:item['common']={k:sorted({h for h,v in pairs}) for k,pairs in sorted(witnesses.items()) if pairs}
        if item['common']:
            public=next(iter(item['common']));assert compatible(contract,dict(public_board=public,actual_exact_action_line=native.LINE,acting_seat=0))
            proof['selected']=dict(turn=turn,public_board=public);break
    locked=[b['reach'] for t in proof['turns'] for b in t['policies'].get('exp_oop',{}).get('boards',{}).values()]
    joint=[r for r in locked if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None]
    proof.update(positive_distinct_flops=int(bool(proof['selected'])),locked_named_boards=len(locked),joint_halfpot_assessed=len(joint),
        nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    proof['native_file_sha256']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(proof))
    print(json.dumps({k:proof[k] for k in ('flop','selected','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=[FLOP],default=FLOP);p.add_argument('--driver',type=Path);p.add_argument('--rust-source',type=Path)
    p.add_argument('--preflight',action='store_true');run(p.parse_args())
