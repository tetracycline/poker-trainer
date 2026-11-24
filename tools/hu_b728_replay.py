"""Replay B727's original rank229 work and the published B679 partial in an isolated stage."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b679_publish as prior
import hu_b727_rank229 as native
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b710_publish import unpack_original
from hu_board_reach_corrections import source_key

RUN=45328741294
HEAD='b6381a2c0b7c6b1a1df4c8547223f9df0485ac41'
BRANCH='fix/nl2-hu-lines-audit-20261118'
WORKFLOW='.github/workflows/nl2-hu-b727-rank229-rivers.yml'
WORKER='tools/hu_b727_rank229.py'
ROUTE='tools/hu_b676_checked_routes.cjs'
EVIDENCE=Path('data/solver_evidence')
OLD_ROOT_NAME='NL2_B728_SB3_KSQH4D_ORIGINAL_ROOT.zip'
JOBS={'KsQh4d':138224496317,'KdQc5h':138224496265,'KhJc4s':138224495982}
ARTIFACTS={
    "KdQc5h": [
        14891086994,
        "f8b197eaff99f0d7f07849d2ec7166968f18df5a7bd8f6424490f272eb4d693f"
    ],
    "KhJc4s": [
        14891037314,
        "534a4b8716797c0944408e0fde45583b210c72d36223c3adf7a39357fa75c700"
    ],
    "KsQh4d": [
        14890259054,
        "736625ae1bd73c3d8363c886838c797b73f5335949964223b4da2a50e3d6d677"
    ]
}
PRIOR_BLOBS={
    'partial/rank229.json':'979f1788b78c67b33b2f17ad4159a55cb1bb1806',
    'partial/b679_rank229_locked_medium.json':'1ff3dfac837d4fc2510010b09b96275c18320e16',
    'partial/b679_auth_receipt.json':'25273cb7da6753debe763775a3644480bf7215f3',
    'NL2_B676_SB3_KC9D4H.zip':'b7357ee1e05931262438e069b0757cc5949da455',
    'NL2_MULTIBOARD_B679_R229_KC9D4H.json.gz':'a84a3ed30d65e08aeb51501426232d6841ff44b2',
}
STEPS={'Check the original ranges, branch prices and displayed middle pairs','Compile the pinned native solver',
    'Solve the missing river trees and replay both policies','Run actions/upload-artifact@v4'}


def read(path):
    return json.loads(path.read_bytes())


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json_bytes(value))


def git_blob(path):
    return subprocess.check_output(['git','hash-object',str(path)],text=True).strip()


def fields(mapping,names):
    return {key:mapping[key] for key in names.split()}


def authenticate(raw):
    run=raw['run'];r=fields(run,'id head_sha head_branch path status conclusion run_attempt')
    r['repository']=fields(run['repository'],'id full_name')
    assert (r['id'],r['head_sha'],r['head_branch'],r['path'],r['status'],r['conclusion'])==(RUN,HEAD,BRANCH,WORKFLOW,'completed','success')
    assert r['repository']==dict(id=1438346845,full_name='tetracycline/poker-trainer')
    result=dict(run=r,jobs=[],artifacts=[])
    assert set(ARTIFACTS)==set(JOBS) and len(raw['jobs'])==len(raw['artifacts'])==3
    for flop,(aid,digest) in ARTIFACTS.items():
        job,=[j for j in raw['jobs'] if j['id']==JOBS[flop]]
        assert (job['run_id'],job['head_sha'],job['run_attempt'],job['name'],job['status'],job['conclusion'])==(
            RUN,HEAD,r['run_attempt'],f'solve ({flop})','completed','success')
        assert STEPS<={s['name'] for s in job['steps'] if (s['status'],s['conclusion'])==('completed','success')}
        j=fields(job,'id run_id head_sha run_attempt name status conclusion')
        j['steps']=[fields(s,'number name status conclusion') for s in job['steps']]
        a,=[t for t in raw['artifacts'] if t['id']==aid]
        assert (a['name'],a['digest'],a['expired'])==('B727-R229-'+flop,'sha256:'+digest,False)
        t=fields(a,'id name digest size_in_bytes created_at expires_at expired')
        t['workflow_run']=fields(a['workflow_run'],'id head_sha head_branch repository_id head_repository_id')
        assert t['workflow_run']==dict(id=RUN,head_sha=HEAD,head_branch=BRANCH,repository_id=1438346845,head_repository_id=1438346845)
        result['jobs'].append(j);result['artifacts'].append(t)
    return result


def compare_hand_policies(g,e,public,route):
    a,ga=prior.decision(g,public,route)
    b,eb=prior.decision(e,public,route)
    common=[]
    for h in sorted(ga.keys()&eb.keys()):
        classes,label,g_policy=ga[h]
        assert (classes,label)==eb[h][:2] and label=='過'
        assert all('x' in policy['accepted_actions'] for policy in (g_policy,eb[h][2]))
        common.append(dict(hand=h,flop_class=classes[0],turn_class=classes[1],river_class=classes[2],
            displayed_suggestion=label,gto=g_policy,nl2=eb[h][2]))
    for row in (a,b):
        assert row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0 and row['b50'] is not None
        row['rendered_decision_hands']=common
    return common,a,b


def verify_prior(folder,solver,pipeline,pool,routes):
    for path,digest in PRIOR_BLOBS.items():assert git_blob(EVIDENCE/path)==digest
    group=read(EVIDENCE/'partial/rank229.json')
    board,=group['boards'];pin,=group['pins']
    assert (group['model_id'],group['rank'],board['flop'],board['public_board'])==(native.MODEL,229,'Kc9d4h','4h9dKc8h3d')
    archive=(EVIDENCE/('NL2_'+pin['archive_code']+'.zip')).read_bytes()
    assert sha(archive)==pin['archive_sha256']
    viewer=EVIDENCE/('NL2_MULTIBOARD_'+pin['viewer_archive_code']+'.json.gz')
    assert sha(viewer.read_bytes())==pin['viewer_sha256']
    receipt=read(EVIDENCE/'partial/b679_auth_receipt.json')
    job,=[x for x in receipt['workers'] if x['artifact']['id']==pin['worker_artifact']]
    w,=[x for x in prior.WORKERS if x['id']==pin['worker_artifact']]
    prior.authenticate(receipt['run'],job['job'],job['artifact'],w)
    folder.mkdir()
    unpack_original(archive,folder)
    old=(folder/'proof.json').read_bytes()
    assert (folder/'rendered-routes.json').read_bytes()==routes
    prior.native.run(SimpleNamespace(solver=solver,flop='Kc9d4h',output=folder,routes=folder/'rendered-routes.json',driver=None))
    assert (folder/'proof.json').read_bytes()==old
    selected=json.loads(old)['selected']['229']
    g,e=prior.sources(folder,w,selected,pipeline,pool,pin['archive_code'])
    assert (g['source_sha256'],e['source_sha256'])==(pin['original_GTO_SHA256'],pin['actual_NL2_SHA256'])
    hands,grow,erow=compare_hand_policies(g,e,board['public_board'],json.loads(routes)['229'])
    assert hands==pin['rendered_decision_hands'] and [x['hand'] for x in hands]==['6h9h']
    medium=read(EVIDENCE/'partial/b679_rank229_locked_medium.json')
    for key,row in (('gto_references',grow),('references',erow)):
        assert medium[key]=={source_key(native.MODEL,row):row}
    return group,medium


def source_workspace(temp):
    # The source worker asserted its historical APPROX status. Materialize this
    # commit so the archives continue to replay after a future promotion.
    import tarfile
    import io
    paths=['tools','lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js',
        'data/nl2_hu_multiboard_status_current.json','data/nl2_hu_b485_original_artifacts.json','data/solver_evidence/partial/rank229.json']
    content=subprocess.check_output(['git','archive','--format=tar',HEAD,'--',*paths])
    with tarfile.open(fileobj=io.BytesIO(content)) as archive:
        for m in archive:
            path=Path(m.name)
            assert not path.is_absolute() and '..' not in path.parts
            final=temp/path
            if m.isdir(): final.mkdir(parents=True,exist_ok=True)
            else:
                assert m.isfile() and not final.exists()
                final.parent.mkdir(parents=True,exist_ok=True)
                final.write_bytes(archive.extractfile(m).read())
    assert git_blob(temp/WORKER)=='601385f1ead29779ca5bf30f40237f13abba2c43'
    assert git_blob(temp/ROUTE)=='522ea33d7326c38a7493507cbde96b5df4a6f3f7'


def old_root_receipt(info):
    r=fields(info,'id name digest')
    r['workflow_run']=fields(info['workflow_run'],'id head_sha repository_id head_repository_id')
    assert (r['id'],r['name'],r['digest'])==(native.ARTIFACT,native.PIN['name'],'sha256:'+native.PIN['sha256'])
    assert r['workflow_run']==dict(id=native.PIN['run'],head_sha=native.PIN['head'],repository_id=1438346845,head_repository_id=1438346845)
    return r


def negative(folder,temp,root,flop,raw,solver,routes,old_inputs):
    aid,digest=ARTIFACTS[flop]
    assert sha(raw)==digest
    paths=unpack_original(raw,folder)
    original=(folder/'proof.json').read_bytes()
    d=json.loads(original)
    assert (d['schema'],d['rank'],d['model'],d['flop'],d['spot'],d['line'],d['actor'])==(
        'NL2_B727_CHECKED_SB3_R229_V1',229,native.MODEL,flop,native.SPOT,native.LINE,0)
    assert d['solver']==native.SOLVER and d['rust']==native.RUST and d['pool_sha256']==native.POOL
    assert d['route_sha256']==sha(routes) and (folder/'rendered-routes.json').read_bytes()==routes
    assert [t['turn'] for t in d['turns']]==native.CASES[flop] and not d['flop_solves_repeated']
    expected={'proof.json','rendered-routes.json'}
    if flop!=native.OLD:
        expected|={'flop/job.json','flop/result.json'}
        assert d['source']==dict(new_native_flop=True)
        root=read(folder/'flop/result.json')
    for t in d['turns']:
        for version,key in (('gto','gto'),('exp_oop','nl2')):
            if t[key]:expected.update(t['turn']+'-'+version+'/'+n for n in ('job.json','result.json'))
    assert paths==expected and paths==set(d['native_files'])|{'proof.json'}
    assert all(sha((folder/path).read_bytes())==v for path,v in d['native_files'].items())
    subprocess.run([sys.executable,str(temp/WORKER),'--solver',str(solver),'--receipts',str(old_inputs),
        '--flop',flop,'--output',str(folder)],cwd=temp,check=True,stdout=subprocess.DEVNULL)
    assert (folder/'proof.json').read_bytes()==original
    assert all(sha((folder/path).read_bytes())==v for path,v in d['native_files'].items())
    turns=[]
    for t in d['turns']:
        turn=t['turn']
        assert not t['common']
        row=dict(turn=turn,parent_compatible_rendered_hands=t['gate']['compatible_hero_hands'],
            gto_displayed_nodes=sum(bool(o['displayed_check_hands']) for o in t['gto'].values()))
        turns.append(row)
        if not t['nl2']:
            assert flop=='KhJc4s' and not t['gto'] and not t['gate']['river_extracts']
            continue
        assert row['gto_displayed_nodes']>0
        e=read(folder/(turn+'-exp_oop')/'result.json')
        job=read(folder/(turn+'-exp_oop')/'job.json')
        assert job['hero']==0 and job['locks'] and e['info']['lock_stats']
        measures=t['measured_lock_application']
        actual=[p for p,n in measures['driver_tree_nodes'].items() if n>0 and p in measures['marginal_targets']]
        assert actual
        picks=t['gate']['river_extracts']
        e.update(line0='x x',rivers=picks,turn=turn)
        masks=native.game_reach(root,e)[0]
        nodes={n['board']:n for n in e['nodes'] if (n['player'],n['line'])==(0,native.LINE)}
        assert nodes.keys()==t['nl2'].keys() and len(nodes)==len(picks)==16
        for public,n in nodes.items():
            assert (n['pot'],n['bets'],e['stack'])==(2100,[0,0],9000)
            o=native.proof(root,e,n,masks)
            assert t['nl2'][public]==dict(reach=o,displayed_check_hands=[])
            assert (o['strict_legal_combos'],o['compatible_hole_card_pairs'],o['b50'])==(0,0,None)
        row.update(zero_joint_locked_public_boards=sorted(nodes),applied_pool_patterns=len(actual),
            locked_native_job_sha256=d['native_files'][turn+'-exp_oop/job.json'],
            locked_native_result_sha256=d['native_files'][turn+'-exp_oop/result.json'])
    total=sum(len(t.get('zero_joint_locked_public_boards',[])) for t in turns)
    assert d['selected'] is None and d['positive_distinct_flops']==0
    assert (d['native_locked_public_boards'],d['joint_halfpot_assessed'],d['nonpolarized_candidates'])==(total,0,0)
    return dict(flop=flop,worker_artifact=aid,worker_job=JOBS[flop],archive_sha256=digest,proof_sha256=sha(original),
        source_origin=d['source'],zero_joint_locked_public_boards=total,turns=turns)


def main(a):
    assert sys.version_info[:2]==(3,11)
    stage=a.output.resolve();solver=a.solver.resolve()
    assert not stage.exists() and Path('data').resolve() not in (stage,*stage.parents)
    evidence=stage/'solver_evidence';evidence.mkdir(parents=True)
    source_api=read(a.receipts)
    auth=authenticate(source_api)
    old_input=a.original_root or a.archives
    old_path=old_input/f'{native.ARTIFACT}.zip'
    if not old_path.exists():old_path=old_input/OLD_ROOT_NAME
    oldraw=old_path.read_bytes();assert sha(oldraw)==native.PIN['sha256']
    if 'old_root_artifact' in source_api:old_receipt=source_api['old_root_artifact']
    else:old_receipt=read(old_input/f'{native.ARTIFACT}.json')
    auth['old_root_artifact']=old_root_receipt(old_receipt)
    (evidence/OLD_ROOT_NAME).write_bytes(oldraw)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    py=solver/'postflop/py'
    assert sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    sys.path.insert(0,str(py));import pipeline,ranges
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==native.POOL
    pool=json.loads(poolraw)['NL2']
    routes=subprocess.check_output(['node',ROUTE])
    reports=[]
    with TemporaryDirectory(prefix='b728-r229-') as td:
        tree=Path(td)/'source'
        source_workspace(tree)
        group,medium=verify_prior(Path(td)/'prior',solver,pipeline,pool,routes)
        old_inputs=Path(td)/'old-root';old_inputs.mkdir()
        (old_inputs/f'{native.ARTIFACT}.zip').write_bytes(oldraw)
        write(old_inputs/f'{native.ARTIFACT}.json',auth['old_root_artifact'])
        boundary=native.load_original(old_inputs,native.ARTIFACT,native.PIN,native.SPOT,native.OLD,'Tc','gto',
            pot=2100,stack=9000,pipeline=pipeline,ranges=ranges)
        for flop in JOBS:
            aid,digest=ARTIFACTS[flop];file='NL2_B727_R229_'+flop.upper()+'.zip'
            path=a.archives/f'{aid}.zip'
            raw=(path if path.exists() else a.archives/file).read_bytes()
            folder=Path(td)/flop;folder.mkdir()
            rec=negative(folder,tree,boundary['source']['root'],flop,raw,solver,routes,old_inputs)
            if flop==native.OLD:assert rec['source_origin']==boundary['identity']
            reports.append(dict(archive=file,**rec))
            (evidence/file).write_bytes(raw)
    all_nodes=[n for r in reports for t in r['turns'] for n in t.get('zero_joint_locked_public_boards',[])]
    assert len(all_nodes)==len(set(all_nodes))==64
    retained=group['pins'][0]
    summary=dict(schema='NL2_HU_B728_R229_ORIGINAL_LOCKED_ZERO_JOINT_RIVERS_V1',rank=229,model_id=native.MODEL,
        source_run=RUN,source_head=HEAD,source_workers=reports,retained_prior_positive_flops=1,new_positive_flops=0,
        distinct_positive_flops=1,cert_eligible_ranks=[],new_named_locked_public_boards=64,new_zero_joint_locked_public_boards=64,
        new_joint_halfpot_assessments=0,new_nonpolarized_candidates=0,new_native_flop_roots=2,reused_native_flop_roots=1,
        retained_original_positive=dict(flop=retained['flop'],public_board=retained['public_board'],raw_flop_archive=retained['archive_code'],
            raw_flop_archive_sha256=retained['archive_sha256'],viewer_sha256=retained['viewer_sha256'],
            rendered_decision_hands=retained['rendered_decision_hands'],positive_gto_pairs=retained['GTO_compatible_hole_card_pairs'],
            positive_nl2_pairs=retained['NL2_compatible_hole_card_pairs']),publisher_native_solves_repeated=0)
    write(stage/'nl2_hu_b728_summary.json',summary)
    write(stage/'nl2_hu_b728_source_receipts.json',auth)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('source_workers','retained_original_positive')}))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--archives',type=Path,default=EVIDENCE)
    cli.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b728_source_receipts.json'))
    cli.add_argument('--original-root',type=Path)
    for key in ('solver','output'):cli.add_argument('--'+key,type=Path,required=True)
    main(cli.parse_args())
