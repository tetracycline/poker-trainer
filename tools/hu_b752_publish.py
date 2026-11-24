"""Replay B751's authenticated turn policies and archive the 36 original rank224 river decisions."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b751_rank224_rivers as worker
import hu_b752_collect as collect
from hu_b467_river_source_gate import compact,json_bytes,sha
from collections import Counter
from hu_b710_publish import unpack_original

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json_bytes(obj))



def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,pin in collect.FILES.items():
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        assert subprocess.check_output(['git','rev-parse',collect.HEAD+':'+path],text=True).strip()==pin
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    pool=worker.load(solver/'inputs/pool_stats.json')['NL2']
    model=worker.load('data/nl2_hu_multiboard_status_current.json')['records'][worker.MODEL]
    contract=worker.load('data/nl2_hu_verified_extensions.json')['trainer_route_contract']['routes'][worker.MODEL]
    assert (model['frequency_rank'],model['assumed_model_node_spr'],contract['seat'])==(224,4.513,0)
    stage=a.output.resolve();assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';ev.mkdir(parents=True)
    auth=collect.validate(worker.load(a.receipts))
    save(stage/'nl2_hu_b752_source_receipts.json',auth)
    counters=[];route_raw=subprocess.check_output(['node','tools/hu_b751_river_routes.cjs']);route=json.loads(route_raw)
    with TemporaryDirectory(prefix='b752-') as temp:
        root=Path(temp);route_file=root/'routes.json';route_file.write_bytes(route_raw)
        for flop in worker.CASES:
            aid,digest=collect.PINS[flop];code='B751_R224_'+flop.upper();name='NL2_'+code+'.zip'
            f=a.archives/f'{aid}.zip';raw=(f if f.exists() else a.archives/name).read_bytes()
            assert len(raw)==next(x['size_in_bytes'] for x in auth['artifacts'] if x['id']==aid) and sha(raw)==digest
            folder=root/flop;names=unpack_original(raw,folder);proof=(folder/'proof.json').read_bytes();d=json.loads(proof)
            assert (d['rank'],d['model_id'],d['line'],d['flop'],d['turn'],d['original_flop_solves_repeated'])==(224,worker.MODEL,worker.LINE,flop,worker.CASES[flop][0],0)
            assert (folder/'rendered-routes.json').read_bytes()==route_raw and d['route_sha256']==sha(route_raw)
            assert names=={'proof.json','rendered-routes.json'}|{d['turn']+'-'+v+'/'+n for v in d['policies'] for n in ('result.json','job.json')}
            worker.run(SimpleNamespace(flop=flop,solver=solver,routes=route_file,output=folder,preflight=False,driver=None))
            assert (folder/'proof.json').read_bytes()==proof
            (ev/name).write_bytes(raw)
            assert d['selected_public_board'] is None and d['common']=={}
            turn=d['turn'];g=d['policies']['gto'];e=d['policies']['exp_oop']
            assert len(g['boards'])==len(e['boards'])==12 and g['boards'].keys()==e['boards'].keys()
            original,game,jobs,rules,pin=worker.originals(flop,pipeline,pool)
            allowed,gate=worker.preflight(original,game,turn,route,route['children']['224'])
            witnesses={};games={}
            for version in ('gto','exp_oop'):
                claim=d['policies'][version];path=folder/(turn+'-'+version)
                sr=worker.load(path/'result.json');job=worker.load(path/'job.json')
                assert sha((path/'result.json').read_bytes())==claim['source_sha256'] and sha((path/'job.json').read_bytes())==claim['job_sha256']
                original_nodes=[n for n in sr['nodes'] if len(n['board'])==8]
                assert len(original_nodes)==18 and original_nodes==game[version]['nodes']
                assert claim['original_18_node_sha256']==sha(compact(original_nodes))
                rvs=d['parent_gate']['preregistered_rivers']
                assert rvs==[list(allowed)[round(i*(len(allowed)-1)/11)] for i in range(12)]
                assert job==dict(jobs[version],extract=jobs[version]['extract']+[dict(prefix=['b50','c',r],street=False,raw=True) for r in rvs])
                if version=='exp_oop':
                    measured=worker.native.audit_patterns(sr,job,dict(locks=rules),pool,0)
                    assert measured==claim['measured_lock_application']
                    assert any(v>0 for k,v in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
                rows,active=worker.observe(original,sr,turn,rvs,allowed,route['children']['224'],contract)
                assert rows==claim['boards']
                games[version]=sr;witnesses[version]=active
            policy_divergence=Counter()
            for public,gd in witnesses['gto'].items():
                assert not witnesses['exp_oop'][public] and not (gd & witnesses['exp_oop'][public])
                assert e['boards'][public]['reach']['compatible_hole_card_pairs']>0 and e['boards'][public]['reach']['b50'] is not None
                sub=games['exp_oop'];node,=[n for n in sub['nodes'] if n['board']==public and n['line']==worker.LINE]
                mask=base64.b64decode(e['boards'][public]['reach']['compatible_action_mask_b64'],validate=True)
                by_hand={worker.native.cardkey(h):b for h,b in zip(sub['hands'][0],mask,strict=True)}
                for h in {bb for bb,co in gd}:
                    bits=by_hand.get(h,0);actions=[token for i,token in enumerate(node['acts']) if bits&(1<<i)]
                    policy_divergence['+'.join(actions) if actions else 'NO_COMPATIBLE_NODE_REACH']+=1
            gto_rows=sum(bool(r['displayed_hands']) for r in g['boards'].values())
            assert gto_rows=={'3s3h2d':12,'4s4h2d':12,'5c5d2h':11}[flop]
            assert not any(r['displayed_hands'] for r in e['boards'].values())
            counters.append(dict(flop=flop,turn=d['turn'],source_run=collect.RUN,source_head=collect.HEAD,archive_code=code,
                artifact_id=aid,job_id=collect.JOBS[flop],archive_sha256=digest,proof_sha256=sha(proof),parent_gate=d['parent_gate'],
                selected_public_board=d['selected_public_board'],positive_named_boards=len(d['common']),gto_ui_rivers=gto_rows,nl2_ui_rivers=0,
                accepted_nl2_actions_for_gto_ui_hands_by_hero_river=dict(sorted(policy_divergence.items())),
                **{k:d[k] for k in ('native_locked_public_boards','joint_halfpot_assessed','nonpolarized_candidates','positive_distinct_flops')}))
    assert len(counters)==3 and all(c['positive_distinct_flops']==0 for c in counters)
    summary=dict(schema='NL2_B752_RANK224_ORIGINAL_RIVER_OBSERVATIONS_V1',rank=224,model_id=worker.MODEL,workers=counters,source_run=collect.RUN,source_head=collect.HEAD,
        cert_eligible_ranks=[],original_flop_recomputations=0,publisher_solver_calls=0,
        **{k:sum(c[k] for c in counters) for k in ('positive_distinct_flops','native_locked_public_boards','joint_halfpot_assessed','nonpolarized_candidates')})
    assert (summary['native_locked_public_boards'],summary['joint_halfpot_assessed'],summary['nonpolarized_candidates'])==(36,36,0)
    save(stage/'nl2_hu_b752_results.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='workers'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output','archives','receipts'):p.add_argument('--'+key,type=Path,required=True)
    publish(p.parse_args())
