"""Independently replay original B689 OOP workers; stage rank84 evidence without changing the registry."""
import argparse
import base64
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b695_rank84_collect import FLOPS, PRICE_PINS, SOURCE_BLOBS, check_source, check_worker

import hu_reverified_board_pair as pairs
from hu_b463_rank45_gate import SOLVER,RUST
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE,POOL,RANGES,proof
from hu_b514_turn_stab import rates
from hu_b536_sb_barrels import tx
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import accepted,cardkey,game_reach,mask_at_node
from verify_hu_multiboard_100bb import lock_scope

sys.path.insert(0,str(Path(__file__).resolve().parent/"lines_pipeline"))
from run10_common import hcls

MODEL="ln-3bp-3b_t_model-ciziut"
LINE="x b33 c/"
CASES={"JhTh8c":["2s","3d","4c","6s"],"Ts9s6h":["2c","3d","4h","7c"],"9h8c5h":["2s","3d","4c","7s"]}
CODE_PINS={"nl2_hu_model.js":"a98cb80d7762b464064874de39dcff6f4bf5707d",
           "nl2.js":"15aee97e53a156fe073c96a120638a8a3679958f"}
ACTIONS={"過":"x","下注 ⅓":"b33","下注 ½":"b50","下注 ¾":"b75"}


def independent_accepted(node,hands,action):
    seat=node['player'];count=len(hands[seat]);choice=node['acts'].index(action);result=set()
    for index,hand in enumerate(hands[seat]):
        if node['w'][seat][index]<=1e-4:continue
        probabilities=[max(0.,float(node['strat'][offset*count+index]))for offset in range(len(node['acts']))]
        total=sum(probabilities)
        if total<=0:continue
        probabilities=[value/total for value in probabilities];best=max(range(len(probabilities)),key=probabilities.__getitem__)
        if choice==best or(probabilities[choice]>=.4-1e-7 and probabilities[choice]>=.7*probabilities[best]-1e-7):
            result.add(cardkey(hand))
    assert result==accepted(node,hands,action),'Independent action-frequency gate disagrees'
    return result


def flop_layers(root):
    nodes={node['line']:node for node in root['nodes']if len(node['board'])==6}
    sets={name:independent_accepted(nodes[line],root['hands'],action)for name,line,action in (
        ('oop_check','','x'),('ip_b33','x','b33'),('oop_call','x b33','c'))}
    summary={name+'_accepted':len(hands)for name,hands in sets.items()}
    summary['oop_check_call_intersection']=len(sets['oop_check']&sets['oop_call'])
    summary['oop_check_call_MID']=sum(hcls(''.join(hand),root['flop'])=='MID'for hand in sets['oop_check']&sets['oop_call'])
    summary['oop_check_MID']=sum(hcls(''.join(hand),root['flop'])=='MID'for hand in sets['oop_check'])
    summary['oop_call_MID']=sum(hcls(''.join(hand),root['flop'])=='MID'for hand in sets['oop_call'])
    node=nodes[''];count=len(root['hands'][0]);choice=node['acts'].index('x')
    values=[]
    for index,weight in enumerate(node['w'][0]):
        if weight<=1e-4:continue
        frequencies=[max(0.,node['strat'][offset*count+index])for offset in range(len(node['acts']))]
        total=sum(frequencies)
        if total>0:values.append((frequencies[choice]/total,weight))
    summary.update(root_check_max_frequency=max(value for value,_ in values),
        root_check_weighted_frequency=sum(value*weight for value,weight in values)/sum(weight for _,weight in values),
        independent_raw_strategy_gate_matches=True)
    return sets,summary


