"""Rebuild the three B717 original rank29 proofs without a native driver."""
import argparse, base64, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from zipfile import ZipFile
from hu_b467_river_source_gate import sha,json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b717_rank29_low_connected import CASES
from hu_b703_rank29_highcards import MODEL, LINE
from hu_b710_collect import REPO,REPO_ID,BRANCH,api

SOURCE='dfedf0e3e17a7da5f68583e250df3fa91de7b8ad'
RUN=45325726065
WORKER='tools/hu_b717_rank29_low_connected.py'
WORKFLOW='.github/workflows/nl2-hu-b717-rank29-low-connected.yml'
JOBS={'8s7s6d':138214736807,'6c5c4h':138214737158,'5d4d2c':138214737075}
PINS={'6c5c4h': (14889986271, '10dd43864d3728cfc7cf47eddcd3cf30e2d02ba5b36187ee2111c96b4eba13c5'), '8s7s6d': (14889801781, '90148d38fb50111bb7828ec004b31283a7b4f113c8e62916d05e87571251cce5'), '5d4d2c': (14889004511, '84b79096e1422754c031a8a6495e28fca282dfdb7d40d65aea2b09bd215b9f8e')}


def export_original(frozen):
    names=['tools','data/nl2_hu_b485_original_artifacts.json','data/nl2_hu_verified_extensions.json',
      'data/nl2_hu_b582_rank29_reach.json','data/solver_evidence/NL2_B580_R27_LMP.zip','lines_data.js','hwrange.js',
      'nl2.js','nl2_cert_registry.js','nl2_reach.js','nl2_hu_model.js','nl2_rules.js','nl2_titles.js']
    with tempfile.TemporaryFile() as archive:
        subprocess.run(['git','archive','--format=tar',SOURCE,'--',*names],check=True,stdout=archive)
        archive.seek(0)
        subprocess.run(['tar','-xf','-','-C',str(frozen)],stdin=archive,check=True)


