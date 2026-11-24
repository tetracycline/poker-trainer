"""Rebuild the three original negative B711 workers. Preserve all raw jobs, results and source receipts."""
import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

import hu_b711_bb_lead_rivers as native
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import proof
from hu_b710_publish import unpack_original
from hu_b715_collect import ARTIFACTS, BLOBS, HEAD, JOBS, RUN, verify_run, verify_worker
from hu_sequential_cfr_reach import game_reach

SCHEMA = 'NL2_HU_B715_CO_BB_MULTI_SIZE_ORIGINAL_LOCKED_MEDIUM_V1'
ROUTE = 'tools/hu_b711_bb_lead_routes.cjs'
WORKER = 'tools/hu_b711_bb_lead_rivers.py'
REGISTRY = Path('data/nl2_hu_multiboard_status_current.json')
CONTRACT = Path('data/nl2_hu_verified_extensions.json')


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def frozen_tree(destination):
    # Resolve indirect imports at the original commit, including the original trainer UI and data.
    paths = ['tools'] + [p for p in BLOBS if not p.startswith('tools/')]
    archive = subprocess.check_output(['git', 'archive', '--format=tar', HEAD, '--', *paths])
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for entry in source:
            path = PurePosixPath(entry.name)
            assert not path.is_absolute() and '..' not in path.parts
            target = destination / path
            if entry.isdir():
                target.mkdir(exist_ok=True, parents=True)
            else:
                assert entry.isfile() and not target.exists()
                target.parent.mkdir(exist_ok=True, parents=True)
                target.write_bytes(source.extractfile(entry).read())
    for path, expected in BLOBS.items():
        assert subprocess.check_output(['git', 'hash-object', destination/path], text=True).strip() == expected


def unpack_replay(folder, archive, frozen, solver, flop, current_routes):
    names = unpack_original(archive, folder)
    proof_path = folder/'proof.json'
    original = proof_path.read_bytes()
    report = json.loads(original)
    assert (report['schema'], report['spot'], report['flop'], report['actor'], report['source_worker_blob'],
            report['source_route_blob']) == ('NL2_B711_CO_BB_MULTI_SIZE_NATIVE_SOURCE_V1', 'CO_BB', flop, 0, BLOBS[WORKER], BLOBS[ROUTE])
    assert (report['solver'], report['rust'], report['pipeline_sha256'], report['ranges_sha256'], report['pool_sha256']) == (
        native.SOLVER, native.RUST, native.PIPELINE, native.RANGES, native.POOL)
    assert [t['turn'] for t in report['turns']] == native.CASES[flop]
    required = {'proof.json', 'rendered-routes.json', 'flop/job.json', 'flop/result.json'}
    for t in report['turns']:
        assert t['gto_solved'] or not t['actor_locked']
        for version, present in (('gto', t['gto_solved']), ('exp_oop', t['actor_locked'])):
            if present:
                required.update(t['turn']+'-'+version+'/'+name for name in ('job.json','result.json'))
    assert names == required and set(report['native_file_sha256']) == names - {'proof.json'}
    assert all(sha((folder/path).read_bytes()) == digest for path, digest in report['native_file_sha256'].items())
    assert (folder/'rendered-routes.json').read_bytes() == current_routes
    args = [sys.executable, str(frozen/WORKER), '--solver', str(solver), '--flop', flop,
            '--routes', str(folder/'rendered-routes.json'), '--output', str(folder)]
    subprocess.run(args, cwd=frozen, check=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=subprocess.DEVNULL)
    assert proof_path.read_bytes() == original and all(sha((folder/path).read_bytes()) == value for path, value in report['native_file_sha256'].items())
    return report, original