def turn_layers(root,sub,row,route):
    sets,_=flop_layers(root)
    node,=[node for node in sub['nodes']if(node['line'],node['player'])==(LINE,0)]
    public=node['board'];public_cards={public[i:i+2]for i in range(0,8,2)}
    initial=mask_at_node(node,sub['hands']);hands=[cardkey(hand)for hand in sub['hands'][0]]
    active={hand for hand,bits in zip(hands,initial,strict=True)if bits and public_cards.isdisjoint(hand)}
    check_bit=1<<node['acts'].index('x')
    checks={hand for hand,bits in zip(hands,initial,strict=True)if bits&check_bit}
    parents=route['routes'].get(tx(public[:6]),{}).get('parents',[])
    decisions=route['routes'].get(tx(public),{}).get('decisions',{})
    ui={hand for hand in active if hcls(''.join(hand),public[:6])in parents and decisions.get(hcls(''.join(hand),public))=='過'}
    after_check=active&sets['oop_check'];after_call=after_check&sets['oop_call']
    villains={cardkey(hand)for hand,weight in zip(sub['hands'][1],node['w'][1],strict=True)
        if weight>1e-4 and public_cards.isdisjoint(cardkey(hand))}&sets['ip_b33']
    deals={hand:sum(set(hand).isdisjoint(other)for other in villains)for hand in after_call}
    joint={hand for hand,count in deals.items()if count}
    actual=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    assert joint=={hand for hand,bits in zip(hands,actual,strict=True)if bits}
    assert sum(deals.values())==row['compatible_hole_card_pairs']
    return dict(turn_initial_accepted_hands=len(active),turn_initial_check_mask=len(checks),
        after_oop_flop_check=len(after_check),after_oop_flop_check_call=len(after_call),
        opponent_flop_b33_accepted=len(villains),compatible_hole_card_pairs=sum(deals.values()),strict_legal_combos=len(joint),
        ui_MID_before_ancestry=len(ui),ui_MID_check_before_ancestry=len(ui&checks),
        ui_MID_after_ancestry=len(ui&joint),final_rendered_check=len(ui&joint&checks))


def expected_root(flop,pipeline):
    job=pipeline.make_job("SB3_BTN","gto",flop,"result.json",iters=2200,target=.4,compress=True)
    job.update(flop_oop="33%",flop_ip="33%",extract=[dict(prefix=[],street=True)]+[
        dict(prefix=["x","b33","c",t],street=False,raw=True) for t in CASES[flop]])
    return job


def expected_turn(root,turn,pipeline):
    parent,=(n for n in root["nodes"] if n["line"]=="x b33 c/" and n["board"].endswith(turn))
    assert (parent["player"],parent["pot"],parent["bets"])==(0,3486,[693,693])
    job=pipeline.make_job("SB3_BTN","gto",root["flop"],"result.json",iters=2300,target=.4,rank=.4,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",pot=3486,stack=8307,turn=turn,line0=["x","b33","c","/"],root_no_bet=False,
        turn_oop="33%,50%,75%,100%",turn_ip="33%,50%,75%,100%",
        river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",extract=[dict(prefix=[],street=True)])
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return job


def observation(source,route):
    root,sub=source["root"],source["subgame"]
    node,=(n for n in sub["nodes"] if (n["line"],n["player"])==(LINE,0))
    assert (node["pot"],node["bets"])==(3486,[0,0])
    assert abs(8307/3486/route["spr"]-1)<.001
    row=proof(root,sub,node,game_reach(root,sub)[0])
    info=sub["info"]
    row.update(version=source["version"],spot="SB3_BTN",family="3BP",flop=sub["flop"],turn=sub["turn"],
        source_run_id=source["run"],source_sha256=source["source_sha256"],archive_sha256=source["archive_sha256"],
        root_sha256=source["root_sha256"],root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],root_locked_hero_gap_pct=None,
        gto_gap_pct=info["gto_expl_pct"],locked_hero_gap_pct=info.get("hero_gap_pct"),
        lock_scope=lock_scope(sub,source["manifest"]["locks"],source["version"]),root_applied_rust_lock_nodes=0,
        subgame_applied_rust_lock_nodes=sum(v["nodes"] for v in info.get("lock_stats",{}).values()))
    public=node["board"]
    assert len(public)==8 and public[-2:]==sub["turn"]
    assert {public[i:i+2] for i in (0,2,4)}=={root["flop"][i:i+2] for i in (0,2,4)}
    parents=route["routes"].get(tx(public[:6]),{}).get("parents",[])
    decisions=route["routes"].get(tx(public),{}).get("decisions",{})
    masks=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    hands={}
    for i,(hand,bits) in enumerate(zip(sub["hands"][0],masks,strict=True)):
        if not bits:continue
        fc,tc=hcls(hand,public[:6]),hcls(hand,public)
        label=decisions.get(tc);action=ACTIONS.get(label)
        if fc not in parents or action not in node["acts"] or not bits&(1<<node["acts"].index(action)):continue
        frequencies=[max(0,node["strat"][k*len(masks)+i]) for k in range(len(node["acts"]))]
        total=sum(frequencies);assert total>0
        hands["".join(cardkey(hand))]=dict(flop_class=fc,turn_class=tc,displayed_suggestion=label,
            action_order=node["acts"],accepted_mask=bits,
            accepted_actions=[a for k,a in enumerate(node["acts"]) if bits&(1<<k)],
            strategy={a:round(v/total,7) for a,v in zip(node["acts"],frequencies,strict=True)})
    return row,hands


