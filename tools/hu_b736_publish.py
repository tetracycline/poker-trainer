"""Authenticate B733 original jobs and replay every named rank114 river without solving CFR."""
import argparse
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

import hu_b733_rank114 as native
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b514_turn_stab import rates
from hu_b710_publish import unpack_original
from hu_board_reach_corrections import source_key, summarize
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import accepted
from hu_trainer_route_gate import compatible
from verify_hu_multiboard_100bb import lock_scope

RUN=45330756191
HEAD='665b44531e5aeb87785799c7f4580da497294af2'
BRANCH='fix/nl2-hu-lines-audit-20261118'
WF='.github/workflows/nl2-hu-b733-rank114-rivers.yml'
WORKER='tools/hu_b733_rank114.py'
ROUTE='tools/hu_b733_rank114_routes.cjs'
PINS={WORKER:'2f53916d07a51b949dd2645527aa944d53306119',ROUTE:'7386f6544c15b1793419e4a0e9ffb49a190e774f',WF:'e049d82fbe593b3b60da44294b7dd60356dcdc69'}
JOBS={'8s8h3d':138231133103,'7s7h4d':138231132715,'JcJh5d':138231133049}
ARTIFACTS={
    "7s7h4d": [
        14892853040,
        "50bb6bea253842010794d8ea78aa4a6d67d8f070426832c8778900ec1c39a5d2"
    ],
    "JcJh5d": [
        14892079183,
        "154a82a07b9cb04ec0468fe048dcfbdeb20763cdfd6b1cbbff979f3dd7566b78"
    ],
    "8s8h3d": [
        14891617506,
        "af431d377cfacb4d4ae562ca515c55bde6c783c5a1c9a95cd6b0cd6d888d4b80"
    ]
}
ORIGINAL_NAME='NL2_B736_B3_LMP_8S8H3D_ORIGINAL.zip'
STEPS=['Check the original ranges, branch prices and displayed middle pairs','Compile the pinned native solver',
       'Solve the missing river trees and replay both policies','Run actions/upload-artifact@v4']


def read(path):
    return json.loads(path.read_bytes())


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(json_bytes(data))


def fields(obj, names):
    return {name:obj[name] for name in names.split()}


def run_receipt(raw,pin,ref,workflow):
    row=fields(raw,'id head_sha head_branch path status conclusion run_attempt')
    row['repository']=fields(raw['repository'],'id full_name')
    assert row['repository']==dict(id=1438346845,full_name='tetracycline/poker-trainer')
    assert (row['id'],row['head_sha'],row['head_branch'],row['path'],row['status'],row['conclusion'])==(
        pin,ref,BRANCH,workflow,'completed','success')
    return row


def job_receipt(raw,run,job_id,name,steps):
    row=fields(raw,'id run_id head_sha run_attempt name status conclusion')
    row['steps']=[fields(s,'number name status conclusion') for s in raw['steps']]
    assert (row['id'],row['run_id'],row['head_sha'],row['run_attempt'],row['name'],row['status'],row['conclusion'])==(
        job_id,run['id'],run['head_sha'],run['run_attempt'],name,'completed','success')
    assert set(steps)<={s['name'] for s in row['steps'] if (s['status'],s['conclusion'])==('completed','success')}
    return row


def artifact_receipt(raw,run,artifact_id,name,digest):
    row=fields(raw,'id name digest size_in_bytes created_at expires_at expired')
    row['workflow_run']=fields(raw['workflow_run'],'id head_sha head_branch repository_id head_repository_id')
    assert (row['id'],row['name'],row['digest'],row['expired'])==(artifact_id,name,'sha256:'+digest,False)
    assert row['workflow_run']==dict(id=run['id'],head_sha=run['head_sha'],head_branch=BRANCH,
        repository_id=1438346845,head_repository_id=1438346845)
    return row


