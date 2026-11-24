"""Solve rank309 only at the published B581 checked-through Qc boundary."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b463_rank45_gate import SOLVER, RUST
from hu_b537_threebet_checked import RANGE_SHA
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_b676_checked_rivers import DECK, public_cards
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible
from solve_hu_missing_branches import EXTRA_SPOTS

SPOT, MODEL = 'CO3_BTN', 'ln-3bp-3b_r_model-sk61px'
FLOP, TURN, LINE = '9h7h5h', 'Qc', 'x x/x x/x'
POT, STACK = 1650, 9250
ARCHIVE = Path('data/solver_evidence/NL2_B581_R261_9H7H5H.zip')
ARCHIVE_SHA = 'e303c7ef0566109a9e45e464006df828c353677c62ff0e1283708f44a58fa1a3'
ROOT_SHA = 'ac852ea78726d6d1fdac741ceb8df4a5224b701f2a26490fa39f0c610c51a56e'
ROOT_JOB_SHA = '0282a68081ed4bf915143fb0290b256ea95891785997c0742723391e2fe5bfa3'
TEMPLATE_SHA = '41fea2f5e915ed0601bd50b786b26a6268867f844d730ccd2a8c58f0a8f0e7eb'


def node(game, board, line, seat):
    result, = (n for n in game['nodes'] if (n['board'], n['line'], n['player']) == (board, line, seat))
    assert (result['pot'], result['bets']) == (POT, [0, 0])
    return result


def original(ranges):
    assert sha(ARCHIVE.read_bytes()) == ARCHIVE_SHA
    pins = json.loads(Path('data/nl2_hu_b581_checked_river_inputs.json').read_bytes())
    pin, = (b for b in pins['boards'] if b['flop'] == FLOP)
    assert (pins['solver'], pins['rust'], pin['sha256'], pin['archive'], pin['turn']) == (SOLVER, RUST, ARCHIVE_SHA, ARCHIVE.name, '2d')
    with ZipFile(ARCHIVE) as archive:
        raw, job_raw, template_raw = [archive.read(k) for k in ('root.json', 'root.job.json', 'gto.job.json')]
    assert [sha(v) for v in (raw, job_raw, template_raw)] == [ROOT_SHA, ROOT_JOB_SHA, TEMPLATE_SHA]
    root, root_job, template = map(json.loads, (raw, job_raw, template_raw))
    ranges.SPOTS.update(EXTRA_SPOTS)
    profile = ranges.SPOTS[SPOT]
    assert (profile['oopc'],profile['ipc']) == ([('COrfi','open'),('COopen>BTN3b','call')],[('COopen>BTN','3bet')])
    assert (profile['oop'],profile['ip'],profile['pot'],profile['stack']) == ('CO','BTN',16.5,92.5)
    weights = [ranges.to_str(w) for w in ranges.ranges(SPOT,'gto')]
    assert weights == [root_job['oop'],root_job['ip']] and sha(compact(weights)) == RANGE_SHA['gto']
    assert (root['flop'], root['pot'], root['stack']) == (FLOP,POT,STACK) and 0 <= root['info']['gto_expl_pct'] <= .5
    assert not root_job.get('locks') and not root['info'].get('lock_stats')
    assert (root_job['flop_oop'],root_job['flop_ip'],root_job['rake_rate'],root_job['rake_cap']) == ('33%,50%,75%,100%','33%,50%,75%,100%',.05,1000)
    assert template['line0'] == ['x','x','/'] and template['turn'] == '2d' and template['root_no_bet'] is False
    assert all(template[k] == v for k,v in {'pot':POT,'stack':STACK,'flop':FLOP,'turn_oop':'50%,100%','turn_ip':'50%,100%','river_oop':'50%,100%,a','river_ip':'50%,100%,a'}.items())
    assert not template.get('locks') and template.get('hero') is None
    public = '5h7h9h'+TURN
    boundary = node(root,public,'x x/',0)
    assert public_cards(public[:6]) == public_cards(FLOP) and {'prefix':['x','x',TURN],'street':False,'raw':True} in root_job['extract']
    return root, template, boundary, raw, job_raw


def preflight(root, boundary, route):
    public = boundary['board']
    earlier = []
    for seat,line in enumerate(('', 'x')):
        action = accepted(node(root,public[:6],line,seat),root['hands'],'x')
        weighted = {cardkey(h) for h,w in zip(root['hands'][seat],boundary['wr'][seat],strict=True) if w > 1e-4}
        earlier.append({h for h in action & weighted if public_cards(public).isdisjoint(h)})
    co, btn = earlier
    shown = sorted(h for h in btn if all(route[s].get(hand_cell(''.join(h),p)[0]) == '過'
        for s,p in [('flop',public[:6]),('turn',public)]) and any(set(h).isdisjoint(v) for v in co))
    witness = [cardkey('2cAc'),cardkey('8c8d')]
    assert witness[0] in co and witness[1] in shown and set(witness[0]).isdisjoint(witness[1])
    assert witness[0] in accepted(boundary,root['hands'],'x')
    raw_weights = [boundary['wr'][seat][list(map(cardkey,root['hands'][seat])).index(h)] for seat,h in enumerate(witness)]
    assert raw_weights == [.96794,.33721]
    possible = {r:sorted(''.join(h) for h in shown if r not in h
        and route['river'].get(hand_cell(''.join(h),public+r)[0])=='過'
        and any(public_cards(public+r+''.join(h)).isdisjoint(v) for v in co))
        for r in DECK if r not in public_cards(public)}
    legal = [r for r in possible if possible[r]]
    assert '8c8d' in possible['2d']
    # Keep the traced witness and sample across the other eligible ranks/suits, before CFR.
    others = [r for r in legal if r!='2d']
    selected = ['2d'] + (others if len(others)<=15 else [others[round(i*(len(others)-1)/14)] for i in range(15)])
    assert len(selected)==len(set(selected)) and set(selected)<=set(legal)
    report = dict(public_board=public,original_raw_boundary_sha256=sha(compact(boundary)),
        strict_flop_checks_with_boundary_weight=[len(co),len(btn)],raw_range_combos=[sum(w>1e-4 for w in ws) for ws in boundary['wr']],
        displayed_btn_hands=[''.join(h) for h in shown],legal_rivers=len(legal),selected_rivers=selected,
        witness=dict(co='2cAc',btn='8c8d',flop_actions=['x','x'],original_wr=raw_weights,ui_example=public+'2d'))
    assert report['original_raw_boundary_sha256'] == 'bcc8a6c8588e62dbee41f55e3e5fb95c11621f386c75acc34211116d87aa70a2'
    assert (len(co),len(btn),len(shown),len(legal),len(selected)) == (151,75,6,40,16)
    assert report['raw_range_combos']==[156,98]
    return co, {r:possible[r] for r in selected}, report


def assessment(root,sub,boundary,allowed,original_co):
    rivers=list(allowed)
    sub.update(line0='x x',turn=TURN,rivers=rivers)
    masks=game_reach(root,sub)[0]
    public=boundary['board']
    turn_co=original_co & accepted(node(sub,public,'x x/',0),sub['hands'],'x')
    rows={}
    for river in rivers:
        board=public+river
        co_node=node(sub,board,'x x/x x/',0)
        btn_node=node(sub,board,LINE,1)
        co=turn_co & accepted(co_node,sub['hands'],'x')
        live={cardkey(h) for h,w in zip(sub['hands'][0],btn_node['w'][0],strict=True) if w>1e-4}
        co &= live
        row=proof(root,sub,btn_node,masks)
        assert {'x','b50'}<=set(row['source_actions'])
        bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        check=1<<btn_node['acts'].index('x')
        found={}
        for h,mask in zip(sub['hands'][1],bits,strict=True):
            hand=''.join(cardkey(h))
            if hand not in allowed[river] or not mask&check:continue
            opponents=sorted(''.join(v) for v in co if public_cards(board+hand).isdisjoint(v))
            if opponents:found[hand]=opponents
        rows[board]=dict(reach=row,co_by_displayed_btn=found)
    return rows


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve()
    git=lambda p:subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip()
    assert git(solver)==SOLVER
    native=solver/'postflop/py'
    assert sha((native/'pipeline.py').read_bytes())==PIPELINE and sha((native/'ranges.py').read_bytes())==RANGES
    if a.driver:
        assert git(solver/'postflop/postflop-solver')==RUST and a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
    sys.path.insert(0,str(native))
    import pipeline,ranges
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    route_raw=subprocess.check_output(['node',str(Path(__file__).with_name('hu_b796_rank309_routes.cjs'))])
    route=json.loads(route_raw)
    record=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert (record['frequency_rank'],record['solver_profile'],record['abstract_action_history'])==(309,SPOT,'對手過、你過|對手過、你過|對手過')
    assert contract['streets']==['x x','x x','x'] and contract['seat']==1 and abs(STACK/POT-record['assumed_model_node_spr'])<.001
    assert route['id']==MODEL and route['turn']==route['river']=={'KQ_high:2':'過','mono:2':'過'}
    root,template,boundary,raw,job_raw=original(ranges)
    co,allowed,gate=preflight(root,boundary,route)
    gto=dict(template,turn=TURN,extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in allowed])
    for seat,key in enumerate(('oop_w','ip_w')):
        gto[key]=[[h,w] for h,w in zip(root['hands'][seat],boundary['wr'][seat],strict=True) if w>1e-4]
    locked,meta=prepare_job(dict(source=dict(root=root,version='gto',manifest=dict(spot=SPOT)),job=gto),'exp_ip',pool,pipeline)
    locked['out']='result.json'
    assert locked['hero']==1 and locked['locks'] and [gto[k] for k in ('oop_w','ip_w')]==[locked[k] for k in ('oop_w','ip_w')]
    if a.preflight:
        print(json.dumps(gate));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True)
    def keep(name,data):
        p=out/name
        if a.driver:p.write_bytes(data)
        else:assert p.read_bytes()==data,name
    for name,data in [('original-flop.json',raw),('original-flop.job.json',job_raw),('rendered-routes.json',route_raw)]:keep(name,data)
    report=dict(schema='NL2_B796_CO3_BTN_ORIGINAL_CHECKED_QC_V1',rank=309,model_id=MODEL,spot=SPOT,flop=FLOP,turn=TURN,actor=1,line=LINE,
        pot=POT,stack=STACK,archive=ARCHIVE.name,archive_sha256=ARCHIVE_SHA,root_sha256=ROOT_SHA,root_job_sha256=ROOT_JOB_SHA,
        template_sha256=TEMPLATE_SHA,route_sha256=sha(route_raw),pool_sha256=POOL,solver=SOLVER,rust=RUST,
        lock_scope='FROZEN_GTO_FLOP_MEASURED_CO_MARGINALS_IN_CONDITIONAL_TURN_AND_RIVER',observed_private_hand_frequencies=False,
        gate=gate,policies={},common={},selected=None)
    first_hands=None
    for mode,job in [('gto',gto),('exp_ip',locked)]:
        path=out/(TURN+'-'+mode)
        game=solve(path,job,a.driver)
        assert (path/'job.json').read_bytes()==compact(job)
        assert (game['flop'],game['pot'],game['stack'])==(FLOP,POT,STACK) and 0<=game['info']['gto_expl_pct']<=.5
        applied=None
        if mode=='gto':
            assert not game['info'].get('lock_stats')
            first_hands=game['hands']
        else:
            assert first_hands==game['hands'] and 0<=game['info']['hero_gap_pct']<=.5 and game['info']['lock_stats']
            applied=audit_patterns(game,job,dict(locks=meta),pool,hero_seat=1)
            assert any(count>0 for key,count in applied['driver_tree_nodes'].items() if key in applied['marginal_targets'])
        rows=assessment(root,game,boundary,allowed,co)
        report['policies'][mode]=dict(job_sha256=sha(compact(job)),source_sha256=sha((path/'result.json').read_bytes()),applied=applied,boards=rows)
    before,after=(report['policies'][m]['boards'] for m in ('gto','exp_ip'))
    for board in sorted(before):
        g,e=(p[board]['co_by_displayed_btn'] for p in (before,after))
        common={h:sorted(set(g[h])&set(e[h])) for h in sorted(g.keys()&e.keys())}
        common={h:v for h,v in common.items() if v}
        if common:
            assert compatible(contract,dict(public_board=board,actual_exact_action_line=LINE,acting_seat=1))
            report['common'][board]=common
    if report['common']:
        board=min(report['common'])
        hero=min(report['common'][board])
        report['selected']=dict(public_board=board,btn=hero,co_hands=report['common'][board][hero])
    medium=[v['reach']['b50'] for v in after.values() if v['reach']['strict_legal_combos']>0 and v['reach']['compatible_hole_card_pairs']>0]
    assert all(v is not None for v in medium)
    report.update(positive_distinct_flops=int(bool(report['common'])),locked_public_boards=len(after),
        joint_halfpot_assessed=len(medium),halfpot_candidates=sum(bool(v['candidate']) for v in medium))
    keep('proof.json',json_bytes(report))
    print(json.dumps({k:report[k] for k in ('selected','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--driver',type=Path)
    parser.add_argument('--preflight',action='store_true')
    run(parser.parse_args())
