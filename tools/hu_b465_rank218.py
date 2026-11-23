"""Replay eight original CFR artifacts and certify rank 218 for its actual bet sizes."""
import argparse
import json
import pathlib
import subprocess

from hu_b427_rank216218_three_true_sources_promote import legacy_b2_check, verify_pin
from hu_b433_rank216218_four_source_promote import (
    B412, B421, B431, FLOPS, LINE, TARGET, TRIAGE, attach_source_paths, pair_pin, read, sha,
)
from hu_b421_rank216_218_true_co_ip_pairs import check as check_full_source
from hu_b431_rank216218_one_new_texture_nl2_ip_pair import check as check_low_flop
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import strict_medium_evidence
from hu_cert_lock_medium_audit import audit
from hu_cert_lock_medium_coverage_matrix import create

DATA = pathlib.Path('data')
BASE = DATA / 'nl2_hu_multiboard_status_v51_b453_rank32.json'
PROOF = DATA / 'nl2_hu_b465_rank218_four_board_gate.json'
STATUS = DATA / 'nl2_hu_multiboard_status_v53_b465_rank218.json'
MATRIX = DATA / 'nl2_hu_cert_lock_medium_matrix_v53_b465.json'
SCHEMA = 'NL2_HU_392_MULTIBOARD_CERT_STATUS_V53_B465_R218'
ID = TARGET[218]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify_originals(downloads):
    subprocess.run(['node', 'tools/hu_b465_model_bet_sizes.cjs'], check=True)
    model = read(BASE)['records'][ID]
    assert (model['solver_profile'], model['frequency_rank'], model['assumed_model_node_spr']) == ('CO_BB', 218, 4.057)
    triage = next(r for r in read(TRIAGE)['source_blind_selected_ten'] if r['model_id'] == ID)
    historical, = triage['strictly_measured_pairs']
    boards, pins = [], []
    for flop, directory, proof_path in zip(FLOPS, ('historical', 'td', 'js', 'low'), (None, B412, B421, B431)):
        roots = [downloads / (directory + suffix) for suffix in ('-gto', '-exp')]
        if proof_path is None:
            gto_sha, exp_sha = historical['gto_source_sha256'], historical['nl2_hero_lock_sha256']
            sources = [legacy_b2_check(root, flop, version, digest) for root, version, digest in
                       zip(roots, ('gto', 'exp_ip'), (gto_sha, exp_sha))]
            public_board = historical['exact_public_board']
            exp_case, = sources[1]['real_cases']
            pin = dict(flop=flop, turn=public_board[6:8], public_board=public_board,
                       GTO_run_id=historical['gto_source_run_id'], NL2_hero_IP_run_id=historical['nl2_hero_lock_run_id'],
                       original_GTO_source_sha256=gto_sha, NL2_IP_source_sha256=exp_sha,
                       GTO_legal_40_70_hero_IP_combos=historical['strict_legal_combo_count'],
                       NL2_IP_legal_40_70_hero_IP_combos=exp_case['actor_IP_target_nodes'][public_board]['strict_40_70_IP_hero_combos'],
                       actual_spr=historical['actual_spr'])
        else:
            previous = read(proof_path)
            row = next(r for r in previous['positive_40_70_named_river_pairs_by_rank']['218'] if r['flop'] == flop)
            pin = pair_pin(row, proof_path)
            sources = []
            for root, version, field, run in zip(roots, ('gto', 'exp_ip'), ('original_GTO', 'actual_partial_NL2_IP'),
                                                 (pin['GTO_run_id'], pin['NL2_hero_IP_run_id'])):
                source = check_low_flop(root, version, run) if directory == 'low' else check_full_source(root, flop, version, None)
                recorded = previous['source_evidence'][0][field]
                for key in ('manifest_sha256', 'root_original_Rust_SHA256'):
                    assert source[key] == recorded[key], (flop, version, key)
                sources.append(source)
        original, locked = (attach_source_paths(source) for source in sources)
        joint = {}
        for root, source, version, source_sha in zip(roots, sources, ('gto', 'exp_ip'),
                                                      (pin['original_GTO_source_sha256'],pin['NL2_IP_source_sha256'])):
            case, = (c for c in source['real_cases'] if c['source_sha256'] == source_sha)
            postflop = root / 'solver/postflop'
            sub_path = postflop / case['source_path']
            sub = read(sub_path)
            root_game = read(postflop / source['manifest']['file_flop'])
            for stage in (root_game, sub):
                assert 0 <= stage['info']['gto_expl_pct'] <= .5
                if version == 'exp_ip':
                    assert 0 <= stage['info']['hero_gap_pct'] <= .5
            node, = (n for n in sub['nodes'] if (n['board'], n['line'], n['player']) == (pin['public_board'], LINE, 1))
            masks, _ = game_reach(root_game, sub)
            actor_reach = masks['|'.join((pin['public_board'], LINE, '1'))]
            compatible = compatible_node_reach(root_game, sub, node, actor_reach)
            assert compatible['count'] > 0 and compatible['compatible_hole_card_pairs'] > 0
            joint[version] = {k: compatible[k] for k in ('count', 'compatible_opponent_combos', 'compatible_hole_card_pairs')}
            if version == 'gto':
                medium = strict_medium_evidence(node, sub, compatible['mask'])
            job = read(sub_path.with_suffix('.job.json'))
            assert (job['rake_rate'], job['rake_cap']) == (0.05, 1000)
            if version == 'exp_ip':
                assert job['hero'] == 1 and job['locks']
            else:
                assert job.get('hero') is None and not job.get('locks')
        board, proof = verify_pin(model, pin, original, locked, *roots, 218)
        board.update(strict_full_street_combo_reachable=joint['gto']['count'],
                     medium_50pct_eligible_combos=medium['eligible'],
                     b50_nonpolarized_relative_equity_research_candidate=medium['candidate'])
        proof['GTO_strict_combos'] = joint['gto']['count']
        proof['NL2_strict_combos'] = joint['exp_ip']['count']
        proof['compatible_reach'] = joint
        assert board['actual_pot_bb'] == 22 and board['actual_effective_stack_bb'] == 89.25
        assert board['actual_exact_action_line'] == LINE
        boards.append(board)
        pins.append(proof)
    assert all(len(set(flop[1::2])) == 3 for flop in FLOPS)
    return dict(rank=218, model_id=ID, flops=list(FLOPS), actor='CO_IP', spot='CO_BB', line=LINE,
                trainer_scope=dict(enabled_texture_handclass_cells=['mono:3'], exact_named_flop_suit_texture='RAINBOW',
                                   directly_verified_trainer_cells=[], scope='NAMED_ACTION_LINE_EXAMPLES_ONLY'),
                model_flop_bet_fraction=0.5, model_turn_bet_fraction=0.5, boards=boards, pins=pins,
                excluded_model=dict(rank=216, model_id=TARGET[216], model_flop_bet_fraction=0.333,
                                    model_turn_bet_fraction=0.75, reason='EXACT_BET_SIZES_DIFFER'),
                scope='NAMED_BOARDS_AND_PER_VERSION_STRICT_HERO_COMBOS_ONLY')


