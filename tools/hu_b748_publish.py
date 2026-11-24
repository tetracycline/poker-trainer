"""Authenticate and replay B741's BTN–BB check-raise turn workers in a separate evidence stage."""
import argparse
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

import hu_b741_rank172 as native
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b710_publish import unpack_original
from hu_b736_publish import fields, run_receipt, job_receipt, artifact_receipt, read, write
from hu_board_reach_corrections import source_key, summarize
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible
from verify_hu_multiboard_100bb import lock_scope

RUN=45333267554
HEAD='c7c107b0ccc384debf92231ac62349e454ea2975'
JOBS={'Th8d4c':138239206138,'6d5h3s':138239206430,'Jd9s3c':138239206437}
ARTIFACTS={
   "Jd9s3c": [
      14893880659,
      "1ae39a74ab67690fad02583c85d4b77a272be95b330eb12453c713a3915a2b68"
   ],
   "6d5h3s": [
      14893051681,
      "4a4f273fad67ed7baf54f87a3642deba8c79cded41d06bbca4747c5c0cd1d294"
   ],
   "Th8d4c": [
      14892529506,
      "b1fe003e7b7123646b6c03cbe0392a668b53206a549d042dd40952340de11599"
   ]
}
WF='.github/workflows/nl2-hu-b741-rank172-turns.yml'
WORKER='tools/hu_b741_rank172.py'
ROUTE='tools/hu_b741_rank172_routes.cjs'
PINS={WF:'e3c2a1acb26d0d321a6ea4ab6c2d7033a05c674c',WORKER:'6948a5b0d6f979152c5731af8434107039c3113a',ROUTE:'aa8c82a8013ea2bd634ea4b2dca5193dcb1ee63b'}
STEPS=['Check observed BB check-raises, compatible BTN calls and displayed turns','Compile the pinned native solver',
       'Solve the new flop and conditional check-raise turns, then replay both policies','Run actions/upload-artifact@v4']


def auth(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WF)
    assert set(JOBS)==set(ARTIFACTS)==set(native.CASES) and len(raw['jobs'])==len(raw['artifacts'])==3
    out=dict(run=run,jobs=[],artifacts=[])
    for flop in JOBS:
        aid,digest=ARTIFACTS[flop]
        job,=[j for j in raw['jobs'] if j['id']==JOBS[flop]]
        artifact,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(job,run,JOBS[flop],f'solve ({flop})',STEPS))
        out['artifacts'].append(artifact_receipt(artifact,run,aid,'B741-R172-'+flop,digest))
    return out


def source_tree(tree):
    paths=['tools',WF,'lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js',
           'data/nl2_hu_multiboard_status_current.json','data/nl2_hu_b485_original_artifacts.json']
    paths += ['data/solver_evidence/'+r[0] for r in native.REFERENCES.values()]
    raw=subprocess.check_output(['git','archive',HEAD,'--',*paths])
    with tarfile.open(fileobj=io.BytesIO(raw)) as z:
        for entry in z:
            name=Path(entry.name)
            assert not name.is_absolute() and '..' not in name.parts
            if entry.isdir():continue
            assert entry.isfile();path=tree/name;path.parent.mkdir(exist_ok=True,parents=True);path.write_bytes(z.extractfile(entry).read())
    for n,pin in PINS.items():assert subprocess.check_output(['git','hash-object',str(tree/n)],text=True).strip()==pin


