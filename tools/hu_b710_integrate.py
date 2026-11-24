"""Publish one river decision after proving five original, distinct flops."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from hu_b580_rank27_rivers import suit_isomorphism_class

MODEL = 'ln-ipfr-r_model-bqgbuq'
CENTRAL = ['data/nl2_hu_multiboard_status_current.json', 'data/nl2_hu_verified_extensions.json',
           'data/nl2_hu_model_history_crosswalk.json', 'data/nl2_hu_model_source_references.json']
OLD = {'Qs7h3d': ('Qh','Ac'), 'Jc6d2s': ('Jh','Ac')}
NEW = {'Td8c3h': ('8h','4d'), 'Jh7d4c': ('7s','2c'), 'Qc9s5d': ('9d','6s')}


def read(path): return json.loads(Path(path).read_bytes())
def digest(data): return hashlib.sha256(data).hexdigest()


def integrate(args):
    stage = args.stage.resolve(); assert stage.is_dir() and stage != Path('data').resolve()
    before_bytes=Path(CENTRAL[0]).read_bytes();before=json.loads(before_bytes)
    assert (before['CERT_MULTIBOARD'],before['APPROX'],before['TOTAL']) == (150,242,392)
    protected={k:v for k,v in before['records'].items() if v['label']=='CERT-MULTIBOARD'}
    assert len(protected)==150 and before['records'][MODEL]['label']=='APPROX'
    summary=read(stage/'nl2_hu_b710_summary.json')
    for key,value in dict(rank=89, model_id=MODEL, prior_positive_flops=2,new_positive_flops=3,
            distinct_positive_flops=5,certified_eligible=True,native_actor_locked_turn_jobs=3,
            native_locked_river_nodes=48,actor_locked_joint_boards=48,half_pot_assessed_joint_boards=48,
            half_pot_nonpolarized_candidates=22, selected_combined_actor_locked_boards=5,
            selected_combined_half_pot_assessed_boards=5,native_solves_repeated=0).items():
        assert summary[key]==value,(key,summary[key],value)
    rel='solver_evidence/reverified/rank89.json';group=read(stage/rel)
    assert (group['rank'],group['model_id'],len(group['boards']),len(group['pins']))==(89,MODEL,5,5)
    assert {b['flop'] for b in group['boards']}==OLD.keys()|NEW.keys()
    assert len({suit_isomorphism_class(b['flop']) for b in group['boards']})==5
    prior=read('data/solver_evidence/partial/b702_rank89.json')
    for key in ('boards','pins'):
        assert [b for b in group[key] if b['flop'] in OLD]==prior[key], 'Retained partial board or pin was rewritten'
    for board,pin in zip(group['boards'],group['pins'],strict=True):
        flop=board['flop'];turn,river=(OLD|NEW)[flop]; public=board['public_board']
        assert all(board[k]==pin[k] for k in ('flop','turn','river','public_board','actual_spr'))
        assert (board['turn'],board['river'])==(turn,river) and len(public)==10 and public[6:]==turn+river
        cards=lambda x: {x[i:i+2] for i in range(0,len(x),2)}
        assert cards(flop)==cards(public[:6]) and len(cards(public))==5
        assert (board['actual_exact_action_line'],board['acting_seat'],board['actual_pot_bb'],board['actual_effective_stack_bb'])==('x x/b50 c/x',1,11,94.75)
        assert abs(board['actual_spr']-94.75/11)<.00001
        assert pin['GTO_compatible_hole_card_pairs']>=pin['GTO_strict_combos']>0
        assert pin['NL2_compatible_hole_card_pairs']>=pin['NL2_strict_combos']>0
        assert pin['rendered_decision_hands'] and pin['pool_observed_marginal_lock_nodes']>0
        assert len(board['nl2_locked_variants'])==1 and board['nl2_locked_variants'][0]['version']=='exp_ip'
        archive=stage/('solver_evidence/NL2_'+pin['archive_code']+'.zip')
        assert digest(archive.read_bytes())==pin['archive_sha256']
    expected={'nl2_hu_b710_'+s+'.json' for s in ('workers','results','summary','registry_guard','locked_medium')}
    expected|={rel}|{'solver_evidence/partial/b710_'+s+'.json' for s in ('rank89','rank89_locked_medium','all_native_node_observations','auth_receipt')}
    for flop in NEW:
        name=flop.upper();expected|={'solver_evidence/NL2_B709_R89_'+name+'.zip','solver_evidence/NL2_MULTIBOARD_B710_R89_'+name+'.json.gz','solver_evidence/partial/b710_R89_'+name+'_proof.json'}
    assert len(expected)==19
    prior_pins=read(stage/'solver_evidence/partial/b710_auth_receipt.json')['prior_stage_original_replay_sha256']
    assert len(prior_pins)==34 and not expected.intersection(prior_pins)
    files={p.relative_to(stage).as_posix():p for p in stage.rglob('*') if p.is_file()}
    assert len(files)==53 and files.keys()==expected|prior_pins.keys()
    for key,path in files.items():
        assert not path.is_symlink() and path.resolve().is_relative_to(stage) and '..' not in Path(key).parts
        target=Path('data')/key; raw=path.read_bytes()
        if key not in expected:
            assert digest(raw)==prior_pins[key] and target.read_bytes()==raw, ('Retained B702 file differs', key)
            continue
        assert not target.exists() or target.read_bytes()==raw, ('Refuse to replace different evidence',key)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    subprocess.run([sys.executable,'tools/hu_apply_cert_extensions.py','--out',CENTRAL[0]],check=True)
    after=read(CENTRAL[0]); assert after['records'].keys()==before['records'].keys()
    assert all(after['records'][k]==v for k,v in before['records'].items() if k!=MODEL)
    assert all(after['records'][k]==v for k,v in protected.items())
    assert (after['CERT_MULTIBOARD'],after['APPROX'],after['TOTAL'])==(151,241,392)
    target=after['records'][MODEL];assert target['label']=='CERT-MULTIBOARD' and target['proven_exact_board_count']==5
    assert {b['public_board'] for b in target['certified_3_to_5_exact_flop_boards']}=={b['public_board'] for b in group['boards']}
    report='data/nl2_hu_b710_integration.json'
    Path(report).write_text(json.dumps(dict(schema='NL2_HU_B710_RANK89_INTEGRATION_V1',rank=89,
        before_registry_sha256=digest(before_bytes),after_registry_sha256=digest(Path(CENTRAL[0]).read_bytes()),
        unchanged_other_records=391,protected_certificates=150,new_certificates=1,distinct_certified_flops=5,
        retained_published_files=34,new_evidence_files=19,native_solves_repeated=0,
        new_joint_locked_public_boards=48,new_medium_assessments=48,new_nonpolarized_candidates=22,
        CERT_MULTIBOARD=151,APPROX=241,TOTAL=392),sort_keys=True,indent=2)+'\n')
    args.paths.write_text('\n'.join(sorted({'data/'+p for p in expected}|set(CENTRAL)|{report}))+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('stage','paths'):p.add_argument('--'+key,type=Path,required=True)
    integrate(p.parse_args())
