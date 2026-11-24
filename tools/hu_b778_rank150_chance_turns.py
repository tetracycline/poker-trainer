"""Use held-out native B724 ranges to solve three unexported turns on the same Ts9s5h flop."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b724_rank150_rivers as native
import hu_b760_rank150_rivers as old
import hu_b765_rank150_low_flanks as deals
import hu_b766_rank75_chance_turns as chance
from hu_b467_river_source_gate import compact,json_bytes,sha

FLOP=old.FLOP
TURNS=('9h','5c','Th')
ORIGINALS=('7d','8h','Jc','9d')
ORIGINAL_DEALS={('JcQh','6hJh'),('JdQh','6hJh')}
WORKER='tools/hu_b778_rank150_chance_turns.py'
ORIGINAL_ARCHIVE_SHA='36a1bbfb5b27d78dd7e52787d35a4e7adfda18cbd0595f5150ef8c03a5bd021f'
PINS={**deals.base.PINS,deals.WORKER:'3b528ee6849904817131e67063c7beb9aae8792f',
      'tools/hu_b766_rank75_chance_turns.py':'2624730b49abd405db6aa82b2f87c5e8bf728c64',
      'tools/hu_b760_rank150_rivers.py':'1480d68ea05eeae56b86f3f4d3f2bff9cd0c0256'}


def build_job(template,root,turn,weights,rivers):
    job=dict(template,flop=FLOP,turn=turn,line0=['x','b33','c','/'],root_no_bet=False,
             flop_oop='33%,50%,75%,100%',flop_ip='33%,50%,75%,100%',turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',
             river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',pot=416,stack=9817,oop='',ip='',
             iters=2200,rank_pct=.45,target_pct=.45,compress=False,out='result.json',
             extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
    for i,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][i],weights[i],strict=True) if w>1e-4]
    assert job['oop_w'] and job['ip_w'] and (job['rake_rate'],job['rake_cap'])==(.05,1000)
    return job


def range_view(root,turn,weights):
    # Supply chance-adjusted range input without creating a native strategy or replacing any source node.
    n,=[n for n in root['nodes'] if n['line']=='x b33 c/' and n['board'].endswith(ORIGINALS[0])]
    assert (n['player'],n['pot'],n['bets'])==(0,416,[83,83])
    boundary=dict(line='x b33 c/',board=n['board'][:6]+turn,player=0,pot=416,bets=[83,83],wr=weights)
    return dict(root,nodes=root['nodes']+[boundary])


def original(route):
    receipt=Path('data/solver_evidence/partial/b731_auth_receipt.json')
    auth=json.loads(receipt.read_bytes());old.origin.authenticate(auth)
    aid,jid,digest=old.origin.PINS[FLOP]
    assert digest==ORIGINAL_ARCHIVE_SHA and any(a['id']==aid and a['digest']=='sha256:'+digest for a in auth['artifacts'])
    assert any(j['id']==jid and j['conclusion']=='success' for j in auth['jobs'])
    with ZipFile(native.limp.TEMPLATE) as z:
        assert sha(Path(native.limp.TEMPLATE).read_bytes())==native.limp.TEMPLATE_SHA
        template=json.loads(z.read('original-turn.job.json'))
    assert sha(Path(old.ORIGINAL).read_bytes())==digest
    with ZipFile(old.ORIGINAL) as z:
        claim=json.loads(z.read('proof.json'));assert claim['flop']==FLOP and claim['selected'] is None
        assert sha(z.read('flop/result.json'))==old.ROOT_SHA==claim['root_sha256']
        assert all(sha(z.read(name))==digest for name,digest in claim['native_file_sha256'].items())
        raw={f:z.read(f) for f in ('flop/job.json','flop/result.json','rendered-routes.json','original-manifest.json')}
        assert json.loads(raw['rendered-routes.json'])==route
        root=json.loads(raw['flop/result.json']);manifest=json.loads(raw['original-manifest.json'])
        native.limp.check_limp_source(dict(manifest=manifest,root_job=json.loads(raw['flop/job.json']),subgame_job=None))
        observed={n['board'][6:]:n for n in root['nodes'] if n['line']=='x b33 c/'}
        assert set(observed)==set(ORIGINALS) and set(ORIGINALS).isdisjoint(TURNS)
        masks={t:chance.blocked(root['hands'],t) for t in ORIGINALS+TURNS}
        verified={}
        for turn in ORIGINALS:
            weights=chance.reconstruct(root,observed,masks,[o for o in ORIGINALS if o!=turn],turn)
            assert all(chance.weight_bytes(w)==chance.weight_bytes(v) for w,v in zip(weights,observed[turn]['wr'],strict=True))
            rec,=[r for r in claim['turns'] if r['turn']==turn]
            job=build_job(template,root,turn,weights,rec['preregistered_rivers']);stored=z.read(turn+'-gto/job.json')
            assert compact(job)==stored
            verified[turn]=dict(original_full_job_sha256=sha(stored),binary64_seat_sha256=[sha(chance.weight_bytes(w)) for w in weights])
        pairs=[]
        for ver in ('gto','exp_ip'):
            result=z.read('9d-'+ver+'/result.json');j=z.read('9d-'+ver+'/job.json')
            assert (sha(result),sha(j))==old.PINS[ver]
            candidate,_,_=old.parent(root,json.loads(result),route);pairs.append(candidate)
        same={(''.join(h),''.join(v)) for h,v in pairs[0]&pairs[1]}
        assert same==ORIGINAL_DEALS
    assert set((t[0],t[1] if t[1] in ('s','h') else 'off') for t in ORIGINALS).isdisjoint(
        {(t[0],t[1] if t[1] in ('s','h') else 'off') for t in TURNS})
    plans={}
    for turn in TURNS:
        weights=chance.reconstruct(root,observed,masks,ORIGINALS,turn);view=range_view(root,turn,weights)
        _,eligible,_,gate=native.parent_gate(view,turn,route)
        live=[{''.join(native.cardkey(h)) for h,w in zip(root['hands'][i],weights[i],strict=True) if w>1e-4} for i in (0,1)]
        assert all(h in live[1] and v in live[0] for h,v in same)
        named_hands={r:[(h,v) for h,v in sorted(same) if h in hs and native.cards(FLOP+turn+r+h).isdisjoint(native.cards(v))] for r,hs in eligible.items()}
        options=[r for r,hs in named_hands.items() if hs]
        assert options and {h for vs in named_hands.values() for h,v in vs}=={h for h,v in same}
        rivers=options if len(options)<=12 else [options[round(i*(len(options)-1)/11)] for i in range(12)]
        job=build_job(template,root,turn,weights,rivers)
        plans[turn]=dict(view=view,eligible=eligible,rivers=rivers,job=job,gate=dict(gate,derived_boundary=True,
                         binary64_seat_sha256=[sha(chance.weight_bytes(w)) for w in weights],all_matching_rivers=len(options),
                         preregistered_prior_deals={r:named_hands[r] for r in rivers}))
    provenance=dict(original_run=old.origin.RUN,original_head=old.origin.HEAD,original_artifact=aid,original_job=jid,
                    original_archive_sha256=digest,original_flop_sha256=old.ROOT_SHA,root_job_sha256=claim['root_job_sha256'],
                    held_out_binary64_and_full_jobs=verified,original_9d_two_policy_turn_deals=sorted([list(x) for x in same]),
                    original_9d_policy_sha256=old.PINS,rust_files=chance.RUST_FILES,driver_source=chance.DRIVER_SOURCE)
    return raw,root,manifest,plans,provenance


def observed(root,view,game,turn,plan,route,first):
    rows=native.observations(root,game,turn,plan['rivers'],plan['eligible'],route)
    witnesses={}
    for public,row in rows.items():
        co,bb=deals.hand_pairs(view,game,turn,public)
        shared={(''.join(h),''.join(v)) for h in co if ''.join(h) in row['hands'] for v in bb if set(h).isdisjoint(v)}
        if first is not None:shared &= first[public]
        heroes={h for h,v in shared}
        row['hands']={h:row['hands'][h] for h in sorted(heroes)}
        row['compatible_bb_per_co']={h:sorted(v for x,v in shared if x==h) for h in sorted(heroes)}
        witnesses[public]=shared
    return rows,witnesses


def run(a):
    solver=a.solver.resolve();rust=a.rust_source or solver/'postflop/postflop-solver'
    assert sys.version_info[:2]==(3,11) and subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.limp.SOLVER
    assert all(native.limp.git_blob(rust/path)==pin for path,pin in chance.RUST_FILES.items())
    assert native.limp.git_blob(solver/'postflop/pfdriver/src/main.rs')==chance.DRIVER_SOURCE
    assert all(native.limp.git_blob(p)==h for p,h in PINS.items())
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and rust.resolve()==solver/'postflop/postflop-solver'
        assert subprocess.check_output(['git','-C',rust,'rev-parse','HEAD'],text=True).strip()==native.limp.RUST
    py=solver/'postflop/py';sys.path.insert(0,str(py));import pipeline
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw_pool)==native.POOL and sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    pool=json.loads(raw_pool)['NL2'];route_bytes=subprocess.check_output(['node',native.ROUTE]);route=json.loads(route_bytes)
    assert (route['model_id'],route['line'],route['actor'],route['native_price'])==(native.MODEL,native.LINE,1,[416,9817])
    assert abs(9817/416/route['model_price'][2]-1)<.002
    inputs,root,manifest,plans,origin=original(route);assert inputs['rendered-routes.json']==route_bytes
    if a.preflight:
        print(json.dumps(dict(held_out=list(origin['held_out_binary64_and_full_jobs']),plans={t:p['gate']['all_matching_rivers'] for t,p in plans.items()})))
        return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    out.mkdir(parents=True,exist_ok=True)
    for name,raw in inputs.items():
        dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if a.driver:dest.write_bytes(raw)
        else:assert dest.read_bytes()==raw
    report=dict(schema='NL2_B778_RANK150_HELD_OUT_CHANCE_TURNS_V1',rank=150,model_id=native.MODEL,actor=1,line=native.LINE,flop=FLOP,
                source_worker_blob=native.limp.git_blob(WORKER),origin=origin,solver=native.limp.SOLVER,rust=native.limp.RUST,pool_sha256=native.POOL,
                assumed_preflop_ranges=True,lock_scope='FROZEN_GTO_FLOP_WITH_MEASURED_PARTIAL_TURN_RIVER_NL2_MARGINALS',
                no_observed_per_private_hand_frequency=True,root_native_solves_repeated=0,
                preregistered_turns=list(TURNS),new_turn_job_sha256={t:sha(compact(p['job'])) for t,p in plans.items()},turns=[],selected=None)
    for turn,p in plans.items():
        item=dict(turn=turn,root_gate=p['gate'],preregistered_rivers=p['rivers'],policies={},common={});report['turns'].append(item)
        job=p['job'];first=None
        for version in ('gto','exp_ip'):
            if version=='gto':target,rules=job,[]
            else:
                target,rules=native.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=job),'exp_ip',pool,pipeline)
                target['out']='result.json';assert target['hero']==1 and target['locks']
            folder=out/(turn+'-'+version);game=native.solve(folder,target,a.driver)
            assert (folder/'job.json').read_bytes()==compact(target) and native.cards(game['flop'])==native.cards(FLOP)
            assert (game['pot'],game['stack'])==(416,9817) and 0<=game['info']['gto_expl_pct']<=.5
            app=None
            if version=='exp_ip':
                assert game['hands']==gto_hands and 0<=game['info']['hero_gap_pct']<=.5
                app=native.audit_patterns(game,target,dict(manifest,locks=rules),pool,1)
                assert any(v>0 for k,v in app['driver_tree_nodes'].items() if k in app['marginal_targets'])
            else:
                assert not game['info'].get('lock_stats')
                gto_hands=game['hands']
            boards,witness=observed(root,p['view'],game,turn,p,route,first)
            item['policies'][version]=dict(source_sha256=sha((folder/'result.json').read_bytes()),job_sha256=sha(compact(target)),
                                           measured_lock_application=app,boards=boards)
            if version=='gto':
                first=witness
                if not any(first.values()):
                    item['negative_reason']='NO_GTO_RENDERED_CO_BB_RIVER_CHECK';break
            else:
                item['common']={public:sorted({h for h,v in hands}) for public,hands in sorted(witness.items()) if hands}
                if not item['common']:item['negative_reason']='NO_COMMON_GTO_AND_NL2_PHYSICAL_CO_BB'
        if item['common']:
            report['selected']=dict(turn=turn,public_board=next(iter(item['common'])));break
    locked=[b['reach'] for t in report['turns'] for b in t['policies'].get('exp_ip',{}).get('boards',{}).values()]
    joint=[b for b in locked if b['strict_legal_combos']>0 and b['compatible_hole_card_pairs']>0 and b['b50'] is not None]
    report.update(positive_distinct_flops=int(bool(report['selected'])),locked_named_boards=len(locked),joint_halfpot_assessed=len(joint),
                  nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    report['native_file_sha256']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('selected','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--rust-source',type=Path);p.add_argument('--preflight',action='store_true');p.add_argument('--driver',type=Path)
    run(p.parse_args())