def verify_one(tree,folder,flop,raw,solver,current):
    aid,digest=ARTIFACTS[flop];assert sha(raw)==digest
    folder.mkdir();names=unpack_original(raw,folder);proof=(folder/'proof.json').read_bytes();d=json.loads(proof)
    assert (d['schema'],d['rank'],d['model_id'],d['line'],d['actor'],d['spot'],d['flop'])==(
        'NL2_B741_BTN_BB_R172_CHECK_RAISE_TURN_V1',172,native.MODEL,native.LINE,0,native.SPOT,flop)
    assert (d['root_pot'],d['root_stack'],d['opponent_bet'],d['bb_raise_total'],d['turn_pot'],d['turn_stack'])==(550,9750,413,1239,3028,8511)
    assert d['original_prerequisite']['displayed_bb_with_compatible_btn']==native.REFERENCES[flop][-1]
    required={'flop/job.json','flop/result.json','proof.json','rendered-routes.json'}
    scheduled=native.CASES[flop][0]
    assert [t['turn'] for t in d['turns']]==scheduled[:len(d['turns'])]
    if not d['selected']:assert len(d['turns'])==len(scheduled)
    turns=[]
    for t in d['turns']:
        assert bool(t['gto'])==bool(t['gate']['bb_displayed_compatible'])
        assert bool(t['nl2'])==bool(t['gto'] and t['gto']['hands'])
        for ver,key in [('gto','gto'),('exp_oop','nl2')]:
            if t[key] is not None:required|={t['turn']+'-'+ver+'/'+n for n in ('job.json','result.json')}
        e=t['nl2'];g=t['gto'];joint=0;cand=False
        if e:
            assert t['common']==sorted(g['hands'].keys()&e['hands'].keys())
            r=e['reach'];joint=int(r['strict_legal_combos']>0)
            assert bool(r['compatible_hole_card_pairs'])==bool(joint)==bool(r['b50'] is not None)
            if joint:cand=r['b50']['candidate']
        turns.append(dict(turn=t['turn'],public_board=t['gate']['public_board'],bb_check_raise=t['gate']['bb_check_raise'],
            btn_bet_call=t['gate']['btn_bet_call'],displayed_bb_with_compatible_btn=len(t['gate']['bb_displayed_compatible']),
            gto_solved=bool(g),gto_displayed=len(g['hands']) if g else 0,nl2_locked=bool(e),nl2_displayed=len(e['hands']) if e else 0,
            joint_halfpot_assessed=joint,nonpolarized_candidate=cand,common=t['common']))
    assert names==required and set(d['native_files'])==required-{'proof.json'}
    assert all(sha((folder/n).read_bytes())==v for n,v in d['native_files'].items())
    assert (folder/'rendered-routes.json').read_bytes()==current and d['route_sha256']==sha(current)
    subprocess.run([sys.executable,str(tree/WORKER),'--solver',str(solver),'--flop',flop,'--output',str(folder)],cwd=tree,check=True,stdout=subprocess.DEVNULL)
    assert (folder/'proof.json').read_bytes()==proof
    assert all(sha((folder/n).read_bytes())==v for n,v in d['native_files'].items())
    counts=dict(native_locked_public_boards=sum(t['nl2_locked'] for t in turns),joint_halfpot_assessed=sum(t['joint_halfpot_assessed'] for t in turns),
        nonpolarized_candidates=sum(t['nonpolarized_candidate'] for t in turns),positive_distinct_flops=int(any(t['common'] for t in turns)))
    assert all(d[k]==v for k,v in counts.items())
    return d,dict(flop=flop,original_flop_prerequisite=d['original_prerequisite'],artifact_id=aid,job_id=JOBS[flop],archive_sha256=digest,
        sha256_files=d['native_files'],proof_sha256=sha(proof),turns=turns,selected=d['selected'],**counts)


