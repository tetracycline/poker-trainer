"""Recompute both-seat joint check histories from three immutable B782 native workers, without solving."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import hu_b679_publish as original
import hu_b747_rank150_replay as replay
import hu_b782_rank230_mid_pairs as worker
import hu_b784_collect as source
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible

MODEL=worker.MODEL
LINE=worker.native.LINE
EVIDENCE=Path('data/solver_evidence')
def read(path):return json.loads(path.read_bytes())
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json_bytes(data))


def hands(s,turn,public,shown):
    root,sub=s['root'],s['subgame']
    boundary,=[n for n in root['nodes'] if n['line']=='x x/' and n['board']==public[:8]]
    result=[]
    for i,(fl,tl) in enumerate((('','x x/'),('x','x x/x'))):
        fn,=[n for n in root['nodes'] if n['line']==fl and n['board']==public[:6]]
        tn,=[n for n in sub['nodes'] if n['line']==tl and n['board']==public[:8]]
        rn,=[n for n in sub['nodes'] if n['line']==LINE and n['board']==public]
        assert (fn['player'],tn['player'],rn['player'])==(i,i,0)
        raw={worker.native.cardkey(h) for h,w in zip(root['hands'][i],boundary['wr'][i],strict=True) if w>1e-4}
        final={worker.native.cardkey(h) for h,w in zip(sub['hands'][i],rn['w'][i],strict=True) if w>1e-4}
        active=raw&final&worker.native.accepted(fn,root['hands'],'x')&worker.native.accepted(tn,sub['hands'],'x')
        if i==0:active &= worker.native.accepted(rn,sub['hands'],'x')
        result.append({h for h in active if worker.native.public_cards(public).isdisjoint(h)})
    return {(''.join(h),''.join(v)) for h in result[0] if ''.join(h) in shown for v in result[1] if set(h).isdisjoint(v)}


def selected(folder,d,artifact,model,contract,route,pipeline,pool,group,medium):
    flop=d['flop'];public=d['selected']['public_board'];turn=d['selected']['turn'];rec,=[r for r in d['turns'] if r['turn']==turn]
    g,e=original.sources(folder,dict(run=source.RUN,sha256=artifact['digest'][7:]),d['selected'],pipeline,pool,'B782_R230_'+flop.upper())
    assert g['root_sha256']==sha(compact(read(folder/'flop/result.json')))
    measurements=[];display=[];joint=[]
    for s in (g,e):
        v=s['version'];p=rec['policies'][v];raw=p['boards'][public]
        assert s['source_sha256']==p['source_sha256']
        assert sha((folder/(turn+'-'+v)/'job.json').read_bytes())==p['job_sha256']
        if v=='exp_oop':
            assert s['measured_lock_application']==p['measured_lock_application'] and s['applied_rust_rates']
        row,byhand=original.decision(s,public,route)
        assert all(row[k]==x for k,x in raw['reach'].items())
        assert row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0 and row['b50'] is not None
        measurements.append(row);display.append(byhand);joint.append(hands(s,turn,public,byhand))
    common=joint[0]&joint[1];heroes=sorted({h for h,v in common})
    assert heroes==rec['common'][public] and heroes
    witness=[]
    for h in heroes:
        villains=sorted(v for c,v in common if c==h)
        assert rec['policies']['exp_oop']['boards'][public]['compatible_btn_witnesses'][h]==dict(example=villains[0],count=len(villains))
        categories,label,gpol=display[0][h];ecat,elabel,epol=display[1][h]
        assert categories==ecat==['MID','MID','MID'] and label==elabel=='過'
        assert all('x' in p['accepted_actions'] for p in (gpol,epol))
        witness.append(dict(hand=h,flop_class=categories[0],turn_class=categories[1],river_class=categories[2],displayed_suggestion=label,
            gto=gpol,nl2=epol,compatible_opponent_example=villains[0],joint_policy_opponent_count=len(villains)))
    b,p=pairs.emit_board(model,g,e,public,LINE,texture(flop),viewer_code='B784_R230_'+flop.upper())
    assert b and compatible(contract,b) and (b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==(0,21,90)
    assert not b['assumed_preflop_ranges'] and p['pool_observed_marginal_lock_nodes']>0
    for v,key,row in zip(('GTO','NL2'),('gto_references','references'),measurements,strict=True):
        assert (p[v+'_strict_combos'],p[v+'_compatible_hole_card_pairs'])==(row['strict_legal_combos'],row['compatible_hole_card_pairs'])
        row['rendered_decision_hands']=witness;medium[key][source_key(MODEL,row)]=row
    b.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=source.RUN,certification_scope=d['lock_scope'],
        original_flop_source_run_id=d['origin']['worker']['run'],original_flop_reexports=1,original_nodes_exactly_reproduced=14,
        restricted_flop_bet_sizes_pct=[33],flop_bet_size_menu='33%')
    b['nl2_locked_variants'][0].update(source_run_role=b['source_run_role'],origin_solve_run_id=source.RUN,pool_sha256=worker.native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),gto_parent_source_run_id=source.RUN,
        gto_parent_source_sha256=g['root_sha256'],viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    p.update(rendered_decision_hands=witness,source_blob_head=source.HEAD,worker_artifact=artifact['id'],worker_job=source.JOBS[flop],
        source_original_flop=d['origin'],reexported_root_sha256=d['root_sha256'],reexported_job_sha256=d['root_job_sha256'],
        new_boundary_sha256=d['new_raw_boundaries'][turn],conditional_job_sha256={v:rec['policies'][v]['job_sha256'] for v in ('gto','exp_oop')})
    group['boards'].append(b);group['pins'].append(p)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,digest in source.PINS.items():
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==digest and worker.blob(path)==digest
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==worker.native.SOLVER
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes();assert sha(raw_pool)==worker.native.POOL;pool=json.loads(raw_pool)['NL2']
    registry=Path('data/nl2_hu_multiboard_status_current.json');baseline=registry.read_bytes();model=json.loads(baseline)['records'][MODEL]
    assert (model['label'],model['frequency_rank'],model['solver_profile'])==('APPROX',230,'SB3_BTN')
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(0,['x x','x x',''])
    group=read(EVIDENCE/'partial/rank230.json');assert group==dict(rank=230,model_id=MODEL,pins=[],boards=[])
    medium=dict(schema='NL2_HU_B784_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';ev.mkdir(parents=True);pairs.EVIDENCE=ev
    route_bytes=subprocess.check_output(['node',worker.ROUTE]);route=json.loads(route_bytes)['230']
    auth=source.validate(read(a.receipts));write(out/'nl2_hu_b784_source_receipts.json',auth);workers=[]
    with TemporaryDirectory(prefix='b784-originals-') as temp:
        parent=Path(temp);frozen=parent/'frozen';replay.materialize(source.HEAD,frozen)
        for flop in source.JOBS:
            art,=[a for a in auth['artifacts'] if a['name']=='B782-R230-'+flop]
            name='NL2_'+source.SOURCES[art['name']]+'.zip';path=a.archives/f"{art['id']}.zip"
            raw=(path if path.exists() else a.archives/name).read_bytes()
            assert sha(raw)==art['digest'][7:] and len(raw)==art['size_in_bytes'];(ev/name).write_bytes(raw)
            folder=parent/flop;unpack_original(raw,folder);d=replay.replay_exact(frozen,source.WORKER,solver,folder,flop)
            assert (d['schema'],d['flop'],d['model_id'],d['actor'],d['line'],d['source_worker_blob'])==('NL2_B782_R230_ORIGINAL_CHECKED_MIDDLE_PAIRS_V1',flop,MODEL,0,LINE,source.PINS[source.WORKER])
            old,job,origin=worker.original(flop,ranges);root=read(folder/'flop/result.json');bounds=worker.exact_root(old,root,flop)
            assert origin==d['origin'] and d['unchanged_original_nodes']==len(old['nodes'])==14 and d['no_observed_per_private_hand_frequency']
            assert (folder/'flop/job.json').read_bytes()==compact(job) and (folder/'rendered-routes.json').read_bytes()==route_bytes
            assert d['new_raw_boundaries']=={t:sha(compact(n)) for t,n in bounds.items()} and d['original_flop_reexports']==1
            turns=d['turns'];scheduled=list(worker.SPEC[flop][1]);assert d['preregistered_turns']==scheduled and [r['turn'] for r in turns]==scheduled[:len(turns)]
            if d['selected']:
                assert turns[-1]['common'] and d['selected']['turn']==turns[-1]['turn']
                selected(folder,d,art,model,contract,route,pipeline,pool,group,medium)
            else:assert len(turns)==len(scheduled) and all(not t['common'] for t in turns)
            locks=[b['reach'] for t in turns for b in t['policies'].get('exp_oop',{}).get('boards',{}).values()]
            assert len(locks)==len({r['public_board'] for r in locks})
            joint=[r for r in locks if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None]
            counts=(len(locks),len(joint),sum(r['b50']['candidate'] for r in joint))
            assert counts==(d['locked_named_boards'],d['joint_halfpot_assessed'],d['nonpolarized_candidates'])
            workers.append(dict(flop=flop,artifact=art['id'],job_id=source.JOBS[flop],sha256=sha(raw),proof_sha256=sha((folder/'proof.json').read_bytes()),
                   original_source=origin,selected=d['selected'],locked_named_boards=counts[0],joint_halfpot_assessed=counts[1],nonpolarized_candidates=counts[2]))
    n=len(group['boards']);assert n==len(group['pins'])==len({suit_isomorphism_class(b['flop']) for b in group['boards']})==sum(bool(w['selected']) for w in workers)
    assert n==len(medium['references'])==len(medium['gto_references']) and 0<=n<=3
    if n==3:write(ev/'reverified/rank230.json',group);write(out/'nl2_hu_b784_locked_medium.json',medium)
    else:write(ev/'partial/b784_rank230.json',group);write(ev/'partial/b784_rank230_locked_medium.json',medium)
    summary=dict(schema='NL2_B784_AUTHENTICATED_RANK230_CHECKED_FLOPS_V1',rank=230,model_id=MODEL,source_run=source.RUN,source_head=source.HEAD,
                 workers=workers,positive_distinct_flops=n,cert_eligible_ranks=[230] if n==3 else [],
                 **{k:sum(w[k] for w in workers) for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')})
    write(out/'nl2_hu_b784_results.json',summary);assert registry.read_bytes()==baseline
    print(json.dumps({k:v for k,v in summary.items() if k!='workers'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','archives','receipts','output'):p.add_argument('--'+k,type=Path,required=True)
    publish(p.parse_args())
