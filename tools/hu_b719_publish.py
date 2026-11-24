"""Independently replay four historical river policies and all three B714 workers."""
import argparse
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b488_archive_reevaluation as legacy
import hu_b714_rank255_rivers as native
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_b719_collect import HEAD, OLD, RUN, validate
from hu_board_reach_corrections import source_key, summarize
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible
from solve_hu_missing_branches import EXTRA_SPOTS

MODEL, LINE = native.MODEL, native.LINE
SCHEMA = 'NL2_HU_B719_ORIGINAL_LOCKED_MEDIUM_V1'
IMPLEMENTATIONS = {
    'tools/hu_b714_rank255_rivers.py':'8481a56d5a9ca431bcc69f028a973d5477b886fd',
    '.github/workflows/nl2-hu-b714-rank255-rivers.yml':'d8c3e3c25552fb289da742914adce35ebde29acd',
    'data/nl2_hu_b485_original_artifacts.json':'51940e0a9a39503e95419c0e66d8a7a872288d1e',
    'tools/hu_b485_locked_medium.py':'1308dd7289ff7ea83458194f1742ee2a345fb618',
    'tools/hu_b488_archive_reevaluation.py':'80507e5a6ef9be2e49ee648ae7a09a6da1dc3687',
    'tools/hu_b483_locked_medium.py':'018ac485d3fc115f125c777399d96ce38b0f5f04',
    'tools/hu_b470_rank73_new_rivers.py':'39336981ae910b385744a2b0aaea237397babb38',
    'tools/hu_sequential_cfr_reach.py':'f26df926c088e5b4117bb911956cbc5031e2458d',
    'tools/hu_checked_gto_boundary.py':'219f46b0a259fa3e71f1225046ab5b12c44c28c6',
    'tools/verify_hu_multiboard_100bb.py':'df06b9480c0beef93165c46b13e71dd641f82177',
    'tools/hu_reverified_board_pair.py':'ac58961ba8890d989165b03e3432d4f27b9cd5c6',
    'tools/hu_board_reach_corrections.py':'002b20cedf32ef43bf0bbd1cf1ae2c7d0bec666a',
    'hwrange.js':'1871d8706adf85e5e6e0f4a7ba94f72454bdb06f',
    'lines_data.js':'a0c64c5cb7f611d23edfa21518fce51347a9e877',
    'nl2_reach.js':'45a600fdfe80781a550f4f3dc4b2914d4771c972',
    'nl2_rules.js':'bf96f090d114b932f96a2a56dadc00dc94cb0939',
    'nl2_titles.js':'7fea5003d96b48fd06ff80c192c38198979551d4',
    **native.PINS,
}


def visible_policies(source, row, route, allowed=None):
    sub = source['subgame']
    public = row['public_board']
    node, = [n for n in sub['nodes'] if (n['board'],n['line'],n['player']) == (public,LINE,1)]
    assert (node['pot'],node['bets'],sub['stack']) == (3404,[0,0],8323)
    assert native.cards(public[:6]) == native.cards(sub['flop']) and public[6:8] == sub['turn']
    masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    found={}
    for ix,(hole,mask) in enumerate(zip(sub['hands'][1],masks,strict=True)):
        if not mask & (1 << node['acts'].index('x')):
            continue
        key = ''.join(native.cardkey(hole))
        if allowed is not None and key not in allowed:
            continue
        cells = [native.hand_cell(hole,public[:end]) for end in (6,8,10)]
        if cells[0][0] not in route['flop'] or cells[1][0] not in route['turn'] or route['river'].get(cells[2][0])!='過':
            continue
        weights=[max(0,node['strat'][a*len(masks)+ix]) for a in range(len(node['acts']))]
        total=sum(weights)
        assert total>0
        actions=[a for i,a in enumerate(node['acts']) if mask & (1<<i)]
        found[key]=dict(classes=[c[1] for c in cells],displayed_suggestion='過',
            policy=dict(action_order=node['acts'],accepted_mask=mask,accepted_actions=actions,
                strategy={a:round(w/total,7) for a,w in zip(node['acts'],weights,strict=True)}))
    return found


