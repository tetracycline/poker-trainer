"""Replay the B733 same-root B770 extension and certify rank150 only with its two previous witnesses."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import hu_b747_rank150_replay as old
import hu_b770_rank150_straight_draw as worker
from hu_b756_rank150 import previous as recovered_two
import hu_b775_collect as source
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
    medium['schema']='NL2_HU_B775_ORIGINAL_LOCKED_MEDIUM_V1'
    return group,medium


def checkpoint(archive,folder,old_root):
    with ZipFile(io.BytesIO(archive)) as z:
        expected=['checkpoint.json','flop/job.json','flop/result.json']
        assert sorted(n for n in z.namelist() if not n.endswith('/'))==expected
        for name in expected:
            assert z.read(name)==(folder/name).read_bytes()
    proof=read(folder/'checkpoint.json')
    assert proof['worker_blob']==source.PINS[source.WORKER] and proof['old_nodes_identical']==37
    assert sha((folder/'flop/job.json').read_bytes())==proof['expanded_job_sha256']
    assert sha((folder/'flop/result.json').read_bytes())==proof['expanded_result_sha256']
    assert worker.verify_root(old_root,read(folder/'flop/result.json'))==proof['added_raw_boundaries']
    return proof


def replay(frozen,solver,folder):
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
originals={p.parent for p in folder.rglob('job.json')};observed=set()
def verified(path,job,driver):
    assert driver is None and path in originals and path not in observed
    assert (path/'job.json').read_bytes()==compact(job),path
    observed.add(path)
    return saved(path,job,None)
reader.solve=verified
runpy.run_path(program,run_name='__main__')
assert observed==originals
"""
    subprocess.run([sys.executable,'-c',audit,str(frozen/source.WORKER),'--solver',str(solver),'--output',str(folder)],cwd=frozen,check=True)
    assert (folder/'proof.json').read_bytes()==proof
    assert all(sha((folder/p).read_bytes())==h for p,h in original.items())
    return claim

