"""Authenticate the two B762 river extractions, verify each physical deal, and archive at most one original flop."""
import argparse
import base64
from pathlib import Path
import json
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b762_rank199_rivers as source
import hu_b764_collect as receipt
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b514_turn_stab import rates
from hu_b568_caller_rivers import hand_cell
from hu_b710_publish import unpack_original
from hu_b719_publish import comparisons
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import accepted,cardkey,game_reach


def read(p):
    return json.loads(p.read_bytes())


def policy(root,game,turn,policy,route,raw_wr):
    n=source.native
    node={v['line']:v for v in root['nodes'] if len(v['board'])==6}
    tn={v['line']:v for v in game['nodes'] if len(v['board'])==8}
    line='x b50 c/'
    co=accepted(node['x'],root['hands'],'b50') & accepted(tn[line+'x'],game['hands'],'b33')
    bb=accepted(node[''],root['hands'],'x') & accepted(node['x b50'],root['hands'],'c')
    bb&=accepted(tn[line],game['hands'],'x') & accepted(tn[line+'x b33'],game['hands'],'c')
    live_root=[{cardkey(h) for h,w in zip(root['hands'][s],raw_wr[s],strict=True) if w>1e-4} for s in (0,1)]
    bb&=live_root[0];co&=live_root[1]
    masks=game_reach(root,game)[0]
    by_node={(v['board'],v['line'],v['player']):v for v in game['nodes']};out={}
    for public,reported in policy['boards'].items():
        target=by_node[public,source.LINE,1];start=by_node[public,source.LINE[:-1],0]
        assert (target['pot'],target['bets'],public[6:8])==(830,[165,165],turn)
        row=n.proof(root,game,target,masks)
        assert row==reported['reach']
        active=[{cardkey(h) for h,w in zip(game['hands'][s],target['w'][s],strict=True) if w>1e-4 and n.cards(public).isdisjoint(cardkey(h))} for s in (0,1)]
        foes=bb&active[0]&accepted(start,game['hands'],'x')
        heroes=co&active[1]&accepted(target,game['hands'],'x')
        bm=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        seq={cardkey(h):(i,b) for i,(h,b) in enumerate(zip(game['hands'][1],bm,strict=True))}
        actual={}
        for h in sorted(heroes):
            hand=''.join(h);cells=[hand_cell(hand,public[:i]) for i in (6,8,10)]
            if cells[0][0] not in route['flop'] or cells[1][0] not in route['turn'] or route['river'].get(cells[2][0])!='過':continue
            if not any(set(h).isdisjoint(v) for v in foes):continue
            i,b=seq[h];actions=target['acts']
            assert b&(1<<actions.index('x'))
            w=[max(0.0,target['strat'][j*len(bm)+i]) for j in range(len(actions))]
            total=sum(w);assert total>0
            actual[hand]=dict(classes=[k[1] for k in cells],displayed_suggestion='過',
                policy=dict(action_order=actions,accepted_mask=b,accepted_actions=[k for j,k in enumerate(actions) if b&(1<<j)],
                            strategy={k:round(q/total,7) for k,q in zip(actions,w,strict=True)}))
        # B762's two-policy preflight additionally restricts the input common hands and
        # opponents. Individual policies can offer more private deals before this intersection.
        assert set(reported['displayed_hands'])<=set(actual)
        out[public]=(actual,foes)
    return out


