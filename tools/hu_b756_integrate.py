"""Apply B756's verified data in a clean candidate checkout and protect all unrelated decisions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b719_integrate import CENTRAL
from hu_b756_collect import FLOPS,HEAD,RUN,validate
from hu_b756_rank150 import EVIDENCE,LINE,MODEL,OLD_GROUP,read,write


def integrate(a):
    stage=a.stage.resolve();dest=Path('data').resolve();assert stage.is_dir() and not stage.is_relative_to(dest)
    registry=Path(CENTRAL[0]);before=read(registry);initial={p:Path(p).read_bytes() for p in CENTRAL}
    records=before['records'];original=records[MODEL]
    assert len(records)==392 and (original['label'],original['frequency_rank'])==('APPROX',150)
    summary=read(stage/'nl2_hu_b756_results.json');auth=validate(read(stage/'nl2_hu_b756_source_receipts.json'))
    assert (summary['source_run'],summary['source_head'],summary['rank'],summary['model_id'])==(RUN,HEAD,150,MODEL)
    n=summary['positive_distinct_flops'];eligible=n>=3
    assert n in (2,3,4) and summary['cert_eligible_ranks']==([150] if eligible else [])
    gp='solver_evidence/reverified/rank150.json' if eligible else 'solver_evidence/partial/b756_rank150.json'
    mp='nl2_hu_b756_locked_medium.json' if eligible else 'solver_evidence/partial/b756_rank150_locked_medium.json'
    g=read(stage/gp);m=read(stage/mp)
    previous=read(EVIDENCE/OLD_GROUP)
    assert g['boards'][:2]==previous['boards'] and g['pins'][:2]==previous['pins']
    assert g['model_id']==MODEL and g['rank']==150 and n==len(g['boards'])==len(g['pins'])
    assert n==len({suit_isomorphism_class(b['flop']) for b in g['boards']})
    public={b['public_board'] for b in g['boards']}
    assert all(len(m[policy])==n and {x['public_board'] for x in m[policy].values()}==public for policy in ('gto_references','references'))
    expected={gp,mp,'nl2_hu_b756_results.json','nl2_hu_b756_source_receipts.json'}
    assert [w['flop'] for w in summary['workers']]==list(FLOPS)
    selected={w['flop']:w['selected']['public_board'] for w in summary['workers'] if w['selected']}
    assert selected=={b['flop']:b['public_board'] for b in g['boards'][2:]}
    for b,p in zip(g['boards'],g['pins'],strict=True):
        assert b['flop']==p['flop'] and b['public_board']==p['public_board'] and b['actual_exact_action_line']==LINE
        assert (b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==(1,4.16,98.17)
        assert p['pool_observed_marginal_lock_nodes']>0 and p['rendered_decision_hands']
        for w in p['rendered_decision_hands']:
            assert w['displayed_suggestion']=='過' and all('x' in w[pol]['accepted_actions'] for pol in ('gto','nl2'))
        for pol in ('GTO','NL2'):assert p[pol+'_compatible_hole_card_pairs']>=p[pol+'_strict_combos']>0
        if b['flop'] in selected:
            f=b['flop'];assert p['source_blob_head']==HEAD and p['source_run_id']==RUN
            assert p['viewer_archive_code']=='B756_R150_'+f.upper() and p['archive_code']=='B754_R150_'+f.upper()
            viewer='solver_evidence/NL2_MULTIBOARD_'+p['viewer_archive_code']+'.json.gz'
            assert sha((stage/viewer).read_bytes())==p['viewer_sha256']
            expected.add(viewer)
    for f in FLOPS:
        for ap,sp in [('B754-R150-','B754_R150_'),('B754-root-R150-','B754_ROOT_R150_')]:
            ar,=[a for a in auth['artifacts'] if a['name']==ap+f]
            name='solver_evidence/NL2_'+sp+f.upper()+'.zip'
            assert sha((stage/name).read_bytes())==ar['digest'][7:]
            expected.add(name)
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    assert actual==expected,actual^expected
    for name in sorted(expected):
        src=stage/name;target=dest/name
        assert not src.is_symlink() and src.resolve().is_relative_to(stage) and not target.is_symlink() and target.resolve().is_relative_to(dest)
        assert not target.exists() or target.read_bytes()==src.read_bytes()
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
    if eligible:
        subprocess.run([sys.executable,'tools/hu_apply_cert_extensions.py','--out',str(registry)],check=True)
        after=read(registry);r=after['records']
        assert r.keys()==records.keys() and all(v==r[k] for k,v in records.items() if k!=MODEL)
        assert (after['CERT_MULTIBOARD'],after['APPROX'],after['TOTAL'])==(before['CERT_MULTIBOARD']+1,before['APPROX']-1,392)
        assert r[MODEL]['label']=='CERT-MULTIBOARD' and r[MODEL]['proven_exact_board_count']==n
        assert public=={b['public_board'] for b in r[MODEL]['certified_3_to_5_exact_flop_boards']}
    else:
        assert all(Path(p).read_bytes()==raw for p,raw in initial.items())
        after=before
    paths={'data/'+p for p in expected}|(set(CENTRAL) if eligible else set())
    report=dest/'nl2_hu_b756_integration.json'
    write(report,dict(schema='NL2_B756_RANK150_INTEGRATION_V1',model_id=MODEL,source_head=HEAD,source_run=RUN,
        prior_records_preserved=391 if eligible else 392,rank150_label=after['records'][MODEL]['label'],protected_prior_certificates=before['CERT_MULTIBOARD'],
        CERT_MULTIBOARD=after['CERT_MULTIBOARD'],APPROX=after['APPROX'],positive_distinct_flops=n,
        locked_named_boards=summary['locked_named_boards'],joint_halfpot_assessed=summary['joint_halfpot_assessed'],nonpolarized_candidates=summary['nonpolarized_candidates']))
    a.paths.write_text('\n'.join(sorted(paths|{'data/'+report.name}))+'\n')
    a.group.write_text('data/'+gp+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for opt in ('stage','paths','group'):p.add_argument('--'+opt,type=Path,required=True)
    integrate(p.parse_args())
