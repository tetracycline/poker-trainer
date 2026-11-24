"""Install only B784's independently verified data and protect all other registry decisions."""
import argparse
from pathlib import Path
import subprocess
import sys

from hu_b467_river_source_gate import sha
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b719_integrate import CENTRAL
from hu_b782_rank230_mid_pairs import ROOTS
from hu_b784_collect import HEAD,RUN,SOURCES,validate
from hu_b784_rank230 import LINE,MODEL,read,write


def integrate(a):
    stage=a.stage.resolve();data=Path('data').resolve();assert stage.is_dir() and not stage.is_relative_to(data)
    reg=Path(CENTRAL[0]);baseline=read(reg);original={p:Path(p).read_bytes() for p in CENTRAL};records=baseline['records']
    assert len(records)==392 and (records[MODEL]['label'],records[MODEL]['frequency_rank'])==('APPROX',230)
    auth=validate(read(stage/'nl2_hu_b784_source_receipts.json'));summary=read(stage/'nl2_hu_b784_results.json')
    assert (summary['source_run'],summary['source_head'],summary['rank'],summary['model_id'])==(RUN,HEAD,230,MODEL)
    n=summary['positive_distinct_flops'];eligible=n==3;assert n in (0,1,2,3) and summary['cert_eligible_ranks']==([230] if eligible else [])
    gp='solver_evidence/reverified/rank230.json' if eligible else 'solver_evidence/partial/b784_rank230.json'
    mp='nl2_hu_b784_locked_medium.json' if eligible else 'solver_evidence/partial/b784_rank230_locked_medium.json'
    g=read(stage/gp);m=read(stage/mp);assert (g['rank'],g['model_id'])==(230,MODEL)
    assert n==len(g['boards'])==len(g['pins'])==len({suit_isomorphism_class(b['flop']) for b in g['boards']})
    pubs={b['public_board'] for b in g['boards']}
    assert m['schema']=='NL2_HU_B784_ORIGINAL_LOCKED_MEDIUM_V1'
    assert all(len(m[k])==n and {r['public_board'] for r in m[k].values()}==pubs for k in ('references','gto_references'))
    expected={gp,mp,'nl2_hu_b784_results.json','nl2_hu_b784_source_receipts.json'}
    workers={r['flop']:r for r in summary['workers']};assert set(workers)==set(ROOTS)
    assert {f:r['selected']['public_board'] for f,r in workers.items() if r['selected']}=={b['flop']:b['public_board'] for b in g['boards']}
    for arow in auth['artifacts']:
        code=SOURCES[arow['name']];f=arow['name'].split('-')[-1];w=workers[f]
        path='solver_evidence/NL2_'+code+'.zip';assert sha((stage/path).read_bytes())==w['sha256']==arow['digest'][7:]
        assert w['artifact']==arow['id'] and w['original_source']['root_result_sha256']==ROOTS[f]
        expected.add(path)
    for b,p in zip(g['boards'],g['pins'],strict=True):
        f=b['flop'];public=b['public_board']
        assert (p['public_board'],p['flop'],b['actual_exact_action_line'])==(public,f,LINE)
        assert (b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'],b['source_run_id'])==(0,21,90,RUN)
        assert b['restricted_flop_bet_sizes_pct']==[33] and b['original_nodes_exactly_reproduced']==14
        assert p['source_blob_head']==HEAD and p['source_original_flop']==workers[f]['original_source']
        assert p['pool_observed_marginal_lock_nodes']>0 and p['rendered_decision_hands']
        assert all(p[v+'_compatible_hole_card_pairs']>=p[v+'_strict_combos']>0 for v in ('GTO','NL2'))
        for hand in p['rendered_decision_hands']:
            assert hand['flop_class']==hand['turn_class']==hand['river_class']=='MID'
            assert hand['displayed_suggestion']=='過' and all('x' in hand[v]['accepted_actions'] for v in ('gto','nl2'))
            assert hand['joint_policy_opponent_count']>0
            deck=[(x[:2],x[2:]) for x in (hand['hand'],hand['compatible_opponent_example'])]
            assert len(set(deck[0]+deck[1]))==4
        assert p['viewer_archive_code']=='B784_R230_'+f.upper() and p['archive_code']=='B782_R230_'+f.upper()
        path='solver_evidence/NL2_MULTIBOARD_'+p['viewer_archive_code']+'.json.gz'
        assert sha((stage/path).read_bytes())==p['viewer_sha256'];expected.add(path)
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()};assert actual==expected,actual^expected
    for name in sorted(expected):
        src=stage/name;target=data/name;assert not src.is_symlink() and not target.is_symlink() and target.resolve().is_relative_to(data)
        assert not target.exists() or target.read_bytes()==src.read_bytes()
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
    if eligible:
        subprocess.run([sys.executable,'tools/hu_apply_cert_extensions.py','--out',str(reg)],check=True)
        after=read(reg);r=after['records'];assert set(r)==set(records) and all(v==r[k] for k,v in records.items() if k!=MODEL)
        assert r[MODEL]['label']=='CERT-MULTIBOARD' and r[MODEL]['proven_exact_board_count']==3
        assert {b['public_board'] for b in r[MODEL]['certified_3_to_5_exact_flop_boards']}==pubs
        assert (after['CERT_MULTIBOARD'],after['APPROX'])==(baseline['CERT_MULTIBOARD']+1,baseline['APPROX']-1)
    else:
        assert all(Path(p).read_bytes()==raw for p,raw in original.items());after=baseline
    report=data/'nl2_hu_b784_integration.json'
    write(report,dict(schema='NL2_B784_R230_INTEGRATION_V1',model_id=MODEL,source_run=RUN,source_head=HEAD,prior_records_preserved=391 if eligible else 392,
        protected_prior_certificates=baseline['CERT_MULTIBOARD'],CERT_MULTIBOARD=after['CERT_MULTIBOARD'],APPROX=after['APPROX'],positive_distinct_flops=n,
        **{k:summary[k] for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))
    paths={'data/'+v for v in expected}|{'data/'+report.name}|(set(CENTRAL) if eligible else set())
    a.paths.write_text('\n'.join(sorted(paths))+'\n');a.group.write_text('data/'+gp+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('stage','paths','group'):p.add_argument('--'+k,type=Path,required=True)
    integrate(p.parse_args())
