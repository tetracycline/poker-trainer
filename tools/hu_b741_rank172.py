"""Check new BB check-raise turns after BTN's displayed 75% c-bet in a single-raised pot."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_b676_checked_rivers import public_cards
from hu_b686_rank121 import ACTIONS
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

MODEL='ln-bb-t_model-jenhr8'
SPOT='BTN_BB'
FLOP_LINE='x b75 r c'
LINE=FLOP_LINE+'/'
CASES={'Jd9s3c':(['2c','4d','5s','Kh'],'8cTc','T8s'),
       'Th8d4c':(['2h','3s','5c','Qs'],'7h9h','97s'),
       '6d5h3s':(['8h','Td','Js','Qc'],'4cKc','K4s')}
REFERENCES={
    "Jd9s3c": [
        "NL2_B492_BTN_BB_JS9H4D_TS_GTO.zip",
        "original-flop.json",
        "original-flop.job.json",
        "a3f58ea122c15add648c2e74a5eac5bbb4c50479e9f6e553e55a8b977badca42",
        "707e525006628c2fda778bf6e8cc6950773f59c3c212f6fc3f79e5ab814082f7",
        8
    ],
    "6d5h3s": [
        "NL2_B524_R8_6S5H4D_GTO.zip",
        "solver/postflop/out/BTN_BB/gto/6s5h4d_multiboard.json",
        "solver/postflop/out/BTN_BB/gto/6s5h4d_multiboard.job.json",
        "df887d5566b9f99505a5310b3e236205c6bfbd55b19013266fbf3e91071a442b",
        "1ac6d7bd850b2388d9b0a366ef807571e0ea6078d949b6fa6a0b8e50d27293c2",
        23
    ],
    "Th8d4c": [
        "NL2_B709_R89_TD8C3H.zip",
        "flop/result.json",
        "flop/job.json",
        "139033aee47ce8525da1a56036af1a45238b79db8286aaefd8304fa73013c077",
        "09d839ec5342b3a90433185608473ce18eace92d3e7f43b65c640d3de7117ddd",
        18
    ]
}
EVID=Path('data/solver_evidence')


def flop_ranges(root):
    flop=root['flop']
    ns={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    for line,seat,pot,bets in [('',0,550,[0,0]),('x',1,550,[0,0]),('x b75',0,963,[0,413]),('x b75 r',1,2202,[1239,413])]:
        node=ns[line]
        assert (node['player'],node['pot'],node['bets'])==(seat,pot,bets) and public_cards(node['board'])==public_cards(flop)
    hero=accepted(ns[''],root['hands'],'x')&accepted(ns['x b75'],root['hands'],'r')
    opponent=accepted(ns['x'],root['hands'],'b75')&accepted(ns['x b75 r'],root['hands'],'c')
    return hero,opponent


def original_screen(flop,routes,expected_ranges):
    archive,path,job_path,archive_sha,root_sha,expected=REFERENCES[flop]
    raw=(EVID/archive).read_bytes();assert sha(raw)==archive_sha
    with ZipFile(EVID/archive) as z:
        source=z.read(path);assert sha(source)==root_sha
        root=json.loads(source);job=json.loads(z.read(job_path))
    assert (job['oop'],job['ip'])==expected_ranges and (job['pot'],job['stack'])==(550,9750)
    assert not job.get('locks') and not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    hs,vs=flop_ranges(root)
    joint=[h for h in hs if hand_cell(''.join(h),root['flop'])[0] in routes['flop'] and any(set(h).isdisjoint(v) for v in vs)]
    assert len(joint)==expected
    return dict(flop=root['flop'],archive=archive,archive_sha256=archive_sha,root_file=path,root_sha256=root_sha,
                full_bb_check_raise_combos=len(hs),full_btn_bet_call_combos=len(vs),displayed_bb_with_compatible_btn=len(joint))


def boundary(root,turn,routes):
    node,=[n for n in root['nodes'] if n['line']==LINE and n['board'][6:]==turn]
    assert (node['player'],node['pot'],node['bets'])==(0,3028,[1239,1239])
    b=node['board'];known=public_cards(b)
    assert len(known)==4 and known-{turn}==public_cards(root['flop'])
    hs,vs=flop_ranges(root);weighted=[{cardkey(h) for h,w in zip(root['hands'][k],node['wr'][k],strict=True)
        if w>1e-4 and known.isdisjoint(cardkey(h))} for k in (0,1)]
    hero,opp=hs&weighted[0],vs&weighted[1]
    shown={h for h in hero if hand_cell(''.join(h),b[:6])[0] in routes['flop'] and hand_cell(''.join(h),b)[0] in routes['turn']}
    pairs={''.join(h):sum(set(h).isdisjoint(v) for v in opp) for h in sorted(shown)}
    return node,dict(public_board=b,bb_check_raise=len(hs),btn_bet_call=len(vs),bb_with_raw_boundary=len(hero),
        btn_with_raw_boundary=len(opp),bb_displayed=len(shown),bb_displayed_compatible={h:n for h,n in pairs.items() if n})


def decision(root,sub,turn,route):
    sub.update(line0=FLOP_LINE,turn=turn,rivers=[])
    n,=[n for n in sub['nodes'] if (n['line'],n['player'])==(LINE,0)]
    assert (n['pot'],n['bets'],sub['stack'])==(3028,[0,0],8511)
    assert {'x','b33','b50','b75'}<=set(n['acts'])
    reach=proof(root,sub,n,game_reach(root,sub)[0])
    mask=base64.b64decode(reach['compatible_action_mask_b64'],validate=True);b=n['board'];hands={}
    for i,(hole,bits) in enumerate(zip(sub['hands'][0],mask,strict=True)):
        if not bits:continue
        f,t=hand_cell(hole,b[:6]),hand_cell(hole,b)
        if f[0] not in route['flop'] or t[0] not in route['turn']:continue
        label=route['turn'][t[0]];action=ACTIONS[label]
        if not bits&(1<<n['acts'].index(action)):continue
        n_hands=len(mask);w=[max(0,float(n['strat'][j*n_hands+i])) for j in range(len(n['acts']))]
        hands[''.join(cardkey(hole))]=dict(flop_class=f[1],turn_class=t[1],displayed_suggestion=label,
            action_order=n['acts'],accepted_mask=bits,accepted_actions=[a for j,a in enumerate(n['acts']) if bits&(1<<j)],
            strategy={a:round(v/sum(w),7) for a,v in zip(n['acts'],w,strict=True)})
    return dict(reach=reach,hands=hands)


def run(a):
    solver=a.solver.resolve();flop=a.flop
    assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    for p,pin in [('postflop/py/pipeline.py',PIPELINE),('postflop/py/ranges.py',RANGES),('inputs/pool_stats.json',POOL)]:
        assert sha((solver/p).read_bytes())==pin
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2'];weights=ranges.ranges(SPOT,'gto')
    expected=tuple(ranges.to_str(w) for w in weights)
    raw=subprocess.check_output(['node','tools/hu_b741_rank172_routes.cjs']);ui=json.loads(raw);routes=ui['route']
    assert (ui['id'],ui['actor'],ui['model_spr'])==(MODEL,0,2.887) and abs(8511/3028/ui['model_spr']-1)<.05
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (reg['frequency_rank'],reg['solver_profile'],reg['source_model_id'])==(172,SPOT,ui['facing'])
    source=original_screen(flop,routes,expected);turns,hero,cls=CASES[flop];villain='AsJc'
    old_flops=['Js9h4d','6s5h4d','Td8c3h','Ks7s2s','KsQh4d','8s8h3d','As9h2d','9s6h3d','AsQh8d','AsAh5h','Jh9d6s']
    assert len({suit_isomorphism_class(f) for f in [*old_flops,*CASES]})==len(old_flops)+3
    assert weights[0][ranges.NAMES.index(cls)]>0 and weights[1][ranges.NAMES.index('AJo')]>0
    for t in turns:
        assert len(public_cards(flop+t+hero+villain))==8
        assert hand_cell(hero,flop)[0] in routes['flop'] and hand_cell(hero,flop+t)[0] in routes['turn']
    if a.preflight:
        print(json.dumps(dict(new_flop=flop,reference=source,static_bb=hero,static_btn=villain)));return
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    def native(path,job):
        folder=out/path;g=solve(folder,job,None if (folder/'result.json').is_file() else a.driver)
        assert 0<=g['info']['gto_expl_pct']<=.5
        return g
    job=pipeline.make_job(SPOT,'gto',flop,'result.json',iters=2400,target=.45,compress=True)
    job.update(flop_oop='33%,50%,75%',flop_ip='33%,50%,75%',flop_raise='3x,a',
        extract=[dict(prefix=[],street=True)]+[dict(prefix=FLOP_LINE.split()+[t],raw=True,street=False) for t in turns])
    assert (job['oop'],job['ip'])==expected and (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(550,9750,.05,1000)
    root=native('flop',job)
    assert (root['flop'],root['pot'],root['stack'])==(flop,550,9750) and not root['info'].get('lock_stats')
    attempts=[];selected=None
    for t in turns:
        par,gate=boundary(root,t,routes);row=dict(turn=t,gate=gate,gto=None,nl2=None,common=[]);attempts.append(row)
        if not gate['bb_displayed_compatible']:continue
        turnjob=pipeline.make_job(SPOT,'gto',flop,'result.json',iters=2200,target=.4,rank=.4,compress=False)
        turnjob.update(pipeline.SUB)
        turnjob.update(oop='',ip='',pot=3028,stack=8511,turn=t,line0=FLOP_LINE.split()+['/'],root_no_bet=False,
            turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',
            extract=[dict(prefix=[],street=False)])
        for k,key in enumerate(('oop_w','ip_w')):
            turnjob[key]=[[h,w] for h,w in zip(root['hands'][k],par['wr'][k],strict=True) if w>1e-4]
        g=native(t+'-gto',turnjob);assert not g['info'].get('lock_stats')
        row['gto']=decision(root,g,t,routes)
        if not row['gto']['hands']:continue
        ej,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot=SPOT)),job=turnjob),
            'exp_oop',pool,pipeline);ej['out']='result.json'
        assert ej['hero']==0 and ej['locks']
        e=native(t+'-exp_oop',ej);assert e['hands']==g['hands'] and 0<=e['info']['hero_gap_pct']<=.5
        measured=audit_patterns(e,ej,dict(locks=rules),pool,0)
        assert any(v>0 for k,v in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
        row['measured_lock_application']=measured;row['nl2']=decision(root,e,t,routes)
        common=sorted(row['gto']['hands'].keys()&row['nl2']['hands'].keys());row['common']=common
        if common:
            assert all(h in gate['bb_displayed_compatible'] for h in common)
            selected=dict(public_board=gate['public_board'],flop=flop,turn=t,hands=common);break
    (out/'rendered-routes.json').write_bytes(raw)
    files={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    locked=[t['nl2']['reach'] for t in attempts if t['nl2']]
    joint=[r for r in locked if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0]
    assert all(r['b50'] is not None for r in joint)
    counts=dict(positive_distinct_flops=int(bool(selected)),native_locked_public_boards=len(locked),
        joint_halfpot_assessed=len(joint),nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    (out/'proof.json').write_bytes(json_bytes(dict(schema='NL2_B741_BTN_BB_R172_CHECK_RAISE_TURN_V1',rank=172,model_id=MODEL,
        spot=SPOT,actor=0,line=LINE,flop=flop,original_prerequisite=source,root_pot=550,root_stack=9750,opponent_bet=413,
        bb_raise_total=1239,turn_pot=3028,turn_stack=8511,model_spr=ui['model_spr'],solver=SOLVER,rust=RUST,pool_sha256=POOL,
        ranges_sha256=RANGES,route_sha256=sha(raw),scope='Frozen GTO flop, measured NL2 street marginals for BTN in turn/river with explicit fallback. No per-hand empirical frequencies.',
        turns=attempts,selected=selected,native_files=files,**counts)))
    print(json.dumps(counts))

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output'):cli.add_argument('--'+key,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True);cli.add_argument('--driver',type=Path);cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
