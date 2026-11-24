"""Promote only rank233 after all three B737 independent river comparisons pass."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import json_bytes, sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b719_integrate import CENTRAL
from hu_b738_collect import PINS, RUN, HEAD
from hu_b737_rank233_rivers import CASES, LINE, MODEL, cards

BOARDS={'Ts9s6h':'6h9sTs2c3h','Th9h7c':'7c9hTh2s6c','Ts8s7h':'7h8sTs2cKc'}


def read(p):return json.loads(p.read_bytes())


def integrate(a):
    stage=a.stage.resolve();dest=Path('data').resolve()
    assert stage.is_dir() and not stage.is_relative_to(dest)
    reg=Path(CENTRAL[0]);raw=reg.read_bytes();before=json.loads(raw);rs=before['records']
    original_count=before['CERT_MULTIBOARD'];protected={k:v for k,v in rs.items() if v['label']=='CERT-MULTIBOARD'}
    assert len(protected)==original_count>=152 and len(rs)==392
    assert (rs[MODEL]['frequency_rank'],rs[MODEL]['label'],rs[MODEL]['assumed_model_node_spr'])==(233,'APPROX',2.383)
    gpath='solver_evidence/reverified/rank233.json';g=read(stage/gpath)
    assert (g['rank'],g['model_id'],len(g['boards']),len(g['pins']))==(233,MODEL,3,3)
    assert len({suit_isomorphism_class(b['flop']) for b in g['boards']})==3
    assert {b['flop']:b['public_board'] for b in g['boards']}==BOARDS
    summary=read(stage/'nl2_hu_b738_summary.json');assert summary['source_run']==RUN and summary['source_head']==HEAD
    assert (summary['positive_distinct_flops'],summary['cert_eligible_ranks'],summary['joint_reachable_locked_boards'],
            summary['half_pot_assessed'],summary['half_pot_candidates'])==(3,[233],36,36,0)
    medium=read(stage/'nl2_hu_b738_locked_medium.json')
    for pol in ('gto_references','references'):
        assert {r['public_board'] for r in medium[pol].values()}==set(BOARDS.values()) and len(medium[pol])==3
    paths={gpath,'nl2_hu_b738_summary.json','nl2_hu_b738_source_receipts.json','nl2_hu_b738_locked_medium.json',
           'solver_evidence/partial/b738_rank233_routes.json'}
    for b,p in zip(g['boards'],g['pins'],strict=True):
        flop=b['flop'];public=BOARDS[flop];aid,digest=PINS[flop]
        assert all(b[k]==p[k] for k in ('flop','turn','public_board','river','source_run_id','actual_spr'))
        assert p['source_run_id']==RUN and p['worker_artifact']==aid and p['worker_head']==HEAD
        assert (b['turn'],cards(public[:6]),public[-4:])==(CASES[flop][0],cards(flop),b['turn']+b['river'])
        assert (b['actual_exact_action_line'],b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==(LINE,0,34.86,83.07)
        assert abs(b['actual_spr']-8307/3486)<1e-6 and b['original_18_turn_nodes_unchanged'] and b['flop_native_solves_repeated']==0
        assert len(b['nl2_locked_variants'])==1 and b['nl2_locked_variants'][0]['version']=='exp_oop' and p['pool_observed_marginal_lock_nodes']>0
        for policy in ('GTO','NL2'):assert p[policy+'_compatible_hole_card_pairs']>=p[policy+'_strict_combos']>0
        witnesses=p['rendered_decision_hands'];assert 0<len(witnesses)==len({w['hand'] for w in witnesses})<=p['common_legal_hero_combos']
        for w in witnesses:
            assert [w[k] for k in ('flop_class','turn_class','river_class','displayed_suggestion')]==['MID','MID','MID','過']
            for policy in ('gto','nl2'):
                v=w[policy];assert 'x' in v['accepted_actions'] and v['accepted_mask']&(1<<v['action_order'].index('x'))
        assert p['locked_original_archive_code']==p['archive_code']=='B737_R233_'+flop.upper()
        assert p['locked_original_archive_sha256']==p['archive_sha256']==digest
        archive='solver_evidence/NL2_'+p['archive_code']+'.zip'
        viewer='solver_evidence/NL2_MULTIBOARD_'+p['viewer_archive_code']+'.json.gz'
        assert sha((stage/archive).read_bytes())==digest and sha((stage/viewer).read_bytes())==p['viewer_sha256']
        paths|={archive,viewer,'solver_evidence/partial/b738_'+flop.lower()+'_proof.json'}
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    assert actual==paths,actual^paths
    for rel in sorted(paths):
        source=stage/rel;target=dest/rel
        assert not source.is_symlink() and source.resolve().is_relative_to(stage)
        assert not target.exists() or source.read_bytes()==target.read_bytes()
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    subprocess.run([sys.executable,'tools/hu_apply_cert_extensions.py','--out',str(reg)],check=True)
    after=read(reg);rr=after['records']
    assert rr.keys()==rs.keys() and all(rr[k]==v for k,v in rs.items() if k!=MODEL) and all(rr[k]==v for k,v in protected.items())
    assert (after['CERT_MULTIBOARD'],after['APPROX'],after['TOTAL'])==(original_count+1,391-original_count,392)
    assert rr[MODEL]['label']=='CERT-MULTIBOARD' and rr[MODEL]['proven_exact_board_count']==3
    assert {b['public_board'] for b in rr[MODEL]['certified_3_to_5_exact_flop_boards']}==set(BOARDS.values())
    report=dest/'nl2_hu_b738_integration.json';report.write_bytes(json_bytes(dict(schema='NL2_B738_RANK233_PROMOTION_V1',
        rank=233,model_id=MODEL,source_run=RUN,source_head=HEAD,previous_registry_sha256=sha(raw),new_registry_sha256=sha(reg.read_bytes()),
        preserved_prior_certificates=original_count,unchanged_other_records=391,distinct_positive_flops=3,
        CERT_MULTIBOARD=after['CERT_MULTIBOARD'],APPROX=after['APPROX'],TOTAL=392)))
    a.paths.write_text('\n'.join(sorted(set(CENTRAL)|{'data/'+r for r in paths}|{'data/'+report.name}))+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--paths',type=Path,required=True)
    integrate(p.parse_args())

