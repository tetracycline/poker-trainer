"""Verify the three B783 original roots and retain the two published rank229 river checks."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b781_rank229_partial as prior
import hu_b783_rank229_king_nines as worker
import hu_b786_collect as source
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b710_publish import unpack_original
from hu_b747_rank150_replay import materialize

ROOT=Path('data/solver_evidence')
RECEIPT_PIN='63fc75d8fd5c4cbad26d51f832f84b8c1df176dd'
model_id=worker.base.MODEL


def read(p):
    return json.loads(p.read_bytes())


def previous(directory,solver):
    """Verify both old policies, viewers and the precise published group."""
    a=directory/'prior-input';a.mkdir()
    prior_art,prior_sha=prior.receipt.PINS['Kd9c5h']
    raw=(ROOT/'NL2_B780_R229_KD9C5H.zip').read_bytes()
    assert sha(raw)==prior_sha
    (a/(str(prior_art)+'.zip')).write_bytes(raw)
    (a/'receipt.json').write_bytes(Path('data/nl2_hu_b781_source_manifest.json').read_bytes())
    st=directory/'reverified-prior'
    prior.run(SimpleNamespace(archives=a,output=st,solver=solver))
    ev=st/'solver_evidence'
    for grp in ('partial/b781_rank229.json','partial/b781_rank229_locked_medium.json'):
        assert (ev/grp).read_bytes()==(ROOT/grp).read_bytes()
    group=read(ev/'partial/b781_rank229.json')
    medium=read(ev/'partial/b781_rank229_locked_medium.json')
    assert [b['flop'] for b in group['boards']]==['Kc9d4h','Kd9c5h'] and len(group['pins'])==2
    for pin in group['pins']:
        view='NL2_MULTIBOARD_'+pin['viewer_archive_code']+'.json.gz'
        assert sha((ROOT/view).read_bytes())==pin['viewer_sha256']
        if pin['flop']=='Kd9c5h':
            assert (ev/view).read_bytes()==(ROOT/view).read_bytes()
    medium['schema']='NL2_HU_B786_ORIGINAL_LOCKED_MEDIUM_V1'
    return group,medium


def verify(frozen,folder,source_zip,checkpoint_zip,flop,solver,route):
    names=unpack_original(source_zip,folder)
    assert names=={'flop/job.json','flop/result.json','rendered-routes.json','proof.json'}
    original=(folder/'proof.json').read_bytes()
    claim=json.loads(original)
    with ZipFile(io.BytesIO(checkpoint_zip)) as cp:
        assert sorted(n for n in cp.namelist() if not n.endswith('/'))==['checkpoint.json','flop/job.json','flop/result.json']
        assert all(cp.read(n)==(folder/n).read_bytes() for n in ('flop/job.json','flop/result.json'))
        checkpoint=json.loads(cp.read('checkpoint.json'))
    assert (folder/'rendered-routes.json').read_bytes()==route
    assert (claim['rank'],claim['model_id'],claim['schema'],claim['source_worker_blob'],claim['flop'],claim['line'],claim['actor'])==(
        229,model_id,'NL2_B783_RANK229_NEW_96S_ROOTS_V1',source.BLOBS[source.WORKER],flop,worker.LINE,0)
    assert checkpoint==claim['original_flop_source'] and checkpoint['flop']==flop
    expected={n:sha((folder/n).read_bytes()) for n in sorted(names-{'proof.json'})}
    assert expected==claim['native_file_sha256'] and checkpoint['root_job_sha256']==expected['flop/job.json'] and checkpoint['root_result_sha256']==expected['flop/result.json']
    # No native executable. The frozen worker reconstructs the complete job and
    # checks serialized bytes, pinned prior policy pairs, root ranges and UI.
    audit="""
import runpy,sys
from pathlib import Path
program=sys.argv.pop(1);sys.argv[0]=program;sys.path.insert(0,str(Path(program).parent))
import hu_b637_rank57 as reader
from hu_b467_river_source_gate import compact
out=Path(sys.argv[sys.argv.index('--output')+1])
saved=reader.solve;seen=[]
def checked(path,job,driver):
    assert driver is None and path==out/'flop' and not seen
    assert (path/'job.json').read_bytes()==compact(job)
    seen.append(path)
    return saved(path,job,None)
