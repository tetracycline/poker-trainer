"""Resolve rank264 on two unexported B645 river continuations and one new original flop."""
import argparse
from base64 import b64decode
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b677_rank264_checks as source
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b645_rank195 import STUDY, original_template
from hu_b711_bb_lead_rivers import cards
from hu_checked_stab_turns import replay
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

CASES={'Js7s4d':['3d'],'Ts7s3h':['4c'],'Jc9c5d':['2h','4s','3d']}
OLD={'Js7s4d':('0b59b6d8d9148147e350165778d1ef689171c00daac04660a3e8abc5d15b5189',8),
     'Ts7s3h':('c8da04d9a1408033a1c76fd744c01fd3a338b4694a2829818ed6bb0288eebf1b',7)}
OLD_RUN=45270338166
NEW='Jc9c5d'
ROUTE='tools/hu_b677_rank264_routes.cjs'
LINE=source.LINE
TARGET=source.MODEL


def original(flop, template, pool, pipeline, registry):
    spec,=[s for s in json.loads(Path('data/nl2_hu_b645_bb_checked_inputs.json').read_bytes()) if s['flop']==flop]
    assert spec['sha256']==OLD[flop][0] and [spec['turn']]==CASES[flop]
    route=json.loads(subprocess.check_output(['node','tools/hu_b592_iso_turn_routes.cjs','195']))['195']
    _,(g,_),_,_,_=replay(STUDY,spec,template,pool,pipeline,OLD_RUN,route,registry[STUDY.model])
    with ZipFile(source.EVIDENCE/('NL2_'+STUDY.archive_code(flop)+'.zip')) as archive:
        raw={k:archive.read(k) for k in ('root.job.json','root.json','gto.job.json','gto.json')}
    assert source.sha(raw['gto.json'])==g['source_sha256']
    j=json.loads(raw['gto.job.json'])
    assert j['river_oop']==j['river_ip']=='50%,100%,a'
    assert not any(len(n['board'])==10 for n in g['subgame']['nodes'])
    return raw,g['subgame'],j


def parent(root,turn):
    node,=[n for n in root['nodes'] if n['line']=='x x/' and n['board'][6:]==turn]
    assert (node['player'],node['pot'],node['bets'])==(0,2050,[0,0])
    assert len(node['board'])==8 and cards(node['board'][:6])==cards(root['flop'])
    return node


def gate(root,turn,route,old_sub):
    p=parent(root,turn)
    public=p['board']
    f={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    seats=[]
    for seat,key in enumerate(('', 'x')):
        n=f[key]
        assert (n['player'],n['pot'],n['bets'])==(seat,2050,[0,0]) and cards(n['board'])==cards(root['flop'])
        strict=accepted(n,root['hands'],'x')
        weighted={cardkey(h) for h,w in zip(root['hands'][seat],p['wr'][seat],strict=True) if w>1e-4 and cards(public).isdisjoint(cardkey(h))}
        seats.append(strict&weighted)
    root_counts=list(map(len,seats))
    if old_sub:
        for seat,key in enumerate(('x x/','x x/x')):
            n,=[n for n in old_sub['nodes'] if (n['line'],n['board'],n['player'])==(key,public,seat)]
            seats[seat]&=accepted(n,old_sub['hands'],'x')
    own,opp=seats
    heroes=[h for h in sorted(own) if hand_cell(''.join(h),public[:6])[0] in route['flop']
            and hand_cell(''.join(h),public)[0] in route['turn'] and any(set(h).isdisjoint(v) for v in opp)]
    if old_sub:assert len(heroes)==OLD[root['flop']][1]
    by_river={}
    for river in source.DECK:
        if river in cards(public):continue
        eligible=[h for h in heroes if river not in h and hand_cell(''.join(h),public+river)[0] in route['river']
            and any(river not in v and set(h).isdisjoint(v) for v in opp)]
        if eligible:by_river[river]=len(eligible)
    legal=list(by_river)
    picks=legal if len(legal)<=12 else [legal[round(i*(len(legal)-1)/11)] for i in range(12)]
    return dict(public=public,root_weighted_check_hands_by_seat=root_counts,used_original_gto_turn_preflight=bool(old_sub),
        ancestry_hands_by_seat=list(map(len,seats)),compatible_rendered_mid_hands=len(heroes),
        legal_river_hands=by_river,preregistered_rivers=picks)


def continuation(root,turn,picks,template):
    p=parent(root,turn)
    job=deepcopy(template['subgame_job'])
    job.update(flop=root['flop'],turn=turn,out='result.json',line0=['x','x','/'],pot=2050,stack=9000,root_no_bet=False,
        turn_oop='33%,50%,75%',turn_ip='33%,50%,75%',river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',
        iters=2500,target_pct=.4,rank_pct=.4,compress=False,
        extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=False) for r in picks])
    for seat,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][seat],p['wr'][seat],strict=True) if w>1e-4]
        assert job[key]
    return job