def expected_root_gate(root,turn,route):
    sets,summary=flop_layers(root)
    parent,=[node for node in root['nodes']if node['line']==LINE and node['board'].endswith(turn)]
    assert (parent['player'],parent['pot'],parent['bets'])==(0,3486,[693,693])
    public=parent['board'];dead={public[i:i+2]for i in range(0,8,2)}
    weighted=[{cardkey(hand)for hand,weight in zip(root['hands'][seat],parent['wr'][seat],strict=True)if weight>1e-4}
        for seat in (0,1)]
    actors={hand for hand in sets['oop_check']&sets['oop_call']&weighted[0]if dead.isdisjoint(hand)}
    villains={hand for hand in sets['ip_b33']&weighted[1]if dead.isdisjoint(hand)}
    deals={hand:sum(set(hand).isdisjoint(villain)for villain in villains)for hand in actors}
    joint={hand for hand,count in deals.items()if count}
    parents=route['routes'].get(tx(public[:6]),{}).get('parents',[])
    decisions=route['routes'].get(tx(public),{}).get('decisions',{})
    shown={hand for hand in joint if hcls(''.join(hand),public[:6])in parents and hcls(''.join(hand),public)in decisions}
    return dict(oop_check_combos=summary['oop_check_accepted'],oop_call_combos=summary['oop_call_accepted'],
        ip_b33_combos=summary['ip_b33_accepted'],oop_check_MID=summary['oop_check_MID'],oop_call_MID=summary['oop_call_MID'],
        oop_check_call_MID=summary['oop_check_call_MID'],oop_check_call_intersection=summary['oop_check_call_intersection'],
        turn_compatible_hero_combos=len(joint),turn_compatible_pairs=sum(deals.values()),
        rendered_mid_hero_combos=len(shown),rendered_mid_hands=sorted(''.join(hand)for hand in shown))


def decision_diagnostic(source,row,route):
    sub=source['subgame'];node,=[node for node in sub['nodes']if(node['line'],node['player'])==(LINE,0)]
    public=node['board'];parents=route['routes'].get(tx(public[:6]),{}).get('parents',[])
    decisions=route['routes'].get(tx(public),{}).get('decisions',{})
    result=dict(strict_hero_combos=row['strict_legal_combos'],compatible_pairs=row['compatible_hole_card_pairs'],
        flop_ui_combos=0,turn_ui_combos=0,displayed_action_combos=0,flop_classes={},turn_classes={})
    masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    for hand,bits in zip(sub['hands'][0],masks,strict=True):
        if not bits:continue
        fc,tc=hcls(hand,public[:6]),hcls(hand,public)
        for field,value in (('flop_classes',fc),('turn_classes',tc)):
            result[field][value]=result[field].get(value,0)+1
        if fc not in parents:continue
        result['flop_ui_combos']+=1
        label=decisions.get(tc)
        if label is None:continue
        result['turn_ui_combos']+=1
        action=ACTIONS[label]
        if action in node['acts']and bits&(1<<node['acts'].index(action)):
            result['displayed_action_combos']+=1
    return result


