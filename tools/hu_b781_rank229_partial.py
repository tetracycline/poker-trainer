"""Recheck the original Kc9d4h private deal and preserve at most one new verified Kd9c5h flop."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b728_replay as prior
import hu_b780_rank229_suited_turns as worker
import hu_b781_collect as receipt
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture

EV=Path('data/solver_evidence')
ARCHIVE='B780_R229_KD9C5H'

def replay_foes(root,game,t,pub):
    """Intersect physical hands and raw weights at the original flop, turn and river."""
    fs={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    ts={n['line']:n for n in game['nodes'] if n['board']==pub[:8]}
    start,=[n for n in root['nodes'] if n['board']==pub[:8] and n['line']=='x x/']
    final,=[n for n in game['nodes'] if n['board']==pub and n['line']==worker.LINE and n['player']==0]
    alive=[{worker.cardkey(h) for h,w in zip(root['hands'][i],start['wr'][i],strict=True) if w>1e-4}
           &{worker.cardkey(h) for h,w in zip(game['hands'][i],final['w'][i],strict=True) if w>1e-4}
           for i in (0,1)]
    sb=alive[0]&worker.accepted(fs[''],root['hands'],'x')&worker.accepted(ts['x x/'],game['hands'],'x')&worker.accepted(final,game['hands'],'x')
    hero=worker.cardkey(worker.HERO)
    if hero not in sb:return []
    btn=alive[1]&worker.accepted(fs['x'],root['hands'],'x')&worker.accepted(ts['x x/x'],game['hands'],'x')
    held=worker.public_cards(pub+worker.HERO)
    return sorted(''.join(v) for v in btn if held.isdisjoint(v))

def replay_new(folder,routes,pipeline,pool,raw,solver):
    aid,digest=receipt.PINS[worker.FLOP];assert sha(raw)==digest
    names=unpack_original(raw,folder);proof=(folder/'proof.json').read_bytes();claim=json.loads(proof)
    assert names=={'proof.json','original-b681.zip','rendered-routes.json','flop/job.json','flop/result.json'}|{
        t['turn']+'-'+pol+'/'+filename for t in claim['turns'] for pol in t['policies'] for filename in ('job.json','result.json')}
    assert (folder/'rendered-routes.json').read_bytes()==routes
    worker.run(SimpleNamespace(solver=solver,archive=folder/'original-b681.zip',output=folder,driver=None,preflight=False))
    assert (folder/'proof.json').read_bytes()==proof
    root=worker.read(folder/'flop/result.json');csha=sha(compact(root));chosen=None
    assert [t['turn'] for t in claim['turns']]==list(worker.TURNS)[:len(claim['turns'])]
    assert claim['original_nodes_unchanged']==14 and len(root['nodes'])==17
    route=json.loads(routes)['229'];totals=dict(locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0)
    verified=[]
    for t in claim['turns']:
        turn=t['turn'];sources={};witnesses={}
        for mode,p in t['policies'].items():
            work=folder/(turn+'-'+mode);game=worker.read(work/'result.json');job=worker.read(work/'job.json')
            assert (sha((work/'result.json').read_bytes()),sha((work/'job.json').read_bytes()))==(p['source_sha256'],p['job_sha256'])
            game.update(line0='x x',turn=turn,rivers=t['river_cards'])
            computed={pub:replay_foes(root,game,turn,pub) for pub in p['boards']}
            for pub,foes in computed.items():
                displayed=p['boards'][pub]['displayed_check_hands']
                if not all(worker.hand_cell(worker.HERO,pub[:n])[0] in route[k] for n,k in ((6,'flop'),(8,'turn'),(10,'river'))):
                    computed[pub]=[];continue
                assert set(displayed)<={worker.HERO} and (not foes or worker.HERO in displayed)
            witnesses[mode]={b:h for b,h in computed.items() if h}
            assert witnesses[mode]==p['compatible_btn_by_public_board']
            s=dict(root=root,root_sha256=csha,subgame=game,source_sha256=p['source_sha256'],archive_sha256=digest,
                   archive_code=ARCHIVE,version=mode,run=receipt.RUN,manifest=dict(spot='SB3_BTN',pot_family='3BP',locks=[]))
            if mode==worker.MODE:
                gtojob=worker.read(folder/(turn+'-gto/job.json'))
                exp,rules=worker.prepare_job(dict(source=dict(root=root,version='gto',manifest=dict(spot='SB3_BTN')),job=gtojob),mode,pool,pipeline)
                exp['out']='result.json';assert exp==job and job['hero']==0
                applied=worker.audit_patterns(game,job,dict(locks=rules),pool,0);assert applied==p['applied_lock']
                s['manifest'].update(locks=rules,gto_parent_source_run_id=receipt.RUN,gto_parent_source_sha256=csha)
                s.update(verified_gto_parent=dict(run=receipt.RUN,sha256=csha),measured_lock_application=applied,applied_rust_rates=game['info']['lock_stats'])
                locked=[v['reach'] for v in p['boards'].values()]
                half=[v for v in locked if v['strict_legal_combos'] and v['compatible_hole_card_pairs'] and 'b50'in v['source_actions'] and v['b50'] is not None]
                totals['locked_public_boards']+=len(locked);totals['joint_halfpot_assessed']+=len(half);totals['halfpot_candidates']+=sum(bool(r['b50']['candidate']) for r in half)
            sources[mode]=s
        common={}
        for pub,btn in witnesses.get('gto',{}).items():
            shared=sorted(set(btn)&set(witnesses.get(worker.MODE,{}).get(pub,[])))
            if shared:common[pub]=dict(sb=worker.HERO,btn_hands=shared)
        assert common==t['common'];verified.append(dict(turn=turn,common=common))
        if common:
            assert chosen is None and turn==claim['turns'][-1]['turn']
            public=min(common);chosen=(public,sources,common[public]['btn_hands'])
            assert claim['selected']==dict(turn=turn,public_board=public,**common[public])
    assert all(claim[k]==v for k,v in totals.items()) and claim['positive_distinct_flops']==int(chosen is not None)
    return claim,totals,chosen,verified

def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    pool=worker.read(solver/'inputs/pool_stats.json')['NL2']
    for path,blob in receipt.FILES.items():assert prior.git_blob(path)==blob
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    model=json.loads(before)['records'][worker.MODEL]
    assert (model['frequency_rank'],model['solver_profile'])==(229,'SB3_BTN')
    routes=subprocess.check_output(['node',worker.ROUTE])
    st=a.output.resolve();assert not st.exists() and not st.is_relative_to(Path('data').resolve())
    ev=st/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    pairs.EVIDENCE=ev;validate=receipt.validate(worker.read(a.archives/'receipt.json'))
    (st/'nl2_hu_b781_source_manifest.json').write_bytes(json_bytes(validate))
    aid,digest=receipt.PINS[worker.FLOP];raw=(a.archives/(str(aid)+'.zip')).read_bytes()
    with TemporaryDirectory(prefix='b781-') as tmp:
        temp=Path(tmp);group,medium=prior.verify_prior(temp/'b676',solver,pipeline,pool,routes)
        medium['schema']='NL2_HU_B781_ORIGINAL_LOCKED_MEDIUM_V1'
        claim,totals,chosen,verified=replay_new(temp/'b780',routes,pipeline,pool,raw,solver)
        if chosen:
            public,s,foes=chosen;g=s['gto'];e=s[worker.MODE]
            decisions,grow,erow=prior.compare_hand_policies(g,e,public,json.loads(routes)['229'])
            assert [w['hand'] for w in decisions]==[worker.HERO]
            decisions[0].update(compatible_btn_hand=foes[0],same_policy_opponents=len(foes))
            b,p=pairs.emit_board(model,g,e,public,worker.LINE,texture(worker.FLOP),viewer_code='B781_R229_KD9C5H')
            assert b and (b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==(0,21,90)
            b['nl2_locked_variants'][0].update(origin_solve_run_id=receipt.RUN,pool_sha256=worker.POOL,applied_street_rates=rates(e),
                gto_parent_source_run_id=receipt.RUN,gto_parent_source_sha256=e['root_sha256'])
            p.update(rendered_decision_hands=decisions,worker_artifact=aid,worker_sha256=digest,worker_head=receipt.HEAD,
                original_job_id=receipt.JOBS[worker.FLOP],original_b681_source=claim['source'],new_raw_boundary_sha256=claim['new_raw_boundary_sha256'][b['turn']])
            group['boards'].append(b);group['pins'].append(p)
            for key,row in [('gto_references',grow),('references',erow)]:
                row['rendered_decision_hands']=decisions;medium[key][source_key(worker.MODEL,row)]=row
    count=len(group['boards']);assert 1<=count<=2 and count==len({suit_isomorphism_class(x['flop']) for x in group['boards']})
    old=worker.read(EV/'partial/rank229.json');assert group['boards'][:1]==old['boards'] and group['pins'][:1]==old['pins']
    (ev/('NL2_'+ARCHIVE+'.zip')).write_bytes(raw)
    (partial/'b781_rank229.json').write_bytes(json_bytes(group));(partial/'b781_rank229_locked_medium.json').write_bytes(json_bytes(medium))
    (partial/'b781_rank229_turns.json').write_bytes(json_bytes(dict(source_proof=claim,checked=verified)))
    summary=dict(rank=229,model_id=worker.MODEL,source_run=receipt.RUN,source_head=receipt.HEAD,original_worker=receipt.JOBS[worker.FLOP],
                 worker_artifact=aid,archive_sha256=digest,prior_positive_flops=1,positive_distinct_flops=count,
                 new_positive_flops=claim['positive_distinct_flops'],selected=claim['selected'],cert_eligible_ranks=[],
                 original_nodes_unchanged=14,publisher_native_solves_repeated=0,**totals)
    (st/'nl2_hu_b781_results.json').write_bytes(json_bytes(summary));assert registry.read_bytes()==before
    print(json.dumps(dict(positive_distinct_flops=count,**totals)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('archives','output','solver'):p.add_argument('--'+k,type=Path,required=True)
    run(p.parse_args())