def run(a):
    assert sys.version_info[:2]==(3,11) and set(CASES)==set(JOBS)==set(PINS)
    raw=json.loads((a.receipts/'source-receipt.json').read_bytes())
    run,jobs,arts=raw['run'],raw['jobs'],raw['artifacts']
    assert (run['id'],run['head_sha'],run['head_branch'],run['path'],run['status'],run['conclusion'])==(RUN,SOURCE,BRANCH,WORKFLOW,'completed','success')
    assert (run['repository']['id'],run['repository']['full_name'])==(REPO_ID,REPO)
    assert len(jobs)==len(arts)==3
    evidence=a.output/'data/solver_evidence';evidence.mkdir(parents=True,exist_ok=False);stats=[];certs=[];auth=[]
    with tempfile.TemporaryDirectory() as tmp:
        frozen=Path(tmp)/'source';frozen.mkdir();export_original(frozen)
        for flop in CASES:
            jid=JOBS[flop];aid,digest=PINS[flop]
            j,=[j for j in jobs if j['id']==jid];m,=[m for m in arts if m['id']==aid]
            assert (j['run_id'],j['head_sha'],j['run_attempt'],j['name'],j['status'],j['conclusion'])==(RUN,SOURCE,run['run_attempt'],f'solve ({flop})','completed','success')
            successful={v['name'] for v in j['steps'] if (v['status'],v['conclusion'])==('completed','success')}
            assert {'Build the pinned native solver','Solve native roots and only reachable displayed GTO and actor-locked rivers','Run actions/upload-artifact@v4'}<=successful
            w=m['workflow_run']
            assert (w['id'],w['head_sha'],w['head_branch'],w['repository_id'],w['head_repository_id'])==(RUN,SOURCE,BRANCH,REPO_ID,REPO_ID)
            assert (m['digest'],m['name'])==('sha256:'+digest,'B717-R29-'+flop)
            zipfile=a.receipts/(str(aid)+'.zip');assert sha(zipfile.read_bytes())==digest
            folder=Path(tmp)/flop;folder.mkdir()
            with ZipFile(zipfile) as z:
                original=z.read('proof.json');q=json.loads(original)
                names={'proof.json','rendered-routes.json','original-manifest.json','flop/job.json','flop/result.json'}
                for t in q['turns']:
                    assert t['turn'] in CASES[flop]
                    for kind,present in [('gto',t['gto_solved']),('exp_oop',t['actor_locked'])]:
                        if present:names.update(t['turn']+'-'+kind+'/'+f for f in ('job.json','result.json'))
                assert (q['rank'],q['flop'],q['model_id'],q['line'],q['actor'])==(29,flop,MODEL,LINE,0)
                assert q['schema']=='NL2_B717_R29_LOW_CONNECTED_ORIGINAL_V1' and q['not_a_certification']
                assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==names
                assert set(q['native_file_sha256'])==names-{'proof.json'} and sum(e.file_size for e in z.infolist())<120*1024*1024
                for n in names:
                    f=folder/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
                    if n!='proof.json':assert sha(f.read_bytes())==q['native_file_sha256'][n]
            subprocess.run([sys.executable,str(frozen/WORKER),'--solver',str(a.solver.resolve()),'--output',str(folder),'--flop',flop],
                cwd=frozen,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),check=True,stdout=subprocess.DEVNULL)
            assert (folder/'proof.json').read_bytes()==original
            assert json.loads(subprocess.check_output(['node','tools/hu_b703_rank29_routes.cjs']))==json.loads((folder/'rendered-routes.json').read_bytes())
            locked=set();reached=set();medium=set();checks=[];gto_count=0
            for t in q['turns']:
                gto_count+=len(t.get('gto_rivers',{}))
                for public,v in t.get('nl2_rivers',{}).items():
                    assert public not in locked;locked.add(public)
                    if not v['strict_legal_combos']:
                        assert v['compatible_hole_card_pairs']==0 and v['b50'] is None
                        continue
                    assert v['compatible_hole_card_pairs']>=v['strict_legal_combos']>0 and v['b50'] is not None
                    assert any(base64.b64decode(v['compatible_action_mask_b64'],validate=True));reached.add(public)
                    if v['b50']['candidate']:medium.add(public)
                for v in t['checks']:
                    pub=v['public_board'];g=t['gto_rivers'][pub];e=t['nl2_rivers'][pub]
                    common=sorted(set(g['displayed_b75_hands'])&set(e['displayed_b75_hands']))
                    assert pub in reached and g['compatible_hole_card_pairs']>=g['strict_legal_combos']>0 and common and v['shared_hands']==common
                    checks.append(v)
            assert (len(locked),len(reached),len(reached),len(medium),int(bool(checks)))==tuple(q[k] for k in ('native_locked_public_boards','reachable_locked_public_boards','half_pot_assessments','nonpolarized_candidates','positive_distinct_flops'))
            name='NL2_B717_R29_'+flop.upper()+'.zip';shutil.copyfile(zipfile,evidence/name)
            if checks:certs.append(flop)
            auth.append(dict(flop=flop,job=jid,artifact=aid,pinned_sha256=digest,archive=name,proof_sha256=sha(original),job_name=j['name'],source_job_steps=sorted(successful),artifact_name=m['name'],repository_id=REPO_ID,run_attempt=j['run_attempt']))
            stats.append(dict(flop=flop,flop_source=q['root_sha256'],static_witnesses=q['preregistered_range_witnesses'],gto_turns=q['gto_turn_subgames'],actor_locked_turns=q['actor_locked_turn_subgames'],gto_river_decisions=gto_count,native_locked_public_boards=len(locked),zero_joint_locked_boards=len(locked-reached),reachable_locked_public_boards=len(reached),half_pot_assessments=len(reached),nonpolarized_candidates=len(medium),fully_displayed_both_policy_decisions=checks,negative_stages=[dict(turn=t['turn'],stage=t['negative_stage'],oop_b50_accepted=t['root_gate']['oop_b50_accepted'],flop_ui_after_ancestry=t['root_gate']['flop_ui_after_ancestry'],turn_ui_after_ancestry=t['root_gate']['turn_ui_after_ancestry']) for t in q['turns']]))
    assert len({suit_isomorphism_class(f) for f in certs})==len(certs)
    summary=dict(schema='NL2_B721_AUTHENTICATED_R29_CONTINUATIONS_V1',rank=29,model_id=MODEL,source_run=RUN,source_head=SOURCE,source_workflow=WORKFLOW,source_workers=auth,
        rows=stats,positive_original_flops=certs,native_solves_repeated=0,locked_boards_with_positive_joint_reach=sum(s['reachable_locked_public_boards'] for s in stats),
        native_locked_public_boards=sum(s['native_locked_public_boards'] for s in stats),half_pot_assessed_boards=sum(s['half_pot_assessments'] for s in stats),nonpolarized_candidates=sum(s['nonpolarized_candidates'] for s in stats))
    # Keep stable provenance only; signed download URLs and moving PR pointers are not evidence.
    pick=lambda d,ks:{k:d[k] for k in ks.split()}
    fixed=pick(run,'id head_sha head_branch path status conclusion run_attempt')
    fixed['repository']=pick(run['repository'],'id full_name')
    checked_jobs=[]
    for item in sorted(jobs,key=lambda j:j['id']):
        record=pick(item,'id run_id head_sha run_attempt name status conclusion')
        record['steps']=[pick(t,'name status conclusion') for t in item['steps']];checked_jobs.append(record)
    checked_artifacts=[]
    for art in sorted(arts,key=lambda m:m['id']):
        record=pick(art,'id name digest')
        record['workflow_run']=pick(art['workflow_run'],'id head_sha head_branch repository_id head_repository_id')
        checked_artifacts.append(record)
    (a.output/'data/nl2_hu_b721_source_receipt.json').write_bytes(json_bytes(dict(run=fixed,jobs=checked_jobs,artifacts=checked_artifacts)))
    (a.output/'data/nl2_hu_b721_rank29_receipt.json').write_bytes(json_bytes(summary))
    print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','source_workers')}))


def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    r=json.loads(api(f'actions/runs/{RUN}'));j=json.loads(api(f'actions/runs/{RUN}/jobs?filter=latest&per_page=100'));arts=json.loads(api(f'actions/runs/{RUN}/artifacts?per_page=100'))
    assert j['total_count']==arts['total_count']==3
    (folder/'source-receipt.json').write_bytes(json_bytes(dict(run=r,jobs=j['jobs'],artifacts=arts['artifacts'])))
    for aid,expected in PINS.values():
        raw=api(f'actions/artifacts/{aid}/zip');assert sha(raw)==expected;(folder/(str(aid)+'.zip')).write_bytes(raw)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','receipts','output'):p.add_argument('--'+k,required=True,type=Path)
    g=p.add_mutually_exclusive_group();g.add_argument('--collect',action='store_true');g.add_argument('--published',type=Path,help='Published data directory for a fully offline replay');a=p.parse_args()
    if a.collect:collect(a.receipts)
    if a.published:
        a.receipts.mkdir(parents=True,exist_ok=False)
        shutil.copyfile(a.published/'nl2_hu_b721_source_receipt.json',a.receipts/'source-receipt.json')
        for flop,(aid,_) in PINS.items():
            shutil.copyfile(a.published/'solver_evidence'/('NL2_B717_R29_'+flop.upper()+'.zip'),a.receipts/(str(aid)+'.zip'))
    run(a)