def authentication(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WF)
    assert len(raw['jobs'])==len(raw['artifacts'])==len(ARTIFACTS)==3
    out=dict(run=run,jobs=[],artifacts=[])
    for flop in JOBS:
        aid,digest=ARTIFACTS[flop]
        j,=[r for r in raw['jobs'] if r['id']==JOBS[flop]]
        a,=[r for r in raw['artifacts'] if r['id']==aid]
        out['jobs'].append(job_receipt(j,run,JOBS[flop],f'solve ({flop})',STEPS))
        out['artifacts'].append(artifact_receipt(a,run,aid,'B733-R114-'+flop,digest))
    b=raw['original_source']
    old=run_receipt(b['run'],native.PIN['run'],native.PIN['head'],'.github/workflows/nl2-hu-stage3-b3.yml')
    out['original_source']=dict(run=old,job=job_receipt(b['job'],old,136056300749,'solve (LMP_CO_BB, 8s8h3d, gto)',
        ['Build pinned authentic Rust CFR postflop engine','Preserve true node-size/pot/SPR/raw combo results and NL2 lock sample/defaults']),
        artifact=artifact_receipt(b['artifact'],old,native.ARTIFACT,native.PIN['name'],native.PIN['sha256']))
    return out


def source_tree(folder):
    paths=['tools',WF,'lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js',
           'data/nl2_hu_multiboard_status_current.json','data/nl2_hu_b485_original_artifacts.json']
    raw=subprocess.check_output(['git','archive',HEAD,'--',*paths])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive:
            name=Path(item.name)
            assert not name.is_absolute() and '..' not in name.parts
            if item.isdir():continue
            assert item.isfile()
            path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.extractfile(item).read())
    for name,expected in PINS.items():
        assert subprocess.check_output(['git','hash-object',str(folder/name)],text=True).strip()==expected


def observed_sources(folder,flop,selected,turn_report,old,pipeline,pool):
    aid,digest=ARTIFACTS[flop];version='exp_oop';turn=selected['turn'];cards=turn_report['gate']['river_extracts']
    if flop==native.OLD:
        root=old['source']['root'];origin_run=native.PIN['run'];original_sha=old['identity']['root_sha256']
    else:
        raw=(folder/'flop/result.json').read_bytes();root=json.loads(raw);origin_run=RUN;original_sha=sha(raw)
    root_sha=sha(compact(root))
    gj=native.turn_job(old['job'],root,turn,cards)
    assert read(folder/(turn+'-gto/job.json'))==json.loads(compact(gj))
    code='B733_R114_'+flop.upper();g=dict(root=root,run=RUN,version='gto',root_sha256=root_sha,
        original_root_sha256=original_sha,archive_code=code,archive_sha256=digest,
        manifest=dict(spot=native.SPOT,pot_family='LMP',locks=[],preflop_ranges=dict(source='ASSUMED_EXPLICIT_169CLASS')))
    ej,rules=native.prepare_job(dict(source=g,job=gj),version,pool,pipeline);ej['out']='result.json'
    assert read(folder/(turn+'-'+version+'/job.json'))==json.loads(compact(ej))
    e=dict(g,version=version,verified_gto_parent=dict(run=origin_run,sha256=root_sha),
        manifest=dict(g['manifest'],locks=rules,gto_parent_source_run_id=origin_run,gto_parent_source_sha256=root_sha))
    for source in (g,e):
        raw=(folder/(turn+'-'+source['version'])/'result.json').read_bytes()
        sub=json.loads(raw);sub.update(line0='x x',turn=turn,rivers=cards)
        source.update(subgame=sub,source_sha256=sha(raw))
    application=native.audit_patterns(e['subgame'],ej,e['manifest'],pool,0)
    assert application==turn_report['measured_lock_application']
    e.update(applied_rust_rates=e['subgame']['info']['lock_stats'],measured_lock_application=application)
    return g,e,origin_run,original_sha


def selected_row(source,public,route,expected):
    root=source['root'];sub=source['subgame'];hlist=sub['hands'][0];v=source['version']
    node,=[n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,native.LINE,0)]
    assert (node['pot'],node['bets'],sub['stack'])==(580,[165,165],9900)
    row=native.proof(root,sub,node,native.game_reach(root,sub)[0]);assert row==expected['reach']
    assert row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0 and row['b50'] is not None
    row.update(version=v,spot=native.SPOT,family='LMP',flop=root['flop'],turn=sub['turn'],source_run_id=RUN,
        source_sha256=source['source_sha256'],archive_sha256=source['archive_sha256'],root_sha256=source['root_sha256'],
        original_root_sha256=source['original_root_sha256'],root_gto_stage_gap_pct=root['info']['gto_expl_pct'],
        root_locked_hero_gap_pct=None,gto_gap_pct=sub['info']['gto_expl_pct'],locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
        root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(v['nodes'] for v in sub['info'].get('lock_stats',{}).values()),
        lock_scope=lock_scope(sub,source['manifest']['locks'],v))
    summarize(row)
    mask=base64.b64decode(row['compatible_action_mask_b64'],validate=True);acts=node['acts'];found={}
    for i,(hand,bits) in enumerate(zip(hlist,mask,strict=True)):
        if not bits&(1<<acts.index('x')):continue
        cells=[native.hand_cell(hand,public[:n]) for n in (6,8,10)]
        if any(c[0] not in route[s] for c,s in zip(cells,('flop','turn','river'),strict=True)):continue
        assert route['river'][cells[2][0]]=='過'
        freq=[max(0.,float(node['strat'][j*len(hlist)+i])) for j in range(len(acts))]
        found[''.join(native.cardkey(hand))]=dict(classes=[c[1] for c in cells],policy=dict(action_order=acts,accepted_mask=bits,
            accepted_actions=[a for j,a in enumerate(acts) if bits&(1<<j)],strategy={a:round(w/sum(freq),7) for a,w in zip(acts,freq,strict=True)}))
    assert sorted(found)==expected['displayed_check_hands']
    return row,found


