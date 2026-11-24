"""Replay B755's original extractions and require an identical physical CO/BB deal in both policies."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b755_rank151 as native
import hu_b757_collect as receipt
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_board_reach_corrections import source_key, summarize
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import accepted, cardkey


def read(path):
    return json.loads(path.read_bytes())


def full_deals(root, sub, route, reported):
    f={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    t={n['line']:n for n in sub['nodes'] if len(n['board'])==8}
    assert f['']['player']==f['x b50']['player']==t['x b50 c/']['player']==0
    assert f['x']['player']==t['x b50 c/x']['player']==1
    bb=accepted(f[''],root['hands'],'x') & accepted(f['x b50'],root['hands'],'c') & accepted(t['x b50 c/'],sub['hands'],'x')
    co=accepted(f['x'],root['hands'],'b50') & accepted(t['x b50 c/x'],sub['hands'],'x')
    river_bb={n['board']:n for n in sub['nodes'] if n['line']=='x b50 c/x x/' and n['player']==0}
    result={}
    for n in sub['nodes']:
        if n['line']!=native.LINE:
            continue
        public=n['board'];dead=native.cards(public)
        assert (len(dead),n['player'],n['pot'],n['bets'])==(5,1,500,[0,0])
        live=[{cardkey(h) for h,w in zip(sub['hands'][i],n['w'][i],strict=True) if w>1e-4 and dead.isdisjoint(cardkey(h))} for i in (0,1)]
        vset=bb & accepted(river_bb[public],sub['hands'],'x') & live[0]
        hset=co & accepted(n,sub['hands'],'x') & live[1]
        reach=reported[public]['reach']
        masks=base64.b64decode(reach['compatible_action_mask_b64'],validate=True)
        hotels={cardkey(h):(i,b) for i,(h,b) in enumerate(zip(sub['hands'][1],masks,strict=True))}
        valid={}
        for h in sorted(hset):
            hand=''.join(h)
            cells=[native.hand_cell(hand,public[:i]) for i in (6,8,10)]
            if not(cells[0][0] in route['flop'] and cells[1][0] in route['turn'] and route['river'].get(cells[2][0])=='過'):
                continue
            if not any(set(h).isdisjoint(v) for v in vset):
                continue
            i,bits=hotels[h]
            assert bits & (1<<n['acts'].index('x'))
            w=[max(0.0,n['strat'][j*len(masks)+i]) for j in range(len(n['acts']))]
            total=sum(w);assert total>0
            valid[hand]=dict(classes=[c[1] for c in cells],displayed_suggestion='過',
                             policy=dict(action_order=n['acts'],accepted_mask=bits,accepted_actions=[a for j,a in enumerate(n['acts']) if bits & (1<<j)],
                                         strategy={a:round(x/total,7) for a,x in zip(n['acts'],w,strict=True)}))
        assert sorted(valid)==reported[public]['displayed_hands'],public
        result[public]=(valid,vset)
    assert result.keys()==reported.keys()
    return result


def stage_board(flop,public,common,selected,origin,contract,model,group,medium):
    sources,rows=[],[]
    for mode in ('gto','exp_ip'):
        s,counts=selected[mode]
        obs=audit_decision(s,public,native.LINE,1,s['root_sha256'])
        assert obs and {k:obs[k] for k in counts[public]['reach']}==counts[public]['reach']
        summarize(obs)
        rows.append(obs);sources.append(s)
    board,pin=pairs.emit_board(model,*sources,public,native.LINE,texture(flop),viewer_code='B757_R151_'+flop.upper())
    assert board and native.compatible(contract,board)
    assert (board['actual_spr'],board['acting_seat'],board['actual_pot_bb'],board['actual_effective_stack_bb'])==(19.55,1,5,97.75)
    for item in (board,pin):
        item.update(native_flop_bet_menu='50% only for both players',original_root_archive=origin['archive'],
                    original_root_archive_sha256=origin['archive_sha256'],original_root_sha256=origin['root_sha256'],
                    origin_solve_run_id=receipt.RUN,source_run_role='REPLAYED_FROZEN_RESTRICTED_ROOT_NEW_CHANCE_BOUNDARIES_THEN_NATIVE_TURN')
    locked=sources[1]
    board['nl2_locked_variants'][0].update(origin_solve_run_id=receipt.RUN,pool_sha256=native.POOL,
        measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(locked),
        gto_parent_source_run_id=receipt.RUN,gto_parent_source_sha256=locked['root_sha256'],
        viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
    assert pin['pool_observed_marginal_lock_nodes']>0
    pin.update(rendered_decision_hands=common,worker_artifact=receipt.PINS[flop][0],worker_sha256=receipt.PINS[flop][1],
               worker_head=receipt.HEAD,original_job_id=receipt.JOBS[flop],original_flop_comparison='ALL_ORIGINAL_NODES_EXACT')
    for label,row in zip(('gto_references','references'),rows,strict=True):
        row['rendered_decision_hands']=common
        medium[label][source_key(native.MODEL,row)]=row
    group['boards'].append(board);group['pins'].append(pin)


def worker(flop,folder,archive,rawroute,route_path,solver,pool,pipeline,model,contract,group,medium):
    ident,digest=receipt.PINS[flop]
    assert sha(archive)==digest
    names=unpack_original(archive,folder)
    original_proof=(folder/'proof.json').read_bytes()
    claim=json.loads(original_proof)
    assert (claim['rank'],claim['flop'],claim['actor'],claim['line'])==(151,flop,1,native.LINE)
    assert (folder/'rendered-routes.json').read_bytes()==rawroute
    expected={'flop/job.json','flop/result.json','rendered-routes.json','proof.json'}
    expected|={t['turn']+'-'+m+'/'+n for t in claim['turns'] for m in t['policies'] for n in ('job.json','result.json')}
    assert names==expected
    native.run(SimpleNamespace(flop=flop,solver=solver,routes=route_path,output=folder,driver=None,preflight=False))
    assert (folder/'proof.json').read_bytes()==original_proof
    frozen,_,manifest,pin,j=native.source(flop)
    root=read(folder/'flop/result.json');root_sha=sha(compact(root))
    assert claim['source']==pin and claim['original_fully_compared_nodes']==len(frozen['nodes'])
    assert root_sha==claim['canonical_frozen_flop_sha256']
    boundaries=native.compare_extraction(frozen,root,native.CASES[flop])
    assert read(folder/'flop/job.json')==j
    code='B755_R151_'+flop.upper()
    route=json.loads(rawroute);turns=[]
    counters=dict(locked_public_boards=0,joint_locked_boards=0,halfpot_assessed=0,halfpot_candidates=0)
    did_emit=False
    for t in claim['turns']:
        turn=t['turn']
        assert t['boundary_sha256']==sha(compact(boundaries[turn]))
        policies={};verified={}
        for mode,policy in t['policies'].items():
            folder2=folder/(turn+'-'+mode)
            game=read(folder2/'result.json')
            assert (sha((folder2/'result.json').read_bytes()),sha((folder2/'job.json').read_bytes()))==(policy['source_sha256'],policy['job_sha256'])
            game.update(line0='x b50 c',turn=turn,rivers=t['gate']['selected_rivers'])
            source=dict(root=root,root_sha256=root_sha,source_sha256=policy['source_sha256'],run=receipt.RUN,version=mode,
                        subgame=game,manifest=dict(manifest,locks=[]),archive_code=code,archive_sha256=digest)
            if mode=='exp_ip':
                gj=read(folder/(turn+'-gto/job.json'))
                ej,rules=native.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=gj),'exp_ip',pool,pipeline)
                ej['out']='result.json'
                assert ej==read(folder2/'job.json') and ej['hero']==1
                applied=native.audit_patterns(game,ej,dict(locks=rules),pool,hero_seat=1)
                assert applied==policy['measured_lock_application']
                source['manifest'].update(locks=rules,gto_parent_source_run_id=receipt.RUN,gto_parent_source_sha256=root_sha)
                source.update(verified_gto_parent=dict(run=receipt.RUN,sha256=root_sha),applied_rust_rates=game['info']['lock_stats'],measured_lock_application=applied)
                for entry in policy['boards'].values():
                    row=entry['reach'];counters['locked_public_boards']+=1
                    if row['strict_legal_combos'] and row['compatible_hole_card_pairs']:
                        counters['joint_locked_boards']+=1
                        if 'b50' in row['source_actions'] and row['b50'] is not None:
                            counters['halfpot_assessed']+=1
                            counters['halfpot_candidates']+=int(row['b50']['candidate'])
            verified[mode]=full_deals(root,game,route,policy['boards'])
            policies[mode]=(source,policy['boards'])
        witnesses={}
        if 'exp_ip' in verified:
            for public in sorted(verified['gto']):
                g,gv=verified['gto'][public];e,ev=verified['exp_ip'][public]
                choices=comparisons(g,e)
                assert [w['hand'] for w in choices]==t['common'].get(public,[])
                shared_bb=sorted(gv&ev)
                for w in choices:
                    h=native.cards(w['hand'])
                    actual=next((v for v in shared_bb if h.isdisjoint(v)),None)
                    if actual is not None:
                        witnesses.setdefault(public,[]).append(dict(w,compatible_bb_hand=''.join(actual)))
            if witnesses and not did_emit:
                public=sorted(witnesses)[0]
                stage_board(flop,public,witnesses[public],policies,pin,contract,model,group,medium)
                did_emit=True
        turns.append(dict(turn=turn,original_common_co_by_river=t['common'],same_co_and_bb_by_river=witnesses,
                          source_policies=list(t['policies']),gate=t['gate']))
    return dict(flop=flop,source_run=receipt.RUN,source_head=receipt.HEAD,worker_artifact=ident,archive_sha256=digest,
                worker_job=receipt.JOBS[flop],original=pin,original_nodes_fully_equal=len(frozen['nodes']),
                turns=turns,positive_distinct_flops=int(did_emit),**counters)


def publish(args):
    assert sys.version_info[:2]==(3,11)
    for p,blob in receipt.FILES.items():
        assert subprocess.check_output(['git','hash-object',p],text=True).strip()==blob
    solver=args.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    live=Path('data/nl2_hu_multiboard_status_current.json').read_bytes()
    model=json.loads(live)['records'][native.MODEL]
    assert (model['label'],model['frequency_rank'],model['assumed_model_node_spr'])==('APPROX',151,19.55)
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][native.MODEL]
    stage=args.output.resolve();assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    rawroute=subprocess.check_output(['node',native.ROUTE])
    route_file=partial/'b757_rank151_routes.json';route_file.write_bytes(rawroute)
    auth=receipt.validate(read(args.receipts));(stage/'nl2_hu_b757_source_receipts.json').write_bytes(json_bytes(auth))
    group=dict(rank=151,model_id=native.MODEL,boards=[],pins=[]);pairs.EVIDENCE=ev
    medium=dict(schema='NL2_HU_B757_ORIGINAL_LOCKED_MEDIUM_V1',gto_references={},references={})
    results=[]
    with TemporaryDirectory(prefix='b757-replay-') as temp:
        for flop,(aid,_) in receipt.PINS.items():
            name='NL2_B755_R151_'+flop.upper()+'.zip'
            path=args.archives/(str(aid)+'.zip')
            raw=(path if path.exists() else args.archives/name).read_bytes()
            result=worker(flop,Path(temp)/flop,raw,rawroute,route_file,solver,pool,pipeline,model,contract,group,medium)
            (ev/name).write_bytes(raw)
            (partial/('b757_rank151_'+flop.lower()+'.json')).write_bytes(json_bytes(result))
            results.append({k:v for k,v in result.items() if k!='turns'})
    certified=len(group['boards'])==3
    if certified:
        assert len({native.suit_isomorphism_class(b['flop']) for b in group['boards']})==3
        target=ev/'reverified'/'rank151.json'
    else:
        target=partial/'b757_rank151.json'
    target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(json_bytes(group))
    (stage/'nl2_hu_b757_locked_medium.json').write_bytes(json_bytes(medium))
    totals={k:sum(r[k] for r in results) for k in ('locked_public_boards','joint_locked_boards','halfpot_assessed','halfpot_candidates')}
    summary=dict(rank=151,source_run=receipt.RUN,source_head=receipt.HEAD,workers=results,positive_distinct_flops=len(group['boards']),
                 cert_eligible_ranks=[151] if certified else [],publisher_native_solves_repeated=0,**totals)
    (stage/'nl2_hu_b757_summary.json').write_bytes(json_bytes(summary))
    assert Path('data/nl2_hu_multiboard_status_current.json').read_bytes()==live
    print(json.dumps(dict(positive_distinct_flops=len(group['boards']),**totals)))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--archives',type=Path,default=Path('data/solver_evidence'))
    cli.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b757_source_receipts.json'))
    cli.add_argument('--solver',type=Path,required=True);cli.add_argument('--output',type=Path,required=True)
    publish(cli.parse_args())