def comparisons(g,e):
    out=[]
    for hand in sorted(g.keys() & e.keys()):
        left,right=g[hand],e[hand]
        assert left['classes']==right['classes'] and left['displayed_suggestion']==right['displayed_suggestion']=='過'
        out.append(dict(hand=hand,flop_class=left['classes'][0],turn_class=left['classes'][1],
            river_class=left['classes'][2],displayed_suggestion='過',gto=left['policy'],nl2=right['policy']))
    return out


def stage_board(group,medium,model,contract,sources,rows,policies,provenance,scope):
    g,e=sources
    public=rows[0]['public_board']
    assert rows[1]['public_board']==public
    witnesses=comparisons(*policies)
    assert witnesses and compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
    flop=g['subgame']['flop']
    b,p=pairs.emit_board(model,g,e,public,LINE,texture(flop),viewer_code='B719_R255_'+flop.upper())
    assert b and p and len(witnesses)<=p['common_legal_hero_combos']
    assert b['actual_pot_bb']==34.04 and b['actual_effective_stack_bb']==83.23
    assert p['pool_observed_marginal_lock_nodes']>0
    for version,row,k in zip(('GTO','NL2'),rows,('gto_references','references'),strict=True):
        summarize(row)
        assert p[version+'_strict_combos']==row['strict_legal_combos']>0
        assert p[version+'_compatible_hole_card_pairs']==row['compatible_hole_card_pairs']>0
        assert row['b50'] is not None and 'b50' in row['source_actions']
        row['rendered_decision_hands']=witnesses
        medium[k][source_key(MODEL,row)]=row
    b.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',certification_scope=scope,
        origin_solve_run_id=g['run'],source_root_reused='verified_gto_parent' in e,flop_native_solves_repeated=0,
        restricted_flop_bet_sizes_pct=[33,50,75],flop_bet_size_menu='33%,50%,75%',
        turn_bet_size_menu=g['provenance']['turn_bet_size_menu'],river_bet_size_menu=g['provenance']['river_bet_size_menu'])
    variant=b['nl2_locked_variants'][0]
    variant.update(source_run_role=b['source_run_role'],origin_solve_run_id=e['run'],
        pool_sha256=POOL,measurement_policy=scope,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
    if 'measured_lock_application' in e:
        variant.update(applied_street_rates=rates(e),gto_parent_source_run_id=e['verified_gto_parent']['run'],
            gto_parent_source_sha256=e['verified_gto_parent']['sha256'])
    p.update(rendered_decision_hands=witnesses,source_run_role=b['source_run_role'],source_provenance=provenance,
        GTO_archive_provenance=g['provenance'],NL2_archive_provenance=e['provenance'])
    group['boards'].append(b)
    group['pins'].append(p)


def old_boards(receipts,sources,auth,evidence,model,route,contract,solver,pipeline,ranges,pool,group,medium,tmp):
    catalog=legacy.origins()
    for flop,(public,gid,eid) in OLD.items():
        boards=[];rows=[];hands=[]
        for ident,version in ((gid,'gto'),(eid,'exp_ip')):
            pin=sources[ident]
            archive=(receipts/f'{ident}.zip').read_bytes()
            assert sha(archive)==pin['sha256']
            assert catalog[ident][:2]==(pin['run'],pin['head']) and catalog[ident][2]['sha256']==pin['sha256']
            code=f'B719_GHA_{ident}'
            (evidence/('NL2_'+code+'.zip')).write_bytes(archive)
            (tmp/f'{ident}.zip').write_bytes(archive)
            listings=[a for a in auth['artifacts'].values() if a['workflow_run']['id']==pin['run']]
            (tmp/f'{pin["run"]}.json').write_bytes(json_bytes(dict(artifacts=listings)))
            board=dict(flop=flop,turn=public[6:8],public_board=public,actual_exact_action_line=LINE,
                exact_flop_action='b33 c',acting_seat=1,actual_pot_bb=34.04,actual_effective_stack_bb=83.23)
            original,row=legacy.original(tmp,catalog,ident,version,model,board,solver,pipeline,ranges,pool)
            original['archive_code']=code
            with ZipFile(io.BytesIO(archive)) as z:
                mf,=[n for n in z.namelist() if n.startswith('evidence/') and n.endswith('.json')]
                manifest=json.loads(z.read(mf))
                assert manifest['flop_bet_sizes']=='33%,50%,75%'
                case,=[c for c in manifest['cases'] if (c['flop'],c['turn'],c['line'])==(flop,public[6:8],'b33 c')]
                job=json.loads(z.read('solver/postflop/'+case['sub_json'].replace('.json','.job.json')))
                assert job['turn_oop']==job['turn_ip'] and job['river_oop']==job['river_ip']
                original['provenance'].update(turn_bet_size_menu=job['turn_ip'],river_bet_size_menu=job['river_ip'])
                if version=='exp_ip':
                    original['provenance'].update(verified_pool_source_patterns=manifest['pool_lock_evidence'][flop]['source_patterns'],
                        applied_flop_marginals=original['root']['info']['lock_stats'],
                        applied_turn_river_marginals=original['subgame']['info']['lock_stats'])
            boards.append(original);rows.append(row);hands.append(visible_policies(original,row,route))
        stage_board(group,medium,model,contract,boards,rows,hands,dict(legacy_workers=[sources[gid],sources[eid]]),
            'ORIGINAL_GTO_AND_NL2_ACTOR_SPECIFIC_FLOP_AND_TURN_RIVER_POLICIES')
    return len(OLD)


def new_worker(pin,raw,folder,evidence,partial,model,route,old_route,route_raw,contract,solver,pipeline,ranges,pool,group,medium):
    flop=pin['flop']
    names=unpack_original(raw,folder)
    original=(folder/'proof.json').read_bytes()
    claim=json.loads(original)
    assert (claim['flop'],claim['model_id'],claim['source_worker_blob'])==(flop,MODEL,IMPLEMENTATIONS['tools/hu_b714_rank255_rivers.py'])
    assert set(claim['native_file_sha256'])==names-{'proof.json'}
    expected={'proof.json','rank255-routes.json'}
    for turn in claim['turns']:
        for version in turn['policies']:
            expected.update(turn['turn']+'-'+version+'/'+file for file in ('job.json','result.json'))
    assert names==expected and (folder/'rank255-routes.json').read_bytes()==route_raw
    assert all(sha((folder/n).read_bytes())==v for n,v in claim['native_file_sha256'].items())
    # No driver is supplied on publication. Rebuild original jobs and masks from the stored output.
    native.run(SimpleNamespace(solver=solver,flop=flop,output=folder,driver=None,preflight=False))
    assert (folder/'proof.json').read_bytes()==original
    assert all(sha((folder/n).read_bytes())==v for n,v in claim['native_file_sha256'].items())
    code='B719_R255_'+flop.upper()
    (evidence/('NL2_'+code+'.zip')).write_bytes(raw)
    (partial/('b719_'+flop.lower()+'_proof.json')).write_bytes(original)
    origin,parent,*_=native.authenticated_parent(flop,pipeline,ranges,pool,old_route)
    assert origin==claim['parent_pin'] and parent['root_sha256']==claim['canonical_root_sha256']
    chosen=claim['selected']
    if chosen:
        t=next(t for t in claim['turns'] if t['turn']==chosen['turn'])
        turn=t['turn'];public=chosen['public_board'];rivers=t['preregistered_rivers']
        allowed,_=native.new_parent_rivers(parent['root'],turn,route)
        g_job=native.parent.expected_turn(parent['root'],turn,pipeline)
        g_job['extract'] += [dict(prefix=['x','x',r],street=True) for r in rivers]
        e_job,metadata=native.prepare_job(dict(source=parent,job=g_job),'exp_ip',pool,pipeline)
        e_job['out']='result.json'
        sources=[];rows=[];hands=[]
        for version,job in (('gto',g_job),('exp_ip',e_job)):
            result=t['policies'][version]
            archive_folder=folder/(turn+'-'+version)
            assert (archive_folder/'job.json').read_bytes()==compact(job)
            result_raw=(archive_folder/'result.json').read_bytes()
            sub=json.loads(result_raw)
            sub.update(line0='b33 c',turn=turn,rivers=rivers)
            m=dict(spot='BB3_BTN',pot_family='3BP',locks=[])
            s=dict(root=parent['root'],subgame=sub,run=RUN,version=version,root_sha256=parent['root_sha256'],
                source_sha256=sha(result_raw),archive_sha256=pin['sha256'],archive_code=code,manifest=m,
                provenance=dict(worker=pin,root_worker=origin,original_root_sha256=claim['root_sha256'],
                    original_job_sha256=result['job_sha256'],original_source_sha256=result['source_sha256'],
                    turn_bet_size_menu=job['turn_ip'],river_bet_size_menu=job['river_ip']))
            assert s['source_sha256']==result['source_sha256'] and job['turn_ip']==job['turn_oop'] and job['river_ip']==job['river_oop']
            if version=='exp_ip':
                m.update(locks=metadata,gto_parent_source_run_id=origin['run'],gto_parent_source_sha256=s['root_sha256'])
                s.update(verified_gto_parent=dict(run=origin['run'],sha256=s['root_sha256']),
                    measured_lock_application=result['measured_lock_application'],applied_rust_rates=sub['info']['lock_stats'])
            row=audit_decision(s,public,LINE,1,s['root_sha256'])
            original_node=result['boards'][public]
            assert {k:row[k] for k in original_node['reach']}==original_node['reach']
            found=visible_policies(s,row,route,allowed[public[-2:]])
            assert {h:dict(classes=v['classes'],displayed_suggestion=v['displayed_suggestion'],
                accepted_actions=v['policy']['accepted_actions']) for h,v in found.items()}==original_node['hands']
            sources.append(s);rows.append(row);hands.append(found)
        assert [h['hand'] for h in comparisons(*hands)]==t['common'][public]
        stage_board(group,medium,model,contract,sources,rows,hands,dict(worker=pin,root_worker=origin),claim['scope'])
    locked=[board['reach'] for t in claim['turns'] for board in t['policies'].get('exp_ip',{}).get('boards',{}).values()]
    joint=[r for r in locked if r['strict_legal_combos']>0 and r['compatible_hole_card_pairs']>0]
    assessed=[r for r in joint if r['b50'] is not None and 'b50' in r['source_actions']]
    return dict(flop=flop,root_worker=origin,worker=pin,selected=chosen,original_proof_sha256=sha(original),
        byte_identical_original_proof=True,native_gto_turn_jobs=sum('gto' in t['policies'] for t in claim['turns']),
        native_actor_locked_turn_jobs=sum('exp_ip' in t['policies'] for t in claim['turns']),
        native_locked_river_nodes=len(locked),actor_locked_joint_boards=len(joint),half_pot_assessed_joint_boards=len(assessed),
        half_pot_nonpolarized_candidates=sum(r['b50']['candidate'] for r in assessed),
        both_policies_rendered_positive_rivers=sum(len(t['common']) for t in claim['turns']))


def publish(args):
    assert sys.version_info[:2]==(3,11)
    for path,digest in IMPLEMENTATIONS.items():
        assert native.blob(path)==digest,path
        assert subprocess.check_output(['git','rev-parse',HEAD+':'+path],text=True).strip()==digest,path
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    registry_raw=registry.read_bytes()
    records=json.loads(registry_raw)['records'];model=records[MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['street'],model['assumed_model_node_spr'],
        model['label'])==(255,'BB3_BTN','3BP',2,2.445,'APPROX')
    assert not model['certified_3_to_5_exact_flop_boards'] and len(records)==392
    protected=sum(r['label']=='CERT-MULTIBOARD' for r in records.values())
    assert protected>=151
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.parent.SOLVER
    py=solver/'postflop/py'
    assert sha((py/'ranges.py').read_bytes())==RANGES and sha((py/'pipeline.py').read_bytes())==PIPELINE
    sys.path.insert(0,str(py))
    import pipeline,ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    old_route,route,route_raw=native.routes()
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    data=(args.output/'data').resolve()
    assert data!=Path('data').resolve() and Path('data').resolve() not in data.parents and not data.exists()
    evidence=data/'solver_evidence';partial=evidence/'partial';partial.mkdir(parents=True)
    pairs.EVIDENCE=evidence
    (partial/'b719_rank255_routes.json').write_bytes(route_raw)
    receipt=json.loads((args.receipts/'receipt.json').read_bytes())
    pins=validate(receipt)
    (partial/'b719_auth_receipt.json').write_bytes(json_bytes(receipt))
    group=dict(rank=255,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema=SCHEMA,gto_references={},references={})
    results=[]
    with TemporaryDirectory(prefix='b719-replay-') as temp:
        directory=Path(temp)
        old=old_boards(args.receipts,pins,receipt,evidence,model,route,contract,solver,pipeline,ranges,pool,group,medium,directory)
        for flop in native.CASES:
            pin,=[p for p in pins.values() if p['version']=='paired' and p['flop']==flop]
            raw=(args.receipts/f'{pin["id"]}.zip').read_bytes()
            assert sha(raw)==pin['sha256']
            results.append(new_worker(pin,raw,directory/flop,evidence,partial,model,route,old_route,route_raw,
                contract,solver,pipeline,ranges,pool,group,medium))
    flops=[b['flop'] for b in group['boards']]
    assert len(flops)==len({suit_isomorphism_class(f) for f in flops})==len(group['pins'])<=5
    assert set(native.CASES)=={r['flop'] for r in results} and len(results)==3
    eligible=len(flops)>=3
    if eligible:
        (evidence/'reverified').mkdir()
        (evidence/'reverified/rank255.json').write_bytes(json_bytes(group))
        (data/'nl2_hu_b719_locked_medium.json').write_bytes(json_bytes(medium))
    else:
        (partial/'b719_rank255.json').write_bytes(json_bytes(group))
        (partial/'b719_rank255_locked_medium.json').write_bytes(json_bytes(medium))
    totals={k:sum(r[k] for r in results) for k in ('native_gto_turn_jobs','native_actor_locked_turn_jobs','native_locked_river_nodes',
        'actor_locked_joint_boards','half_pot_assessed_joint_boards','half_pot_nonpolarized_candidates','both_policies_rendered_positive_rivers')}
    summary=dict(rank=255,model_id=MODEL,source_run_id=RUN,source_head=HEAD,prior_positive_flops=old,
        new_positive_flops=sum(bool(r['selected']) for r in results),negative_new_flops=sum(not r['selected'] for r in results),
        distinct_positive_flops=len(flops),selected_exact_boards=flops,certified_eligible=eligible,
        selected_combined_actor_locked_boards=len(medium['references']),selected_combined_half_pot_assessed_boards=len(medium['references']),
        native_solves_repeated=0,protected_cert_records=protected,live_registry_written=False,**totals)
    (data/'nl2_hu_b719_summary.json').write_bytes(json_bytes(summary))
    (data/'nl2_hu_b719_results.json').write_bytes(json_bytes(results))
    assert registry.read_bytes()==registry_raw
    print(json.dumps(summary))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','receipts','output'):
        cli.add_argument('--'+name,required=True,type=Path)
    publish(cli.parse_args())