def negative_worker(folder, frozen, solver, pipeline, pin, archive, routes_raw, evidence):
    """Independently replay both seats and verify precisely where each negative ends."""
    flop = pin['flop']
    report, original = unpack_replay(folder, archive, frozen, solver, flop, routes_raw)
    routes = json.loads(routes_raw)
    root = read(folder/'flop/result.json')
    assert (folder/'flop/job.json').read_bytes() == compact(native.root_job(flop,pipeline))
    assert (report['native_flop_solves'], report['actor_locked_turn_subgames'], report['locked_river_decisions'],
            report['unique_locked_public_boards'],report['positive_joint_locked_decisions'],report['medium_assessments'],
            report['unique_medium_assessed_public_boards'],report['unique_nonpolarized_candidate_public_boards']) == (1,0,0,0,0,0,0,0)
    assert report['selected_by_rank'] == {k:None for k in routes}
    assert report['positive_distinct_flops_by_rank'] == {k:0 for k in routes}
    decisions = []
    by_rank = {rank:0 for rank in routes}
    n_gto = 0
    negatives = []
    for rec in report['turns']:
        turn = rec['turn']
        diag, picks = native.gate(root,turn,routes)
        assert (diag,picks) == (rec['root_gate'],rec['river_extracts_by_rank'])
        assert not rec['actor_locked'] and not rec['nl2'] and not any(rec['common_by_rank'].values())
        negatives.append(dict(turn=turn,stage=rec['negative_stage'],co_halfpot_accepted=diag['co_b50_accepted'],
            bb_check_call_accepted=diag['bb_check_call_intersection'],root_compatible_pairs=diag['compatible_hole_card_pairs'],
            sampled_rivers_by_rank=picks))
        if not any(picks.values()):
            assert not rec['gto_solved'] and not rec['gto'] and rec['negative_stage']=='ZERO_ROOT_JOINT_UI_RIVERS'
            assert flop in ('8s6d2c','7c5d3h') and diag['co_b50_accepted']==0
            continue
        n_gto += 1
        assert flop=='9d7h4c' and rec['gto_solved'] and rec['negative_stage']=='ZERO_GTO_RENDERED_ACTION_WITNESSES'
        assert diag['co_b50_accepted']==1 and diag['compatible_hole_card_pairs']>0
        job_path=folder/(turn+'-gto')/'job.json'
        assert job_path.read_bytes() == compact(native.turn_job(root,turn,picks,pipeline))
        sub = read(folder/(turn+'-gto')/'result.json')
        sub.update(line0=native.FLOP_LINE,turn=turn,rivers=sorted({r for group in picks.values() for r in group}))
        masks = game_reach(root,sub)[0]
        for rank,c in routes.items():
            nodes=[n for n in sub['nodes'] if (n['line'],n['player'])==(c['line'],0)]
            assert {n['board'][-2:] for n in nodes}==set(picks[rank]) and len(nodes)==len(picks[rank])
            for node in nodes:
                public=node['board']
                assert native.cards(public[:6])==native.cards(flop) and public[6:8]==turn
                bet=(1100*c['pct']+50)//100
                assert (node['pot'],node['bets'],sub['stack']-max(node['bets']))==(c['river_pot'],[bet,bet],c['river_stack'])
                reach=proof(root,sub,node,masks)
                assert rec['gto'][rank][public] == dict(reach=reach,displayed_hands={})
                assert (reach['strict_legal_combos'],reach['compatible_hole_card_pairs'],reach['b50'])==(0,0,None)
                decisions.append(dict(rank=int(rank),public_board=public,line=c['line'],status=reach['status']))
                by_rank[rank]+=1
    assert n_gto==report['gto_turn_subgames']
    assert {r:c['gto_river_decisions'] for r,c in report['counts_by_rank'].items()}==by_rank
    assert all(all(n==0 for k,n in c.items() if k!='gto_river_decisions') for c in report['counts_by_rank'].values())
    archive_path = evidence/('NL2_B711_CO_BB_'+flop.upper()+'.zip')
    archive_path.write_bytes(archive)
    proof_path=evidence/'partial'/('b715_'+flop.upper()+'_proof.json')
    proof_path.write_bytes(original)
    return dict(flop=flop,source_run=RUN,source_head=HEAD,job_id=pin['job_id'],artifact=pin['id'],archive=archive_path.name,
        archive_sha256=pin['sha256'],proof_path=proof_path.relative_to(evidence).as_posix(),proof_sha256=sha(original),
        root_job_sha256=report['root_job_sha256'],root_source_sha256=report['root_source_sha256'],
        gto_turn_subgames=n_gto,negative_turns=negatives,gto_negative_river_decisions=decisions,bytes_replayed=True)