def add_board(group,medium,folder,flop,old,pipeline,pool,model,contract,route,d):
    s=d['selected'];t,=[t for t in d['turns'] if t['turn']==s['turn']];board=s['public_board']
    g,e,origin,raw_root=observed_sources(folder,flop,s,t,old,pipeline,pool)
    rows,hands=zip(*(selected_row(source,board,route,t[prefix][board]) for source,prefix in ((g,'gto'),(e,'nl2'))),strict=True)
    common=sorted(hands[0].keys()&hands[1].keys())
    assert common and common==s['hands']==t['common'][board]
    witness=[]
    for h in common:
        left,right=hands[0][h],hands[1][h]
        assert left['classes']==right['classes']
        a,b,c=left['classes']
        witness.append(dict(hand=h,flop_class=a,turn_class=b,river_class=c,displayed_suggestion='過',gto=left['policy'],nl2=right['policy']))
    item,pin=pairs.emit_board(model,g,e,board,native.LINE,texture(flop),viewer_code='B736_R114_'+flop.upper())
    assert item and compatible(contract,item)
    assert (item['actual_pot_bb'],item['actual_effective_stack_bb'])==(5.8,97.35)
    assert pin['pool_observed_marginal_lock_nodes']>0
    aid,digest=ARTIFACTS[flop]
    item.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=RUN,original_flop_run_id=origin,
        flop_bet_size_menu='33%,50%,75%,100%',turn_ip_bet_size_menu='33%,66%,100%',actual_turn_bet_bb=1.65)
    item['nl2_locked_variants'][0].update(source_run_role=item['source_run_role'],origin_solve_run_id=RUN,
        pool_sha256=native.POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),
        gto_parent_source_run_id=origin,gto_parent_source_sha256=g['root_sha256'],viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
    pin.update(rendered_decision_hands=witness,worker_artifact=aid,worker_sha256=digest,original_flop_run_id=origin,
        original_flop_sha256=raw_root,source_run_role=item['source_run_role'])
    for key,row in zip(('gto_references','references'),rows,strict=True):
        row['rendered_decision_hands']=witness;medium[key][source_key(native.MODEL,row)]=row
    group['boards'].append(item);group['pins'].append(pin)


def turn_ancestry(root,game,route):
    def policy(source,line,action):
        node,=[n for n in source['nodes'] if n['line']==line]
        return accepted(node,source['hands'],action)
    hero=policy(root,'','x');villain=policy(root,'x','x')
    turn_check=policy(game,'x x/','x');bet=policy(game,'x x/x','b66');call=policy(game,'x x/x b66','c')
    node,=[n for n in game['nodes'] if n['line']=='x x/']
    public=node['board'];public_cards=native.public_cards(public)
    hs={h for h in hero & turn_check & call if public_cards.isdisjoint(h)}
    vs={h for h in villain & bet if public_cards.isdisjoint(h)}
    shown={h for h in hs if native.hand_cell(''.join(h),public[:6])[0] in route['flop']
           and native.hand_cell(''.join(h),public)[0] in route['turn']}
    return dict(bb_flop_check=len(hero),co_flop_check=len(villain),bb_turn_check=len(turn_check),
        co_turn_b66=len(bet),bb_turn_call=len(call),bb_full_line=len(hs),co_full_line=len(vs),
        bb_full_line_displayed=len(shown),bb_displayed_with_compatible_co=sum(any(set(h).isdisjoint(v) for v in vs) for h in shown))


