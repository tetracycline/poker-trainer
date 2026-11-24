"""Authenticate rank90 worker bytes and stage exact two-seat board certificates.

Fewer than three distinct positive flops are written only to partial/; they
cannot be picked up by the cumulative CERT importer.
"""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b666_rank90 as native
import hu_reverified_board_pair as pairs
from hu_b467_river_source_gate import json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES
from hu_b514_turn_stab import rates
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_trainer_route_gate import compatible


def publish(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    py=solver/'postflop/py'
    assert sha((py/'pipeline.py').read_bytes())==PIPELINE
    assert sha((py/'ranges.py').read_bytes())==RANGES
    sys.path.insert(0,str(py))
    import pipeline,ranges
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    inputs=json.loads(args.workers.read_bytes())
    assert 1<=len(inputs)<=5 and len({p['id'] for p in inputs})==len(inputs)
    assert len({suit_isomorphism_class(p['flop']) for p in inputs})==len(inputs)
    data=args.output/'data';evidence=data/'solver_evidence'
    evidence.mkdir(parents=True,exist_ok=True)
    native.EVIDENCE=pairs.EVIDENCE=evidence
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][native.MODEL]
    route=json.loads(subprocess.check_output(['node','tools/hu_b666_rank90_route.cjs']))
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][native.MODEL]
    group=dict(rank=90,model_id=native.MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B673_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    report=[]
    for pin in inputs:
        receipt=json.loads((args.receipts/f'{pin["id"]}.json').read_bytes())
        ident=receipt['workflow_run']
        assert (receipt['id'],receipt['name'],ident['id'],ident['head_sha'],ident['repository_id'])==(
            pin['id'],pin['name'],pin['run'],pin['head'],1438346845)
        assert pin['name'] in ('B666-rank90-'+pin['flop'],'B673-rank90-'+pin['flop'])
        outer=(args.receipts/f'{pin["id"]}.zip').read_bytes()
        assert receipt['digest']=='sha256:'+pin['sha256'] and sha(outer)==pin['sha256']
        with ZipFile(io.BytesIO(outer)) as worker:
            spec=json.loads(worker.read('selected.json'))
            attempts=json.loads(worker.read('attempts.json'))
            if spec is None:
                assert set(worker.namelist())=={'selected.json','attempts.json'}
                assert attempts and all(not a['shared_hands'] for a in attempts)
                report.append(dict(flop=pin['flop'],shared_hands=0,excluded_reason='NO_SHARED_RENDERED_HAND',
                    source_run_id=pin['run'],worker_artifact=pin['id']))
                continue
            assert spec['flop']==pin['flop']
            name='NL2_B666_R90_'+pin['flop'].upper()+'.zip'
            assert set(worker.namelist())=={name,'selected.json','attempts.json'}
            raw=worker.read(name)
        assert sha(raw)==spec['archive_sha256']
        (evidence/name).write_bytes(raw)
        original,locked=native.sources(spec,pipeline,pool,ranges,pin['run'],None,{})
        public=next(n['board'] for n in original['subgame']['nodes'] if n['line']==native.LINE and n['board'].endswith(spec['river']))
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=native.LINE,acting_seat=0))
        rows,hands=zip(*(native.decision(s,public,route) for s in (original,locked)),strict=True)
        common=sorted(hands[0].keys()&hands[1].keys())
        assert common and len(common)==spec['shared_hands']
        assert attempts[-1]==dict(public_board=public,shared_hands=len(common))
        board,proof=pairs.emit_board(model,original,locked,public,native.LINE,texture(spec['flop']),viewer_code='B666_R90_'+spec['flop'].upper())
        assert board is not None and proof['GTO_compatible_hole_card_pairs']>0 and proof['NL2_compatible_hole_card_pairs']>0
        comparisons=[]
        for hand in common:
            labels,label,gpolicy=hands[0][hand]
            assert hands[1][hand][:2]==hands[0][hand][:2]
            comparisons.append(dict(hand=hand,flop_class=labels[0],turn_class=labels[1],river_class=labels[2],
                displayed_suggestion=label,gto=gpolicy,nl2=hands[1][hand][2]))
        board.update(source_run_role='ORIGINAL_WORKFLOW_NATIVE_CFR',origin_solve_run_id=pin['run'],
            restricted_flop_bet_sizes_pct=[33],flop_bet_size_menu=spec['flop_menu'])
        proof.update(rendered_decision_hands=comparisons,source_run_role=board['source_run_role'],
            exact_root_sizing=spec['root_sizing'],worker_artifact=pin['id'],worker_sha256=pin['sha256'])
        board['nl2_locked_variants'][0].update(source_run_role=board['source_run_role'],origin_solve_run_id=pin['run'],
            pool_sha256=POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(locked),
            gto_parent_source_run_id=pin['run'],gto_parent_source_sha256=original['root_sha256'],
            viewer_archive_code=proof['viewer_archive_code'],viewer_sha256=proof['viewer_sha256'])
        group['boards'].append(board);group['pins'].append(proof)
        for key,row in zip(('gto_references','references'),rows,strict=True):
            medium[key][source_key(native.MODEL,row)]=row
        report.append(dict(flop=spec['flop'],public_board=public,shared_hands=len(common),
            compatible_pairs=[r['compatible_hole_card_pairs'] for r in rows],
            locked_half_pot_candidate=rows[1]['b50']['candidate'],source_run_id=pin['run'],worker_artifact=pin['id']))
    destination=evidence/('reverified' if len(group['boards'])>=3 else 'partial')
    destination.mkdir(exist_ok=True)
    (destination/'rank90.json').write_bytes(json_bytes(group))
    (data/'nl2_hu_b673_locked_medium.json').write_bytes(json_bytes(medium))
    (data/'nl2_hu_b673_rank90_results.json').write_bytes(json_bytes(report))
    (data/'nl2_hu_b673_rank90_workers.json').write_bytes(json_bytes(inputs))
    print(json.dumps(dict(boards=len(group['boards']),cert_eligible=len(group['boards'])>=3,
        actor_locked_boards=len(group['boards']),half_pot_assessed=len(group['boards']),
        half_pot_candidates=sum(r.get('locked_half_pot_candidate',False) for r in report),workers=report)))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ('solver','receipts','output'):
        cli.add_argument('--'+field,type=Path,required=True)
    cli.add_argument('--workers',type=Path,default=Path('data/nl2_hu_b673_rank90_workers.json'))
    publish(cli.parse_args())