def latest_parent():
    # V52 may be absent if rank45 is still being solved or had zero reach.
    candidates = list(DATA.glob('nl2_hu_multiboard_status_v52_b463*.json'))
    assert len(candidates) <= 1
    if not candidates:
        return BASE
    registry = read(candidates[0])
    assert registry['records']['ln-iso-iso_t_model-1x553s3']['label'] == 'CERT-MULTIBOARD'
    return candidates[0]


def update_source_references(boards):
    crosswalk_path = DATA / 'nl2_hu_model_history_crosswalk.json'
    references_path = DATA / 'nl2_hu_model_source_references.json'
    crosswalk, references = read(crosswalk_path), read(references_path)
    examples = []
    for board in boards:
        lock, = board['nl2_locked_variants']
        examples.append(dict(flop=board['flop'], turn=board['turn'], public_board=board['public_board'],
                             exact_solver_node_line=LINE, acting_seat=1, source_run_id=board['source_run_id'],
                             source_sha256=board['source_sha256'], nl2_ip_run_id=lock['run_id'],
                             nl2_ip_sha256=lock['sha256'], strict_full_street_reachable_combos=board['strict_full_street_combo_reachable']))
    # Preserve historical exploratory references and their original count semantics.
    crosswalk['records'][ID].update(board_specific_certification_status='CERT_MULTIBOARD',
                                     certified_named_board_examples=examples)
    references['items'][ID]['certified_named_board_references'] = examples
    save(crosswalk_path, crosswalk)
    save(references_path, references)


def promote(base_path, proof):
    registry = read(base_path)
    previous_audit = audit(registry)
    record = registry['records'][ID]
    assert record['label'] == 'APPROX' and registry['records'][TARGET[216]]['label'] == 'APPROX'
    assert registry['records']['ln-opfr-t_model-qx9t0u']['label'] == 'CERT-MULTIBOARD'
    assert [(b['flop'], b['source_sha256']) for b in proof['boards']] == [
        (p['flop'], p['original_GTO_SHA256']) for p in proof['pins']]
    record.update(label='CERT-MULTIBOARD', proven_exact_board_count=len(proof['boards']),
                  certified_3_to_5_exact_flop_boards=proof['boards'], blocked_reason=None,
                  source_blind_expansion_preregistered=True, source_blind_expansion_rank=218,
                  source_credibility='ORIGINAL_GTO_AND_NL2_IP_40_70_EXACT_MODEL_BET_SIZES')
    registry.update(schema=SCHEMA, CERT_MULTIBOARD=registry['CERT_MULTIBOARD']+1,
                    APPROX=registry['APPROX']-1, supplementary_cert_count=registry['supplementary_cert_count']+1,
                    parent_B465_registry_sha256=sha(base_path), source_blind_expansion_ranks=sorted(
                        set(registry['source_blind_expansion_ranks']) | {218}))
    registry['B465_rank218_four_original_sources'] = {k:v for k,v in proof.items() if k != 'boards'}
    checked = audit(registry)
    for field in ('named_board_proofs', 'paired_hero_locked_source_variants'):
        assert checked['aggregate'][field] == previous_audit['aggregate'][field] + 4
    matrix = create(registry)
    save(STATUS, registry)
    matrix['source_status_sha256'] = sha(STATUS)
    matrix['schema'] = 'NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V53_B465'
    save(MATRIX, matrix)
    update_source_references(proof['boards'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', type=pathlib.Path, required=True)
    parser.add_argument('--write-proof', action='store_true')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    result = verify_originals(args.downloads)
    if args.write_proof:
        save(PROOF, result)
    else:
        assert read(PROOF) == result, 'Original CFR replay disagrees with committed evidence'
    if args.publish:
        promote(latest_parent(), result)
