"""B859: authenticate cancelled B858 ZIPs and screen saved B724 roots for ranks 115,116,118; never invoke native driver."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile
from io import BytesIO

from hu_b732_rank80_boundaries import load_source, gate, source
from hu_b467_river_source_gate import compact, sha, json_bytes

REPO = 'tetracycline/poker-trainer'
RECEIPT = Path('data/nl2_hu_b859_b858_cancelled_receipts.json')
MODELS = {115:'ln-iso-lmp_r_model-17dzvwx',116:'ln-iso-lmp_r_model-1c6f833',118:'ln-iso-lmp_r_model-zhthyp'}

def api(path):
    return subprocess.check_output(['gh','api','repos/'+REPO+'/'+path])

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    receipt=json.loads(RECEIPT.read_bytes())
    run=json.loads(api('actions/runs/'+str(receipt['source_run'])))
    assert (run['head_sha'],run['head_branch'],run['status'],run['conclusion'])==(receipt['source_head'],'fix/nl2-hu-lines-audit-20261118','completed','cancelled')
    results=[]
    for r in receipt['archives']:
        job=json.loads(api('actions/jobs/'+str(r['job'])))
        art=json.loads(api('actions/artifacts/'+str(r['artifact'])))
        assert (job['run_id'],job['head_sha'],job['name'],job['conclusion'])==(receipt['source_run'],receipt['source_head'],'solve ('+r['flop']+')','cancelled')
        steps={s['name']:s['conclusion'] for s in job['steps']}
        assert steps['Compile the pinned native solver']=='success'
        assert steps['Solve the missing river trees and replay both policies']=='cancelled'
        assert (art['name'],art['digest'],art['size_in_bytes'],art['workflow_run']['head_sha'])==('B858-R114-'+r['flop'],'sha256:'+r['sha256'],r['size'],receipt['source_head'])
        raw=api('actions/artifacts/'+str(r['artifact'])+'/zip')
        assert len(raw)==r['size'] and sha(raw)==r['sha256']
        with ZipFile(BytesIO(raw)) as z:
            assert not any(n.endswith('proof.json') for n in z.namelist())
            files={n:sha(z.read(n)) for n in z.namelist() if not n.endswith('/')}
        (out/(str(r['artifact'])+'.zip')).write_bytes(raw)
        results.append(dict(**r,member_sha256=files,status='CANCELLED_NO_CERT',completed_native_results=[n for n in files if n.endswith('result.json')]))
    raw=subprocess.check_output(['node','tools/hu_b718_limp_routes.cjs'])
    routes=json.loads(raw)
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    assert subprocess.check_output(['git','hash-object',str(registry)],text=True).strip()==receipt['registry_git_blob']
    status=json.loads(registry.read_bytes())
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['TOTAL'])==(158,234,392)
    priority=json.loads(Path('data/nl2_hu_b838_234_approx_frequency_priority.json').read_bytes())
    rows=[]
    for rank,mid in MODELS.items():
        route=routes[str(rank)]
        assert (route['id'],route['turn_pct'],status['records'][mid]['label'])==(mid,{115:33,116:50,118:66}[rank],'APPROX')
        p,=[p for p in priority['rows'] if p['rank']==rank]
        assert p['passes_min_0_2_pct_frequency'] and p['model_id']==mid
        # Reuse original completed flop boundaries only; no new native computation.
        for flop in source.CASES:
            root,template,manifest,pin=load_source(flop,Path('data/solver_evidence'))
            for turn,_,_ in source.CASES[flop]:
                _,g=gate(root,turn,route)
                assert g['boundary_sha256']==pin['boundaries'][turn]
                rows.append(dict(rank=rank,model=mid,flop=flop,turn=turn,source=pin,gate=g))
    assert len(rows)==36
    report=dict(schema='NL2_B859_B858_QUARANTINE_AND_B724_BOUNDARIES_V1',cancelled_sources=results,
        root_boundary_screen=rows,rendered_routes_sha256=sha(raw),registry_sha256=sha(registry.read_bytes()),
        cert_promotions=0,locked_public_boards=0,joint_halfpot_assessed=0,nonpolarized_candidates=0,native_solves=0,
        model_opportunity_coverage_pct=priority['current_certified_opportunity_share_pct'],
        scope='Original GTO flop boundary and displayed flop/turn/river class only; no turn action proof, NL2 lock or CERT. Existing B718 and B729 solved negatives are not rerun.')
    (out/'report.json').write_bytes(json_bytes(report))
    (out/'rendered-routes.json').write_bytes(raw)
    print(json.dumps({'screened':len(rows),'eligible_by_rank':{r:sum(bool(x['gate']['river_witnesses']) for x in rows if x['rank']==r) for r in MODELS},'native_solves':0,'cert_promotions':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output)