reader.solve=checked
runpy.run_path(program,run_name='__main__')
assert seen==[out/'flop']
"""
    subprocess.run([sys.executable,'-c',audit,str(frozen/source.WORKER),'--solver',str(solver),'--output',str(folder),'--flop',flop],cwd=frozen,check=True)
    assert (folder/'proof.json').read_bytes()==original and all(sha((folder/n).read_bytes())==d for n,d in expected.items())
    root=read(folder/'flop/result.json');job=read(folder/'flop/job.json')
    assert (job['flop'],job['flop_oop'],job['flop_ip'],job['pot'],job['stack'])==(flop,'50%','50%',2100,9000)
    assert (root['flop'],root['pot'],root['stack'])==(flop,2100,9000) and 0<=root['info']['gto_expl_pct']<=.5
    assert checkpoint['root_nodes_sha256']==sha(compact(root['nodes'])) and not root['info'].get('lock_stats')
    first,=(r for r in root['nodes'] if r['line']=='')
    after,=(r for r in root['nodes'] if r['line']=='x')
    sb=worker.base.accepted(first,root['hands'],'x');btn=worker.base.accepted(after,root['hands'],'x')
    assert not sb and len(btn)>0 and first['acts']==['x','b50']
    sb_nonzero=sum(w>1e-4 for w in first['w'][0])
    check=[]
    for i,w in enumerate(first['w'][0]):
        if w<=1e-4:continue
        n=len(root['hands'][0]);x,b=(first['strat'][k*n+i] for k in (0,1))
        assert b>0 and x>=0
        check.append(x/(x+b))
    assert len(check)==sb_nonzero
    assert claim['positive_distinct_flops']==0 and claim['selected'] is None
    assert [t['turn'] for t in claim['turns']]==worker.CASES[flop]
    for t in claim['turns']:
        turn=t['turn'];hero='6'+turn[1]+'9'+turn[1]
        boundary,foes,gate=worker.flop_gate(root,turn,hero,json.loads(route)['229'])
        assert gate==t['root_gate'] and t['hero']==hero and not gate['hero_flop_check']
        assert gate['two_street_ui'] and gate['eligible_rivers']==[] and t['policies']==t['common']=={}
    return dict(flop=flop,raw_root_nodes=len(root['nodes']),flop_menu_both='50%',root_identity=checkpoint,
                root_gto_gap_pct=root['info']['gto_expl_pct'],original_sb_hand_count=len(root['hands'][0]),
                original_positive_weight_sb_hands=sb_nonzero,original_sb_accepted_check=len(sb),original_btn_accepted_check=len(btn),
                max_original_sb_check_frequency=max(check),turns=claim['turns'],original_proof_sha256=sha(original),
                conditional_cfr_jobs=0,negative_reason='NO_SB_FLOP_CHECK_ACCEPTED_IN_ENTIRE_ORIGINAL_RANGE')


def publish(args):
    assert sys.version_info[:2]==(3,11)
    reg=Path('data/nl2_hu_multiboard_status_current.json');initial=reg.read_bytes()
    model=json.loads(initial)['records'][model_id]
    assert (model['frequency_rank'],model['solver_profile'])==(229,'SB3_BTN')
    solver=args.solver.resolve()
    for path,pin in source.BLOBS.items():
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==pin
    receipt=args.archives/'receipt.json'
    assert worker.blob(receipt)==RECEIPT_PIN
    auth=source.validate(read(receipt));assert receipt.read_bytes()==json_bytes(auth)
    out=args.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    route=subprocess.check_output(['node',worker.ROUTE])
    details=[]
    with TemporaryDirectory(prefix='b786-') as tmp:
        directory=Path(tmp);frozen=directory/'frozen'
        materialize(source.HEAD,frozen)
        assert route==subprocess.check_output(['node',worker.ROUTE],cwd=frozen)
        group,medium=previous(directory,solver)
        for flop,job_id in source.JOBS.items():
            archive=[]
            for prefix,name in [('B783-R229-','B783_R229_'),('B783-root-R229-','B783_ROOT_R229_')]:
                meta,=(a for a in auth['artifacts'] if a['name']==prefix+flop)
                raw=(args.archives/(str(meta['id'])+'.zip')).read_bytes()
                assert len(raw)==meta['size_in_bytes'] and 'sha256:'+sha(raw)==meta['digest']
                (ev/('NL2_'+name+flop.upper()+'.zip')).write_bytes(raw)
                archive.append((meta,raw))
            (full,raw),(cp,root_raw)=archive
            v=verify(frozen,directory/flop,raw,root_raw,flop,solver,route)
            v.update(original_job_id=job_id,worker_artifact=full['id'],worker_sha256=sha(raw),
                     checkpoint_artifact=cp['id'],checkpoint_sha256=sha(root_raw))
            details.append(v)
    result=dict(schema='NL2_HU_B786_VERIFIED_RANK229_FLOP_CHECKS_V1',rank=229,model_id=model_id,
                source_run=source.RUN,source_head=source.HEAD,selected_by_flop={},positive_distinct_flops=2,
                new_positive_flops=0,new_original_flops=3,cert_eligible_ranks=[],locked_public_boards=0,
                joint_halfpot_assessed=0,halfpot_candidates=0,native_gto_turn_jobs=0,workers=details,changed_registry_records=0)
    (out/'nl2_hu_b786_results.json').write_bytes(json_bytes(result))
    (out/'nl2_hu_b786_source_manifest.json').write_bytes(receipt.read_bytes())
    (partial/'b786_rank229.json').write_bytes(json_bytes(group))
    (partial/'b786_rank229_locked_medium.json').write_bytes(json_bytes(medium))
    assert reg.read_bytes()==initial


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','archives','output'):cli.add_argument('--'+k,type=Path,required=True)
    publish(cli.parse_args())