def make_sources(folder,flop,d,pipeline,pool):
    root=read(folder/'flop/result.json');root_sha=sha(compact(root));original_root_sha=sha((folder/'flop/result.json').read_bytes())
    turn=d['selected']['turn'];t,=[t for t in d['turns'] if t['turn']==turn]
    src=dict(root=root,run=RUN,version='gto',root_sha256=root_sha,original_root_sha256=original_root_sha,
        archive_code='B741_R172_'+flop.upper(),archive_sha256=ARTIFACTS[flop][1],
        manifest=dict(spot='BTN_BB',pot_family='SRP',locks=[],preflop_ranges=dict(source='PINNED_POKER_SOLVER_PREFLOP_CFR')))
    gj=read(folder/(turn+'-gto/job.json'))
    par,=[n for n in root['nodes'] if n['line']==native.LINE and n['board'][6:]==turn]
    for seat,key in enumerate(('oop_w','ip_w')):assert gj[key]==[[h,w] for h,w in zip(root['hands'][seat],par['wr'][seat],strict=True) if w>1e-4]
    ej,rules=native.prepare_job(dict(source=src,job=gj),'exp_oop',pool,pipeline);ej['out']='result.json'
    assert read(folder/(turn+'-exp_oop/job.json'))==json.loads(compact(ej))
    locked=dict(src,version='exp_oop',verified_gto_parent=dict(run=RUN,sha256=root_sha),
        manifest=dict(src['manifest'],locks=rules,gto_parent_source_run_id=RUN,gto_parent_source_sha256=root_sha))
    for v in (src,locked):
        path=turn+'-'+v['version']+'/result.json';raw=(folder/path).read_bytes();assert sha(raw)==d['native_files'][path]
        sub=json.loads(raw);sub.update(line0=native.FLOP_LINE,turn=turn,rivers=[]);v.update(subgame=sub,source_sha256=sha(raw))
    measured=native.audit_patterns(locked['subgame'],ej,locked['manifest'],pool,0)
    assert measured==t['measured_lock_application']
    locked.update(applied_rust_rates=locked['subgame']['info']['lock_stats'],measured_lock_application=measured)
    return src,locked,t


