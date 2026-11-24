"""Replay B784's two positives and the four new conditional B793 turns before deciding rank230."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import hu_b679_publish as original
import hu_b747_rank150_replay as replay
import hu_b782_rank230_mid_pairs as base
import hu_b784_collect as prior_source
import hu_b784_rank230 as prior
import hu_b787_rank230 as earlier
import hu_b793_rank230_heart_turns as worker
import hu_b795_collect as source
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible

EVIDENCE,LINE,MODEL,read,write=prior.EVIDENCE,prior.LINE,prior.MODEL,prior.read,prior.write
PRIOR_PUBLICATION='f531e93ec5af6ceaf1fee6ebc7210f21f2af4dee'
PRIOR_GROUP='partial/b784_rank230.json'
PRIOR_MEDIUM='partial/b784_rank230_locked_medium.json'
COUNTS=('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')


def frozen_replay(frozen,solver,rust,folder):
    proof=(folder/'proof.json').read_bytes();claim=json.loads(proof)
    original={p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file() and p.name!='proof.json'}
    assert original==claim['native_file_sha256']
    audit="""
import runpy,sys
from pathlib import Path
program=sys.argv.pop(1);sys.argv[0]=program;sys.path.insert(0,str(Path(program).parent))
from hu_b467_river_source_gate import compact
import hu_b637_rank57 as reader
saved=reader.solve
folder=Path(sys.argv[sys.argv.index('--output')+1])
originals={p.parent for p in folder.rglob('job.json')};observed=set()
def verified(path,job,driver):
    assert driver is None and path in originals and path not in observed
    assert (path/'job.json').read_bytes()==compact(job),path
    observed.add(path)
    return saved(path,job,None)
