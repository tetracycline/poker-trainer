"""Promote only rank255 from the four source-checked GTO + NL2 board pairs."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from hu_b580_rank27_rivers import suit_isomorphism_class

MODEL='ln-3bp-3c_r_model-13bw264'
CENTRAL=['data/nl2_hu_multiboard_status_current.json','data/nl2_hu_verified_extensions.json',
         'data/nl2_hu_model_history_crosswalk.json','data/nl2_hu_model_source_references.json']
BOARDS={'Ks7h2d':'2d7hKs9d5s','KsQh4d':'4dQhKsTc3h','Qs8h4d':'4d8hQsTc2c','Jh8d3c':'3c8dJhQs2c'}
ORIG={'Ks7h2d','KsQh4d'}
read=lambda p:json.loads(Path(p).read_bytes())
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def integrate(a):
    dest=Path('data').resolve();stage=a.stage.resolve()
    assert stage.is_dir() and not stage.is_relative_to(dest)
    initial=Path(CENTRAL[0]).read_bytes();before=json.loads(initial);records=before['records']
    protected={k:v for k,v in records.items() if v['label']=='CERT-MULTIBOARD'}
    assert (len(records),len(protected),before['CERT_MULTIBOARD'],before['APPROX'])==(392,151,151,241)
    assert (records[MODEL]['frequency_rank'],records[MODEL]['label'],records[MODEL]['solver_profile'],records[MODEL]['assumed_model_node_spr'])==(255,'APPROX','BB3_BTN',2.445)
    gpath='solver_evidence/reverified/rank255.json';g=read(stage/gpath)
    assert (g['rank'],g['model_id'])==(255,MODEL) and len(g['boards'])==len(g['pins'])==4
    assert {b['flop']:b['public_board'] for b in g['boards']}==BOARDS and len({suit_isomorphism_class(f) for f in BOARDS})==4
    medium=read(stage/'nl2_hu_b719_locked_medium.json')
    assert len(medium['references'])==len(medium['gto_references'])==4
    old={p['flop']:p for p in read(dest/'solver_evidence/reverified/rank256.json')['pins']}
    archives={};viewers=set()
    for b,p in zip(g['boards'],g['pins'],strict=True):
        f=b['flop'];public=BOARDS[f]
        assert all(b[k]==p[k] for k in ('flop','public_board','turn','river','actual_spr'))
        assert b['turn']+b['river']==public[-4:] and b['public_board']==public
        assert (b['actual_exact_action_line'],b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==('b33 c/x x/x',1,34.04,83.23)
        assert abs(b['actual_spr']-83.23/34.04)<1e-6 and len(b['nl2_locked_variants'])==1 and b['nl2_locked_variants'][0]['version']=='exp_ip'
        assert p['pool_observed_marginal_lock_nodes']>0
        for pol in ('GTO','NL2'): assert p[pol+'_compatible_hole_card_pairs']>=p[pol+'_strict_combos']>0
        hands=p['rendered_decision_hands']; assert hands and len({w['hand'] for w in hands})==len(hands)
        for h in hands:
            assert h['displayed_suggestion']=='過'
            for k in ('gto','nl2'):
                v=h[k];assert 'x' in v['accepted_actions'] and v['accepted_mask']&(1<<v['action_order'].index('x'))
        for prefix in ('','locked_original_'):
            rel='solver_evidence/NL2_'+p[prefix+'archive_code']+'.zip';digest=p[prefix+'archive_sha256']
            assert sha((stage/rel).read_bytes())==digest
            archives[rel]=digest
        if f in ORIG:
            for k in ('original_GTO_SHA256','actual_NL2_SHA256','archive_sha256','locked_original_archive_sha256'):
                assert p[k]==old[f][k], ('Original source differs',f,k)
        view='solver_evidence/NL2_MULTIBOARD_'+p['viewer_archive_code']+'.json.gz'
        assert sha((stage/view).read_bytes())==p['viewer_sha256'];viewers.add(view)
    assert len(viewers)==4 and len(archives)==6
    selected={gpath}|viewers|set(archives)|{'solver_evidence/NL2_B719_R255_9C6C3H.zip'}
    selected|={'nl2_hu_b719_'+k+'.json' for k in ('summary','results','locked_medium')}
    selected|={'solver_evidence/partial/b719_'+k+'.json' for k in ('auth_receipt','rank255_routes','qs8h4d_proof','jh8d3c_proof','9c6c3h_proof')}
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    assert len(selected)==20 and actual==selected,('unexpected evidence paths',actual^selected)
    for rel in sorted(selected):
        p=stage/rel;assert not p.is_symlink() and p.resolve().is_relative_to(stage)
        out=dest/rel;assert not out.exists() or out.read_bytes()==p.read_bytes(),('Refuse to overwrite evidence',rel)
        out.parent.mkdir(exist_ok=True,parents=True);out.write_bytes(p.read_bytes())
    subprocess.run([sys.executable,'tools/hu_apply_cert_extensions.py','--out',CENTRAL[0]],check=True)
    after=read(CENTRAL[0]);rr=after['records']
    assert rr.keys()==records.keys() and all(rr[k]==v for k,v in records.items() if k!=MODEL)
    assert all(rr[k]==v for k,v in protected.items()) and (after['CERT_MULTIBOARD'],after['APPROX'],after['TOTAL'])==(152,240,392)
    assert (rr[MODEL]['label'],rr[MODEL]['proven_exact_board_count'])==('CERT-MULTIBOARD',4)
    assert {b['public_board'] for b in rr[MODEL]['certified_3_to_5_exact_flop_boards']}==set(BOARDS.values())
    report='data/nl2_hu_b719_integration.json'
    Path(report).write_text(json.dumps(dict(schema='NL2_B719_RANK255_FOUR_ORIGINAL_FLOPS_V1',model_id=MODEL,rank=255,
        previous_registry_sha256=sha(initial),published_registry_sha256=sha(Path(CENTRAL[0]).read_bytes()),unchanged_other_records=391,
        preserved_certificates=151,reverified_old_flops=2,new_positive_flops=2,distinct_certified_flops=4,all_four_named_boards_lock_and_halfpot_checked=True,
        CERT_MULTIBOARD=152,APPROX=240,TOTAL=392),indent=2,sort_keys=True)+'\n')
    a.paths.write_text('\n'.join(sorted(set(CENTRAL)|{report}|{'data/'+r for r in selected}))+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--paths',type=Path,required=True)
    integrate(p.parse_args())
