"""Authenticate the original three B724 workers and replay the rank150 decisions."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b724_rank150_rivers as native
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_board_reach_corrections import source_key, summarize
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture

RUN=45329555043
HEAD='7dd111dc5e4d9860a867893e912981c95062349a'
WORKER='tools/hu_b724_rank150_rivers.py'
WORKER_BLOB='854dfd8cc37fb3bcfb7481573a74bb78c3419120'
WORKFLOW='.github/workflows/nl2-hu-b724-rank150-rivers.yml'
BRANCH='fix/nl2-hu-lines-audit-20261118'
PINS={
  "8s8h5s": [
    14892117865,
    138227163340,
    "719239bca0a11a71ffb711ad1b5c16714ee0a5bac323b723d927c0a17948bd3b"
  ],
  "9c9h6c": [
    14891728442,
    138227163492,
    "9410fbd73365fafacf681007f7bb425b747d317ae26a2eea15bee27c2c4df289"
  ],
  "Ts9s5h": [
    14891519205,
    138227163611,
    "36a1bbfb5b27d78dd7e52787d35a4e7adfda18cbd0595f5150ef8c03a5bd021f"
  ]
}
STEPS={
    'Verify exact ranked third-pot UI route and both original preflop ranges',
    'Build the pinned native solver',
    'Solve original flop and only two-seat reachable checked river continuations',
    'Run actions/upload-artifact@v4',
}


def authenticate(auth):
    r=auth['run']
    assert (r['id'],r['head_sha'],r['head_branch'],r['path'],r['status'],r['conclusion'])==(
        RUN,HEAD,BRANCH,WORKFLOW,'completed','success')
    assert (r['repository']['id'],r['repository']['full_name'])==(1438346845,'tetracycline/poker-trainer')
    assert set(PINS)==set(native.CASES) and len(auth['jobs'])==len(auth['artifacts'])==3
    for flop,(aid,jid,digest) in PINS.items():
        j,=[entry for entry in auth['jobs'] if entry['id']==jid]
        assert (j['run_id'],j['head_sha'],j['run_attempt'],j['name'],j['status'],j['conclusion'])==(
            RUN,HEAD,r['run_attempt'],'solve ('+flop+')','completed','success')
        assert STEPS<={s['name'] for s in j['steps'] if (s['status'],s['conclusion'])==('completed','success')}
        a,=[entry for entry in auth['artifacts'] if entry['id']==aid]
        assert (a['name'],a['expired'],a['digest'])==('B724-R150-'+flop,False,'sha256:'+digest)
        w=a['workflow_run']
        assert (w['id'],w['head_sha'],w['head_branch'],w['repository_id'],w['head_repository_id'])==(RUN,HEAD,BRANCH,1438346845,1438346845)


def hand_policies(s,row,item):
    sub=s['subgame'];public=row['public_board']
    n,=[n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,native.LINE,1)]
    bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    found={}
    for ix,(h,mask) in enumerate(zip(sub['hands'][1],bits,strict=True)):
        key=''.join(native.cardkey(h))
        if key not in item['hands']:
            continue
        raw=item['hands'][key]
        actions=[a for i,a in enumerate(n['acts']) if mask&(1<<i)]
        assert actions==raw['accepted_actions'] and 'x' in actions
        assert [native.hand_cell(h,public[:k])[1] for k in (6,8,10)]==raw['classes']
        weights=[max(0,n['strat'][i*len(bits)+ix]) for i in range(len(n['acts']))]
        total=sum(weights);assert total>0
        found[key]=dict(classes=raw['classes'],displayed_suggestion=raw['displayed_suggestion'],
            policy=dict(action_order=n['acts'],accepted_mask=mask,accepted_actions=actions,
                strategy={a:round(w/total,7) for a,w in zip(n['acts'],weights,strict=True)}))
    assert found.keys()==item['hands'].keys()
    return found


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
        rows.append(row);policies.append(hand_policies(s,row,original))
    common=comparisons(*policies)
    assert [h['hand'] for h in common]==record['common'][public] and common
    b,p=pairs.emit_board(model,g,e,public,native.LINE,texture(claim['flop']),viewer_code='B731_R150_'+claim['flop'].upper())
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


def run(args):
    assert sys.version_info[:2]==(3,11) and native.limp.git_blob(WORKER)==WORKER_BLOB
    for p,d in {WORKER:WORKER_BLOB,WORKFLOW:'634b630f6fe7d410912253a06f79dbeaccc0fa15',**native.PINS}.items():
        assert subprocess.check_output(['git','rev-parse',HEAD+':'+p],text=True).strip()==d
        assert native.limp.git_blob(p)==d
    registry=Path('data/nl2_hu_multiboard_status_current.json');initial=registry.read_bytes()
    records=json.loads(initial)['records'];model=records[native.MODEL]
    assert (len(records),model['frequency_rank'],model['label'],model['solver_profile'],model['assumed_model_node_spr'])==(392,150,'APPROX','LMP_CO_BB',23.558)
    assert not model['certified_3_to_5_exact_flop_boards']
    data=(args.output/'data').resolve()
    assert not data.exists() and not data.is_relative_to(Path('data').resolve())
    evidence=data/'solver_evidence';partial=evidence/'partial';partial.mkdir(parents=True);pairs.EVIDENCE=evidence
    auth=json.loads((args.receipts/'receipt.json').read_bytes());authenticate(auth)
    (partial/'b731_auth_receipt.json').write_bytes(json_bytes(auth))
    solver=args.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    group=dict(rank=150,model_id=native.MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B731_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    route_raw=subprocess.check_output(['node',native.ROUTE]);(partial/'b731_rank150_routes.json').write_bytes(route_raw)
    results=[]
    with TemporaryDirectory(prefix='b731-replay-') as td:
        for flop,pin in PINS.items():
            raw=(args.receipts/f'{pin[0]}.zip').read_bytes()
            assert sha(raw)==pin[2];folder=Path(td)/flop;names=unpack_original(raw,folder)
            original=(folder/'proof.json').read_bytes();claim=json.loads(original)
            assert (claim['flop'],claim['model_id'],claim['source_worker_blob'])==(flop,native.MODEL,WORKER_BLOB)
            expected={'proof.json','original-manifest.json','rendered-routes.json','flop/job.json','flop/result.json'}
            for t in claim['turns']:
                for v in t['policies']:
                    expected.update(t['turn']+'-'+v+'/'+n for n in ('job.json','result.json'))
            assert names==expected and set(claim['native_file_sha256'])==names-{'proof.json'}
            assert (folder/'rendered-routes.json').read_bytes()==route_raw
            assert all(sha((folder/n).read_bytes())==d for n,d in claim['native_file_sha256'].items())
            native.run(SimpleNamespace(solver=solver,flop=flop,driver=None,preflight=False,output=folder))
            assert (folder/'proof.json').read_bytes()==original
            assert all(sha((folder/n).read_bytes())==d for n,d in claim['native_file_sha256'].items())
            code='B724_R150_'+flop.upper()
            (evidence/('NL2_'+code+'.zip')).write_bytes(raw)
            (partial/('b731_'+flop.lower()+'_proof.json')).write_bytes(original)
            if claim['selected']:
                stage_choice(folder,claim,code,pin,model,pipeline,pool,group,medium)
            locked=[o['reach'] for t in claim['turns'] for o in t['policies'].get('exp_ip',{}).get('boards',{}).values()]
            joint=[row for row in locked if row['strict_legal_combos']>0 and row['compatible_hole_card_pairs']>0]
            assessed=[row for row in joint if row['b50'] is not None and 'b50' in row['source_actions']]
            results.append(dict(flop=flop,source_run=RUN,source_head=HEAD,artifact_id=pin[0],job_id=pin[1],archive_sha256=pin[2],
                selected=claim['selected'],original_proof_sha256=sha(original),byte_identical_original_proof=True,
                original_root_sha256=claim['root_sha256'],original_root_job_sha256=claim['root_job_sha256'],
                original_b33_call_boundaries=claim['additional_original_b33_call_boundaries'],
                native_gto_root_jobs=1,native_gto_turn_jobs=sum('gto' in t['policies'] for t in claim['turns']),
                native_locked_turn_jobs=sum('exp_ip' in t['policies'] for t in claim['turns']),
                native_locked_river_nodes=len(locked),actor_locked_joint_boards=len(joint),half_pot_assessed_joint_boards=len(assessed),
                half_pot_nonpolarized_candidates=sum(row['b50']['candidate'] for row in assessed),
                both_policies_rendered_positive_rivers=sum(len(t['common']) for t in claim['turns'])))
    flops=[b['flop'] for b in group['boards']]
    assert len(flops)==len({suit_isomorphism_class(f) for f in flops})==len(group['pins'])<=3
    eligible=len(flops)>=3
    if eligible:
        verified=evidence/'reverified';verified.mkdir()
        (verified/'rank150.json').write_bytes(json_bytes(group))
        (data/'nl2_hu_b731_locked_medium.json').write_bytes(json_bytes(medium))
    else:
        (partial/'b731_rank150.json').write_bytes(json_bytes(group))
        (partial/'b731_rank150_locked_medium.json').write_bytes(json_bytes(medium))
    totals={k:sum(r[k] for r in results) for k in ('native_gto_root_jobs','native_gto_turn_jobs','native_locked_turn_jobs','native_locked_river_nodes',
        'actor_locked_joint_boards','half_pot_assessed_joint_boards','half_pot_nonpolarized_candidates','both_policies_rendered_positive_rivers')}
    summary=dict(rank=150,model_id=native.MODEL,source_run=RUN,source_head=HEAD,positive_flops=flops,remaining_to_three=3-len(flops),
        certified_eligible=eligible,zero_added_legacy_KsQh4d=True,per_flop=results,native_solves_repeated=0,live_registry_written=False,**totals)
    (data/'nl2_hu_b731_summary.json').write_bytes(json_bytes(summary))
    assert registry.read_bytes()==initial
    print(json.dumps(summary))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','receipts','output'):cli.add_argument('--'+name,type=Path,required=True)
    run(cli.parse_args())
