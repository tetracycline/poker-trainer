#!/usr/bin/env python3
"""B281 source-audited rank71 exact GTO zero-actor/reach registry:
six immutable genuine Rust 100bb original GTO flops with zero target
BB-OOP b50 c/x b50 c/ strict legal combos. NEVER generalize to
different turn, changed solver tree or different betting line. Preserve
rank71 two original true GTO+NL2 actor-paired flops unchanged.
"""
import collections,gzip,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit
D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
OLD=D/'nl2_hu_b278_v41_238_approx_rank46_and_71_oneflop_true_sourceblind.json'
HISTORY=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
OUT=D/'nl2_hu_b281_v41_rank71_sha_zero_legal_actor_flop_dedup.json'
MD=DOC/'NL2_HU_B281_RANK71_SIX_SHA_PINNED_ZERO_ACTOR_FLOP_DEDUP.md'
REJECTED=[
  ('B156_R71_KS7H2D_GTO','Ks7h2d','9d',44860317844),
  ('B173_R71_9S6H3D_GTO','9s6h3d','Ts',44866269911),
  ('B180_R71_7S7H2D_GTO','7s7h2d','3s',44872996340),
  ('B184_R71_8S8H3D_GTO','8s8h3d','5s',44873071277),
  ('B216_R71_9S8H4D_GTO','9s8h4d','Ah',44884042851),
  ('B222_R71_2S4H6D_GTO','2s4h6d','Kh',44890080840),
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
    s=load(STATUS);prior=load(OLD);historical=load(HISTORY)
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(154,238,0,392)
    assert prior['current_V41_status_sha256']==sha(STATUS)
    assert [z['rank'] for z in prior['one_flop_short_sourceblind_priorities']]==[46,71]
    assert s['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    rank71=next(x for x in historical['rows'] if x['rank']==71)
    assert rank71['hero_seat']==0 and rank71['model_id']=='ln-iso-lmp_r_model-vlgh2t'
    assert rank71['distinct_GTO_plus_NL2_hero_flops']==['4s4h2d','7s5h3d']
    assert all(x['exact_line']=='b50 c/x b50 c/' and x['actor']==0 and
       x['true_NL2_actor_locked'] and x['strict_legal_combos']>0
       for x in rank71['exact_authentic_gto_source_proofs'])
    rejected=[]
    for batch,flop,turn,run in REJECTED:
        indexpath=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.index.json'
        archive=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.json.gz'
        assert indexpath.is_file() and archive.is_file(),batch
        idx=load(indexpath)
        assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
        assert idx['batch']==batch and idx['run_id']==run
        assert (idx['gto_cases'],idx['locked_cases'],idx['verified_cases'])==(1,0,1)
        assert idx['target_line']=='b50 c/x b50 c/' and idx['turn']==turn
        assert idx['frozen_high_frequency_rank']==71
        assert idx['exact_target_actor_OOP_river_nodes']==0
        assert idx['exact_target_actor_OOP_strict_combos']==0
        assert idx['no_generic_model_certification'] and idx['immediate_CERT_upgrades']==0
        assert len(idx['source_sha256'])==len(idx['gzip_sha256'])==64
        assert idx['gzip_sha256']==sha(archive)
        assert idx['source_sha256']==hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest()
        rejected.append(dict(batch=batch,flop=flop,turn=turn,source_run_id=run,
           exact_line='b50 c/x b50 c/',actor=0,
           strict_legal_hero_combos=0,authentic_gto_sources=1,
           source_sha256=idx['source_sha256'],gzip_sha256=idx['gzip_sha256'],
           constrained_scope='EXACT_PUBLIC_FLOP_TURN_LINE_100BB_SOURCE_ONLY',
           no_false_boardwide_or_all_turn_rejection=True,
           may_research_different_prespecified_turn_tree=True))
    assert len(rejected)==6 and len({x['flop'] for x in rejected})==6
    assert len({x['source_sha256'] for x in rejected})==6
    assert set(rank71['distinct_GTO_plus_NL2_hero_flops']).isdisjoint({x['flop'] for x in rejected})
    audit_result=audit(s)
    assert (audit_result['cert_multiboard'],audit_result['approx'],audit_result['EST'])==(154,238,0)
    assert (audit_result['aggregate']['named_board_proofs'],
         audit_result['aggregate']['paired_hero_locked_source_variants'],
         audit_result['aggregate']['board_examples_with_b50_candidate'])==(590,682,134)
    assert audit_result['not_generalized_handclass_GTO'] and audit_result['not_actual_NL2_earnings']
    duplicate=next(x for x in rejected if x['batch'].startswith('B173_'))
    assert (duplicate['flop'],duplicate['turn'],duplicate['strict_legal_hero_combos'])==('9s6h3d','Ts',0)
    output=dict(schema='NL2_HU_B281_V41_R71_GENUINE_GTO_ZERO_STRICT_ACTOR_SHA_DEDUP_V1',
       V41_status_sha256=sha(STATUS),parent_B278_sourceblind_sha256=sha(OLD),
       CERT_MULTIBOARD=154,APPROX=238,EST=0,TOTAL=392,
       prior_rank71_two_genuine_GTO_plus_NL2_hero_pair_flops=rank71['distinct_GTO_plus_NL2_hero_flops'],
       exact_rank71_OOP_river_negative_100bb_GTO_sources=rejected,
       zero_legal_actor_known_exact_flop_turn_pairs=len(rejected),
       queued_B276_same_9s6h3d_Ts_exact_source_was_previously_tested_by_B173=True,
       queued_B274_and_B275_different_flops_are_not_proven_by_this_register=True,
       all_source_SHA_bytes_independently_rechecked=True,
       no_automatic_CERT_upgrade=True,
       no_extrapolation_to_different_turn_or_tree=True,
       no_unknown_NL2_hole_card_rates_fabricated=True,
       all_existing_590_CERT_named_boards_and_682_lock_source_unchanged=True,
       exact_b50_nonpolarized_research_candidates=134,
       PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    lines=['# B281 rank71: six original 100bb exact GTO SHA-confirmed zero legal OOP sources','',
      '**154 CERT / 238 APPROX / 0 EST** unchanged. Two real positive paired rank71 flops: 4s4h2d, 7s5h3d.',
      'All six sources below are genuine 100bb Rust original GTO, SHA checked end-to-end, with ZERO '
      'strictly reachable actor BB-OOP node combos on EXACT public flop/turn and b50 c/x b50 c/ line.',
      'This is NOT a global rejection for all turns, actor positions, game trees or flop textures.',
      '',
      '| Batch | Public flop / turn | Original GTO run | Strict actor combos |',
      '|---|---|---:|---:|']
    for x in rejected:
        lines.append(f"|{x['batch']}|{x['flop']} / {x['turn']}|{x['source_run_id']}|0|")
    lines.extend(['',
      '**Dedup alert:** B276 9s6h3d/Ts matches the earlier B173 original-GTO zero-actor public board; '
      'do not count B276 simply because it is a distinct Actions run. B274 KsJh4d and B275 8s7h5d '
      'are separate candidate flops and must pass their own exact SHA/40-70 actor/SPR proof.',
      'Unknown villain NL2 action frequencies are not observed per-private-card conditionals. '
      'All existing 590 named board and 2475 HU Actions must PASS before commit. '
      'PR #2 Draft, NEVER MERGE.'])
    MD.write_text('\n'.join(lines)+'\n')
    print('PASS B281',json.dumps(dict(zero_sha_verified=len(rejected),
         duplicated_B276_exact_B173=True,cert=154,approx=238),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
