"""Extend the two verified Ts9s5h/9d policies to previously unexported rivers for rank150."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import hu_b724_rank150_rivers as native
import hu_b731_rank150_replay as origin
import hu_b747_rank150_replay as audit
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b637_rank57 import solve
from hu_b710_publish import unpack_original

FLOP='Ts9s5h'
TURN='9d'
LINE=native.LINE
RIVERS='2d 2h 3d 3h 4c 4h 5c 6c 6d 7c 7d 9h Tc Th Ac Ad'.split()
OLD_RIVERS='2c 3c 4d 5d 6h 7h 9c Td Jd Qd Kh Ah'.split()
ORIGINAL='data/solver_evidence/NL2_B724_R150_TS9S5H.zip'
ROOT_SHA='63aafb0070942125d0cea1e91bfe3f79f7f32eb267de978c9fd17d69de39e322'
PINS={'gto':('6a9ac930a4bce4b4c38c2b349c0d35403a2099110bd9480e787921577fa53bb8','435a10bdd0df5c16428ccda98ae29a9b72ff2fc2e5673fb5449db8760a4c0b0d'),
      'exp_ip':('47cab801dd0303b8b87cede936853e12a1d02907396d64f48f18dc403db68ce0','ad8fe1f79b52688228555ffd42241f42cc94d4e7c4219ccb6729e5d46e7d24c3')}


def read(path):
    return json.loads(path.read_bytes())


def source(temp,solver,current_route,pipeline,pool):
    aid,jid,digest=origin.PINS[FLOP]; archive=Path(ORIGINAL).read_bytes();assert sha(archive)==digest
    evidence=Path('data/solver_evidence/partial')
    origin.authenticate(read(evidence/'b731_auth_receipt.json'))
    folder=temp/'source';unpack_original(archive,folder)
    tree=temp/'b724';audit.materialize(origin.HEAD,tree)
    proof=audit.replay_exact(tree,origin.WORKER,solver,folder,FLOP)
    assert (folder/'proof.json').read_bytes()==(evidence/'b731_ts9s5h_proof.json').read_bytes()
    assert (folder/'rendered-routes.json').read_bytes()==current_route
    assert proof['selected'] is None and proof['root_sha256']==ROOT_SHA==sha((folder/'flop/result.json').read_bytes())
    rec,=[r for r in proof['turns'] if r['turn']==TURN]
    assert rec['common']=={} and rec['preregistered_rivers']==OLD_RIVERS and set(rec['policies'])==set(PINS)
    root=read(folder/'flop/result.json');jobs={};games={}
    for v,(s,j) in PINS.items():
        path=folder/(TURN+'-'+v)
        assert sha((path/'result.json').read_bytes())==s and sha((path/'job.json').read_bytes())==j
        jobs[v]=read(path/'job.json');games[v]=read(path/'result.json')
        assert jobs[v]['extract']==[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in OLD_RIVERS]
        assert len(games[v]['nodes'])==210 and {n['board'][-2:] for n in games[v]['nodes'] if len(n['board'])==10}==set(OLD_RIVERS)
        assert games[v]['hands']==games['gto']['hands'] and 0<=games[v]['info']['gto_expl_pct']<=.5
    manifest=read(folder/'original-manifest.json')
    job,rules=native.prepare_job(dict(source=dict(version='gto',root=root,manifest=manifest),job=jobs['gto']),'exp_ip',pool,pipeline)
    job['out']='result.json';assert job==jobs['exp_ip'] and job['hero']==1
    assert native.audit_patterns(games['exp_ip'],job,dict(locks=rules),pool,1)==rec['policies']['exp_ip']['measured_lock_application']
    return root,games,jobs,rec,rules,dict(run=origin.RUN,head=origin.HEAD,artifact_id=aid,job_id=jid,archive_sha256=digest,
        root_result_sha256=ROOT_SHA,root_job_sha256=proof['root_job_sha256'],proof_sha256=sha((folder/'proof.json').read_bytes()))


def parent(root,game,route):
    public_node,eligible,_,_=native.parent_gate(root,TURN,route);public=public_node['board']
    root_nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    turn_nodes={n['line']:n for n in game['nodes'] if n['board']==public}
    bb=native.accepted(root_nodes[''],root['hands'],'x')&native.accepted(root_nodes['x b33'],root['hands'],'c')
    co=native.accepted(root_nodes['x'],root['hands'],'b33')
    bb &= native.accepted(turn_nodes['x b33 c/'],game['hands'],'x')
    co &= native.accepted(turn_nodes['x b33 c/x'],game['hands'],'x')
    wr=[{native.cardkey(h) for h,w in zip(root['hands'][seat],public_node['wr'][seat],strict=True) if w>1e-4 and native.cards(public).isdisjoint(native.cardkey(h))} for seat in (0,1)]
    co={h for h in co&wr[1] if native.hand_cell(''.join(h),public[:6])[0] in route['flop'] and native.hand_cell(''.join(h),public)[0] in route['turn']}
    return {(h,v) for h in co for v in bb&wr[0] if set(h).isdisjoint(v)},eligible,public


def preregister(root,games,route):
    g,eligible,public=parent(root,games['gto'],route)
    e,other,p=parent(root,games['exp_ip'],route)
    assert p==public and other==eligible
    common=g&e;by_river={}
    for river in native.DECK:
        if river in native.cards(public) or river in OLD_RIVERS:continue
        selected={(h,v) for h,v in common if river not in h and river not in v and ''.join(h) in eligible.get(river,[])}
        if selected:by_river[river]=selected
    assert set(by_river)==set(RIVERS) and set(RIVERS).isdisjoint(OLD_RIVERS)
    assert {''.join(h) for rows in by_river.values() for h,v in rows}=={'JcQh','JdQh'}
    return by_river,eligible,dict(original_checked_turn_private_pairs=len(common),new_rivers=RIVERS,
        same_both_policy_hero_hands=['JcQh','JdQh'],compatible_deals_by_river={r:len(by_river[r]) for r in RIVERS})


def river_pairs(game,observed,allowed):
    root={n['board']:n for n in game['nodes'] if n['line']=='x b33 c/x x/'}
    final={n['board']:n for n in game['nodes'] if n['line']==LINE}
    out={}
    for public,d in observed.items():
        rv=public[-2:]
        if rv not in allowed:continue
        assert (root[public]['player'],final[public]['player'],root[public]['pot'],final[public]['pot'])==(0,1,416,416)
        bb=native.accepted(root[public],game['hands'],'x')
        opponents={native.cardkey(h) for h,w in zip(game['hands'][0],final[public]['w'][0],strict=True) if w>1e-4}
        co=set(d['hands'])
        out[public]={(h,v) for h,v in allowed[rv] if ''.join(h) in co and v in bb and v in opponents}
    assert {p[-2:] for p in out}==set(RIVERS)
    return out


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve();py=solver/'postflop/py'
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.limp.SOLVER
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==native.limp.RUST
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes()
    assert (sha(raw_pool),sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(native.POOL,native.PIPELINE,native.RANGES)
    sys.path.insert(0,str(py));import pipeline
    pool=json.loads(raw_pool)['NL2'];raw=subprocess.check_output(['node',native.ROUTE]);route=json.loads(raw)
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][native.MODEL]
    with TemporaryDirectory(prefix='b760-parents-') as tmp:
        root,games,jobs,rec,rules,pin=source(Path(tmp),solver,raw,pipeline,pool)
    allowed,eligible,gate=preregister(root,games,route)
    if a.preflight:
        print(json.dumps(dict(flop=FLOP,turn=TURN,source=pin,gate=gate)));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True);(out/'rendered-routes.json').write_bytes(raw)
    policies={};deals={};common={}
    for v in ('gto','exp_ip'):
        old=games[v];job=dict(jobs[v],extract=jobs[v]['extract']+[dict(prefix=['x','x',r],street=True) for r in RIVERS])
        path=out/(TURN+'-'+v);game=solve(path,job,a.driver)
        assert (path/'job.json').read_bytes()==compact(job)
        assert all(game[k]==old[k] for k in ('pot','stack','flop','hands'))
        old_nodes=[n for n in game['nodes'] if len(n['board'])==8 or n['board'][-2:] in OLD_RIVERS]
        assert old_nodes==old['nodes'] and len(old_nodes)==210 and 0<=game['info']['gto_expl_pct']<=.5
        assert len(game['nodes'])==210+16*len(RIVERS)
        measured=None
        if v=='exp_ip':
            assert 0<=game['info']['hero_gap_pct']<=.5
            measured=native.audit_patterns(game,job,dict(locks=rules),pool,1);orig=rec['policies'][v]['measured_lock_application']
            assert all(measured[k]==orig[k] for k in ('marginal_targets','driver_tree_nodes'))
            assert any(c>0 for k,c in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
        else:assert not game['info'].get('lock_stats')
        observed=native.observations(root,game,TURN,OLD_RIVERS+RIVERS,eligible,route)
        assert {p:r for p,r in observed.items() if p[-2:] in OLD_RIVERS}==rec['policies'][v]['boards']
        new={p:r for p,r in observed.items() if p[-2:] in RIVERS}
        assert all(native.compatible(contract,dict(public_board=p,actual_exact_action_line=LINE,acting_seat=1)) for p in new)
        actual=river_pairs(game,new,allowed);deals[v]=actual
        policies[v]=dict(source_sha256=sha((path/'result.json').read_bytes()),job_sha256=sha((path/'job.json').read_bytes()),
            original_210_nodes_sha256=sha(compact(old_nodes)),original_result_sha256=PINS[v][0],original_job_sha256=PINS[v][1],
            measured_lock_application=measured,boards=new,eligible_deal_counts={p:len(rows) for p,rows in actual.items()})
        if v=='gto' and not any(actual.values()):break
    if 'exp_ip' in deals:
        for p,rows in deals['gto'].items():
            both=rows&deals['exp_ip'][p]
            if both:
                common[p]=dict(hands=sorted({''.join(h) for h,v in both}),compatible_deals=len(both),
                    opponent_per_hand={''.join(h):''.join(min(v for x,v in both if h==x)) for h in sorted({h for h,v in both})})
    locked=[r['reach'] for r in policies.get('exp_ip',{}).get('boards',{}).values()]
    counts=dict(locked_named_boards=len(locked),joint_halfpot_assessed=sum(r['b50'] is not None for r in locked),
        nonpolarized_candidates=sum(bool((r['b50'] or {}).get('candidate')) for r in locked),positive_distinct_flops=int(bool(common)))
    proof=dict(schema='NL2_B760_R150_UNEXPORTED_TURN_POLICY_RIVERS_V1',rank=150,model_id=native.MODEL,flop=FLOP,turn=TURN,actor=1,line=LINE,
        root_price=[250,9900],river_price=[416,9817],source=pin,preflight=gate,original_rivers=OLD_RIVERS,new_rivers=RIVERS,
        solver=native.limp.SOLVER,rust=native.limp.RUST,pool_sha256=native.POOL,ranges_sha256=native.RANGES,pipeline_sha256=native.PIPELINE,
        rendered_route_sha256=sha(raw),original_flop_roots_repeated=0,original_policy_nodes_preserved=210,
        lock_scope='Frozen original GTO flop and BB partial street-specific pool marginal locks; CO acts at river.',
        no_observed_per_private_hand_frequency=True,policies=policies,common=common,selected_public_board=min(common,default=None),**counts)
    (out/'proof.json').write_bytes(json_bytes(proof))
    print(json.dumps(dict(flop=FLOP,turn=TURN,**counts)))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):cli.add_argument('--'+k,type=Path,required=True)
    cli.add_argument('--driver',type=Path);cli.add_argument('--preflight',action='store_true');run(cli.parse_args())
