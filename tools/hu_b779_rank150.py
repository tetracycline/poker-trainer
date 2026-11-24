"""Verify B778's held-out exact ranges, native turn jobs and possible third rank150 flop."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import hu_b747_rank150_replay as old
import hu_b778_rank150_chance_turns as worker
from hu_b756_rank150 import previous as recovered_two
import hu_b779_collect as source
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_board_reach_corrections import summarize,source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible

EVIDENCE=Path('data/solver_evidence')
MODEL=old.native.MODEL
LINE=old.native.LINE
def read(path):
    return json.loads(path.read_bytes())


def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json_bytes(obj))


def previous(temp,solver,model,pipeline,pool,route):
    group,medium=recovered_two(temp,solver,model,pipeline,pool,route)
    assert group==read(EVIDENCE/'partial/b756_rank150.json') and group==read(EVIDENCE/'partial/b768_rank150.json')
    assert medium==read(EVIDENCE/'partial/b756_rank150_locked_medium.json')
    medium['schema']='NL2_HU_B768_ORIGINAL_LOCKED_MEDIUM_V1'
    assert medium==read(EVIDENCE/'partial/b768_rank150_locked_medium.json')
    medium['schema']='NL2_HU_B779_ORIGINAL_LOCKED_MEDIUM_V1'
    return group,medium


def replay(frozen,solver,rust,folder):
    proof=(folder/'proof.json').read_bytes();claim=json.loads(proof)
    original={p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file() and p.name!='proof.json'}
    assert original==claim['native_file_sha256']
    audit="""
import runpy,sys
from pathlib import Path
program=sys.argv.pop(1);sys.argv[0]=program;sys.path.insert(0,str(Path(program).parent))
from hu_b467_river_source_gate import compact
import hu_b637_rank57 as reader
saved=reader.solve
folder=Path(sys.argv[sys.argv.index('--output')+1])
originals={p.parent for p in folder.rglob('job.json')} - {folder/'flop'};observed=set()
def verified(path,job,driver):
    assert driver is None and path in originals and path not in observed
    assert (path/'job.json').read_bytes()==compact(job),path
    observed.add(path)
    return saved(path,job,None)