def observe_selected(folder,claim,artifact,root_art,job_id,model,contract,pipeline,pool,group,medium):
    flop=claim['flop'];sel=claim['selected'];turn=sel['turn'];public=sel['public_board']
    rec,=[t for t in claim['turns'] if t['turn']==turn]
    root=read(folder/'flop/result.json');rootsha=sha(compact(root));manifest=read(folder/'original-manifest.json')
    gj=read(folder/(turn+'-gto')/'job.json');digest=artifact['digest'][7:]
    code='B770_R150_'+flop.upper()
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
        co,bb=worker.deals.hand_pairs(root,sub,turn,public)
        deals.append({(''.join(h),''.join(v)) for h in co for v in bb if set(h).isdisjoint(v) and ''.join(h) in expected['hands']})
        summarize(row);observations.append(row);shown.append(old.prior.hand_policies(s,row,expected))
    shared=comparisons(*shown)
    assert [h['hand'] for h in shared]==rec['common'][public] and shared
    both=deals[0]&deals[1]
    assert sorted({h for h,v in both})==[h['hand'] for h in shared]
    for witness in shared:
        hand=witness['hand'];villains=sorted(v for h,v in both if h==hand)
        reported=rec['policies']['exp_ip']['boards'][public]['compatible_bb_per_co'][hand]
        assert hand in worker.HANDS and reported==villains and villains
        witness.update(compatible_opponent_example=villains[0],joint_policy_opponent_count=len(villains))
    b,p=pairs.emit_board(model,g,e,public,LINE,texture(flop),viewer_code='B775_R150_'+flop.upper())
    assert b and p and compatible(contract,b) and b['assumed_preflop_ranges']
    assert p['pool_observed_marginal_lock_nodes']>0 and p['common_legal_hero_combos']>=len(shared)
    assert (b['actual_pot_bb'],b['actual_effective_stack_bb'],b['acting_seat'])==(4.16,98.17,1)
    for ver,key,row in zip(('GTO','NL2'),('gto_references','references'),observations,strict=True):
        assert (p[ver+'_strict_combos'],p[ver+'_compatible_hole_card_pairs'])==(row['strict_legal_combos'],row['compatible_hole_card_pairs'])
        row['rendered_decision_hands']=shared;medium[key][source_key(MODEL,row)]=row
    b.update(original_two_policy_co_bb_witness=True,certification_scope=claim['lock_scope'],source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=source.RUN,
        original_flop_source_run_id=worker.prior.RUN,original_flop_source_head=worker.prior.HEAD,
        original_flop_reexports=1,original_nodes_exactly_reproduced=37,flop_bet_size_menu=worker.SIZE,
        original_root_result_sha256=worker.OLD_ROOT_SHA,original_root_job_sha256=worker.OLD_JOB_SHA)
    b['nl2_locked_variants'][0].update(source_run_role=b['source_run_role'],origin_solve_run_id=source.RUN,pool_sha256=old.native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),gto_parent_source_run_id=source.RUN,
        gto_parent_source_sha256=rootsha,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    p.update(rendered_decision_hands=shared,source_blob_head=source.HEAD,worker_artifact=artifact['id'],worker_job=job_id,
        root_checkpoint_artifact_id=root_art['id'],root_checkpoint_sha256=root_art['digest'][7:],
        original_root_result_sha256=worker.OLD_ROOT_SHA,original_root_job_sha256=worker.OLD_JOB_SHA,
        reexported_root_sha256=claim['checkpoint']['expanded_result_sha256'],reexported_root_job_sha256=claim['checkpoint']['expanded_job_sha256'],
        original_flop_source_run_id=worker.prior.RUN,original_flop_archive_sha256=claim['origin']['archive_sha256'],
        original_conditional_jobs_sha256={v:rec['policies'][v]['job_sha256'] for v in ('gto','exp_ip')})
    group['boards'].append(b);group['pins'].append(p)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,digest in source.PINS.items():
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==digest
        assert worker.native.limp.git_blob(path)==digest
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==worker.native.limp.SOLVER
    native_pool=(solver/'inputs/pool_stats.json').read_bytes();assert sha(native_pool)==worker.native.POOL
    pool=json.loads(native_pool)['NL2']
    before_path=Path('data/nl2_hu_multiboard_status_current.json');before=before_path.read_bytes()
    model=json.loads(before)['records'][MODEL]
    assert (model['frequency_rank'],model['label'],model['assumed_model_node_spr'],model['solver_profile'])==(150,'APPROX',23.558,'LMP_CO_BB')
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(1,['x bet c','x x','x'])
    route=subprocess.check_output(['node',worker.native.ROUTE])
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';ev.mkdir(parents=True)
    receipt=source.validate(read(a.receipts));write(out/'nl2_hu_b775_source_receipts.json',receipt)
    archives={}
    for art in receipt['artifacts']:
        name='NL2_'+source.SOURCES[art['name']]+'.zip';path=a.archives/f"{art['id']}.zip"
        raw=(path if path.exists() else a.archives/name).read_bytes()
        assert len(raw)==art['size_in_bytes'] and sha(raw)==art['digest'][7:]
        (ev/name).write_bytes(raw);archives[art['name']]=(raw,art)
    original_job,original_root,origin=worker.original()
    with TemporaryDirectory(prefix='b775-r150-') as temp:
        parent=Path(temp);group,medium=previous(parent,solver,model,pipeline,pool,route);pairs.EVIDENCE=ev
        raw,art=archives['B770-R150-'+source.FLOP];raw_cp,art_cp=archives['B770-root-R150-'+source.FLOP]
        directory=parent/'original';unpack_original(raw,directory)
        cp=checkpoint(raw_cp,directory,original_root);assert cp['source']==origin
        added=[dict(prefix=['x','b33','c',t],street=False,raw=True) for t in worker.TURNS]
        assert (directory/'flop/job.json').read_bytes()==compact(dict(original_job,extract=original_job['extract']+added))
        frozen=parent/'source';old.materialize(source.HEAD,frozen)
        d=replay(frozen,solver,directory)
        assert (d['schema'],d['actor'],d['line'],d['rank'],d['model_id'],d['flop'])==('NL2_B770_ORIGINAL_56S_RANK150_RIVER_SOURCE_V1',1,LINE,150,MODEL,source.FLOP)
        assert (d['original_flops_new'],d['original_root_reexports'],d['flop_solves_repeated_for_continuation'])==(0,1,0)
        assert d['source_worker_blob']==source.PINS[source.WORKER] and d['origin']==origin and d['checkpoint']==cp
        assert d['new_raw_turn_boundaries']==list(worker.TURNS) and d['assumed_preflop_ranges'] and d['no_observed_per_private_hand_frequency']
        assert (directory/'rendered-routes.json').read_bytes()==route
        assert d['prior_exact_flop_ui_deals']==worker.screen(original_root,json.loads(route))
        turns=d['turns'];assert [t['turn'] for t in turns]==list(worker.TURNS[:len(turns)]) and turns
        if d['selected']:
            assert d['selected']['turn']==turns[-1]['turn'] and d['selected']['public_board'] in turns[-1]['common']
            observe_selected(directory,d,art,art_cp,source.JOB,model,contract,pipeline,pool,group,medium)
        else:
            assert len(turns)==len(worker.TURNS) and all(not t['common'] for t in turns)
        sets={v:[b['reach'] for t in turns for b in t['policies'].get(v,{}).get('boards',{}).values()] for v in ('gto','exp_ip')}
        for items in sets.values():
            assert len(items)==len({i['public_board'] for i in items})
        locked=sets['exp_ip'];joint=[i for i in locked if i['strict_legal_combos']>0 and i['compatible_hole_card_pairs']>0 and i['b50'] is not None]
        proof_sha=sha((directory/'proof.json').read_bytes())
    flops=[b['flop'] for b in group['boards']];n=len(flops)
    assert n==len(group['pins'])==len({suit_isomorphism_class(f) for f in flops})==len(medium['references'])==len(medium['gto_references'])
    assert flops[:2]==['9c9h6c','TsTc6s'] and n==2+int(bool(d['selected']))
    if n==3:
        assert flops[-1]==source.FLOP
        write(ev/'reverified/rank150.json',group);write(out/'nl2_hu_b775_locked_medium.json',medium)
    else:
        write(ev/'partial/b775_rank150.json',group);write(ev/'partial/b775_rank150_locked_medium.json',medium)
    summary=dict(schema='NL2_B775_CONFIRMED_RANK150_ORIGINAL_SOURCE_V1',rank=150,model_id=MODEL,
                 source_head=source.HEAD,source_run=source.RUN,job_id=source.JOB,source_artifact=art['id'],source_sha256=art['digest'][7:],
                 checkpoint_artifact=art_cp['id'],checkpoint_sha256=art_cp['digest'][7:],proof_sha256=proof_sha,original=origin,
                 old_native_nodes_identical=cp['old_nodes_identical'],new_raw_boundaries=cp['added_raw_boundaries'],
                 selected=d['selected'],prior_positive_flops=2,positive_distinct_flops=n,cert_eligible_ranks=[150] if n==3 else [],
                 named_gto_boards=len(sets['gto']),gto_joint_reach=sum(r['compatible_hole_card_pairs']>0 for r in sets['gto']),
                 locked_named_boards=len(locked),joint_halfpot_assessed=len(joint),nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    write(out/'nl2_hu_b775_results.json',summary)
    assert before_path.read_bytes()==before
    print(json.dumps({k:summary[k] for k in ('positive_distinct_flops','cert_eligible_ranks','named_gto_boards','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','archives','receipts','output'):p.add_argument('--'+k,type=Path,required=True)
    publish(p.parse_args())