def verify_worker(folder,tree,old_inputs,solver,raw,flop,routes,old):
    aid,digest=ARTIFACTS[flop]
    assert sha(raw)==digest
    folder.mkdir();names=unpack_original(raw,folder)
    saved=(folder/'proof.json').read_bytes();d=json.loads(saved)
    assert (d['schema'],d['flop'],d['rank'],d['model'],d['line'],d['actor'])==(
        'NL2_B733_R114_EXACT_66PCT_RIVERS_V1',flop,114,native.MODEL,native.LINE,0)
    assert (folder/'rendered-routes.json').read_bytes()==routes
    assert d['solver']==native.SOLVER and d['rust']==native.RUST and d['pool_sha256']==native.POOL
    assert (d['root_pot'],d['root_stack'],d['turn_bet'],d['river_pot'],d['river_stack'])==(250,9900,165,580,9735)
    required={'proof.json','rendered-routes.json'}
    if flop!=native.OLD:required|={'flop/job.json','flop/result.json'}
    assert d['native_flop_solves_repeated']==0 and d['reused_native_flop']==(flop==native.OLD)
    assert [t['turn'] for t in d['turns']]==native.CASES[flop][:len(d['turns'])]
    if d['selected'] is None:assert len(d['turns'])==len(native.CASES[flop])
    root=old['source']['root'] if flop==native.OLD else read(folder/'flop/result.json')
    route=json.loads(routes)['routes'];stats=[]
    for t in d['turns']:
        turn=t['turn'];cards=t['gate']['river_extracts']
        assert bool(cards)==bool(t['gto'])
        for version,prefix in [('gto','gto'),('exp_oop','nl2')]:
            if not t[prefix]:continue
            required|={turn+'-'+version+'/'+name for name in ('job.json','result.json')}
            assert sorted(b[8:] for b in t[prefix])==sorted(cards)
        assert bool(t['nl2'])==any(x['displayed_check_hands'] for x in t['gto'].values())
        for b,locked in t['nl2'].items():
            actual=sorted(set(t['gto'][b]['displayed_check_hands'])&set(locked['displayed_check_hands']))
            assert t['common'].get(b,[])==actual
        positive=[b for b,v in t['nl2'].items() if v['reach']['strict_legal_combos']>0]
        assert all(t['nl2'][b]['reach']['compatible_hole_card_pairs']>0 and t['nl2'][b]['reach']['b50'] is not None for b in positive)
        assert all(v['reach']['compatible_hole_card_pairs']==0 and v['reach']['b50'] is None for b,v in t['nl2'].items() if b not in positive)
        stats.append(dict(turn=turn,raw_parent_hands=t['gate']['compatible_displayed_parent_hands'],
            gto_turn_ancestry=turn_ancestry(root,read(folder/(turn+'-gto/result.json')),route) if t['gto'] else None,
            locked_turn_ancestry=turn_ancestry(root,read(folder/(turn+'-exp_oop/result.json')),route) if t['nl2'] else None,
            gto_named=len(t['gto']),gto_displayed=sum(bool(v['displayed_check_hands']) for v in t['gto'].values()),
            locked_public=sorted(t['nl2']),locked_joint=positive,
            halfpot_candidates=[b for b in positive if t['nl2'][b]['reach']['b50']['candidate']],
            common={b:v for b,v in t['common'].items() if v}))
    assert names==required and set(d['native_files'])==required-{'proof.json'}
    assert all(sha((folder/name).read_bytes())==pin for name,pin in d['native_files'].items())
    subprocess.run([sys.executable,str(tree/WORKER),'--solver',str(solver),'--receipts',str(old_inputs),
        '--output',str(folder),'--flop',flop],cwd=tree,check=True,stdout=subprocess.DEVNULL)
    assert (folder/'proof.json').read_bytes()==saved, 'Pinned Python 3.11 source replay differs'
    assert all(sha((folder/name).read_bytes())==pin for name,pin in d['native_files'].items())
    locked=[b for t in stats for b in t['locked_public']]
    assert len(locked)==len(set(locked))==d['native_locked_public_boards']
    n_joint=sum(len(t['locked_joint']) for t in stats);n_cand=sum(len(t['halfpot_candidates']) for t in stats)
    assert (n_joint,n_cand)==(d['joint_halfpot_assessed'],d['nonpolarized_candidates'])
    assert bool(d['selected'])==bool(any(t['common'] for t in stats))==bool(d['positive_distinct_flops'])
    return d,dict(flop=flop,artifact_id=aid,job_id=JOBS[flop],archive_sha256=digest,proof_sha256=sha(saved),
        raw_source_files_sha256=d['native_files'],root_reused=flop==native.OLD,turns=stats,selected=d['selected'],
        native_locked_public_boards=len(locked),joint_halfpot_assessed=n_joint,nonpolarized_candidates=n_cand)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    destination=a.output.resolve();solver=a.solver.resolve()
    assert not destination.exists() and Path('data').resolve() not in (destination,*destination.parents)
    data=destination/'data';evid=data/'solver_evidence';evid.mkdir(parents=True)
    pairs.EVIDENCE=evid
    raw_receipt=read(a.receipts);auth=authentication(raw_receipt)
    archive=a.original_root or a.archives/ORIGINAL_NAME
    old_raw=archive.read_bytes();assert sha(old_raw)==native.PIN['sha256']
    (evid/ORIGINAL_NAME).write_bytes(old_raw)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    current=subprocess.check_output(['node',ROUTE]);route=json.loads(current)['routes']
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][native.MODEL]
    model=read(Path('data/nl2_hu_multiboard_status_current.json'))['records'][native.MODEL]
    assert (model['frequency_rank'],model['assumed_model_node_spr'],contract['seat'],contract['streets'])==(114,17.044,0,['x x','x bet c',''])
    group=dict(rank=114,model_id=native.MODEL,boards=[],pins=[]);medium=dict(schema='NL2_HU_B736_ACTOR_LOCKED_MEDIUM_V1',gto_references={},references={})
    workers=[]
    with TemporaryDirectory(prefix='b736-source-') as tmp:
        parent=Path(tmp);tree=parent/'source';source_tree(tree)
        assert current==subprocess.check_output(['node',ROUTE],cwd=tree)
        receipts=parent/'old';receipts.mkdir();(receipts/f'{native.ARTIFACT}.zip').write_bytes(old_raw)
        write(receipts/f'{native.ARTIFACT}.json',auth['original_source']['artifact'])
        old=native.original(receipts,pipeline,ranges)[0]
        for flop in JOBS:
            aid,digest=ARTIFACTS[flop];name='NL2_B733_R114_'+flop.upper()+'.zip'
            path=a.archives/f'{aid}.zip';raw=(path if path.is_file() else a.archives/name).read_bytes()
            folder=parent/flop;d,w=verify_worker(folder,tree,receipts,solver,raw,flop,current,old)
            assert d['source_template']==old['identity'] and len(raw)==next(r['size_in_bytes'] for r in auth['artifacts'] if r['id']==aid)
            (evid/name).write_bytes(raw);workers.append(w)
            if d['selected']:add_board(group,medium,folder,flop,old,pipeline,pool,model,contract,route,d)
    count=len(group['boards']);assert len({native.suit_isomorphism_class(b['flop']) for b in group['boards']})==count<=3
    if count:
        folder=evid/('reverified' if count>=3 else 'partial')
        write(folder/'rank114.json',group)
        path=data/'nl2_hu_b736_locked_medium.json' if count>=3 else evid/'partial/b736_rank114_locked_medium.json'
        write(path,medium)
    keys=('native_locked_public_boards','joint_halfpot_assessed','nonpolarized_candidates')
    counts={k:sum(w[k] for w in workers) for k in keys}
    summary=dict(schema='NL2_HU_B736_B733_R114_EXACT_66PCT_V1',rank=114,model_id=native.MODEL,run=RUN,head=HEAD,
        source_blobs=PINS,workers=workers,positive_distinct_flops=count,cert_eligible_ranks=([114] if count>=3 else []),
        native_solver_calls_in_publication=0,old_flop_source=old['identity'],old_flop_source_archive=ORIGINAL_NAME,**counts)
    write(data/'nl2_hu_b736_source_receipts.json',auth);write(data/'nl2_hu_b736_results.json',summary)
    print(json.dumps(dict(positive_distinct_flops=count,cert_eligible_ranks=summary['cert_eligible_ranks'],**counts)))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--solver',type=Path,required=True);cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b736_source_receipts.json'))
    cli.add_argument('--archives',type=Path,default=Path('data/solver_evidence'));cli.add_argument('--original-root',type=Path)
    publish(cli.parse_args())