def verify_worker(pin,outer,pipeline,ranges,pool,route):
    with ZipFile(io.BytesIO(outer))as archive:
        assert len(archive.namelist())==len(set(archive.namelist()))
        claim=json.loads(archive.read('proof.json'));flop=pin['flop']
        assert (claim['schema'],claim['rank'],claim['model_id'],claim['flop'],claim['line'],claim['actor'])==(
            'NL2_B689_R84_ORIGINAL_WORKER_V1',84,MODEL,flop,LINE,0)
        assert (claim['solver'],claim['rust'],claim['pipeline_sha256'],claim['ranges_sha256'],claim['pool_sha256'])==(
            SOLVER,RUST,PIPELINE,RANGES,POOL)
        assert (claim['root_pot'],claim['root_stack'],claim['pot'],claim['stack'])==(2100,9000,3486,8307)
        assert claim['not_a_certification']and claim['no_observed_per_hole_card_NL2_frequencies']
        assert claim['restricted_flop_oop_sizes_pct']==claim['restricted_flop_ip_sizes_pct']==[33]
        assert claim['pricing_scope']=='PINNED_B674_EXPLICIT_33_PERCENT_CHECK_CALL_MODEL'
        assert claim['lock_scope']=='FROZEN_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_MARGINALS'
        assert claim['mechanism']=='THREE_NEW_CONNECTED_TWO_SUIT_FLOPS_ROOT_CHECK_CALL_MID_BEFORE_TURN_SOLVE'
        assert claim['root_gate_threshold']=='MAX_FREQUENCY_OR_GE40PCT_AND_GE70PCT_OF_MAX_UNCHANGED'
        routes_raw=archive.read('rendered-routes.json')
        assert sha(routes_raw)==claim['rendered_routes_sha256']and json.loads(routes_raw)==route
        raw=archive.read('flop/result.json');root=json.loads(raw);job=expected_root(flop,pipeline)
        assert json.loads(archive.read('flop/job.json'))==job
        assert claim['root_sha256']==sha(raw)and claim['root_job_sha256']==sha(compact(job))
        assert (root['flop'],root['pot'],root['stack'])==(flop,2100,9000)
        assert (job['rake_rate'],job['rake_cap'])==(.05,1000)
        assert (job['oop'],job['ip'])==tuple(ranges.to_str(value)for value in ranges.ranges('SB3_BTN','gto'))
        assert not job.get('locks')and job.get('hero')is None
        assert not root['info'].get('lock_stats')and root['info'].get('hero_gap_pct')is None
        assert 0<=root['info']['gto_expl_pct']<=.5
        for line,seat,pot,bets,action in [('',0,2100,[0,0],'x'),('x',1,2100,[0,0],'b33'),('x b33',0,2793,[0,693],'c')]:
            node,=[node for node in root['nodes']if node['line']==line]
            assert (node['player'],node['pot'],node['bets'])==(seat,pot,bets)and action in node['acts']
        root_sha=sha(compact(root));archive_code='B695_R84_'+flop.upper()
        base=dict(root=root,run=pin['run'],root_sha256=root_sha,archive_code=archive_code,archive_sha256=sha(outer),
            manifest=dict(spot='SB3_BTN',pot_family='3BP',locks=[],
                preflop_ranges=dict(source='PINNED_POKER_SOLVER_PREFLOP_CFR',spot='SB3_BTN')))
        tested=claim['turns']
        assert tested and [attempt['turn']for attempt in tested]==CASES[flop][:len(tested)]
        expected={'proof.json','rendered-routes.json','flop/job.json','flop/result.json'}
        for attempt in tested:
            if attempt['gto_solved']:expected.update(attempt['turn']+'-gto/'+name for name in ('job.json','result.json'))
            if attempt['paired']:expected.update(attempt['turn']+'-exp_oop/'+name for name in ('job.json','result.json'))
        assert set(archive.namelist())==expected,'Unexpected or missing original native files'
        result=None;summary=[]
        for index,test in enumerate(tested):
            turn=test['turn'];gate=expected_root_gate(root,turn,route)
            assert gate==test['root_gate']
            attempt=dict(turn=turn,root_gate=gate,gto_solved=False,locked=False,shared=0,gto_b50=None,nl2_b50=None)
            summary.append(attempt)
            if not gate['rendered_mid_hero_combos']:
                assert not test['gto_solved']and not test['paired']and not test['shared_hands']
                assert test['negative_stage']=='ROOT_TWO_SEAT_UI_INTERSECTION_ZERO'
                attempt['reason']=test['negative_stage']
                continue
            assert test['gto_solved']
            gjob=expected_turn(root,turn,pipeline)
            grow=archive.read(turn+'-gto/result.json');gsub=json.loads(grow)
            assert json.loads(archive.read(turn+'-gto/job.json'))==gjob and sha(grow)==test['gto_sha256']
            assert (gsub['flop'],gsub['pot'],gsub['stack'])==(flop,3486,8307)
            assert not gsub['info'].get('lock_stats')and 0<=gsub['info']['gto_expl_pct']<=.5
            gsub.update(line0='x b33 c',turn=turn,rivers=[])
            g=dict(base,version='gto',subgame=gsub,source_sha256=sha(grow))
            gr,gh=observation(g,route);gd=decision_diagnostic(g,gr,route)
            assert (test['public_board'],test['gto_rendered_hands'],test['gto_reach'],test['gto_compatible_pairs'],test['gto_b50'])==(
                gr['public_board'],len(gh),gr['strict_legal_combos'],gr['compatible_hole_card_pairs'],gr['b50'])
            assert test['gto_diagnostic']==gd and gd['displayed_action_combos']==len(gh)
            attempt.update(gto_solved=True,public_board=gr['public_board'],gto_rendered=len(gh),gto_source_sha256=sha(grow),
                gto_gap_pct=gsub['info']['gto_expl_pct'],gto_strict_combos=gr['strict_legal_combos'],
                gto_compatible_pairs=gr['compatible_hole_card_pairs'],gto_b50=gr['b50'],gto_diagnostic=gd,
                layers=turn_layers(root,gsub,gr,route))
            if not gh:
                assert not test['paired']and not test['shared_hands']
                assert test['negative_stage']=='GTO_TURN_RENDERED_ACTION_INTERSECTION_ZERO'
                attempt['reason']=test['negative_stage']
                continue
            assert test['paired']
            ejob,rules=prepare_job(dict(source=g,job=gjob),'exp_oop',pool,pipeline);ejob['out']='result.json'
            eraw=archive.read(turn+'-exp_oop/result.json');esub=json.loads(eraw)
            assert json.loads(archive.read(turn+'-exp_oop/job.json'))==ejob and sha(eraw)==test['nl2_sha256']
            assert (esub['flop'],esub['pot'],esub['stack'])==(flop,3486,8307)
            assert esub['hands']==gsub['hands']
            assert ejob['hero']==0 and ejob['locks']and esub['info']['lock_stats']
            assert 0<=esub['info']['gto_expl_pct']<=.5 and 0<=esub['info']['hero_gap_pct']<=.5
            esub.update(line0='x b33 c',turn=turn,rivers=[])
            manifest=dict(base['manifest'],locks=rules,gto_parent_source_run_id=pin['run'],gto_parent_source_sha256=root_sha)
            applied=audit_patterns(esub,ejob,manifest,pool,0)
            e=dict(base,manifest=manifest,version='exp_oop',subgame=esub,source_sha256=sha(eraw),
                verified_gto_parent=dict(run=pin['run'],sha256=root_sha),measured_lock_application=applied,
                applied_rust_rates=esub['info']['lock_stats'])
            er,eh=observation(e,route);ed=decision_diagnostic(e,er,route);common=sorted(gh.keys()&eh.keys())
            assert test['shared_hands']==common and test['measured_lock_application']==applied
            assert (test['nl2_rendered_hands'],test['nl2_reach'],test['nl2_compatible_pairs'],test['nl2_b50'])==(
                len(eh),er['strict_legal_combos'],er['compatible_hole_card_pairs'],er['b50'])
            assert test['nl2_diagnostic']==ed and ed['displayed_action_combos']==len(eh)
            for name,hands in (('gto_witnesses',gh),('nl2_witnesses',eh)):
                assert test[name]=={hand:hands[hand]for hand in common}
            assert test['negative_stage']==(None if common else 'GTO_NL2_RENDERED_HAND_INTERSECTION_ZERO')
            attempt.update(locked=True,shared=len(common),shared_hands=common,nl2_rendered=len(eh),
                nl2_source_sha256=sha(eraw),hero_gap_pct=esub['info']['hero_gap_pct'],nl2_strict_combos=er['strict_legal_combos'],
                nl2_compatible_pairs=er['compatible_hole_card_pairs'],nl2_b50=er['b50'],nl2_diagnostic=ed,
                lock_scope=er['lock_scope'],measured_lock_application=applied,nl2_layers=turn_layers(root,esub,er,route),
                reason='SHARED_RENDERED_CHECK'if common else test['negative_stage'])
            if common:
                assert index==len(tested)-1
                result=(g,e,gr,er,gh,eh,common)
        assert claim['positive_distinct_flops']==int(result is not None)
        assert result is not None or len(tested)==len(CASES[flop])
        return result,summary,flop_layers(root)[1]