reader.solve=verified
runpy.run_path(program,run_name='__main__')
assert observed==originals
"""
    subprocess.run([sys.executable,'-c',audit,str(frozen/source.WORKER),'--solver',str(solver),'--rust-source',str(rust),'--output',str(folder)],cwd=frozen,check=True)
    assert (folder/'proof.json').read_bytes()==proof
    assert all(sha((folder/p).read_bytes())==h for p,h in original.items())
    return claim

def observe_selected(folder,claim,artifact,model,contract,pipeline,pool,group,medium,plan):
    flop=claim['flop'];sel=claim['selected'];turn=sel['turn'];public=sel['public_board']
    rec,=[t for t in claim['turns'] if t['turn']==turn]
    root=read(folder/'flop/result.json');rootsha=sha(compact(root));manifest=read(folder/'original-manifest.json')
    gj=read(folder/(turn+'-gto')/'job.json');digest=artifact['digest'][7:]
    code='B778_R150_'+flop.upper()
    g=dict(version='gto',run=source.RUN,root=root,root_sha256=rootsha,archive_code=code,archive_sha256=digest,manifest=dict(manifest,locks=[]))
    ej,rules=old.native.prepare_job(dict(source=g,job=gj),'exp_ip',pool,pipeline);ej['out']='result.json'
    assert (folder/(turn+'-exp_ip')/'job.json').read_bytes()==compact(ej)
    e=dict(g,version='exp_ip',verified_gto_parent=dict(run=source.RUN,sha256=rootsha),
        manifest=dict(manifest,locks=rules,gto_parent_source_run_id=source.RUN,gto_parent_source_sha256=rootsha))
    observations=[];shown=[];deals=[]
    for s in (g,e):
        ver=s['version'];policy=rec['policies'][ver];raw=(folder/(turn+'-'+ver)/'result.json').read_bytes()
        sub=json.loads(raw);sub.update(line0='x b33 c',turn=turn,rivers=rec['preregistered_rivers'])
        assert sha(raw)==policy['source_sha256']
        s.update(subgame=sub,source_sha256=sha(raw))
        if ver=='exp_ip':
            app=old.native.audit_patterns(sub,ej,s['manifest'],pool,1)
            assert app==policy['measured_lock_application'] and any(v>0 for k,v in app['driver_tree_nodes'].items() if k in app['marginal_targets'])
            s.update(measured_lock_application=app,applied_rust_rates=sub['info']['lock_stats'])
        row=audit_decision(s,public,LINE,1,rootsha);expected=policy['boards'][public]
        assert {k:row[k] for k in expected['reach']}==expected['reach']
        assert row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0 and row['b50'] is not None
        co,bb=worker.deals.hand_pairs(plan['view'],sub,turn,public)
        deals.append({(''.join(h),''.join(v)) for h in co for v in bb if set(h).isdisjoint(v) and ''.join(h) in expected['hands']})
        summarize(row);observations.append(row);shown.append(old.prior.hand_policies(s,row,expected))
    shared=comparisons(*shown)
    assert [h['hand'] for h in shared]==rec['common'][public] and shared
    both=deals[0]&deals[1]
    assert sorted({h for h,v in both})==[h['hand'] for h in shared]
    for witness in shared:
        hand=witness['hand'];villains=sorted(v for h,v in both if h==hand)
        reported=rec['policies']['exp_ip']['boards'][public]['compatible_bb_per_co'][hand]
        assert reported==villains and villains
        witness.update(compatible_opponent_example=villains[0],joint_policy_opponent_count=len(villains))
    b,p=pairs.emit_board(model,g,e,public,LINE,texture(flop),viewer_code='B779_R150_'+flop.upper())
    assert b and p and compatible(contract,b) and b['assumed_preflop_ranges']
    assert p['pool_observed_marginal_lock_nodes']>0 and p['common_legal_hero_combos']>=len(shared)
    assert (b['actual_pot_bb'],b['actual_effective_stack_bb'],b['acting_seat'])==(4.16,98.17,1)
    for ver,key,row in zip(('GTO','NL2'),('gto_references','references'),observations,strict=True):
        assert (p[ver+'_strict_combos'],p[ver+'_compatible_hole_card_pairs'])==(row['strict_legal_combos'],row['compatible_hole_card_pairs'])
        row['rendered_decision_hands']=shared;medium[key][source_key(MODEL,row)]=row
    b.update(original_two_policy_co_bb_witness=True,certification_scope=claim['lock_scope'],source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=source.RUN,
        original_flop_source_run_id=worker.old.origin.RUN,original_flop_source_head=worker.old.origin.HEAD,flop_native_solves_repeated=0,
        conditional_chance_ranges='BINARY64_HELD_OUT_FOUR_ORIGINAL_FULL_JOBS',flop_bet_size_menu='33%,50%,75%,100%',
        original_root_result_sha256=worker.old.ROOT_SHA,original_root_job_sha256=claim['origin']['root_job_sha256'])
    b['nl2_locked_variants'][0].update(source_run_role=b['source_run_role'],origin_solve_run_id=source.RUN,pool_sha256=old.native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),gto_parent_source_run_id=source.RUN,
        gto_parent_source_sha256=rootsha,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    p.update(rendered_decision_hands=shared,source_blob_head=source.HEAD,worker_artifact=artifact['id'],worker_job=source.JOB,
        original_root_result_sha256=worker.old.ROOT_SHA,original_root_job_sha256=claim['origin']['root_job_sha256'],
        original_flop_source_run_id=worker.old.origin.RUN,original_flop_archive_sha256=worker.ORIGINAL_ARCHIVE_SHA,
        conditional_binary64_seat_sha256=plan['gate']['binary64_seat_sha256'],original_four_held_out_jobs=claim['origin']['held_out_binary64_and_full_jobs'],
        original_conditional_jobs_sha256={v:rec['policies'][v]['job_sha256'] for v in ('gto','exp_ip')})
    group['boards'].append(b);group['pins'].append(p)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,pin in source.PINS.items():
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==pin
        assert worker.native.limp.git_blob(path)==pin
    solver=a.solver.resolve();rust=(a.rust_source or solver/'postflop/postflop-solver').resolve()
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==worker.native.limp.SOLVER
    p=(solver/'inputs/pool_stats.json').read_bytes();assert sha(p)==worker.native.POOL;pool=json.loads(p)['NL2']
    reg=Path('data/nl2_hu_multiboard_status_current.json');before=reg.read_bytes();model=json.loads(before)['records'][MODEL]
    assert (model['frequency_rank'],model['label'],model['assumed_model_node_spr'],model['solver_profile'])==(150,'APPROX',23.558,'LMP_CO_BB')
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(1,['x bet c','x x','x'])
    route=subprocess.check_output(['node',worker.native.ROUTE]);inputs,root,manifest,plans,origin=worker.original(json.loads(route))
    assert set(origin['held_out_binary64_and_full_jobs'])==set(worker.ORIGINALS)
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';ev.mkdir(parents=True)
    auth=source.validate(read(a.receipts));write(out/'nl2_hu_b779_source_receipts.json',auth)
    art,=auth['artifacts'];name='NL2_'+source.SOURCES[art['name']]+'.zip';p=a.archives/f"{art['id']}.zip"
    data=(p if p.exists() else a.archives/name).read_bytes();assert len(data)==art['size_in_bytes'] and sha(data)==art['digest'][7:]
    (ev/name).write_bytes(data)
    with TemporaryDirectory(prefix='b779-rank150-') as tmp:
        parent=Path(tmp);group,medium=previous(parent,solver,model,pipeline,pool,route);pairs.EVIDENCE=ev
        folder=parent/'native';unpack_original(data,folder)
        assert all((folder/k).read_bytes()==raw for k,raw in inputs.items())
        frozen=parent/'source';old.materialize(source.HEAD,frozen)
        d=replay(frozen,solver,rust,folder)
        assert (d['schema'],d['flop'],d['actor'],d['line'],d['rank'],d['model_id'])==('NL2_B778_RANK150_HELD_OUT_CHANCE_TURNS_V1',source.FLOP,1,LINE,150,MODEL)
        assert d['origin']==json.loads(json.dumps(origin)) and d['root_native_solves_repeated']==0 and d['source_worker_blob']==source.PINS[source.WORKER]
        assert d['preregistered_turns']==list(worker.TURNS) and d['new_turn_job_sha256']=={t:sha(compact(plan['job'])) for t,plan in plans.items()}
        assert d['assumed_preflop_ranges'] and d['no_observed_per_private_hand_frequency']
        turns=d['turns'];assert turns and [r['turn'] for r in turns]==list(worker.TURNS[:len(turns)])
        for rec in turns:
            t=rec['turn'];plan=plans[t];assert rec['root_gate']==json.loads(json.dumps(plan['gate'])) and rec['preregistered_rivers']==plan['rivers']
            assert (folder/(t+'-gto')/'job.json').read_bytes()==compact(plan['job'])
        if d['selected']:
            t=d['selected']['turn'];assert t==turns[-1]['turn'] and d['selected']['public_board'] in turns[-1]['common']
            observe_selected(folder,d,art,model,contract,pipeline,pool,group,medium,plans[t])
        else:
            assert len(turns)==len(worker.TURNS) and all(not t['common'] for t in turns)
        hashed=sha((folder/'proof.json').read_bytes())
    checks={v:[b['reach'] for r in turns for b in r['policies'].get(v,{}).get('boards',{}).values()] for v in ('gto','exp_ip')}
    assert all(len(rows)==len({r['public_board'] for r in rows}) for rows in checks.values())
    locked=checks['exp_ip'];joint=[r for r in locked if r['strict_legal_combos']>0 and r['compatible_hole_card_pairs']>0 and r['b50'] is not None]
    assert (len(locked),len(joint),sum(r['b50']['candidate'] for r in joint))==(d['locked_named_boards'],d['joint_halfpot_assessed'],d['nonpolarized_candidates'])
    flops=[b['flop'] for b in group['boards']];n=len(flops)
    assert flops[:2]==['9c9h6c','TsTc6s'] and n==2+int(bool(d['selected']))
    assert n==len(group['pins'])==len({suit_isomorphism_class(f) for f in flops})==len(medium['references'])==len(medium['gto_references'])
    if n==3:
        assert flops[-1]==source.FLOP;write(ev/'reverified/rank150.json',group);write(out/'nl2_hu_b779_locked_medium.json',medium)
    else:
        write(ev/'partial/b779_rank150.json',group);write(ev/'partial/b779_rank150_locked_medium.json',medium)
    summary=dict(schema='NL2_B779_RANK150_AUTHENTICATED_CHANCE_TURNS_V1',rank=150,model_id=MODEL,source_run=source.RUN,source_head=source.HEAD,
        job_id=source.JOB,source_artifact=art['id'],source_sha256=art['digest'][7:],proof_sha256=hashed,original=origin,selected=d['selected'],
        prior_positive_flops=2,positive_distinct_flops=n,cert_eligible_ranks=[150] if d['selected'] else [],named_gto_boards=len(checks['gto']),
        gto_joint_reach=sum(r['compatible_hole_card_pairs']>0 for r in checks['gto']),locked_named_boards=len(locked),
        joint_halfpot_assessed=len(joint),nonpolarized_candidates=d['nonpolarized_candidates'])
    write(out/'nl2_hu_b779_results.json',summary);assert reg.read_bytes()==before
    print(json.dumps({k:summary[k] for k in ('selected','positive_distinct_flops','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','receipts','archives','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--rust-source',type=Path)
    publish(p.parse_args())
