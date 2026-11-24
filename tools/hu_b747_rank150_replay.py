"""Authenticate the original B743 roots and compare their policies with the prior rank150 decision."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import hu_b724_rank150_rivers as native
import hu_b731_rank150_replay as prior
import hu_b732_rank80_boundaries as reserved
import hu_b743_rank150_paired as worker
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_board_reach_corrections import source_key, summarize
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture

RUN=45333267578
HEAD='c7c107b0ccc384debf92231ac62349e454ea2975'
WORKER='tools/hu_b743_rank150_paired.py'
WORKFLOW='.github/workflows/nl2-hu-b743-rank150-paired.yml'
WORKER_BLOB='194b86e1c2b8e7ac3cbd6af2f9daa67781aeb765'
PINS={
  "9h9d7h": {
    "job": 138239206466,
    "original": [
      14893967977,
      "6f09942c510df70a0a46484ace41259d4a28cf81976288cd0c0e0ee0464bf30c"
    ],
    "checkpoint": [
      14893003891,
      "3707854c30ca758666c1a6ed31b1ade293758deb9fee9adb884dab3b4b556135"
    ]
  },
  "TsTc6s": {
    "job": 138239206670,
    "original": [
      14893893755,
      "0dc1b2bae2ee0abef3f002a74feec0085600d6d8cf77e897253394394ff534b8"
    ],
    "checkpoint": [
      14894281899,
      "af2f1137d892b552430c81091472a5cd114850c1ae8b337f7087b8de213eb357"
    ]
  },
  "JdJh7d": {
    "job": 138239206617,
    "original": [
      14894415022,
      "78cf7ac5aa7a200f9e435c2de216453d7fda19eaa47775b7e8c9e9be4276bd36"
    ],
    "checkpoint": [
      14893742089,
      "9dbc0c42da8fc473fb04294fbb0b81aaeee54b8c5f176500b3682b75170e79bc"
    ]
  }
}
PRIOR_PINS={
    'data/solver_evidence/NL2_B724_R150_9C9H6C.zip':'ce410045bdb3c43e2b5741e8ef0f889cccf65f7c',
    'data/solver_evidence/NL2_MULTIBOARD_B731_R150_9C9H6C.json.gz':'880a98938de17be611aab00c8525cd71788c8248',
    'data/solver_evidence/partial/b731_9c9h6c_proof.json':'2acaff8bac96b53cce13f086b4f0c7faeb8a61d1',
    'data/solver_evidence/partial/b731_auth_receipt.json':'68af566187d99ee55bd328264fee7d544a4b5277',
    'data/solver_evidence/partial/b731_rank150.json':'f14c92520889bdf41947971c99f674c82a5e0750',
    'data/solver_evidence/partial/b731_rank150_locked_medium.json':'4607c16f2e3c7fc44e5e0ee3b427bd926f3aaf1d',
    'tools/hu_b731_rank150_replay.py':'4f3ae6ea43b39a2d9bc142e385328e3ce116ab25',
}
STEPS={
    'Verify the original A5-suited witness, current UI and both ranges',
    'Build the pinned native solver','Solve just the new full-size flop root',
    'Preserve the completed original before conditional work',
    'Resume the original root and verify both policies on reachable river checks',
    'Preserve the conditional jobs and original decisions',
}


def authenticate(auth):
    r=auth['run']
    assert (r['id'],r['head_sha'],r['head_branch'],r['path'],r['status'],r['conclusion'])==(
        RUN,HEAD,prior.BRANCH,WORKFLOW,'completed','success')
    assert (r['repository']['id'],r['repository']['full_name'])==(1438346845,'tetracycline/poker-trainer')
    assert set(PINS)==set(worker.CASES) and len(auth['jobs'])==3 and len(auth['artifacts'])==6
    for flop,pin in PINS.items():
        j,=[x for x in auth['jobs'] if x['id']==pin['job']]
        assert (j['run_id'],j['head_sha'],j['run_attempt'],j['name'],j['status'],j['conclusion'])==(
            RUN,HEAD,r['run_attempt'],'solve ('+flop+')','completed','success')
        assert STEPS<={s['name'] for s in j['steps'] if (s['status'],s['conclusion'])==('completed','success')}
        for k,name in (('original','B743-R150-'),('checkpoint','B743-root-R150-')):
            aid,digest=pin[k]
            a,=[x for x in auth['artifacts'] if x['id']==aid]
            assert (a['name'],a['expired'],a['digest'])==(name+flop,False,'sha256:'+digest)
            w=a['workflow_run']
            assert (w['id'],w['head_sha'],w['head_branch'],w['repository_id'],w['head_repository_id'])==(RUN,HEAD,prior.BRANCH,1438346845,1438346845)


def materialize(head,dest):
    """Keep source UI, algorithms and contract at their actual solve revision."""
    files=['tools','lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js',
        'data/nl2_hu_verified_extensions.json']
    tree=subprocess.check_output(['git','archive',head,'--',*files])
    with tarfile.open(fileobj=io.BytesIO(tree)) as archive:
        for member in archive:
            path=Path(member.name)
            assert not path.is_absolute() and '..' not in path.parts
            target=dest/path
            if member.isdir():
                target.mkdir(parents=True,exist_ok=True)
            else:
                assert member.isfile()
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    for p in Path('data').iterdir():
        target=dest/'data'/p.name
        if not target.exists():
            target.symlink_to(p.resolve(),target_is_directory=p.is_dir())


def replay_exact(frozen,program,solver,folder,flop):
    proof_raw=(folder/'proof.json').read_bytes()
    claim=json.loads(proof_raw)
    native_files=claim['native_file_sha256']
    paths={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}
    assert paths==set(native_files)|{'proof.json'}
    assert all(sha((folder/n).read_bytes())==d for n,d in native_files.items())
    # The frozen reader checks parsed jobs. Also require exact serialized requested-job bytes at every leaf.
    observer = """