def record_hash(record):
    return sha(json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())


def publish(args):
    assert args.run>0 and len(args.head)==40
    for name,pin in {**SOURCE_BLOBS,**CODE_PINS}.items():
        assert subprocess.check_output(['git','hash-object',name],text=True).strip()==pin,(name,'unrecognized replay source or inactive price pair')
    assert CODE_PINS=={name:values[1]for name,values in PRICE_PINS.items()}
    registry_path=Path('data/nl2_hu_multiboard_status_current.json')
    registry_raw=registry_path.read_bytes();registry=json.loads(registry_raw)
    protected={mid:record_hash(model)for mid,model in registry['records'].items()if model['label']=='CERT-MULTIBOARD'}
    assert len(protected)>=147 and MODEL not in protected
    model=deepcopy(registry['records'][MODEL])
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['street'],model['label'])==(
        84,'SB3_BTN','3BP',1,'APPROX')
    assert not model['certified_3_to_5_exact_flop_boards']
    route=json.loads(subprocess.check_output(['node','tools/hu_b689_rank84_routes.cjs']))
    assert (route['id'],route['source'],route['spot'],route['seat'],route['line'])==(
        MODEL,'ln-3bp-3b_f_vs_donk-12vwqfc','SB3_BTN',0,LINE)
    assert (route['root_pot'],route['root_stack'],route['flop_bet'],route['turn_pot'],route['turn_stack'],route['spr'])==(2100,9000,693,3486,8307,2.383)
    old_spr=model['assumed_model_node_spr']
    model['assumed_model_node_spr']=route['spr']
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    py=solver/'postflop/py'
    assert sha((py/'pipeline.py').read_bytes())==PIPELINE and sha((py/'ranges.py').read_bytes())==RANGES
    sys.path.insert(0,str(py));import pipeline,ranges
    assert ranges.SPOTS['SB3_BTN']==dict(oop='SB',ip='BTN',oopc=[('BTNopen>SB','3bet')],
        ipc=[('BTNrfi','open'),('BTNopen>SB3b','call')],pot=21.0,stack=90.0,pfr='oop',kind='3BP')
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    source_run=json.loads((args.receipts/'source-run.json').read_bytes())
    source_files=json.loads((args.receipts/'source-files.json').read_bytes())
    check_source(source_run,source_files,args.run,args.head)
    inputs=json.loads((args.receipts/'workers.json').read_bytes())
    assert len(inputs)==3 and {pin['flop']for pin in inputs}==set(CASES)==set(FLOPS)
    assert len({pin['id']for pin in inputs})==len({pin['job_id']for pin in inputs})==3
    assert len({suit_isomorphism_class(pin['flop'])for pin in inputs})==3
    data=(args.output/'data').resolve();central=Path('data').resolve()
    assert data!=central and central not in data.parents and not data.exists(),'Use a fresh isolated output directory'
    evidence=data/'solver_evidence';receipts=evidence/'b695_receipts'
    receipts.mkdir(parents=True);pairs.EVIDENCE=evidence
    for name in ('source-run.json','source-files.json','workers.json'):
        (receipts/name).write_bytes((args.receipts/name).read_bytes())
    group=dict(rank=84,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B695_ORIGINAL_LOCKED_MEDIUM_V1',gto_references={},references={})
    reports=[]
    for pin in sorted(inputs,key=lambda value:FLOPS.index(value['flop'])):
        assert (pin['run'],pin['head'],pin['run_attempt'])==(args.run,args.head,source_run['run_attempt'])
        receipt_path=args.receipts/f'{pin["id"]}.json';job_path=args.receipts/f'job-{pin["job_id"]}.json'
        receipt=json.loads(receipt_path.read_bytes());job=json.loads(job_path.read_bytes())
        assert (receipt['id'],job['id'],receipt['name'],job['name'])==(pin['id'],pin['job_id'],pin['name'],pin['job_name'])
        check_worker(job,receipt,pin['flop'],args.run,args.head,source_run['run_attempt'])
        outer=(args.receipts/f'{pin["id"]}.zip').read_bytes()
        assert receipt['digest']=='sha256:'+pin['sha256'] and sha(outer)==pin['sha256']
        verified,attempts,root_ancestry=verify_worker(pin,outer,pipeline,ranges,pool,route)
        archive_code='B695_R84_'+pin['flop'].upper()
        (evidence/('NL2_'+archive_code+'.zip')).write_bytes(outer)
        for path in (receipt_path,job_path):(receipts/path.name).write_bytes(path.read_bytes())
        report=dict(flop=pin['flop'],worker_artifact=pin['id'],worker_sha256=pin['sha256'],original_job_id=pin['job_id'],
            run=args.run,head=args.head,positive=verified is not None,attempts=attempts,root_ancestry=root_ancestry,
            original_worker_archive_code=archive_code)
        reports.append(report)
        if verified is None:continue
        g,e,gr,er,gh,eh,common=verified;public=gr['public_board']
        assert er['public_board']==public and len(public)==8 and common
        assert er['lock_scope']['observed_marginal_source_nodes']>0
        assert min(gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs'])>0
        board,pin2=pairs.emit_board(model,g,e,public,LINE,texture(pin['flop']),viewer_code=archive_code)
        assert board is not None
        assert (board['actual_exact_action_line'],board['exact_flop_action'],board['acting_seat'])==(LINE,'x b33 c',0)
        assert (board['actual_pot_bb'],board['actual_effective_stack_bb'])==(34.86,83.07)
        assert pin2['GTO_compatible_hole_card_pairs']>=pin2['GTO_strict_combos']>0
        assert pin2['NL2_compatible_hole_card_pairs']>=pin2['NL2_strict_combos']>0
        comparisons=[]
        for hand in common:
            assert all(gh[hand][key]==eh[hand][key]for key in ('flop_class','turn_class','displayed_suggestion'))
            assert gh[hand]['displayed_suggestion']=='過'
            comparisons.append(dict(hand=hand,flop_class=gh[hand]['flop_class'],turn_class=gh[hand]['turn_class'],
                displayed_suggestion=gh[hand]['displayed_suggestion'],gto=gh[hand],nl2=eh[hand]))
        board.update(source_run_role='ORIGINAL_GITHUB_ACTIONS_NATIVE_SOLVE',origin_solve_run_id=args.run,
            restricted_flop_oop_sizes_pct=[33],restricted_flop_ip_sizes_pct=[33])
        pin2.update(worker_artifact=pin['id'],worker_sha256=pin['sha256'],worker_head=args.head,original_job_id=pin['job_id'],
            source_run_role=board['source_run_role'],rendered_decision_hands=comparisons,
            initial_check_call_route=dict(initial='ln-3bp-3b_f_cbet-1ueswd8',facing=route['source'],target=MODEL),
            price_source_blobs=CODE_PINS)
        board['nl2_locked_variants'][0].update(pool_sha256=POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
            applied_street_rates=rates(e),origin_solve_run_id=args.run,source_run_role=board['source_run_role'],
            gto_parent_source_run_id=args.run,gto_parent_source_sha256=g['root_sha256'],
            viewer_archive_code=pin2['viewer_archive_code'],viewer_sha256=pin2['viewer_sha256'])
        group['boards'].append(board);group['pins'].append(pin2)
        for key,row in (('gto_references',gr),('references',er)):medium[key][source_key(MODEL,row)]=row
        report.update(public_board=public,shared_hands=len(common),half_pot_candidate=bool(er['b50']and er['b50']['candidate']))
    eligible=len(group['boards'])>=3
    assert len(group['boards'])==len({board['flop']for board in group['boards']})<=3
    destination=evidence/('reverified'if eligible else'partial');destination.mkdir(exist_ok=True)
    (destination/('rank84.json'if eligible else'B695_rank84.json')).write_bytes(json_bytes(group))
    medium_path=data/'nl2_hu_b695_locked_medium.json'if eligible else destination/'B695_locked_medium.json'
    medium_path.write_bytes(json_bytes(medium))
    attempts=[attempt for report in reports for attempt in report['attempts']]
    result=dict(schema='NL2_HU_B695_ORIGINAL_RANK84_OUTCOMES_V1',source_run=args.run,source_head=args.head,
        boards=len(group['boards']),cert_eligible=eligible,retained_original_archives=len(reports),
        source_flops=len(reports),negative_flops=sum(not report['positive']for report in reports),
        root_turns_assessed=len(attempts),root_gate_skipped=sum(not attempt['gto_solved']for attempt in attempts),
        gto_turns_assessed=sum(attempt['gto_solved']for attempt in attempts),actor_locked_boards=sum(attempt['locked']for attempt in attempts),
        gto_half_pot_assessed=sum(attempt['gto_b50']is not None for attempt in attempts),
        half_pot_assessed=sum(attempt.get('nl2_b50')is not None for attempt in attempts),
        half_pot_candidates=sum(bool(attempt.get('nl2_b50')and attempt['nl2_b50']['candidate'])for attempt in attempts),
        cert_qualifying_locked_boards=len(group['boards']),
        registry_model_spr_before=old_spr,verified_priced_ui_spr=route['spr'],
        registry_generation_requires_active_price_pair=CODE_PINS,protected_cert_records=len(protected),workers=reports)
    guard=dict(schema='NL2_HU_B695_PROTECTED_CERT_RECORDS_V1',registry_sha256=sha(registry_raw),
        target_model_id=MODEL,protected_cert_record_sha256=protected)
    (data/'nl2_hu_b695_rank84_results.json').write_bytes(json_bytes(result))
    (data/'nl2_hu_b695_rank84_workers.json').write_bytes(json_bytes(inputs))
    (data/'nl2_hu_b695_registry_guard.json').write_bytes(json_bytes(guard))
    assert registry_path.read_bytes()==registry_raw,'Publication staging must not change the live registry'
    print(json.dumps({key:value for key,value in result.items()if key not in ('workers','registry_generation_requires_active_price_pair')}))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ('solver','receipts','output'):cli.add_argument('--'+field,type=Path,required=True)
    cli.add_argument('--run',type=int,required=True);cli.add_argument('--head',required=True)
    publish(cli.parse_args())
