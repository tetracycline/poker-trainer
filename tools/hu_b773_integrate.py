"""Import immutable rank199 comparisons, rebuilding the four central files only for three positive flops."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import json_bytes,sha
from hu_b719_integrate import CENTRAL
from hu_b771_rank199_third_flop import FLOP, LINE, MODEL
from hu_b773_rank199_publish import PRIOR, PRIOR_BLOB, sha1
from hu_b755_rank151 import cards, suit_isomorphism_class
from hu_b773_collect import HEAD, JOBS, PINS, RUN, validate


def read(p):
    return json.loads(p.read_bytes())


def integrate(a):
    stage=a.stage.resolve()
    base=Path('data').resolve()
    assert not stage.is_relative_to(base)
    central={p:Path(p).read_bytes() for p in CENTRAL}
    reg=Path('data/nl2_hu_multiboard_status_current.json')
    before=read(reg);old=before['records']
    assert len(old)==392 and before['CERT_MULTIBOARD']>=155
    assert (old[MODEL]['label'],old[MODEL]['frequency_rank'],old[MODEL]['assumed_model_node_spr'])==('APPROX',199,11.53)
    summary=read(stage/'nl2_hu_b773_summary.json')
    assert (summary['rank'],summary['source_run'],summary['source_head'],summary['publisher_native_solves_repeated'])==(199,RUN,HEAD,0)
    count=summary['positive_distinct_flops'];cert=count==3
    assert count in (2,3) and summary['cert_eligible_ranks']==([199] if cert else [])
    group_path='solver_evidence/'+('reverified/rank199.json' if cert else 'partial/b773_rank199.json')
    g=read(stage/group_path)
    assert (g['rank'],g['model_id'],len(g['boards']),len(g['pins']))==(199,MODEL,count,count)
    validate(read(stage/'nl2_hu_b773_source_receipts.json'))
    medium_path='nl2_hu_b773_locked_medium.json' if cert else 'solver_evidence/partial/b773_selected_medium.json'
    medium=read(stage/medium_path)
    assert medium['schema']=='NL2_HU_B773_ORIGINAL_LOCKED_MEDIUM_V1'
    assert sha1(PRIOR)==PRIOR_BLOB
    prior=read(PRIOR)
    assert g['boards'][:2]==prior['boards'] and g['pins'][:2]==prior['pins']
    boards={b['public_board'] for b in g['boards']}
    assert len(boards)==len({suit_isomorphism_class(b['flop']) for b in g['boards']})==count
    for rows in (medium['gto_references'],medium['references']):
        assert len(rows)==count and boards=={r['public_board'] for r in rows.values()}
    raw='solver_evidence/NL2_B771_R199_'+FLOP.upper()+'.zip'
    detail='solver_evidence/partial/b773_rank199_turns.json'
    paths={group_path,medium_path,raw,detail,'nl2_hu_b773_source_receipts.json','nl2_hu_b773_summary.json','solver_evidence/partial/b773_rank199_routes.json'}
    aid,digest=PINS[FLOP]
    assert sha((stage/raw).read_bytes())==digest
    report=read(stage/detail);claim=report['source_proof']
    assert (claim['rank'],claim['model_id'],claim['flop'],claim['original_nodes_unchanged'])==(199,MODEL,FLOP,15)
    assert claim['positive_distinct_flops']==int(cert) and claim['selected_turn']==summary['selected_turn']
    for key in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates'):
        assert summary[key]==claim[key]==sum(r['stats'][key] for r in report['turns'])
    assert summary['positive_rivers']==sum(len(r['same_private_pairs']) for r in report['turns'])
    for i,(b,p) in enumerate(zip(g['boards'],g['pins'],strict=True)):
        public=b['public_board']
        assert len(public)==10 and cards(public[:6])==cards(b['flop']) and public[6:8]==b['turn']
        assert all(b[k]==p[k] for k in ('public_board','turn','flop','actual_spr','source_run_id'))
        assert (b['actual_spr'],b['actual_pot_bb'],b['actual_effective_stack_bb'],b['actual_exact_action_line'],b['acting_seat'])==(11.578313,8.3,96.1,LINE,1)
        assert len(b['nl2_locked_variants'])==1 and b['nl2_locked_variants'][0]['version']=='exp_ip' and p['pool_observed_marginal_lock_nodes']>0
        for mode in ('GTO','NL2'):
            assert p[mode+'_compatible_hole_card_pairs']>=p[mode+'_strict_combos']>0
        w=p['rendered_decision_hands']
        assert len(w)==len({v['hand'] for v in w})>0
        for v in w:
            assert len(cards(v['hand']+public+v['compatible_bb_hand']))==9 and v['displayed_suggestion']=='過'
            assert all('x' in v[mode]['accepted_actions'] for mode in ('gto','nl2'))
        viewer='solver_evidence/NL2_MULTIBOARD_'+p['viewer_archive_code']+'.json.gz'
        archive='solver_evidence/NL2_'+p['archive_code']+'.zip'
        folder=base
        if i==2:
            assert cert and b['flop']==FLOP and b['turn']==claim['selected_turn']
            assert archive==raw and (p['worker_artifact'],p['original_job_id'],p['worker_sha256'],p['worker_head'])==(aid,JOBS[FLOP],digest,HEAD)
            sel,=[r for r in report['turns'] if r['stats']['turn']==b['turn']]
            assert w==sel['same_private_pairs'][public]
            assert viewer=='solver_evidence/NL2_MULTIBOARD_B773_R199_'+FLOP.upper()+'.json.gz'
            paths.add(viewer);folder=stage
        assert sha((folder/viewer).read_bytes())==p['viewer_sha256'] and sha((folder/archive).read_bytes())==p['archive_sha256']
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    assert actual==paths,actual^paths
    for path in sorted(paths):
        src=stage/path;dst=base/path
        assert not src.is_symlink() and src.resolve().is_relative_to(stage) and not dst.is_symlink() and dst.resolve().is_relative_to(base)
        assert not dst.exists() or dst.read_bytes()==src.read_bytes()
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
    if cert:
        subprocess.run([sys.executable,'tools/hu_apply_cert_extensions.py','--out',str(reg)],check=True)
        after=read(reg);new=after['records']
        assert new.keys()==old.keys() and all(new[k]==r for k,r in old.items() if k!=MODEL)
        assert (after['CERT_MULTIBOARD'],after['APPROX'],after['TOTAL'])==(before['CERT_MULTIBOARD']+1,before['APPROX']-1,392)
        assert new[MODEL]['label']=='CERT-MULTIBOARD' and new[MODEL]['proven_exact_board_count']==3
        assert {b['public_board'] for b in new[MODEL]['certified_3_to_5_exact_flop_boards']}==boards
    else:
        assert all(Path(p).read_bytes()==r for p,r in central.items())
        after=before
    report=base/'nl2_hu_b773_integration.json'
    report.write_bytes(json_bytes(dict(rank=199,source_run=RUN,source_head=HEAD,positive_distinct_flops=count,
        prior_certificates_preserved=before['CERT_MULTIBOARD'],unchanged_records=391 if cert else 392,
        CERT_MULTIBOARD=after['CERT_MULTIBOARD'],APPROX=after['APPROX'],new_label=after['records'][MODEL]['label'])))
    candidate={'data/'+p for p in paths}|{'data/'+report.name}|(set(CENTRAL) if cert else set())
    a.paths.write_text('\n'.join(sorted(candidate))+'\n')
    a.group.write_text('data/'+group_path+'\n')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ('stage','paths','group'):
        cli.add_argument('--'+k,type=Path,required=True)
    integrate(cli.parse_args())