def emit(folder,flop,d,route,model,contract,group,medium,pipeline,pool):
    g,e,t=make_sources(folder,flop,d,pipeline,pool);s=d['selected'];b=s['public_board'];public=[]
    witnesses=[]
    for v,key in ((g,'gto'),(e,'nl2')):
        sub=v['subgame'];current=native.decision(v['root'],sub,t['turn'],route)
        assert current==t[key];r=current['reach']
        assert r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None
        r.update(version=v['version'],spot=native.SPOT,family='SRP',flop=flop,turn=t['turn'],source_run_id=RUN,
            source_sha256=v['source_sha256'],archive_sha256=v['archive_sha256'],root_sha256=v['root_sha256'],original_root_sha256=v['original_root_sha256'],
            root_gto_stage_gap_pct=v['root']['info']['gto_expl_pct'],root_locked_hero_gap_pct=None,gto_gap_pct=sub['info']['gto_expl_pct'],
            locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(x['nodes'] for x in sub['info'].get('lock_stats',{}).values()),
            lock_scope=lock_scope(sub,v['manifest']['locks'],v['version']))
        summarize(r);public.append(r)
    assert sorted(t['gto']['hands'].keys()&t['nl2']['hands'].keys())==s['hands']==t['common']
    for h in s['hands']:
        l=t['gto']['hands'][h];r=t['nl2']['hands'][h]
        assert all(l[k]==r[k] for k in ('flop_class','turn_class','displayed_suggestion'))
        assert native.ACTIONS[l['displayed_suggestion']] in l['accepted_actions'] and native.ACTIONS[r['displayed_suggestion']] in r['accepted_actions']
        pf='action_order accepted_mask accepted_actions strategy'
        witnesses.append(dict(hand=h,**fields(l,'flop_class turn_class displayed_suggestion'),gto=fields(l,pf),nl2=fields(r,pf)))
    item,pin=pairs.emit_board(model,g,e,b,native.LINE,texture(flop),viewer_code='B748_R172_'+flop.upper())
    assert item and compatible(contract,item) and (item['actual_pot_bb'],item['actual_effective_stack_bb'])==(30.28,85.11)
    assert pin['pool_observed_marginal_lock_nodes']>0
    item.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=RUN,flop_bet_size_menu='33%,50%,75%',
        original_btn_bet_chips=413,original_bb_check_raise_total_chips=1239)
    item['nl2_locked_variants'][0].update(source_run_role=item['source_run_role'],origin_solve_run_id=RUN,pool_sha256=native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),gto_parent_source_run_id=RUN,
        gto_parent_source_sha256=g['root_sha256'],viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
    pin.update(rendered_decision_hands=witnesses,worker_artifact=ARTIFACTS[flop][0],worker_sha256=ARTIFACTS[flop][1],
        source_run_role=item['source_run_role'],original_flop_sha256=g['original_root_sha256'])
    for key,row in zip(('gto_references','references'),public,strict=True):
        row['rendered_decision_hands']=witnesses;medium[key][source_key(native.MODEL,row)]=row
    group['boards'].append(item);group['pins'].append(pin)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    dest=a.output.resolve();solver=a.solver.resolve()
    assert not dest.exists() and Path('data').resolve() not in (dest,*dest.parents)
    data=dest/'data';ev=data/'solver_evidence';ev.mkdir(parents=True);pairs.EVIDENCE=ev
    receipt=auth(read(a.receipts))
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    raw_routes=subprocess.check_output(['node',ROUTE]);route=json.loads(raw_routes)['route']
    model=read(Path('data/nl2_hu_multiboard_status_current.json'))['records'][native.MODEL]
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][native.MODEL]
    assert (model['frequency_rank'],model['assumed_model_node_spr'],contract['seat'])==(172,2.887,0)
    group=dict(rank=172,model_id=native.MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B748_R172_TURN_LOCKED_MEDIUM_V1',references={},gto_references={});workers=[]
    with TemporaryDirectory(prefix='b748-replay-') as tmp:
        parent=Path(tmp);tree=parent/'source';source_tree(tree)
        assert subprocess.check_output(['node',ROUTE],cwd=tree)==raw_routes
        for flop in native.CASES:
            num,digest=ARTIFACTS[flop];name='NL2_B741_R172_'+flop.upper()+'.zip'
            path=a.archives/f'{num}.zip';raw=(path if path.is_file() else a.archives/name).read_bytes()
            assert len(raw)==next(v['size_in_bytes'] for v in receipt['artifacts'] if v['id']==num)
            folder=parent/flop;d,w=verify_one(tree,folder,flop,raw,solver,raw_routes);workers.append(w)
            (ev/name).write_bytes(raw)
            if d['selected']:emit(folder,flop,d,route,model,contract,group,medium,pipeline,pool)
    n=len(group['boards'])
    assert len({native.suit_isomorphism_class(b['flop']) for b in group['boards']})==n<=3
    if n:
        write(ev/('reverified' if n>=3 else 'partial')/'rank172.json',group)
        write(data/'nl2_hu_b748_locked_medium.json' if n>=3 else ev/'partial/b748_rank172_locked_medium.json',medium)
    counts={k:sum(w[k] for w in workers) for k in ('native_locked_public_boards','joint_halfpot_assessed','nonpolarized_candidates')}
    summary=dict(schema='NL2_HU_B748_VERIFIED_CHECK_RAISE_TURNS_V1',rank=172,model_id=native.MODEL,source_run=RUN,
        source_head=HEAD,source_blobs=PINS,workers=workers,native_solver_calls_in_publication=0,positive_distinct_flops=n,
        cert_eligible_ranks=[172] if n>=3 else [],**counts)
    write(data/'nl2_hu_b748_results.json',summary);write(data/'nl2_hu_b748_source_receipts.json',receipt)
    print(json.dumps(dict(positive_distinct_flops=n,cert_eligible_ranks=summary['cert_eligible_ranks'],**counts)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--solver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b748_source_receipts.json'))
    p.add_argument('--archives',type=Path,default=Path('data/solver_evidence'));publish(p.parse_args())
