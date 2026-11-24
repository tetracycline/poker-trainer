"""Replay the sole B776 conditional lock and retain the original rank150 partial."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import hu_b724_rank150_rivers as native
import hu_b765_rank150_low_flanks as old_worker
import hu_b768_rank150 as previous
import hu_b777_collect as source
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b710_publish import unpack_original
from hu_b747_rank150_replay import materialize

MODEL, LINE = native.MODEL, native.LINE
RECEIPT_BLOB = '0eab495324f94c994655cc122332daf04ae3eb1c'
FLOP, TURN, HAND = 'TdTc3d','2c','JdKd'
OLD_SOURCE = 'NL2_B765_R150_TDTC3D.zip'
OLD_SHA = '0b271e142cae8c318ab8231b256421c530f4cccbaf54ca47bb18f2fdff575142'
COPIED = {'rendered-routes.json','original-manifest.json','flop/job.json','flop/result.json','2c-gto/job.json','2c-gto/result.json'}
ROOT = Path('data/solver_evidence')
NATIVE_FILES = COPIED | {'2c-exp_ip/job.json','2c-exp_ip/result.json'}

def read(path):
    return json.loads(path.read_bytes())


def verify_native(frozen,solver,folder):
    check = """
import runpy,sys
from pathlib import Path
program=sys.argv.pop(1);sys.argv[0]=program;sys.path.insert(0,str(Path(program).parent))
import hu_b637_rank57 as reader
from hu_b467_river_source_gate import compact
base=Path(sys.argv[sys.argv.index('--output')+1])
saved=reader.solve
seen=[]
def verified(path,job,driver):
    assert driver is None and path==base/'2c-exp_ip' and not seen
    assert (path/'job.json').read_bytes()==compact(job)
    seen.append(path)
    return saved(path,job,None)
