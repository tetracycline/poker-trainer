"""B800/B801: authenticate and replay completed B798/B799 without native solves."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b798_rank136_new_rivers as r136
import hu_b799_rank230_rainbow as r230
from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import api
from hu_b710_publish import unpack_original
from hu_b738_collect import run_receipt, job_receipt, artifact_receipt

SOURCES=[
 (45353109139,'d2594b41518a245dc63aca44a1a34aeba57741cd','.github/workflows/nl2-hu-b798-rank136-original-rivers.yml',
  'tools/hu_b798_rank136_new_rivers.py',
  ['Authenticate the original B792 game and verify every unextracted eligible river','Build the pinned native solver','Keep both original strategy trees and add only unseen river extracts','Run actions/upload-artifact@v4'],
  [(138304175191,'Ac8h5d','Js',14900438505,'ee78485efcfa937aec161708d1d1221570e8cb1b630a2b9e06ef9fa69d890f98'),
   (138304175646,'Ac8h5d','2h',14901306624,'fed761a8b1ec45f3face8f2b479d2d356442577c5064c73dbd3b057ca0bf7aca'),
   (138304175486,'Ah8d4s','Qc',14901286690,'57c5209c460ab58b597794d3e6ba9e15037466dd3c95ae85b8f3d280287a3b37'),
   (138304175565,'Ah8d4s','Jc',14900992996,'d2e4145fb392d51014367bfe700ef84fc8ff869c7ec3c194936c2073a736cb05')]),
 (45353136810,'7c8cdf0744f8e08aa541ee657d74ebaf23a58a3a','.github/workflows/nl2-hu-b799-rank230-rainbow.yml',
  'tools/hu_b799_rank230_rainbow.py',
  ['Verify J7 suited, its compatible BTN hand and the displayed three-street route','Build the pinned native driver','Solve the original native rainbow flop once with four registered checked boundaries','Preserve the completed original before turn solves','Solve reachable turns and replay real two-seat strategy checks','Preserve both strategies and all positive and negative source decisions'],
  [(138304266967,'Ts9h7c',None,14900783903,'99664020c22ffeff489b7540a3a005f3299e8be11fb582cceb4ca12f0afc64dc'),
   (138304266967,'Ts9h7c','root',14900594212,'4761a457a318d35caa2615ce7b3ba39643209eac7bc56d62592fe5b8485fa705')])
]

def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for rid,head,workflow,worker,steps,entries in SOURCES:
        endpoint='actions/runs/'+str(rid)
        r=run_receipt(json.loads(api(endpoint)),rid,head,workflow)
        assert r['run_attempt']==1
        jobs=json.loads(api(endpoint+'/jobs?per_page=100'))
        artifacts=json.loads(api(endpoint+'/artifacts?per_page=100'))
        assert jobs['total_count']==len({e[0] for e in entries}) and artifacts['total_count']==len(entries)
        receipt=dict(run=r,jobs=[],artifacts=[],blobs={})
        for path in (workflow,worker):
            pinned=json.loads(api('contents/'+path+'?ref='+head))['sha']
            assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pinned
            receipt['blobs'][path]=pinned
        for jid,f,t,aid,digest in entries:
            job,=[j for j in jobs['jobs'] if j['id']==jid]
            art,=[a for a in artifacts['artifacts'] if a['id']==aid]
            if rid==45353109139:
                old_id,old_sha=r136.ARCHIVES[f]
                name=f'solve ({f}, {t}, {old_id}, {old_sha})'
                aname=f'B798-R136-{f}-{t}'
            else:
                name='solve';aname=('B799-root-R230-' if t=='root' else 'B799-R230-')+f
            j=job_receipt(job,r,jid,name,steps)
            if j not in receipt['jobs']:receipt['jobs'].append(j)
            ar=artifact_receipt(art,r,aid,aname,digest)
            receipt['artifacts'].append(ar)
            b=api('actions/artifacts/'+str(aid)+'/zip')
            assert sha(b)==digest and len(b)==ar['size_in_bytes']
            (folder/(str(aid)+'.zip')).write_bytes(b)
        receipts.append(receipt)
    (folder/'receipt.json').write_bytes(json_bytes(receipts))

def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    stage.mkdir(parents=True)
    raw_receipts=json.loads((a.archives/'receipt.json').read_bytes())
    (stage/'nl2_hu_b800_b801_source_receipts.json').write_bytes(json_bytes(raw_receipts))
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    rows={136:[],230:[]}
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    before=registry.read_bytes()
    with TemporaryDirectory(prefix='b800-b801-') as tmp:
        tmp=Path(tmp)
        for i,(rid,head,workflow,worker,steps,entries) in enumerate(SOURCES):
            for jid,f,t,aid,digest in entries:
                raw=(a.archives/(str(aid)+'.zip')).read_bytes();assert sha(raw)==digest
                assert any(x['id']==aid and x['digest']=='sha256:'+digest for x in raw_receipts[i]['artifacts'])
                dest=tmp/str(aid);dest.mkdir()
                names=unpack_original(raw,dest)
                hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
                archive=('NL2_B798_R136_'+f.upper()+'_'+t.upper()+'.zip') if i==0 else ('NL2_B799_R230_'+f.upper()+('_ROOT' if t=='root' else '')+'.zip')
                (ev/archive).write_bytes(raw)
                if i==0:
                    claim=json.loads((dest/'proof.json').read_bytes())
                    (tmp/'original.zip').write_bytes((dest/'original-b792.zip').read_bytes())
                    r136.run(SimpleNamespace(solver=a.solver,archive=tmp/'original.zip',output=dest,flop=f,turn=t,driver=None,preflight=False))
                    actual=json.loads((dest/'proof.json').read_bytes());assert actual==claim
                    assert not actual['common'] and actual['positive_distinct_flops']==0
                    counts=[actual[k] for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')]
                    rank=136
                elif t=='root':
                    full=tmp/'14900783903'
                    assert names=={'flop/job.json','flop/result.json','root-checkpoint.json'}
                    assert all((dest/n).read_bytes()==(full/n).read_bytes() for n in names)
                    continue
                else:
                    claim=json.loads((dest/'proof.json').read_bytes())
                    r230.run(SimpleNamespace(solver=a.solver,output=dest,flop=f,driver=None,preflight=False,root_only=False))
                    actual=json.loads((dest/'proof.json').read_bytes());assert actual==claim
                    assert actual['selected'] is None and actual['positive_distinct_flops']==0 and not any(x['common'] for x in actual['turns'])
                    counts=[actual[k] for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')]
                    rank=230
                assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items() if n!='proof.json')
                # The original archived proof is immutable; JSON equality permits harmless key order.
                rows[rank].append(dict(source_run=rid,source_head=head,job=jid,artifact=aid,archive=archive,sha256=digest,native_file_sha256=hashes,
                    flop=f,turn=t,locked=counts[0],positive_halfpot=counts[1],nonpolarized=counts[2],proof=claim))
    for rank,batch,expected in ((136,800,[26,26,12]),(230,801,[62,0,0])):
        count=[sum(x[k] for x in rows[rank]) for k in ('locked','positive_halfpot','nonpolarized')]
        assert count==expected
        name=f'b{batch}_rank{rank}_original_observations.json'
        (partial/name).write_bytes(json_bytes(dict(rank=rank,positive_distinct_flops=0,cert_eligible_ranks=[],observations=rows[rank])))
        (stage/f'nl2_hu_b{batch}_results.json').write_bytes(json_bytes(dict(rank=rank,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=count[0],joint_halfpot_assessed=count[1],halfpot_candidates=count[2],
            unchanged_registry_sha256=sha(before),source_artifacts=[x['artifact'] for x in rows[rank]])))
    assert before==registry.read_bytes()
    print(json.dumps(dict(B800=[26,26,12],B801=[62,0,0],registry=json.loads(before)['CERT_MULTIBOARD'])))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
