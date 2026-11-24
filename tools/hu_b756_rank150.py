"""Replay the two previous rank150 witnesses and B754's independent native roots without a solver call."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import hu_b747_rank150_replay as old
import hu_b756_collect as source
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
OLD_GROUP='partial/b747_rank150.json'
OLD_MEDIUM='partial/b747_rank150_locked_medium.json'
OLD_VIEW='NL2_MULTIBOARD_B747_R150_TSTC6S.json.gz'
OLD_PINS={OLD_GROUP:'2ea284d590a1d381ca71c21c1bc32744a6cc1251',OLD_MEDIUM:'9a21706a30fe6cf55df390e5677ef59766a024f1',
    'partial/b747_tstc6s_proof.json':'350f64679401ea873e6d8aabfd5ce29327229aa4','partial/b747_auth_receipt.json':'a211d08ffc0e8a4a646291a9aa8b0a246ecb9cb6',
    OLD_VIEW:'69417b69a6f21f7766dedcb59a2d46fb3d709fee'}


def read(path):
    return json.loads(path.read_bytes())


def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json_bytes(obj))


def previous(temp,solver,model,pipeline,pool,route):
    """Independently rebuild the published B724 and B743 positive hands and viewers."""
    assert old.native.limp.git_blob('tools/hu_b747_rank150_replay.py')=='68d8db504f884ed2acbfa9a0a26c9c075ae1e37f'
    for name,pin in OLD_PINS.items():assert old.native.limp.git_blob(EVIDENCE/name)==pin
    group,medium=old.previous(temp,solver,model,pipeline,pool,route)
    old.authenticate(read(EVIDENCE/'partial/b747_auth_receipt.json'))
    flop='TsTc6s';pins=old.PINS[flop];aid,digest=pins['original'];cid,cdigest=pins['checkpoint']
    raw=(EVIDENCE/'NL2_B743_R150_TSTC6S.zip').read_bytes();root=(EVIDENCE/'NL2_B743_ROOT_R150_TSTC6S.zip').read_bytes()
    assert (sha(raw),sha(root))==(digest,cdigest)
    folder=temp/'prior-tens';unpack_original(raw,folder);old.check_checkpoint(root,folder,flop)
    frozen=temp/'b743';old.materialize(old.HEAD,frozen)
    claim=old.replay_exact(frozen,old.WORKER,solver,folder,flop)
    assert (folder/'rendered-routes.json').read_bytes()==route and (folder/'proof.json').read_bytes()==(EVIDENCE/'partial/b747_tstc6s_proof.json').read_bytes()
    old.stage_choice(folder,claim,'B743_R150_TSTC6S',[aid,pins['job'],digest],model,pipeline,pool,group,medium)
    group['pins'][-1].update(root_checkpoint_artifact_id=cid,root_checkpoint_sha256=cdigest)
    assert (pairs.EVIDENCE/OLD_VIEW).read_bytes()==(EVIDENCE/OLD_VIEW).read_bytes()
    assert group==read(EVIDENCE/OLD_GROUP) and medium==read(EVIDENCE/OLD_MEDIUM)
    assert [b['flop'] for b in group['boards']]==['9c9h6c','TsTc6s']
    medium['schema']='NL2_B756_ORIGINAL_RANK150_LOCKED_MEDIUM_V1'
    return group,medium


def checkpoint(raw,folder,flop):
    with ZipFile(io.BytesIO(raw)) as z:
        expected=['checkpoint.json','flop/job.json','flop/result.json']
        assert sorted(n for n in z.namelist() if not n.endswith('/'))==expected
        info=json.loads(z.read('checkpoint.json'))
        assert (info['flop'],info['worker_blob'],info['base_blob'])==(flop,source.WORKER_BLOB,old.prior.WORKER_BLOB)
        for path,key in [('flop/job.json','original_root_job_sha256'),('flop/result.json','original_root_sha256')]:
            value=z.read(path);assert value==(folder/path).read_bytes() and sha(value)==info[key]
    return info


def observe_selected(folder,claim,artifact,root_art,job_id,model,contract,pipeline,pool,group,medium):
    flop=claim['flop'];sel=claim['selected'];turn=sel['turn'];public=sel['public_board']
    rec,=[t for t in claim['turns'] if t['turn']==turn]
    root=read(folder/'flop/result.json');rootsha=sha(compact(root));manifest=read(folder/'original-manifest.json')
    gj=read(folder/(turn+'-gto')/'job.json');digest=artifact['digest'][7:]
    code='B754_R150_'+flop.upper()
    g=dict(version='gto',run=source.RUN,root=root,root_sha256=rootsha,archive_code=code,archive_sha256=digest,manifest=dict(manifest,locks=[]))
    ej,rules=old.native.prepare_job(dict(source=g,job=gj),'exp_ip',pool,pipeline);ej['out']='result.json'
    assert (folder/(turn+'-exp_ip')/'job.json').read_bytes()==compact(ej)
    e=dict(g,version='exp_ip',verified_gto_parent=dict(run=source.RUN,sha256=rootsha),
        manifest=dict(manifest,locks=rules,gto_parent_source_run_id=source.RUN,gto_parent_source_sha256=rootsha))
    observations=[];shown=[]
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
        summarize(row);observations.append(row);shown.append(old.prior.hand_policies(s,row,expected))
    shared=comparisons(*shown)
    assert [h['hand'] for h in shared]==rec['common'][public] and shared
    b,p=pairs.emit_board(model,g,e,public,LINE,texture(flop),viewer_code='B756_R150_'+flop.upper())
    assert b and p and compatible(contract,b) and b['assumed_preflop_ranges']
    assert p['pool_observed_marginal_lock_nodes']>0 and p['common_legal_hero_combos']>=len(shared)
    assert (b['actual_pot_bb'],b['actual_effective_stack_bb'],b['acting_seat'])==(4.16,98.17,1)
    for ver,key,row in zip(('GTO','NL2'),('gto_references','references'),observations,strict=True):
        assert (p[ver+'_strict_combos'],p[ver+'_compatible_hole_card_pairs'])==(row['strict_legal_combos'],row['compatible_hole_card_pairs'])
        row['rendered_decision_hands']=shared;medium[key][source_key(MODEL,row)]=row
    b.update(certification_scope=claim['lock_scope'],source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=source.RUN,
        flop_native_solves_repeated=0,flop_bet_size_menu=claim['original_flop_bet_size_menu'],
        original_root_result_sha256=claim['root_sha256'],original_root_job_sha256=claim['root_job_sha256'])
    b['nl2_locked_variants'][0].update(source_run_role=b['source_run_role'],origin_solve_run_id=source.RUN,pool_sha256=old.native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),gto_parent_source_run_id=source.RUN,
        gto_parent_source_sha256=rootsha,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    p.update(rendered_decision_hands=shared,source_blob_head=source.HEAD,worker_artifact=artifact['id'],worker_job=job_id,
        root_checkpoint_artifact_id=root_art['id'],root_checkpoint_sha256=root_art['digest'][7:],
        original_root_result_sha256=claim['root_sha256'],original_root_job_sha256=claim['root_job_sha256'],
        original_conditional_jobs_sha256={v:rec['policies'][v]['job_sha256'] for v in ('gto','exp_ip')})
    group['boards'].append(b);group['pins'].append(p)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==old.native.limp.SOLVER
    for path,pin in [(source.WORKER,source.WORKER_BLOB),(source.WORKFLOW,source.WORKFLOW_BLOB)]:
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==pin
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==old.native.POOL
    pool=json.loads(pool_raw)['NL2'];registry=Path('data/nl2_hu_multiboard_status_current.json')
    before=registry.read_bytes();status=json.loads(before);model=status['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(150,'LMP_CO_BB',23.558)
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(1,['x bet c','x x','x'])
    current_route=subprocess.check_output(['node',old.native.ROUTE])
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';ev.mkdir(parents=True)
    receipt=source.validate(read(a.receipts));write(out/'nl2_hu_b756_source_receipts.json',receipt)
    workers=[]
    with TemporaryDirectory(prefix='b756-replay-') as temp:
        parent=Path(temp)
        group,medium=previous(parent,solver,model,pipeline,pool,current_route)
        pairs.EVIDENCE=ev
        frozen=parent/'b754';old.materialize(source.HEAD,frozen)
        for flop in source.FLOPS:
            art,=[x for x in receipt['artifacts'] if x['name']=='B754-R150-'+flop]
            root_art,=[x for x in receipt['artifacts'] if x['name']=='B754-root-R150-'+flop]
            job,=[j for j in receipt['jobs'] if j['name']==f'solve ({flop})']
            raw=[]
            for meta,code in [(art,'B754_R150_'),(root_art,'B754_ROOT_R150_')]:
                name='NL2_'+code+flop.upper()+'.zip';p=a.archives/f"{meta['id']}.zip"
                b=(p if p.is_file() else a.archives/name).read_bytes()
                assert len(b)==meta['size_in_bytes'] and 'sha256:'+sha(b)==meta['digest']
                (ev/name).write_bytes(b);raw.append(b)
            folder=parent/flop;unpack_original(raw[0],folder)
            identity=checkpoint(raw[1],folder,flop)
            d=old.replay_exact(frozen,source.WORKER,solver,folder,flop)
            assert (folder/'rendered-routes.json').read_bytes()==current_route
            assert (d['schema'],d['source_worker_blob'],d['checkpoint_worker_blob'],d['base_worker_blob'],d['actor'],d['line'])==(
                'NL2_B754_R150_PAIRED_SIX_SOURCE_V1',source.WORKER_BLOB,old.WORKER_BLOB,old.prior.WORKER_BLOB,1,LINE)
            assert (d['original_flop_roots_per_worker'],d['extra_flop_native_solves_in_continuation'])==(1,0)
            assert (d['root_job_sha256'],d['root_sha256'])==(identity['original_root_job_sha256'],identity['original_root_sha256'])
            if d['selected']:observe_selected(folder,d,art,root_art,job['id'],model,contract,pipeline,pool,group,medium)
            locked=[v['reach'] for t in d['turns'] for v in t['policies'].get('exp_ip',{}).get('boards',{}).values()]
            assert len(locked)==len({r['public_board'] for r in locked})
            measured=[r for r in locked if r['strict_legal_combos']>0 and r['compatible_hole_card_pairs']>0 and r['b50'] is not None]
            workers.append(dict(flop=flop,selected=d['selected'],source_artifact=art['id'],source_sha256=sha(raw[0]),job_id=job['id'],
                checkpoint_artifact=root_art['id'],checkpoint_sha256=sha(raw[1]),root_job_sha256=d['root_job_sha256'],root_sha256=d['root_sha256'],
                proof_sha256=sha((folder/'proof.json').read_bytes()),locked_named_boards=len(locked),joint_halfpot_assessed=len(measured),
                nonpolarized_candidates=sum(r['b50']['candidate'] for r in measured),positive_rivers=sum(len(t['common']) for t in d['turns'])))
    flops=[b['flop'] for b in group['boards']];n=len(flops)
    assert n==len(group['pins'])==len({suit_isomorphism_class(f) for f in flops})==len(medium['references'])==len(medium['gto_references'])
    assert 2<=n<=4 and flops[:2]==['9c9h6c','TsTc6s'] and n==2+sum(bool(w['selected']) for w in workers)
    if n>=3:
        write(ev/'reverified/rank150.json',group);write(out/'nl2_hu_b756_locked_medium.json',medium)
    else:
        write(ev/'partial/b756_rank150.json',group);write(ev/'partial/b756_rank150_locked_medium.json',medium)
    summary=dict(schema='NL2_B756_VERIFIED_RANK150_SOURCES_V1',rank=150,model_id=MODEL,source_run=source.RUN,source_head=source.HEAD,
        workers=workers,prior_positive_flops=2,positive_distinct_flops=n,cert_eligible_ranks=[150] if n>=3 else [],original_flops_repeated=0,
        **{k:sum(w[k] for w in workers) for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')})
    write(out/'nl2_hu_b756_results.json',summary)
    assert before==registry.read_bytes()
    print(json.dumps({k:v for k,v in summary.items() if k!='workers'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for opt in ('solver','archives','receipts','output'):p.add_argument('--'+opt,type=Path,required=True)
    publish(p.parse_args())
