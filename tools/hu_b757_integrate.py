"""Import immutable rank151 comparisons, rebuilding the four central files only for three positive flops."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import json_bytes,sha
from hu_b719_integrate import CENTRAL
from hu_b755_rank151 import CASES, LINE, MODEL, cards, suit_isomorphism_class
from hu_b757_collect import HEAD, JOBS, PINS, RUN, validate


def read(p):
    return json.loads(p.read_bytes())


def integrate(a):
    stage=a.stage.resolve()
    base=Path('data').resolve()
    assert not stage.is_relative_to(base)
    central={p:Path(p).read_bytes() for p in CENTRAL}
    reg=Path('data/nl2_hu_multiboard_status_current.json')
    before=read(reg);old=before['records']
    assert len(old)==392 and before['CERT_MULTIBOARD']>=154
    assert (old[MODEL]['label'],old[MODEL]['frequency_rank'],old[MODEL]['assumed_model_node_spr'])==('APPROX',151,19.55)
    summary=read(stage/'nl2_hu_b757_summary.json')
    assert (summary['rank'],summary['source_run'],summary['source_head'],summary['publisher_native_solves_repeated'])==(151,RUN,HEAD,0)
    count=summary['positive_distinct_flops'];cert=count==3
    assert 0<=count<=3 and summary['cert_eligible_ranks']==([151] if cert else [])
    group_path='solver_evidence/'+('reverified/rank151.json' if cert else 'partial/b757_rank151.json')
    g=read(stage/group_path)
    assert (g['rank'],g['model_id'],len(g['boards']),len(g['pins']))==(151,MODEL,count,count)
    validate(read(stage/'nl2_hu_b757_source_receipts.json'))
    medium=read(stage/'nl2_hu_b757_locked_medium.json')
    boards={b['public_board'] for b in g['boards']}
    assert len(boards)==len({suit_isomorphism_class(b['flop']) for b in g['boards']})==count
    for rows in (medium['gto_references'],medium['references']):
        assert len(rows)==count and boards=={r['public_board'] for r in rows.values()}
    paths={group_path,'nl2_hu_b757_source_receipts.json','nl2_hu_b757_summary.json','nl2_hu_b757_locked_medium.json','solver_evidence/partial/b757_rank151_routes.json'}
    actual_counts=[]
    for f,(aid,h) in PINS.items():
        raw='solver_evidence/NL2_B755_R151_'+f.upper()+'.zip'
        report='solver_evidence/partial/b757_rank151_'+f.lower()+'.json'
        assert sha((stage/raw).read_bytes())==h
        claim=read(stage/report)
        assert (claim['flop'],claim['source_run'],claim['source_head'],claim['archive_sha256'],claim['worker_artifact'],claim['worker_job'])==(f,RUN,HEAD,h,aid,JOBS[f])
        actual_counts.append(claim)
        paths.update((raw,report))
    fields=('locked_public_boards','joint_locked_boards','halfpot_assessed','halfpot_candidates','positive_distinct_flops')
    assert all(summary[k]==sum(r[k] for r in actual_counts) for k in fields)
    assert count==sum(r['positive_distinct_flops'] for r in summary['workers'])
    for b,p in zip(g['boards'],g['pins'],strict=True):
        f=b['flop'];pub=b['public_board'];turn=b['turn']
        assert f in CASES and turn in CASES[f] and len(pub)==10 and pub[6:8]==turn and cards(pub[:6])==cards(f)
        assert all(b[k]==p[k] for k in ('public_board','turn','flop','actual_spr','source_run_id'))
        assert (b['actual_spr'],b['actual_pot_bb'],b['actual_effective_stack_bb'],b['actual_exact_action_line'],b['acting_seat'])==(19.55,5,97.75,LINE,1)
        aid,h=PINS[f]
        assert (p['worker_artifact'],p['original_job_id'],p['worker_sha256'],p['worker_head'])==(aid,JOBS[f],h,HEAD)
        assert (p['archive_code'],p['archive_sha256'])==('B755_R151_'+f.upper(),h) and p['pool_observed_marginal_lock_nodes']>0
        assert len(b['nl2_locked_variants'])==1 and b['nl2_locked_variants'][0]['version']=='exp_ip'
        for q in ('GTO','NL2'):
            assert p[q+'_compatible_hole_card_pairs']>=p[q+'_strict_combos']>0
        w=p['rendered_decision_hands']
        assert len(w)==len({v['hand'] for v in w})>0
        r,=[r for r in actual_counts if r['flop']==f]
        t,=[t for t in r['turns'] if t['turn']==turn]
        assert t['same_co_and_bb_by_river'][pub]==w
        for v in w:
            assert len(cards(v['hand']+pub+v['compatible_bb_hand']))==9 and v['displayed_suggestion']=='過'
            assert all('x' in v[mode]['accepted_actions'] for mode in ('gto','nl2'))
        viewer='solver_evidence/NL2_MULTIBOARD_'+p['viewer_archive_code']+'.json.gz'
        assert sha((stage/viewer).read_bytes())==p['viewer_sha256']
        paths.add(viewer)
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
    report=base/'nl2_hu_b757_integration.json'
    report.write_bytes(json_bytes(dict(rank=151,source_run=RUN,source_head=HEAD,positive_distinct_flops=count,
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