def observation(root,sub,turn,picks,route):
    sub.update(line0='x x',turn=turn,rivers=picks)
    masks=game_reach(root,sub)[0]
    nodes=[n for n in sub['nodes'] if (n['line'],n['player'])==(LINE,0)]
    assert len(nodes)==len(picks) and {n['board'][-2:] for n in nodes}==set(picks)
    rows={}
    for n in nodes:
        b=n['board']
        assert b[:8]==parent(root,turn)['board'] and (n['pot'],n['bets'],sub['stack'])==(2050,[0,0],9000)
        assert {'x','b50','b75'}<=set(n['acts'])
        stats=proof(root,sub,n,masks)
        mask=b64decode(stats['compatible_action_mask_b64'],validate=True)
        check=1<<n['acts'].index('x')
        shown=[]
        for hand,bits in zip(sub['hands'][0],mask,strict=True):
            if not bits&check:continue
            hole=''.join(cardkey(hand))
            if all(hand_cell(hole,b[:size])[0] in route[street] for size,street in ((6,'flop'),(8,'turn'),(10,'river'))):
                shown.append(hole)
        rows[b]=dict(reach=stats,displayed_check_hands=sorted(shown))
    return rows


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==source.SOLVER
    py=solver/'postflop/py'
    assert source.sha((py/'pipeline.py').read_bytes())==PIPELINE and source.sha((py/'ranges.py').read_bytes())==RANGES
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==source.RUST
    sys.path.insert(0,str(py))
    import pipeline,ranges
    assert len({suit_isomorphism_class(f) for f in CASES})==3
    assert all(suit_isomorphism_class(NEW)!=suit_isomorphism_class(f) for f in list(OLD)+list(source.CASES)+['Jh8c5s'])
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert source.sha(poolraw)==POOL
    pool=json.loads(poolraw)['NL2']
    registry=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
    m=registry[TARGET]
    assert (m['frequency_rank'],m['solver_profile'],m['street'],m['assumed_model_node_spr'])==(264,'BB3_BTN',2,4.39)
    assert abs(9000/2050/m['assumed_model_node_spr']-1)<=.05
    rr=subprocess.check_output(['node',ROUTE])
    route=json.loads(rr)
    assert all(route[s]=={'low:2':'過','mid_high:2':'過'} for s in ('flop','turn','river'))
    template_raw=(source.EVIDENCE/STUDY.template).read_bytes()
    assert source.sha(template_raw)==STUDY.template_sha
    template=original_template(template_raw)
    assert (template['root_job']['oop'],template['root_job']['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('BB3_BTN','gto'))
    flop=a.flop
    old_sub=None
    if flop in OLD:
        raw,old_sub,old_job=original(flop,template,pool,pipeline,registry)
        job=json.loads(raw['root.job.json'])
        root=json.loads(raw['root.json'])
        assert job['flop_oop']==job['flop_ip']=='50%'
        origin=dict(role='VERIFICATION_OF_LOCAL_NATIVE_RESULTS',verification_run=OLD_RUN,
            archive=STUDY.archive_code(flop),archive_sha256=OLD[flop][0],root_job_sha256=source.sha(raw['root.job.json']),
            root_result_sha256=source.sha(raw['root.json']),previous_turn_job_sha256=source.sha(raw['gto.job.json']),
            previous_turn_result_sha256=source.sha(raw['gto.json']),previous_river_menu=old_job['river_oop'])
    else:
        job=dict(template['root_job'],flop=flop,out='result.json',flop_oop='33%,50%,75%',flop_ip='33%,50%,75%',
            target_pct=.45,iters=2500,extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',t],street=False,raw=True) for t in CASES[flop]])
        origin=dict(role='NEW_WORKFLOW_NATIVE_CFR')
        # The real preflop ranges give 88 to both seats and QJs to the caller.
        assert '88:0.740' in job['oop'] and 'QJs:1.000' in job['ip']
        for turn in CASES[flop]:
            for b in (flop,flop+turn,flop+turn+'6h'):
                assert hand_cell('8s8h',b)[0] in route[{6:'flop',8:'turn',10:'river'}[len(b)]]
            assert len(cards(flop+turn+'6h'+'8s8h'+'QsJs'))==9
    if a.preflight:
        gates={t:gate(root,t,route,old_sub) for t in CASES[flop]} if old_sub else {}
        print(json.dumps(dict(flop=flop,root_menu=job['flop_oop'],original_gto_turn_gates=gates,no_solver_invocation=True)))
        return
    assert a.run>0 and len(a.head)==40 and all(c in '0123456789abcdef' for c in a.head)
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir()),'Use a fresh native work directory'
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True)
    (out/'rendered-routes.json').write_bytes(rr)
    if old_sub:
        folder=out/'flop';folder.mkdir(exist_ok=True)
        for name,key in [('job.json','root.job.json'),('result.json','root.json')]:
            path=folder/name
            if path.exists():assert path.read_bytes()==raw[key]
            else:path.write_bytes(raw[key])
    else:
        root=source.solve(out/'flop',job,a.driver)
        assert (root['flop'],root['pot'],root['stack'])==(flop,2050,9000)
        origin.update(root_job_sha256=source.sha((out/'flop/job.json').read_bytes()),root_result_sha256=source.sha((out/'flop/result.json').read_bytes()))
    assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    plans={t:gate(root,t,route,old_sub) for t in CASES[flop]}
    report=dict(schema='NL2_HU_B722_BB3_R264_EXPANDED_RIVER_TREE_V1',rank=264,model_id=TARGET,flop=flop,
        source_run=a.run,source_head=a.head,source_worker_blob=subprocess.check_output(['git','hash-object',__file__],text=True).strip(),
        solver=source.SOLVER,rust=source.RUST,pipeline_sha256=PIPELINE,ranges_sha256=RANGES,pool_sha256=POOL,
        route_sha256=source.sha(rr),root_origin=origin,flop_bet_menu=job['flop_oop'],turn_menu='33%,50%,75%',
        river_menu='50%,75%,100%,a',line=LINE,actor=0,root_native_flops=int(flop==NEW),original_flops_resolved_again=0,
        lock_scope='FROZEN_GTO_FLOP_ACTOR_MATCHED_EXP_OOP_STREET_SPECIFIC_NL2_MARGINALS',observed_private_hand_frequencies=False,
        turns=[],selected=None,original_worker_result_not_a_certificate=True)
    for turn,diag in plans.items():
        picks=diag['preregistered_rivers']
        t=dict(turn=turn,parent_gate=diag,gto={},nl2={},shared={},actor_locked=False)
        report['turns'].append(t)
        if not picks:continue
        j=continuation(root,turn,picks,template)
        g=source.solve(out/(turn+'-gto'),j,a.driver)
        assert 0<=g['info']['gto_expl_pct']<=.5 and not g['info'].get('lock_stats')
        before=observation(root,g,turn,picks,route)
        t.update(gto=before,gto_job_sha256=source.sha((out/(turn+'-gto')/'job.json').read_bytes()),
            gto_result_sha256=source.sha((out/(turn+'-gto')/'result.json').read_bytes()))
        if not any(v['displayed_check_hands'] for v in before.values()):continue
        src=dict(version='gto',root=root,manifest=dict(template['manifest'],spot='BB3_BTN',pot_family='3BP'))
        locked,rules=source.prepare_job(dict(source=src,job=j),'exp_oop',pool,pipeline)
        locked['out']='result.json';assert locked['hero']==0 and locked['locks']
        e=source.solve(out/(turn+'-exp_oop'),locked,a.driver)
        assert e['hands']==g['hands'] and 0<=e['info']['hero_gap_pct']<=.5 and 0<=e['info']['gto_expl_pct']<=.5
        measured=source.audit_patterns(e,locked,dict(locks=rules),pool,0)
        assert any(n>0 for pat,n in measured['driver_tree_nodes'].items() if pat in measured['marginal_targets'])
        after=observation(root,e,turn,picks,route)
        t.update(nl2=after,actor_locked=True,measured_lock_application=measured,
            nl2_job_sha256=source.sha((out/(turn+'-exp_oop')/'job.json').read_bytes()),
            nl2_result_sha256=source.sha((out/(turn+'-exp_oop')/'result.json').read_bytes()))
        for public in sorted(before):
            same=sorted(set(before[public]['displayed_check_hands'])&set(after[public]['displayed_check_hands']))
            if same:
                t['shared'][public]=same
                if report['selected'] is None:report['selected']=dict(public_board=public,turn=turn,hands=same)
    rows=[(b,o['reach']) for t in report['turns'] for b,o in t['nl2'].items()]
    report.update(positive_distinct_flops=int(bool(report['selected'])),actor_locked_public_boards=len({b for b,o in rows}),
        joint_medium_assessed_public_boards=len({b for b,o in rows if o['strict_legal_combos'] and o['b50'] is not None}),
        nonpolarized_candidate_public_boards=len({b for b,o in rows if o['b50'] and o['b50']['candidate']}))
    report['native_files']={str(p.relative_to(out)):source.sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(source.json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','positive_distinct_flops','actor_locked_public_boards','joint_medium_assessed_public_boards','nonpolarized_candidate_public_boards')}))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output'):cli.add_argument('--'+key,type=Path,required=True)
    cli.add_argument('--run',type=int,default=0)
    cli.add_argument('--head',default='')
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--preflight',action='store_true')
    cli.add_argument('--driver',type=Path)
    run(cli.parse_args())
