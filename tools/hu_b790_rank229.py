"""Reconstruct the original B788 CFR evidence and preserve every prior rank229 witness."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import hu_b728_replay as policies
import hu_b783_rank229_king_nines as base
import hu_b786_rank229 as established
import hu_b788_rank229_two_suited as worker
import hu_b790_collect as source
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b710_publish import unpack_original
from hu_b747_rank150_replay import materialize
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible

MODEL=base.base.MODEL
LINE=base.LINE
EV=Path('data/solver_evidence')
RECEIPT_PIN='250439307dbf33dc5f4bf056ef6dc2cb8ad41e3e'


def read(p):
    return json.loads(p.read_bytes())


def reconstruct(frozen,folder,full,checkpoint,flop,solver,route):
    names=unpack_original(full,folder)
    proof=(folder/'proof.json').read_bytes();c=json.loads(proof)
    assert (c['schema'],c['rank'],c['model_id'],c['flop'],c['line'],c['source_worker_blob'])==(
        'NL2_B788_R229_TWO_SUITED_ORIGINALS_V1',229,MODEL,flop,LINE,source.BLOBS[source.WORKER])
    assert names==set(c['native_file_sha256'])|{'proof.json'} and (folder/'rendered-routes.json').read_bytes()==route
    assert all(sha((folder/n).read_bytes())==h for n,h in c['native_file_sha256'].items())
    with ZipFile(io.BytesIO(checkpoint)) as z:
        assert sorted(n for n in z.namelist() if not n.endswith('/'))==['checkpoint.json','flop/job.json','flop/result.json','selection.json']
        checkpoint_meta=json.loads(z.read('checkpoint.json'));selection=json.loads(z.read('selection.json'))
        assert c['selection']==selection and c['original_flop_source']==checkpoint_meta
        assert c['checkpoint_source_identity']==sha(z.read('selection.json'))
        assert all(z.read(n)==(folder/n).read_bytes() for n in ('flop/job.json','flop/result.json'))
    assert (checkpoint_meta['source_worker_blob'],c['root_and_turn_algorithm_blob'])==(worker.BASE_BLOB,worker.BASE_BLOB)
    assert (checkpoint_meta['root_job_sha256'],checkpoint_meta['root_result_sha256'])==tuple(c['native_file_sha256']['flop/'+n+'.json'] for n in ('job','result'))
    audit="""
import runpy,sys
from pathlib import Path
program=sys.argv.pop(1);sys.argv[0]=program;sys.path.insert(0,str(Path(program).parent))
import hu_b637_rank57 as reader
from hu_b467_river_source_gate import compact
root=Path(sys.argv[sys.argv.index('--output')+1]);jobs={p.parent for p in root.rglob('job.json')}
saved=reader.solve;seen=set()
def checked(folder,job,driver):
    assert driver is None and folder in jobs and folder not in seen
    assert (folder/'job.json').read_bytes()==compact(job)
    seen.add(folder)
    return saved(folder,job,None)