def publish(args):
    assert sys.version_info[:2]==(3,11)
    data=args.output.resolve()/'data'
    assert not data.exists() and data!=REGISTRY.parent.resolve() and REGISTRY.parent.resolve() not in data.parents
    evidence=data/'solver_evidence'
    (evidence/'partial').mkdir(parents=True)
    receipts=args.receipts.resolve()
    run,files=read(receipts/'source-run.json'),read(receipts/'source-files.json')
    verify_run(run,files)
    workers=read(receipts/'workers.json')
    assert len(workers)==3 and {p['flop'] for p in workers}==set(JOBS)
    solver=args.solver.resolve()
    py=solver/'postflop/py'
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    assert sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    assert sha((solver/'inputs/pool_stats.json').read_bytes())==native.POOL
    sys.path.insert(0,str(py))
    import pipeline
    registry_bytes=REGISTRY.read_bytes()
    registry=json.loads(registry_bytes)
    routes_raw=subprocess.check_output(['node',ROUTE])
    routes=json.loads(routes_raw)
    for rank,c in routes.items():
        model=registry['records'][c['id']]
        assert (model['frequency_rank'],model['label'],model['solver_profile'],model['assumed_model_node_spr'])==(int(rank),'APPROX','CO_BB',c['spr'])
    auth=[]
    results=[]
    with TemporaryDirectory(prefix='b715-originals-') as temp:
        frozen=Path(temp)/'frozen'
        frozen_tree(frozen)
        for pin in workers:
            flop=pin['flop']
            job=read(receipts/f'job-{pin["job_id"]}.json')
            artifact=read(receipts/f'{pin["id"]}.json')
            assert pin==verify_worker(flop,run,job,artifact)
            archive=(receipts/f'{pin["id"]}.zip').read_bytes()
            assert sha(archive)==ARTIFACTS[flop][1]==pin['sha256']
            folder=Path(temp)/flop
            folder.mkdir()
            results.append(negative_worker(folder,frozen,solver,pipeline,pin,archive,routes_raw,evidence))
            auth.append(dict(artifact=artifact,job=job))
    rows=[row for record in results for row in record['gto_negative_river_decisions']]
    by_rank={rank:sum(str(row['rank'])==rank for row in rows) for rank in routes}
    assert by_rank=={'92':24,'93':24,'94':12} and len({row['public_board'] for row in rows})==36
    summary=dict(schema=SCHEMA,source_run=RUN,source_head=HEAD,source_workers=3,
        positive_distinct_flops_by_rank={rank:0 for rank in routes},cert_eligible_ranks=[],
        native_flop_roots=3, gto_turn_subgames=sum(r['gto_turn_subgames'] for r in results),
        gto_zero_joint_river_decisions_by_rank=by_rank,gto_river_decisions=len(rows),gto_unique_public_boards=36,
        actor_locked_turn_subgames=0,actor_locked_river_decisions=0,actor_locked_unique_public_boards=0,
        medium_assessed_decisions=0,medium_assessed_unique_public_boards=0,nonpolarized_candidates=0,
        native_solves_repeated=0,live_registry_written=False)
    assert summary['gto_turn_subgames']==3
    write(evidence/'partial/b715_auth_receipt.json',dict(run=run,source=files,workers=auth))
    write(data/'nl2_hu_b715_workers.json',workers)
    write(data/'nl2_hu_b715_results.json',results)
    write(data/'nl2_hu_b715_summary.json',summary)
    assert REGISTRY.read_bytes()==registry_bytes
    print(json.dumps(summary))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('receipts','solver','output'):
        cli.add_argument('--'+name,type=Path,required=True)
    publish(cli.parse_args())