reader.solve=verified
runpy.run_path(program,run_name='__main__')
assert seen==[base/'2c-exp_ip']
"""
    cmd=[sys.executable,'-c',check,str(frozen/source.WORKER),'--solver',str(solver),'--output',str(folder)]
    subprocess.run(cmd,cwd=frozen,check=True)


def hand_strategy(game,node,hand):
    seat=node['player']
    index,=(i for i,h in enumerate(game['hands'][seat]) if native.cardkey(h)==native.cardkey(hand))
    return {action:node['strat'][j*len(game['hands'][seat])+index] for j,action in enumerate(node['acts'])}


def inspect(folder,claim,route,pipeline,pool):
    root=read(folder/'flop/result.json')
    root_job=read(folder/'flop/job.json')
    job=read(folder/'2c-gto/job.json')
    manifest=read(folder/'original-manifest.json')
    native.limp.check_limp_source(dict(manifest=manifest,root_job=root_job,subgame_job=None))
    assert (root_job['pot'],root_job['stack'],root['pot'],root['stack'])==(250,9900,250,9900)
    parent,eligible,_,gate=native.parent_gate(root,TURN,route)
    assert gate==claim['root_gate'] and (parent['pot'],parent['bets'])==(416,[83,83])
    assert (job['pot'],job['stack'],job['line0'])==(416,9817,['x','b33','c','/'])
    for seat,k in enumerate(('oop_w','ip_w')):
        assert job[k]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    ej,rules=native.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=job),'exp_ip',pool,pipeline)
    ej['out']='result.json'
    assert compact(ej)==(folder/'2c-exp_ip/job.json').read_bytes()
    prior={}
    turns={}
    decisions={}
    for mode in ('gto','exp_ip'):
        g=read(folder/('2c-'+mode)/'result.json')
        assert (g['pot'],g['stack'],g['flop'])==(416,9817,FLOP)
        assert 0<=g['info']['gto_expl_pct']<=.5
        node,=(n for n in g['nodes'] if (n['line'],n['player'])==('x b33 c/x',1))
        accepted=native.cardkey(HAND) in native.accepted(node,g['hands'],'x')
        turns[mode]=dict(raw_action_frequencies=hand_strategy(g,node,HAND),check_accepted=accepted)
        assert accepted==(mode=='gto')
        if mode=='exp_ip':
            assert 0<=g['info']['hero_gap_pct']<=.5
            application=native.audit_patterns(g,ej,dict(manifest,locks=rules),pool,1)
            assert application==claim['exp_ip']['measured_lock_application']
            assert any(v>0 for k,v in application['driver_tree_nodes'].items() if k in application['marginal_targets'])
        rows=native.observations(root,g,TURN,claim['preregistered_rivers'],eligible,route)
        for public,data in rows.items():
            known=claim[mode]['boards'][public]
            r=data['reach']
            assert r==known['reach']
            co,bb=old_worker.hand_pairs(root,g,TURN,public)
            all_pairs={(''.join(h),''.join(v)) for h in co if ''.join(h) in data['hands'] for v in bb if set(h).isdisjoint(v)}
            if mode=='gto':
                prior[public]=all_pairs
                assert {h for h,v in all_pairs} <= {HAND}
                observed=all_pairs
            else:
                observed=all_pairs & prior[public]
            by_hand={h:sorted(v for k,v in observed if k==h) for h in sorted({h for h,v in observed})}
            assert by_hand==known['compatible_bb_per_co'] and set(known['hands'])==set(by_hand)
            result=dict(strict_combos=r['strict_legal_combos'],compatible_pairs=r['compatible_hole_card_pairs'],
                        named_hand_same_bb=sorted(v for h,v in observed if h==HAND),b50=r['b50'])
            if mode=='gto' and observed:
                result['ui_cells']=[native.hand_cell(HAND,public[:length])[0] for length in (6,8,10)]
                assert result['ui_cells']==['paired:3']*3
            decisions.setdefault(public,{})[mode]=result
    assert len(decisions)==12 and sum(bool(v) for v in prior.values())==10
    assert all(not v['exp_ip']['named_hand_same_bb'] for v in decisions.values())
    valid=[r['exp_ip'] for r in decisions.values() if r['exp_ip']['strict_combos']>0 and r['exp_ip']['compatible_pairs']>0 and r['exp_ip']['b50'] is not None]
    assert (len(valid),sum(r['b50']['candidate'] for r in valid))==(12,5)
    return turns,decisions


def publish(args):
    assert sys.version_info[:2]==(3,11)
    solver=args.solver.resolve()
    evidence=Path('data/solver_evidence')
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    original_registry=registry.read_bytes()
    model=json.loads(original_registry)['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(150,'LMP_CO_BB',23.558)
    assert model['label'] in ('APPROX','CERT-MULTIBOARD')
    for name,blob in source.BLOBS.items():
        assert subprocess.check_output(['git','rev-parse',source.HEAD+':'+name],text=True).strip()==blob
    route_raw=subprocess.check_output(['node',native.ROUTE]);route=json.loads(route_raw)
    assert (route['model_id'],route['line'],route['actor'],route['native_price'])==(MODEL,LINE,1,[416,9817])
    receipt=args.archives/'receipt.json'
    assert native.limp.git_blob(receipt)==RECEIPT_BLOB
    auth=source.validate(read(receipt));assert json_bytes(auth)==receipt.read_bytes()
    meta,=auth['artifacts']
    raw=(args.archives/(str(source.ARTIFACT)+'.zip')).read_bytes()
    assert len(raw)==meta['size_in_bytes'] and sha(raw)==source.DIGEST
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes();assert sha(raw_pool)==native.POOL
    pool=json.loads(raw_pool)['NL2']
    out=args.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    partial=out/'solver_evidence/partial';partial.mkdir(parents=True)
    with TemporaryDirectory(prefix='b777-') as tmp:
        root=Path(tmp);frozen=root/'source'
        materialize(source.HEAD,frozen)
        assert route_raw==subprocess.check_output(['node',native.ROUTE],cwd=frozen)
        folder=root/'raw'
        assert unpack_original(raw,folder)==NATIVE_FILES|{'proof.json'}
        old=evidence/OLD_SOURCE
        assert sha(old.read_bytes())==OLD_SHA
        with ZipFile(old) as archive:
            assert all((folder/n).read_bytes()==archive.read(n) for n in COPIED)
        assert (folder/'rendered-routes.json').read_bytes()==route_raw
        proof=(folder/'proof.json').read_bytes();claim=json.loads(proof)
        before={n:sha((folder/n).read_bytes()) for n in sorted(NATIVE_FILES)}
        assert before==claim['native_file_sha256']
        verify_native(frozen,solver,folder)
        assert proof==(folder/'proof.json').read_bytes() and all(sha((folder/n).read_bytes())==d for n,d in before.items())
        assert (claim['schema'],claim['source_worker_blob'],claim['rank'],claim['model_id'],claim['flop'],claim['turn'],claim['actor'])==(
            'NL2_B776_EXACT_GTO_TURN_MISSING_EXP_IP_V1',source.BLOBS[source.WORKER],150,MODEL,FLOP,TURN,1)
        assert (claim['common'],claim['selected'],claim['locked_named_boards'],claim['joint_halfpot_assessed'],claim['nonpolarized_candidates'])==({},None,12,12,5)
        assert (claim['original_flop_cfr_repeated'],claim['original_gto_turn_cfr_repeated'],claim['new_locked_turn_subgames'])==(0,0,1)
        turns,decisions=inspect(folder,claim,route,pipeline,pool)
        group,medium=previous.previous(root,solver,model,pipeline,pool,route_raw)
        assert group==read(evidence/'partial/b768_rank150.json') and medium==read(evidence/'partial/b768_rank150_locked_medium.json')
        medium['schema']='NL2_HU_B777_ORIGINAL_LOCKED_MEDIUM_V1'
    result=dict(schema='NL2_B777_REPLAYED_RANK150_PREEXISTING_GTO_AND_NEW_EXP_IP_V1',rank=150,model_id=MODEL,
                source_run=source.RUN,source_head=source.HEAD,source_job=source.JOB,source_artifact=source.ARTIFACT,archive_sha256=source.DIGEST,
                original_proof_sha256=sha(proof),native_file_sha256=before,original_gto_source=claim['source'],
                native_prices=dict(flop_pot=250,flop_stack=9900,third_pot_bet=83,turn_river_pot=416,turn_river_stack=9817),
                line=LINE,actor=1,hand=HAND,turn_check=turns,board_evidence=decisions,
                assumed_preflop_ranges=True,measured_lock_application=claim['exp_ip']['measured_lock_application'],
                cert_eligible_ranks=[],selected=None,positive_distinct_flops=2,positive_new_flops=0,
                original_flop_cfr_repeated=0,original_gto_turn_cfr_repeated=0,new_locked_turn_subgames=1,
                locked_named_boards=12,joint_halfpot_assessed=12,nonpolarized_candidates=5,
                reason='CO_JdKd_TURN_CHECK_OUTSIDE_EXP_IP_ACCEPTED_POLICY',changed_registry_records=0)
    (out/'nl2_hu_b777_source_manifest.json').write_bytes(receipt.read_bytes())
    (out/'nl2_hu_b777_results.json').write_bytes(json_bytes(result))
    (out/'solver_evidence/NL2_B776_R150_TDTC3D.zip').write_bytes(raw)
    (partial/'b777_rank150.json').write_bytes(json_bytes(group))
    (partial/'b777_rank150_locked_medium.json').write_bytes(json_bytes(medium))
    assert registry.read_bytes()==original_registry
    print(json.dumps({k:result[k] for k in ('positive_distinct_flops','positive_new_flops','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','archives','output'):p.add_argument('--'+name,type=Path,required=True)
    publish(p.parse_args())