import runpy, sys
from pathlib import Path
entry=sys.argv.pop(1);sys.argv[0]=entry
sys.path.insert(0,str(Path(entry).parent))
import hu_b637_rank57 as source_reader
from hu_b467_river_source_gate import compact
read=source_reader.solve
source=Path(sys.argv[sys.argv.index('--output')+1])
originals={p.parent for p in source.rglob('job.json')}
observed=set()
def verify(folder,job,driver):
    assert driver is None and folder in originals and folder not in observed
    assert (folder/'job.json').read_bytes()==compact(job),folder
    observed.add(folder)
    return read(folder,job,driver)
source_reader.solve=verify
runpy.run_path(entry,run_name='__main__')
assert observed==originals
"""
    subprocess.run([sys.executable,'-c',observer,str(frozen/program),'--solver',str(solver),'--flop',flop,'--output',str(folder)],
        cwd=frozen,check=True)
    assert (folder/'proof.json').read_bytes()==proof_raw
    assert all(sha((folder/n).read_bytes())==d for n,d in native_files.items())
    return claim


def previous(directory,solver,model,pipeline,pool,current_route):
    src=Path('data/solver_evidence')
    for p,d in PRIOR_PINS.items():
        assert native.limp.git_blob(p)==d
    raw=(src/'NL2_B724_R150_9C9H6C.zip').read_bytes()
    aid,jid,digest=prior.PINS['9c9h6c']
    assert sha(raw)==digest
    prior.authenticate(json.loads((src/'partial/b731_auth_receipt.json').read_bytes()))
    where=directory/'prior'
    unpack_original(raw,where)
    frozen=directory/'B724-source'
    materialize(prior.HEAD,frozen)
    claim=replay_exact(frozen,prior.WORKER,solver,where,'9c9h6c')
    assert (where/'proof.json').read_bytes()==(src/'partial/b731_9c9h6c_proof.json').read_bytes()
    assert (where/'rendered-routes.json').read_bytes()==current_route
    group=dict(rank=150,model_id=native.MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B731_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    old_out=directory/'prior-view';old_out.mkdir();pairs.EVIDENCE=old_out
    prior.stage_choice(where,claim,'B724_R150_9C9H6C',[aid,jid,digest],model,pipeline,pool,group,medium)
    name='NL2_MULTIBOARD_B731_R150_9C9H6C.json.gz'
    assert (old_out/name).read_bytes()==(src/name).read_bytes()
    assert group==json.loads((src/'partial/b731_rank150.json').read_bytes())
    assert medium==json.loads((src/'partial/b731_rank150_locked_medium.json').read_bytes())
    medium['schema']='NL2_HU_B747_ORIGINAL_LOCKED_MEDIUM_V1'
    return group,medium


def check_checkpoint(raw,full,flop):
    with ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith('/')]
        assert len(names)==3 and set(names)=={'checkpoint.json','flop/job.json','flop/result.json'}
        ident=json.loads(z.read('checkpoint.json'))
        assert (ident['flop'],ident['worker_blob'],ident['base_blob'])==(flop,WORKER_BLOB,prior.WORKER_BLOB)
        for member,key in (('flop/job.json','original_root_job_sha256'),('flop/result.json','original_root_sha256')):
            first=z.read(member)
            assert sha(first)==ident[key] and first==(full/member).read_bytes()
    return ident


def stage_choice(folder,claim,code,pin,model,pipeline,pool,group,medium):
    selected=claim['selected'];turn=selected['turn'];public=selected['public_board']
    record,=[r for r in claim['turns'] if r['turn']==turn]
    root=json.loads((folder/'flop/result.json').read_bytes());rootsha=sha(compact(root))
    manifest=json.loads((folder/'original-manifest.json').read_bytes())
    job=json.loads((folder/(turn+'-gto')/'job.json').read_bytes())
    g=dict(version='gto',run=RUN,root=root,root_sha256=rootsha,archive_code=code,archive_sha256=pin[2],manifest=dict(manifest,locks=[]))
    ejob,meta=native.prepare_job(dict(source=g,job=job),'exp_ip',pool,pipeline);ejob['out']='result.json'
    assert (folder/(turn+'-exp_ip')/'job.json').read_bytes()==compact(ejob)
    e=dict(g,version='exp_ip',verified_gto_parent=dict(run=RUN,sha256=rootsha),
        manifest=dict(manifest,locks=meta,gto_parent_source_run_id=RUN,gto_parent_source_sha256=rootsha))
    rows=[];policies=[]
    for s in (g,e):
        v=s['version'];obs=record['policies'][v]
        raw=(folder/(turn+'-'+v)/'result.json').read_bytes()
        sub=json.loads(raw);sub.update(line0='x b33 c',turn=turn,rivers=record['preregistered_rivers'])
        s.update(subgame=sub,source_sha256=sha(raw))
        assert s['source_sha256']==obs['source_sha256']
        if v=='exp_ip':
            s.update(measured_lock_application=obs['measured_lock_application'],applied_rust_rates=sub['info']['lock_stats'])
        row=audit_decision(s,public,native.LINE,1,rootsha);original=obs['boards'][public]
        assert {k:row[k] for k in original['reach']}==original['reach']
        summarize(row);assert row['strict_legal_combos']>0 and row['b50'] is not None
        rows.append(row);policies.append(prior.hand_policies(s,row,original))
    common=comparisons(*policies)
    assert [h['hand'] for h in common]==record['common'][public] and common
    b,p=pairs.emit_board(model,g,e,public,native.LINE,texture(claim['flop']),viewer_code='B747_R150_'+claim['flop'].upper())
    assert b and b['assumed_preflop_ranges'] and (b['actual_pot_bb'],b['actual_effective_stack_bb'])==(4.16,98.17)
    assert p['pool_observed_marginal_lock_nodes']>0 and p['common_legal_hero_combos']>=len(common)
    for ver,key,row in zip(('GTO','NL2'),('gto_references','references'),rows,strict=True):
        assert p[ver+'_strict_combos']==row['strict_legal_combos'] and p[ver+'_compatible_hole_card_pairs']==row['compatible_hole_card_pairs']
        row['rendered_decision_hands']=common
        medium[key][source_key(native.MODEL,row)]=row
    b.update(certification_scope=claim['lock_scope'],source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',
        origin_solve_run_id=RUN,flop_native_solves_repeated=0,flop_bet_size_menu=claim['original_flop_bet_size_menu'],
        original_root_result_sha256=claim['root_sha256'],original_root_job_sha256=claim['root_job_sha256'])
    b['nl2_locked_variants'][0].update(source_run_role=b['source_run_role'],origin_solve_run_id=RUN,pool_sha256=native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),gto_parent_source_run_id=RUN,
        gto_parent_source_sha256=rootsha,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    p.update(rendered_decision_hands=common,source_blob_head=HEAD,worker_artifact=pin[0],worker_job=pin[1],
        original_root_result_sha256=claim['root_sha256'],original_root_job_sha256=claim['root_job_sha256'],
        original_conditional_jobs_sha256={v:record['policies'][v]['job_sha256'] for v in ('gto','exp_ip')})
    group['boards'].append(b);group['pins'].append(p)


def publish(args):
    assert sys.version_info[:2]==(3,11)
    solver=args.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==native.POOL
    pool=json.loads(pool_raw)['NL2']
    for path,digest in {WORKER:WORKER_BLOB,WORKFLOW:'9472dd758afd0b513c7f1305a9fe4f5a3b7955f4',prior.WORKER:prior.WORKER_BLOB,**native.PINS}.items():
        assert subprocess.check_output(['git','rev-parse',HEAD+':'+path],text=True).strip()==digest
        if path.startswith('tools/') and not path.endswith('hu_trainer_route_contract.cjs'):
            assert native.limp.git_blob(path)==digest
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    records=json.loads(before)['records'];model=records[native.MODEL]
    assert (len(records),model['frequency_rank'],model['label'],model['solver_profile'],model['assumed_model_node_spr'])==(
        392,150,'APPROX','LMP_CO_BB',23.558)
    assert not model['certified_3_to_5_exact_flop_boards']
    data=(args.output/'data').resolve(); assert not data.exists() and not data.is_relative_to(Path('data').resolve())
    evidence=data/'solver_evidence';partial=evidence/'partial';partial.mkdir(parents=True)
    current_route=subprocess.check_output(['node',native.ROUTE])
    (partial/'b747_rank150_routes.json').write_bytes(current_route)
    assert native.limp.git_blob('tools/hu_b732_rank80_boundaries.py')=='566b9b448a11adcae94388f9b9d30f384b77efc2'
    assert native.limp.git_blob(reserved.ROUTE)==reserved.ROUTE_BLOB
    r80=records[reserved.MODEL]
    assert (r80['frequency_rank'],r80['solver_profile'],r80['assumed_model_node_spr'])==(80,'LMP_CO_BB',23.558)
    reserved_route=subprocess.check_output(['node',reserved.ROUTE]);r80route=json.loads(reserved_route)
    receipts=args.receipts
    auth=json.loads((receipts/'receipt.json').read_bytes());authenticate(auth)
    (partial/'b747_auth_receipt.json').write_bytes(json_bytes(auth))
    results=[]
    with TemporaryDirectory(prefix='b747-originals-') as tmp:
        d=Path(tmp)
        group,medium=previous(d,solver,model,pipeline,pool,current_route)
        pairs.EVIDENCE=evidence
        frozen=d/'B743-source';materialize(HEAD,frozen)
        for flop in worker.CASES:
            pins=PINS[flop];aid,digest=pins['original'];cid,cdigest=pins['checkpoint']
            original=(receipts/f'{aid}.zip').read_bytes();root=(receipts/f'{cid}.zip').read_bytes()
            assert sha(original)==digest and sha(root)==cdigest
            folder=d/flop
            names=unpack_original(original,folder)
            identity=check_checkpoint(root,folder,flop)
            claim=replay_exact(frozen,WORKER,solver,folder,flop)
            assert (claim['schema'],claim['model_id'],claim['flop'],claim['source_worker_blob'],claim['base_worker_blob'])==(
                'NL2_B743_R150_PAIRED_A5_SOURCE_V1',native.MODEL,flop,WORKER_BLOB,prior.WORKER_BLOB)
            assert (claim['root_sha256'],claim['root_job_sha256'])==(identity['original_root_sha256'],identity['original_root_job_sha256'])
            assert claim['original_flop_roots_per_worker']==1 and claim['extra_flop_native_solves_in_continuation']==0
            assert (folder/'rendered-routes.json').read_bytes()==current_route
            expect={'proof.json','original-manifest.json','rendered-routes.json','flop/job.json','flop/result.json'}
            for turn in claim['turns']:
                for version in turn['policies']:
                    expect.update(turn['turn']+'-'+version+'/'+n for n in ('job.json','result.json'))
            assert expect==names
            code='B743_R150_'+flop.upper()
            (evidence/('NL2_'+code+'.zip')).write_bytes(original)
            (evidence/('NL2_B743_ROOT_R150_'+flop.upper()+'.zip')).write_bytes(root)
            (partial/('b747_'+flop.lower()+'_proof.json')).write_bytes((folder/'proof.json').read_bytes())
            if claim['selected']:
                stage_choice(folder,claim,code,[aid,pins['job'],digest],model,pipeline,pool,group,medium)
                group['pins'][-1].update(root_checkpoint_artifact_id=cid,root_checkpoint_sha256=cdigest)
            locked=[o['reach'] for t in claim['turns'] for o in t['policies'].get('exp_ip',{}).get('boards',{}).values()]
            joint=[r for r in locked if r['strict_legal_combos']>0 and r['compatible_hole_card_pairs']>0]
            measured=[r for r in joint if r['b50'] is not None and 'b50' in r['source_actions']]
            root_result=json.loads((folder/'flop/result.json').read_bytes())
            reserved_boundaries=[]
            for turn,_,_ in worker.CASES[flop]:
                _,boundary=reserved.gate(root_result,turn,r80route)
                assert boundary['boundary_sha256']==claim['additional_original_b33_call_boundaries'][turn]
                reserved_boundaries.append(boundary)
            results.append(dict(flop=flop,source_run=RUN,source_job=pins['job'],source_artifact=aid,source_sha256=digest,
                independent_original_root_archive=cid,independent_original_root_archive_sha256=cdigest,
                selected=claim['selected'],proof_sha256=sha((folder/'proof.json').read_bytes()),root_identity=identity,
                byte_identical_original_proof=True,same_original_root_bytes=True,reserved_rank80_boundaries=reserved_boundaries,
                native_gto_root_jobs=1,native_gto_turn_jobs=sum('gto' in t['policies'] for t in claim['turns']),
                native_locked_turn_jobs=sum('exp_ip' in t['policies'] for t in claim['turns']),
                native_locked_river_nodes=len(locked),actor_locked_joint_boards=len(joint),
                half_pot_assessed_joint_boards=len(measured),half_pot_nonpolarized_candidates=sum(r['b50']['candidate'] for r in measured),
                both_policies_rendered_positive_rivers=sum(len(t['common']) for t in claim['turns'])))
    flops=[b['flop'] for b in group['boards']]
    assert len(flops)==len({suit_isomorphism_class(f) for f in flops})==len(group['pins'])<=4
    assert flops[0]=='9c9h6c' and len(medium['references'])==len(flops)
    eligible=len(flops)>=3
    if eligible:
        target=evidence/'reverified';target.mkdir()
        (target/'rank150.json').write_bytes(json_bytes(group))
        (data/'nl2_hu_b747_locked_medium.json').write_bytes(json_bytes(medium))
    else:
        (partial/'b747_rank150.json').write_bytes(json_bytes(group))
        (partial/'b747_rank150_locked_medium.json').write_bytes(json_bytes(medium))
    totals={k:sum(r[k] for r in results) for k in ('native_gto_root_jobs','native_gto_turn_jobs','native_locked_turn_jobs','native_locked_river_nodes',
        'actor_locked_joint_boards','half_pot_assessed_joint_boards','half_pot_nonpolarized_candidates','both_policies_rendered_positive_rivers')}
    summary=dict(rank=150,model_id=native.MODEL,source_run_id=RUN,source_head=HEAD,prior_positive_flops=1,
        new_positive_flops=sum(bool(r['selected']) for r in results),distinct_positive_flops=len(flops),selected_exact_boards=flops,
        certified_eligible=eligible,selected_combined_actor_locked_boards=len(flops),selected_combined_half_pot_assessed_boards=len(flops),
        reserved_rank80=dict(model_id=reserved.MODEL,line=reserved.LINE,actor=1,source_route_blob=reserved.ROUTE_BLOB,
            route_sha256=sha(reserved_route),original_root_gate_blob='566b9b448a11adcae94388f9b9d30f384b77efc2',
            inspected_original_boundaries=sum(len(s['reserved_rank80_boundaries']) for s in results),
            feasible_turns=sum(bool(b['river_witnesses']) for s in results for b in s['reserved_rank80_boundaries']),
            native_conditional_jobs=0,new_actor_locked_boards=0,half_pot_assessed_boards=0),
        remaining_to_three=max(0,3-len(flops)),original_prior_pins=PRIOR_PINS,source_workers=results,
        protected_cert_records=sum(v['label']=='CERT-MULTIBOARD' for v in records.values()),native_solves_repeated=0,
        live_registry_written=False,**totals)
    (data/'nl2_hu_b747_summary.json').write_bytes(json_bytes(summary))
    assert registry.read_bytes()==before
    print(json.dumps(summary))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','receipts','output'):cli.add_argument('--'+name,required=True,type=Path)
    publish(cli.parse_args())