def worker(turn,folder,archive,old_archive,route_file,solver,pipeline,pool):
    ident,digest=receipt.PINS[turn];assert sha(archive)==digest
    names=unpack_original(archive,folder);raw=(folder/'proof.json').read_bytes();claim=json.loads(raw)
    assert names=={'rendered-routes.json','proof.json','gto/job.json','gto/result.json','exp_ip/job.json','exp_ip/result.json'}
    assert (claim['rank'],claim['model_id'],claim['flop'],claim['turn'],claim['actor'],claim['line'])==(199,source.MODEL,source.FLOP,turn,1,source.LINE)
    assert route_file.read_bytes()==(folder/'rendered-routes.json').read_bytes()
    source.run(SimpleNamespace(solver=solver,routes=route_file,archive=old_archive,turn=turn,output=folder,preflight=False,driver=None))
    assert raw==(folder/'proof.json').read_bytes()
    route=read(route_file)['199']
    root,m,jobs,old,eligible,pin=source.original(old_archive,turn,route)
    bbraw,=[v['wr'] for v in root['nodes'] if v['line']=='x b50 c/' and v['board'].endswith(turn)]
    ej,rules=source.native.prepare_job(dict(source=dict(root=root,version='gto',manifest=m),job=jobs['gto']),'exp_ip',pool,pipeline)
    ej['out']='result.json';assert ej==jobs['exp_ip']
    modes={};sources={};code='B762_R199_'+source.FLOP.upper()+'_'+turn.upper()
    for mode,p in claim['policies'].items():
        game=read(folder/mode/'result.json')
        assert len(old[mode]['nodes'])==p['original_node_count']==210
        source.compare(old[mode],game,len(eligible))
        game.update(line0='x b50 c',turn=turn,rivers=source.RIVERS[turn])
        assert (sha((folder/mode/'job.json').read_bytes()),sha((folder/mode/'result.json').read_bytes()))==(p['job_sha256'],p['source_sha256'])
        modes[mode]=policy(root,game,turn,p,route,bbraw)
        s=dict(version=mode,run=receipt.RUN,source_sha256=p['source_sha256'],root=root,root_sha256=sha(compact(root)),subgame=game,
               archive_code=code,archive_sha256=digest,manifest=dict(m,locks=[]))
        if mode=='exp_ip':
            rootsha=s['root_sha256'];s['manifest'].update(locks=rules,gto_parent_source_run_id=source.gate.RUN,gto_parent_source_sha256=rootsha)
            s.update(verified_gto_parent=dict(run=source.gate.RUN,sha256=rootsha),measured_lock_application=p['measured_lock_application'],
                     applied_rust_rates=game['info']['lock_stats'])
        sources[mode]=s
    common={}
    for public,(g,gv) in modes['gto'].items():
        e,ev=modes['exp_ip'][public]
        actual={}
        for w in comparisons(g,e):
            h=w['hand'];foe=next((v for v in sorted(gv&ev) if source.native.cards(h).isdisjoint(v)),None)
            if foe:actual[h]=dict(w,compatible_bb_hand=''.join(foe))
        if actual:common[public]=actual
        assert {h:w['compatible_bb_hand'] for h,w in actual.items()}==claim['common_physical_co_bb'].get(public,{})
    assert int(bool(common))==claim['positive_distinct_flops']
    stats=dict(turn=turn,flop=source.FLOP,archive_id=ident,archive_sha256=digest,job=receipt.JOBS[turn],run=receipt.RUN,head=receipt.HEAD,
               original_unchanged_nodes_by_mode={'gto':210,'exp_ip':210},old_flop_recomputed=False,locked_public_boards=claim['locked_public_boards'],
               joint_halfpot_assessed=claim['joint_halfpot_assessed'],halfpot_candidates=claim['halfpot_candidates'],positive_rivers=len(common))
    return stats,common,sources,claim


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for name,pin in receipt.FILES.items():
        assert subprocess.check_output(['git','hash-object',name],text=True).strip()==pin
    live=Path('data/nl2_hu_multiboard_status_current.json');original=live.read_bytes();model=json.loads(original)['records'][source.MODEL]
    assert (model['label'],model['frequency_rank'],model['assumed_model_node_spr'])==('APPROX',199,11.53)
    st=a.output.resolve();assert not st.exists() and not st.is_relative_to(Path('data').resolve())
    ev=st/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    pairs.EVIDENCE=ev
    route=partial/'b764_rank199_routes.json';route.write_bytes(subprocess.check_output(['node',source.ROUTE]))
    auth=receipt.validate(read(a.receipts));(st/'nl2_hu_b764_source_receipts.json').write_bytes(json_bytes(auth))
    old_archive=a.parent_archive
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    pool=read(solver/'inputs/pool_stats.json')['NL2']
    stats=[];group=dict(rank=199,model_id=source.MODEL,boards=[],pins=[]);observations={}
    with TemporaryDirectory(prefix='b764-original-') as temp:
        for turn in source.RIVERS:
            aid,d=receipt.PINS[turn];fname='NL2_B762_R199_'+source.FLOP.upper()+'_'+turn.upper()+'.zip'
            path=a.archives/(str(aid)+'.zip');raw=(path if path.exists() else a.archives/fname).read_bytes()
            item,common,sources,claim=worker(turn,Path(temp)/turn,raw,old_archive,route,solver,pipeline,pool)
            stats.append(item);(ev/fname).write_bytes(raw)
            observations[turn]=dict(stats=item,same_co_and_bb=common,source_proof=claim)
            if common and not group['boards']:
                board=sorted(common)[0];g,e=sources['gto'],sources['exp_ip']
                b,p=pairs.emit_board(model,g,e,board,source.LINE,texture(source.FLOP),viewer_code='B764_R199_'+source.FLOP.upper())
                assert (b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==(1,8.3,96.1)
                assert abs(b['actual_spr']-9610/830)<1e-6 and p['pool_observed_marginal_lock_nodes']>0
                b['nl2_locked_variants'][0].update(origin_solve_run_id=receipt.RUN,pool_sha256=source.native.POOL,
                    gto_parent_source_run_id=source.gate.RUN,gto_parent_source_sha256=e['root_sha256'],applied_street_rates=rates(e))
                p.update(rendered_decision_hands=list(common[board].values()),worker_artifact=aid,worker_sha256=d,worker_head=receipt.HEAD,
                         original_job_id=receipt.JOBS[turn],original_turn_source_run=source.gate.RUN)
                group['boards'].append(b);group['pins'].append(p)
    (partial/'b764_rank199_rivers.json').write_bytes(json_bytes(observations))
    (partial/'b764_rank199.json').write_bytes(json_bytes(group))
    totals={k:sum(t[k] for t in stats) for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates','positive_rivers')}
    assert len(group['boards'])==int(totals['positive_rivers']>0)<=1 and totals['locked_public_boards']==10
    result=dict(rank=199,model_id=source.MODEL,source_run=receipt.RUN,source_head=receipt.HEAD,prior_solve_run=source.gate.RUN,
                workers=stats,verified_original_nodes_per_paired_turn=420,new_native_flop_solves=0,target_turns=2,distinct_original_flops=1,
                positive_distinct_flops=len(group['boards']),cert_eligible_ranks=[],publisher_native_solves_repeated=0,**totals)
    (st/'nl2_hu_b764_summary.json').write_bytes(json_bytes(result))
    assert live.read_bytes()==original
    print(json.dumps(dict(positive_distinct_flops=len(group['boards']),**totals)))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--archives',type=Path,default=Path('data/solver_evidence'))
    cli.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b764_source_receipts.json'))
    cli.add_argument('--parent-archive',type=Path,default=Path('data/solver_evidence/NL2_B755_R151_7H6D4S.zip'))
    cli.add_argument('--solver',type=Path,required=True);cli.add_argument('--output',type=Path,required=True)
    publish(cli.parse_args())