reader.solve=checked
runpy.run_path(program,run_name='__main__')
assert seen==jobs
"""
    subprocess.run([sys.executable,'-c',audit,str(frozen/source.WORKER),'--solver',str(solver),'--output',str(folder),'--flop',flop],cwd=frozen,check=True)
    assert proof==(folder/'proof.json').read_bytes()
    assert all(sha((folder/n).read_bytes())==h for n,h in c['native_file_sha256'].items())
    r=read(folder/'flop/result.json');j=read(folder/'flop/job.json')
    assert (r['flop'],r['pot'],r['stack'])==(flop,2100,9000) and not r['info'].get('lock_stats')
    assert 0<=r['info']['gto_expl_pct']<=.5 and j['flop_oop']==j['flop_ip']=='50%'
    assert sha(compact(r['nodes']))==checkpoint_meta['root_nodes_sha256']
    return c,r,sha(proof)


def same_deals(root,game,public,hero,route):
    """The same private opponent must check on both streets for each policy."""
    flop={n['line']:n for n in root['nodes'] if n['board']==public[:6]}
    turn={n['line']:n for n in game['nodes'] if n['board']==public[:8]}
    start,=(n for n in root['nodes'] if (n['board'],n['line'])==(public[:8],'x x/'))
    river,=(n for n in game['nodes'] if (n['board'],n['line'],n['player'])==(public,LINE,0))
    assert (river['pot'],river['bets'],game['stack'])==(2100,[0,0],9000)
    w=[]
    for seat in (0,1):
        initial={base.base.cardkey(h) for h,v in zip(root['hands'][seat],start['wr'][seat],strict=True) if v>1e-4}
        final={base.base.cardkey(h) for h,v in zip(game['hands'][seat],river['w'][seat],strict=True) if v>1e-4}
        w.append(initial&final)
    sb=w[0]&base.base.accepted(flop[''],root['hands'],'x')&base.base.accepted(turn['x x/'],game['hands'],'x')&base.base.accepted(river,game['hands'],'x')
    if base.base.cardkey(hero) not in sb:return []
    if any(base.hand_cell(hero,public[:cut])[0] not in route[k] for cut,k in ((6,'flop'),(8,'turn'),(10,'river'))):return []
    btn=w[1]&base.base.accepted(flop['x'],root['hands'],'x')&base.base.accepted(turn['x x/x'],game['hands'],'x')
    return sorted(''.join(v) for v in btn if base.public_cards(public+hero).isdisjoint(v))


def verify_policy(root,folder,mode,rec,turn,source_info,route,pipeline,pool):
    results=folder/(turn+'-'+mode);game=read(results/'result.json');job=read(results/'job.json')
    r=rec['policies'][mode]
    assert sha((results/'job.json').read_bytes())==r['job_sha256'] and sha((results/'result.json').read_bytes())==r['source_sha256']
    assert (game['pot'],game['stack'],job['pot'],job['stack'])==(2100,9000,2100,9000)
    assert 0<=game['info']['gto_expl_pct']<=.5
    rivers=rec['root_gate']['eligible_rivers'];game.update(line0='x x',turn=turn,rivers=rivers)
    present={p:same_deals(root,game,p,rec['hero'],route) for p in r['boards']}
    present={p:foes for p,foes in present.items() if foes}
    assert present==r['compatible_btn_by_public_board']
    src=dict(source_info,version=mode,root=root,root_sha256=sha(compact(root)),subgame=game,source_sha256=r['source_sha256'],
             manifest=dict(spot='SB3_BTN',pot_family='3BP',locks=[]))
    if mode=='gto':
        assert not game['info'].get('lock_stats') and not job.get('locks')
    else:
        gto=read(folder/(turn+'-gto')/'job.json')
        ej,rules=base.base.prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='SB3_BTN')),job=gto),mode,pool,pipeline)
        ej['out']='result.json';assert (results/'job.json').read_bytes()==compact(ej) and ej['hero']==0
        lock=base.base.audit_patterns(game,ej,dict(locks=rules),pool,0)
        assert lock==r['applied_lock'] and any(n>0 for k,n in lock['driver_tree_nodes'].items() if k in lock['marginal_targets'])
        assert 0<=game['info']['hero_gap_pct']<=.5
        src['manifest'].update(locks=rules,gto_parent_source_run_id=source.RUN,gto_parent_source_sha256=src['root_sha256'])
        src.update(verified_gto_parent=dict(run=source.RUN,sha256=src['root_sha256']),
                   measured_lock_application=lock,applied_rust_rates=game['info']['lock_stats'])
    return src,present


def emit(group,medium,sources,public,hero,foes,route,contract,model,flop,full_meta,root_meta,claim):
    g,e=sources['gto'],sources['exp_oop']
    hands,grow,erow=policies.compare_hand_policies(g,e,public,route)
    h,=(h for h in hands if h['hand']==hero)
    assert foes and h['displayed_suggestion']=='過' and 'x' in h['gto']['accepted_actions'] and 'x' in h['nl2']['accepted_actions']
    h.update(compatible_btn_hand=foes[0],same_policy_opponents=len(foes))
    board,pin=pairs.emit_board(model,g,e,public,LINE,texture(flop),viewer_code='B790_R229_'+flop.upper())
    assert board and (board['acting_seat'],board['actual_pot_bb'],board['actual_effective_stack_bb'])==(0,21,90)
    assert compatible(contract,board) and pin['pool_observed_marginal_lock_nodes']>0
    board['nl2_locked_variants'][0].update(origin_solve_run_id=source.RUN,pool_sha256=base.base.POOL,applied_street_rates=rates(e),
        gto_parent_source_run_id=source.RUN,gto_parent_source_sha256=e['root_sha256'])
    pin.update(rendered_decision_hands=[h],worker_artifact=full_meta['id'],worker_sha256=full_meta['digest'][7:],
        worker_head=source.HEAD,original_job_id=source.JOBS[flop],checkpoint_artifact_id=root_meta['id'],checkpoint_sha256=root_meta['digest'][7:],
        original_root_source=claim['original_flop_source'],restricted_flop_bet_pct=[50],turn_bet_pct=[33,50,75])
    group['boards'].append(board);group['pins'].append(pin)
    for key,row in (('gto_references',grow),('references',erow)):
        row['rendered_decision_hands']=[h];medium[key][source_key(MODEL,row)]=row


def publish(args):
    solver=args.solver.resolve();assert sys.version_info[:2]==(3,11)
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==base.base.POOL
    pool=json.loads(poolraw)['NL2']
    for path,pin in source.BLOBS.items():assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+path],text=True).strip()==pin
    receipt=args.archives/'receipt.json';assert base.blob(receipt)==RECEIPT_PIN
    auth=source.validate(read(receipt));assert receipt.read_bytes()==json_bytes(auth)
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    model=json.loads(before)['records'][MODEL];assert (model['frequency_rank'],model['solver_profile'])==(229,'SB3_BTN')
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][MODEL]
    route_raw=subprocess.check_output(['node',base.ROUTE]);route=json.loads(route_raw)['229']
    out=args.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    ev=out/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    workers=[];selected={};totals=dict(locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0)
    with TemporaryDirectory(prefix='b790-') as tmp:
        d=Path(tmp);frozen=d/'source';materialize(source.HEAD,frozen)
        assert route_raw==subprocess.check_output(['node',base.ROUTE],cwd=frozen)
        group,medium=established.previous(d,solver)
        assert group==read(EV/'partial/b781_rank229.json')
        medium['schema']='NL2_HU_B790_ORIGINAL_LOCKED_MEDIUM_V1'
        pairs.EVIDENCE=ev
        for flop,job_id in source.JOBS.items():
            archives=[]
            for prefix,code in [('B788-R229-','B788_R229_'),('B788-root-R229-','B788_ROOT_R229_')]:
                meta,=(a for a in auth['artifacts'] if a['name']==prefix+flop);raw=(args.archives/(str(meta['id'])+'.zip')).read_bytes()
                assert sha(raw)==meta['digest'][7:] and len(raw)==meta['size_in_bytes']
                (ev/('NL2_'+code+flop.upper()+'.zip')).write_bytes(raw);archives.append((meta,raw))
            (full,raw),(cp,original)=archives
            path=d/flop;claim,root,proof_sha=reconstruct(frozen,path,raw,original,flop,solver,route_raw)
            turns=[]
            counts={k:0 for k in totals}
            chosen=None
            for rec in claim['turns']:
                turn=rec['turn'];sources={};witnesses={}
                for mode in rec['policies']:
                    s,deal=verify_policy(root,path,mode,rec,turn,dict(archive_code='B788_R229_'+flop.upper(),archive_sha256=sha(raw),run=source.RUN),route,pipeline,pool)
                    sources[mode]=s;witnesses[mode]=deal
                    if mode=='exp_oop':
                        stats=[r['reach'] for r in rec['policies'][mode]['boards'].values()]
                        half=[r for r in stats if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and 'b50' in r['source_actions'] and r['b50'] is not None]
                        counts['locked_public_boards']+=len(stats);counts['joint_halfpot_assessed']+=len(half);counts['halfpot_candidates']+=sum(r['b50']['candidate'] for r in half)
                both={}
                for p,btn in witnesses.get('gto',{}).items():
                    common=sorted(set(btn)&set(witnesses.get('exp_oop',{}).get(p,[])))
                    if common:both[p]=dict(sb=rec['hero'],btn_hands=common)
                assert both==rec['common']
                turns.append(dict(turn=turn,root_gate=rec['root_gate'],modes=list(sources),common=both,
                    displayed_gto_rivers=len(witnesses.get('gto',{})),displayed_nl2_rivers=len(witnesses.get('exp_oop',{}))))
                if both:
                    assert chosen is None and rec==claim['turns'][-1]
                    public=min(both);chosen=dict(turn=turn,public_board=public,**both[public])
                    emit(group,medium,sources,public,rec['hero'],both[public]['btn_hands'],route,contract,model,flop,full,cp,claim)
            assert chosen==claim['selected'] and (chosen is not None)==bool(claim['positive_distinct_flops'])
            if chosen:selected[flop]=chosen
            assert all(counts[k]==claim[k] for k in counts)
            for k in totals:totals[k]+=counts[k]
            workers.append(dict(flop=flop,original_job_id=job_id,worker_artifact=full['id'],worker_sha256=sha(raw),checkpoint_artifact=cp['id'],checkpoint_sha256=sha(original),
                proof_sha256=proof_sha,original_root=claim['original_flop_source'],selection=claim['selection'],turns=turns,selected=chosen,**counts))
    n=len(group['boards']);assert n==2+len(selected)==len({suit_isomorphism_class(b['flop']) for b in group['boards']})==len(group['pins'])
    assert n==len(medium['references'])==len(medium['gto_references']) and 2<=n<=5
    eligible=n>=3 and model['label']=='APPROX'
    target=ev/'reverified' if eligible else partial;target.mkdir(exist_ok=True)
    gp=target/('rank229.json' if eligible else 'b790_rank229.json')
    mp=out/'nl2_hu_b790_locked_medium.json' if eligible else partial/'b790_rank229_locked_medium.json'
    gp.write_bytes(json_bytes(group));mp.write_bytes(json_bytes(medium))
    result=dict(schema='NL2_HU_B790_VERIFIED_RANK229_TWO_SUITED_ROOTS_V1',rank=229,model_id=MODEL,source_run=source.RUN,source_head=source.HEAD,
                selected_by_flop=selected,positive_distinct_flops=n,new_positive_flops=len(selected),new_original_flops=3,
                cert_eligible_ranks=[229] if eligible else [],workers=workers,**totals)
    (out/'nl2_hu_b790_source_manifest.json').write_bytes(receipt.read_bytes())
    (out/'nl2_hu_b790_results.json').write_bytes(json_bytes(result))
    assert before==registry.read_bytes()
    print(json.dumps({k:v for k,v in result.items() if k!='workers'}))


if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','archives','output'):c.add_argument('--'+k,type=Path,required=True)
    publish(c.parse_args())