reader.solve=verified
runpy.run_path(program,run_name='__main__')
assert observed==originals
"""
    subprocess.run([sys.executable,'-c',audit,str(frozen/source.WORKER),'--solver',str(solver),'--rust-source',str(rust),'--output',str(folder)],cwd=frozen,check=True)
    assert (folder/'proof.json').read_bytes()==proof
    assert all(sha((folder/p).read_bytes())==h for p,h in original.items())
    return claim

def selected(folder,d,artifact,view,model,contract,route,pipeline,pool,group,medium):
    flop=d['flop'];public=d['selected']['public_board'];turn=d['selected']['turn'];rec,=[r for r in d['turns'] if r['turn']==turn]
    g,e=original.sources(folder,dict(run=source.RUN,sha256=artifact['digest'][7:]),d['selected'],pipeline,pool,'B793_R230_'+flop.upper())
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
        measurements.append(row);display.append(byhand);joint.append(prior.hands(dict(s,root=view),turn,public,byhand))
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
    b,p=pairs.emit_board(model,g,e,public,LINE,texture(flop),viewer_code='B795_R230_'+flop.upper())
    assert b and compatible(contract,b) and (b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==(0,21,90)
    assert not b['assumed_preflop_ranges'] and p['pool_observed_marginal_lock_nodes']>0
    for v,key,row in zip(('GTO','NL2'),('gto_references','references'),measurements,strict=True):
        assert (p[v+'_strict_combos'],p[v+'_compatible_hole_card_pairs'])==(row['strict_legal_combos'],row['compatible_hole_card_pairs'])
        row['rendered_decision_hands']=witness;medium[key][source_key(MODEL,row)]=row
    b.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=source.RUN,certification_scope=d['lock_scope'],
        original_flop_source_run_id=d['origin']['run'],original_flop_reexports=0,flop_native_solves_repeated=0,
        restricted_flop_bet_sizes_pct=[33],flop_bet_size_menu='33%')
    b['nl2_locked_variants'][0].update(source_run_role=b['source_run_role'],origin_solve_run_id=source.RUN,pool_sha256=base.native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),gto_parent_source_run_id=source.RUN,
        gto_parent_source_sha256=g['root_sha256'],viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    p.update(rendered_decision_hands=witness,source_blob_head=source.HEAD,worker_artifact=artifact['id'],worker_job=source.JOB,
        source_original_flop=d['origin'],original_root_result_sha256=d['root_sha256'],original_root_job_sha256=d['root_job_sha256'],
        held_out_binary64_and_full_jobs=d['origin']['original_five_held_out_jobs'],conditional_binary64_seat_sha256=rec['root_gate']['derived_binary64_seat_sha256'],conditional_job_sha256={v:rec['policies'][v]['job_sha256'] for v in ('gto','exp_oop')})
    group['boards'].append(b);group['pins'].append(p)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,digest in source.PINS.items():
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==digest and base.blob(path)==digest
    assert base.blob(base.WORKER)==worker.previous.SOURCE_BLOB
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==base.native.SOLVER
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==base.native.POOL;pool=json.loads(pool_raw)['NL2']
    registry=Path('data/nl2_hu_multiboard_status_current.json');baseline=registry.read_bytes();model=json.loads(baseline)['records'][MODEL]
    assert (model['label'],model['frequency_rank'],model['solver_profile'])==('APPROX',230,'SB3_BTN')
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][MODEL]
    assert (contract['seat'],contract['streets'])==(0,['x x','x x',''])
    route_bytes=subprocess.check_output(['node',base.ROUTE]);route=json.loads(route_bytes)['230']
    assert route['flop']==route['turn']==route['river']=={'low:2':'過','mid_high:2':'過'}
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';ev.mkdir(parents=True)
    auth=source.validate(read(a.receipts));write(out/'nl2_hu_b795_source_receipts.json',auth)
    art,=auth['artifacts'];name='NL2_'+source.SOURCES[art['name']]+'.zip';path=a.archives/f"{art['id']}.zip"
    raw=(path if path.exists() else a.archives/name).read_bytes()
    assert sha(raw)==art['digest'][7:] and len(raw)==art['size_in_bytes'];(ev/name).write_bytes(raw)
    with TemporaryDirectory(prefix='b795-originals-') as temp:
        parent=Path(temp)
        group,medium=earlier.previous(parent,solver,model,contract,route,pipeline,pool);pairs.EVIDENCE=ev
        medium['schema']='NL2_HU_B791_ORIGINAL_LOCKED_MEDIUM_V1'
        assert group==read(EVIDENCE/'partial/b791_rank230.json') and medium==read(EVIDENCE/'partial/b791_rank230_locked_medium.json')
        medium['schema']='NL2_HU_B795_ORIGINAL_LOCKED_MEDIUM_V1'
        frozen=parent/'b793';replay.materialize(source.HEAD,frozen)
        folder=parent/source.FLOP;unpack_original(raw,folder)
        rust=(a.rust_source or solver/'postflop/postflop-solver').resolve()
        d=frozen_replay(frozen,solver,rust,folder)
        assert (d['schema'],d['flop'],d['model_id'],d['actor'],d['line'],d['source_worker_blob'])==(
            'NL2_B793_R230_HELD_OUT_HEART_TURNS_V1',source.FLOP,MODEL,0,LINE,source.PINS[source.WORKER])
        original_claim,files,jobs,old_pair=worker.checked_input()
        assert all((folder/path).read_bytes()==b for path,b in files.items())
        origin=d['origin'];assert (origin['run'],origin['job'],origin['head'])==(worker.receipt.RUN,worker.receipt.JOBS[source.FLOP],worker.receipt.HEAD)
        root=read(folder/'flop/result.json');held,masks,proposals=worker.plans(root,old_pair,original_claim,jobs,route,pipeline)
        assert origin['original_five_held_out_jobs']==held and origin['original_3h_6h9h']==masks and set(held)==set(worker.OLD)
        assert d['root_sha256']==origin['original_root_result_sha256']==sha(files['flop/result.json'])==worker.ROOT_SHA
        assert d['root_job_sha256']==sha(files['flop/job.json'])==origin['original_root_job_sha256']
        assert d['root_native_solves_repeated']==d['original_flop_reexports']==0 and d['no_observed_per_private_hand_frequency']
        assert (folder/'rendered-routes.json').read_bytes()==route_bytes
        turns=d['turns'];scheduled=list(worker.TURNS)
        assert d['preregistered_turns']==scheduled and [r['turn'] for r in turns]==scheduled[:len(turns)]
        if d['selected']:
            assert turns[-1]['common'] and d['selected']['turn']==turns[-1]['turn']
            view,edge,_,_,gate,_,job=proposals[d['selected']['turn']]
            assert turns[-1]['root_gate']==gate and compact(job)==(folder/(d['selected']['turn']+'-gto')/'job.json').read_bytes()
            selected(folder,d,art,view,model,contract,route,pipeline,pool,group,medium)
        else:assert len(turns)==len(scheduled) and all(not t['common'] for t in turns)
        locks=[b['reach'] for t in turns for b in t['policies'].get('exp_oop',{}).get('boards',{}).values()]
        assert len(locks)==len({r['public_board'] for r in locks})
        joint=[r for r in locks if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None]
        counts=(len(locks),len(joint),sum(r['b50']['candidate'] for r in joint))
        assert counts==tuple(d[k] for k in COUNTS)
        proof_sha=sha((folder/'proof.json').read_bytes())
    n=len(group['boards']);assert n==2+int(bool(d['selected']))==len(group['pins'])==len({suit_isomorphism_class(b['flop']) for b in group['boards']})
    assert n==len(medium['references'])==len(medium['gto_references'])
    if n==3:write(ev/'reverified/rank230.json',group);write(out/'nl2_hu_b795_locked_medium.json',medium)
    else:write(ev/'partial/b795_rank230.json',group);write(ev/'partial/b795_rank230_locked_medium.json',medium)
    summary=dict(schema='NL2_B795_AUTHENTICATED_RANK230_CHECKED_FLOPS_V1',rank=230,model_id=MODEL,source_run=source.RUN,source_head=source.HEAD,
        previous_publication=PRIOR_PUBLICATION,previous_positive_flops=[b['flop'] for b in group['boards'][:2]],
        artifact=art['id'],job_id=source.JOB,archive_sha256=sha(raw),proof_sha256=proof_sha,original_source=origin,selected=d['selected'],
        positive_distinct_flops=n,cert_eligible_ranks=[230] if n==3 else [],**dict(zip(COUNTS,counts,strict=True)))
    write(out/'nl2_hu_b795_results.json',summary);assert registry.read_bytes()==baseline
    print(json.dumps({k:summary[k] for k in ('positive_distinct_flops','selected','cert_eligible_ranks',*COUNTS)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','archives','receipts','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--rust-source',type=Path)
    publish(p.parse_args())
