"""Independently replay all B737 worker outputs and export only witnessed rank233 river policies."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b737_rank233_rivers as native
import hu_b738_collect as collect
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_board_reach_corrections import source_key, summarize
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture


def verify_selected(source,public,expected,allow,route):
    v=source['version'];sub=source['subgame'];hands=sub['hands'][0]
    node,=[n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,native.LINE,0)]
    assert (node['pot'],node['bets'],sub['stack'])==(3486,[0,0],8307)
    row=audit_decision(source,public,native.LINE,0,source['root_sha256'])
    assert {k:row[k] for k in expected['reach']}==expected['reach']
    assert row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0 and row['b50'] is not None
    summarize(row)
    mask=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    accepted={};actions=node['acts'];wanted={h for h,v in allow}
    for i,(h,bits) in enumerate(zip(hands,mask,strict=True)):
        if native.cardkey(h) not in wanted or not bits&(1<<actions.index('x')):continue
        cells=[native.hand_cell(h,public[:n]) for n in (6,8,10)]
        if cells[0][1] not in route['flop_turn'].get(cells[0][0].split(':')[0],{}).get('parents',[]):continue
        if route['flop_turn'].get(cells[1][0].split(':')[0],{}).get('decisions',{}).get(cells[1][1])!='過':continue
        if route['river'].get(cells[2][0])!='過':continue
        weights=[max(0.0,node['strat'][a*len(hands)+i]) for a in range(len(actions))];assert sum(weights)>0
        accepted[''.join(native.cardkey(h))]=dict(classes=[c[1] for c in cells],displayed_suggestion='過',
            policy=dict(action_order=actions,accepted_mask=bits,accepted_actions=[a for j,a in enumerate(actions) if bits&(1<<j)],
                        strategy={a:round(w/sum(weights),7) for a,w in zip(actions,weights,strict=True)}))
    assert sorted(accepted)==expected['displayed_check_hands']
    return row,accepted


def add_board(flop,folder,claim,code,digest,route,model,contract,pipeline,ranges,pool,group,medium):
    public=claim['selected_public_board'];turn=native.CASES[flop][0]
    root,jobs,old,rules,pin,original_root_sha=native.source(flop,pipeline,ranges,pool)
    allowed,rivers,gate=native.preregister(root,old,turn,route)
    assert gate==claim['parent_gate'] and pin==claim['source_parent'] and original_root_sha==claim['source_root_sha256']
    root_sha=sha(compact(root));sources=[];rows=[];visible=[]
    for version in ('gto','exp_oop'):
        folder2=folder/(turn+'-'+version)
        target=dict(jobs[version],extract=jobs[version]['extract']+[dict(prefix=['x','x',r],street=False,raw=True) for r in rivers])
        assert json.loads((folder2/'job.json').read_bytes())==target
        raw=(folder2/'result.json').read_bytes();game=json.loads(raw)
        policy=claim['policies'][version]
        assert (sha(raw),sha((folder2/'job.json').read_bytes()))==(policy['source_sha256'],policy['job_sha256'])
        turn_nodes=[n for n in game['nodes'] if len(n['board'])==8]
        assert turn_nodes==old[version]['nodes'] and len(turn_nodes)==18 and sha(compact(turn_nodes))==policy['original_18_node_sha256']
        assert game['hands']==old[version]['hands']
        game.update(line0='x b33 c',turn=turn,rivers=rivers)
        m=dict(spot='SB3_BTN',pot_family='3BP',locks=[])
        s=dict(root=root,root_sha256=root_sha,original_root_sha256=original_root_sha,subgame=game,manifest=m,
               run=collect.RUN,version=version,archive_sha256=digest,archive_code=code,source_sha256=sha(raw))
        if version=='exp_oop':
            m.update(locks=rules,gto_parent_source_run_id=pin['source_run_id'],gto_parent_source_sha256=root_sha)
            observed=native.audit_patterns(game,target,m,pool,hero_seat=0)
            assert observed==policy['measured_lock_application']
            s.update(verified_gto_parent=dict(run=pin['source_run_id'],sha256=root_sha),measured_lock_application=observed,
                applied_rust_rates=game['info']['lock_stats'])
        row,hands=verify_selected(s,public,policy['boards'][public],allowed[public[-2:]],route)
        sources.append(s);rows.append(row);visible.append(hands)
    witnesses=comparisons(*visible)
    assert witnesses and [w['hand'] for w in witnesses]==claim['common'][public]
    item,p=pairs.emit_board(model,*sources,public,native.LINE,texture(flop),viewer_code='B738_R233_'+flop.upper())
    assert item and native.compatible(contract,item)
    assert (item['actual_pot_bb'],item['actual_effective_stack_bb'],item['acting_seat'])==(34.86,83.07,0)
    assert p['pool_observed_marginal_lock_nodes']>0
    item.update(source_run_role='ORIGINAL_NATIVE_VERIFIED_TURN_NEW_RIVER_EXTRACTS',origin_solve_run_id=collect.RUN,
                original_flop_run_id=pin['source_run_id'],original_18_turn_nodes_unchanged=True,flop_native_solves_repeated=0)
    item['nl2_locked_variants'][0].update(source_run_role=item['source_run_role'],origin_solve_run_id=collect.RUN,
        pool_sha256=native.POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(sources[1]),
        gto_parent_source_run_id=pin['source_run_id'],gto_parent_source_sha256=root_sha,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    p.update(rendered_decision_hands=witnesses,worker_artifact=collect.PINS[flop][0],worker_sha256=digest,worker_head=collect.HEAD,
        original_job_id=collect.JOBS[flop],original_flop_run_id=pin['source_run_id'],original_flop_archive_sha256=pin['archive_sha256'],
        original_flop_sha256=original_root_sha,original_turn_gto_sha256=pin['original_GTO_SHA256'],original_turn_nl2_sha256=pin['actual_NL2_SHA256'])
    for pref,row in zip(('gto_references','references'),rows,strict=True):
        row['rendered_decision_hands']=witnesses;medium[pref][source_key(native.MODEL,row)]=row
    group['boards'].append(item);group['pins'].append(p)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,digest in collect.FILES.items():
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==digest
        assert subprocess.check_output(['git','rev-parse',collect.HEAD+':'+path],text=True).strip()==digest
    solver=a.solver.resolve();py=solver/'postflop/py';sys.path.insert(0,str(py));import pipeline,ranges
    assert sha((solver/'inputs/pool_stats.json').read_bytes())==native.POOL
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    reg=Path('data/nl2_hu_multiboard_status_current.json').read_bytes();registry=json.loads(reg);model=registry['records'][native.MODEL]
    assert (model['label'],model['frequency_rank'],model['solver_profile'])==('APPROX',233,'SB3_BTN')
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][native.MODEL]
    stage=a.output.resolve()
    assert not stage.exists() and Path('data').resolve() not in (stage,*stage.parents)
    evidence=stage/'solver_evidence';partial=evidence/'partial';partial.mkdir(parents=True)
    auth=collect.validate(json.loads((a.receipts/'receipt.json').read_bytes()))
    (stage/'nl2_hu_b738_source_receipts.json').write_bytes(json_bytes(auth))
    route_raw=subprocess.check_output(['node','tools/hu_b737_rank233_routes.cjs'])
    route_path=partial/'b738_rank233_routes.json';route_path.write_bytes(route_raw);route=json.loads(route_raw)
    group=dict(rank=233,model_id=native.MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B738_ORIGINAL_LOCKED_MEDIUM_V1',gto_references={},references={})
    counters=[];pairs.EVIDENCE=evidence
    with TemporaryDirectory(prefix='b738-replay-') as temp:
        for flop in native.CASES:
            aid,digest=collect.PINS[flop];archive=(a.receipts/f'{aid}.zip').read_bytes();assert sha(archive)==digest
            name='B737_R233_'+flop.upper();(evidence/('NL2_'+name+'.zip')).write_bytes(archive)
            folder=Path(temp)/flop;names=unpack_original(archive,folder)
            proof=(folder/'proof.json').read_bytes();claim=json.loads(proof)
            assert (claim['rank'],claim['flop'],claim['line'],claim['actor'],claim['root_recomputed'])==(233,flop,native.LINE,0,False)
            assert (folder/'rendered-routes.json').read_bytes()==route_raw
            expected={'proof.json','rendered-routes.json'}|{claim['turn']+'-'+v+'/'+f for v in claim['policies'] for f in ('job.json','result.json')}
            assert names==expected
            native.run(SimpleNamespace(flop=flop,solver=solver,routes=route_path,driver=None,preflight=False,output=folder))
            assert (folder/'proof.json').read_bytes()==proof
            (partial/('b738_'+flop.lower()+'_proof.json')).write_bytes(proof)
            if claim['selected_public_board']:
                add_board(flop,folder,claim,name,digest,route,model,contract,pipeline,ranges,pool,group,medium)
            locked=[v['reach'] for v in claim['policies'].get('exp_oop',{}).get('boards',{}).values()]
            valid=[r for r in locked if r['strict_legal_combos']>0 and r['compatible_hole_card_pairs']>0]
            assessed=[r for r in valid if r['b50'] is not None and 'b50' in r['source_actions']]
            counters.append(dict(flop=flop,selected=claim['selected_public_board'],positive_rivers=len(claim['common']),
                named_locked_rivers=len(locked),locked_joint_rivers=len(valid),halfpot_assessed=len(assessed),
                halfpot_candidates=sum(r['b50']['candidate'] for r in assessed),original_worker_sha256=digest,proof_sha256=sha(proof)))
    count=len(group['boards']);assert count==len(group['pins'])==len({suit_isomorphism_class(b['flop']) for b in group['boards']})
    if count==3:
        gpath=evidence/'reverified/rank233.json';mpath=stage/'nl2_hu_b738_locked_medium.json'
    else:
        gpath=partial/'b738_rank233.json';mpath=partial/'b738_rank233_locked_medium.json'
    gpath.parent.mkdir(parents=True,exist_ok=True);gpath.write_bytes(json_bytes(group));mpath.write_bytes(json_bytes(medium))
    summary=dict(schema='NL2_B738_R233_ORIGINAL_RIVER_OUTCOMES_V1',rank=233,model_id=native.MODEL,source_run=collect.RUN,source_head=collect.HEAD,
                 positive_distinct_flops=count,cert_eligible_ranks=[233] if count==3 else [],workers=counters,original_flop_roots_reused=3,
                 actor_locked_public_boards=sum(r['named_locked_rivers'] for r in counters),joint_reachable_locked_boards=sum(r['locked_joint_rivers'] for r in counters),
                 half_pot_assessed=sum(r['halfpot_assessed'] for r in counters),half_pot_candidates=sum(r['halfpot_candidates'] for r in counters),
                 publisher_native_solves_repeated=0)
    (stage/'nl2_hu_b738_summary.json').write_bytes(json_bytes(summary))
    assert Path('data/nl2_hu_multiboard_status_current.json').read_bytes()==reg
    print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','receipts','output'):p.add_argument('--'+k,type=Path,required=True)
    publish(p.parse_args())

