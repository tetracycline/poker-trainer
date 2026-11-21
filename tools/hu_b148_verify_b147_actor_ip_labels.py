#!/usr/bin/env python3
"""Independently correct metadata from B147 source-only GTO archive, not GTO data.

B147 original job had carried over rank71 / OOP names from B143.
The raw Rust GTO and sequential reachability proof MUST be inspected before
creating a SHA-bound rank46 actor-IP source label. The ORIGINAL source+index
remain byte-for-byte untouched for auditability.

Never promote a model here. NL2 partial EXP_IP hero lock is independently
required, as is source-blind 3-flop certification and complete navigation.
"""
import gzip,hashlib,json,pathlib

ROOT=pathlib.Path('data')
GZ=ROOT/'solver_evidence/NL2_MULTIBOARD_B147_R46_AS9H2D_GTO.json.gz'
INDEX=ROOT/'solver_evidence/NL2_MULTIBOARD_B147_R46_AS9H2D_GTO.index.json'
OLD_PIN=ROOT/'nl2_hu_b147_rank46_lmp_low64_gto_parent_pin.json'
FREEZE=ROOT/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
NEW_PIN=ROOT/'nl2_hu_b148_rank46_as9h2d_gto_parent_pin.json'
NEW_INDEX=ROOT/'solver_evidence/NL2_MULTIBOARD_B148_R46_AS9H2D_GTO_VERIFIED.index.json'
DOC=pathlib.Path('docs/NL2_HU_B148_RANK46_B147_ORIGINAL_GTO_IP_LABEL_AUDIT.md')
FLOP='As9h2d'; LINE='x b50 c/x'; ACTOR=1; RANK=46
MID='ln-iso-lmp_t_model-17z0wyl'

def read(path):return json.loads(path.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    assert all(p.is_file() for p in (GZ,INDEX,OLD_PIN,FREEZE))
    old=read(INDEX)
    pin=read(OLD_PIN)
    freeze=read(FREEZE)
    assert freeze['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    frozen=next(r for r in freeze['rows'] if r['rank']==RANK)
    assert (frozen['model_id'],frozen['spot'],frozen['street'])==(MID,'LMP_CO_BB',1)
    assert frozen['missing_real_hero_flops_to_3']==2
    assert set(frozen['hero_locked_flops'])=={'8s8h3d'}
    assert '9s6h3d' in frozen['matched_real_gto_flops']
    raw=gzip.decompress(GZ.read_bytes())
    evidence=json.loads(raw)
    assert old['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert old['batch']=='B147_R46_AS9H2D_GTO'
    assert old['source_sha256']==sha(raw) and old['gzip_sha256']==sha(GZ.read_bytes())
    assert (old['gto_cases'],old['locked_cases'],old['verified_cases'])==(1,0,1)
    assert old['actual_spot_flop_version_jobs']==1
    assert old['generic_model_certification'] is False or old['generic_model_certification']==0
    assert old['target_line']==LINE
    # EXACT issue from the B143 -> B147 workflow rewrite, never silently
    # reclassify a different case. Preserve the erroneous upstream labels.
    assert old['frozen_high_frequency_rank']==71
    assert 'exact_target_actor_OOP_gto_river_nodes' in old
    assert (pin['schema'],pin['source_run_id'])==(
        'NL2_HU_B147_RANK46_LMP_AS9H2D_GTO_PARENT_PIN_V1',old['run_id'])
    assert pin['target_rank']==71 and pin['model_id']==MID
    assert (pin['spot'],pin['flop'],pin['flop_line'],pin['turn_line'])==(
        'LMP_CO_BB',FLOP,'x b50 c','x x')
    assert pin['observed_preflop_ranges'] is False and pin['assumed_limped_169class']
    assert evidence['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert evidence['source_run_id']==old['run_id'] and not evidence['errors']
    assert (evidence['exact_board_gto_sources'],
            evidence['imputed_pool_locked_sources'],
            evidence['new_authentic_board_cases'])==(1,0,1)
    assert len(evidence['artifacts'])==1
    a=evidence['artifacts'][0]
    assert (a['spot'],a['version'],a['flop'])==('LMP_CO_BB','gto',FLOP)
    assert not a['errors'] and len(a['cases'])==1
    c=a['cases'][0]
    assert c['flop_line']=='x b50 c' and c['turn']==pin['turn']
    assert c['gto_exploitability_pct']<=.5
    strict=[n for n in c['nodes'] if n['acting_seat']==ACTOR
            and n['exact_node_line']==LINE
            and n['strictly_reachable_combos']>0]
    strict_combos=sum(n['strictly_reachable_combos'] for n in strict)
    assert len(strict)==old['exact_target_actor_OOP_gto_river_nodes']
    assert strict_combos==old['exact_target_actor_OOP_strict_combos']
    assert pin['target_exact_actor_OOP_gto_river_nodes']==len(strict)
    assert pin['target_exact_actor_OOP_strict_combos']==strict_combos
    assert old['original_parent_GTO_root_SHA256']==pin['original_gto_root_sha256']
    assert old['original_parent_GTO_job_SHA256']==pin['original_gto_job_sha256']
    assert old['original_parent_GTO_manifest_SHA256']==pin['original_gto_manifest_sha256']
    assert pin['original_full_100bb_lmp_gto_not_recomputed']
    assert pin['source_gto_job_id'] is None
    corrected=dict(pin)
    corrected['schema']='NL2_HU_B148_RANK46_LMP_AS9H2D_CORRECTED_GTO_PARENT_PIN_V1'
    corrected['target_rank']=RANK
    corrected.pop('target_exact_actor_OOP_gto_river_nodes')
    corrected.pop('target_exact_actor_OOP_strict_combos')
    corrected.update(
        acting_seat=ACTOR,acting_position='CO_IP',
        target_exact_actor_IP_turn_nodes=len(strict),
        target_exact_actor_IP_turn_strict_combos=strict_combos,
        original_upstream_pin_path=str(OLD_PIN),
        original_upstream_pin_sha256=sha(OLD_PIN.read_bytes()),
        original_upstream_wrong_rank_label=71,
        original_upstream_wrong_actor_suffix='OOP_gto_river',
        original_gto_evidence_sha256=sha(raw),
        original_gto_gzip_sha256=sha(GZ.read_bytes()),
        no_unobserved_NL2_private_card_frequency_claim=True,
        no_generic_model_certification=True,
        rank46_stays_APPROX_until_genuine_actor_IP_NL2_and_full_3_flop_gate=True)
    corrected_idx=dict(old)
    corrected_idx.pop('exact_target_actor_OOP_gto_river_nodes')
    corrected_idx.pop('exact_target_actor_OOP_strict_combos')
    corrected_idx.update(
        schema='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1',
        batch='B148_R46_AS9H2D_GTO_VERIFIED',
        frozen_high_frequency_rank=RANK,
        acting_seat=ACTOR,acting_position='CO_IP',
        exact_actor_IP_checked_turn_nodes=len(strict),
        exact_actor_IP_checked_turn_strict_combos=strict_combos,
        corrected_pin_path=str(NEW_PIN),
        original_upstream_index_path=str(INDEX),
        original_upstream_index_sha256=sha(INDEX.read_bytes()),
        original_upstream_rank_label=71,
        original_upstream_actor_label='OOP_gto_river',
        no_generic_model_certification=0,immediate_CERT_upgrades=0)
    NEW_PIN.write_text(json.dumps(corrected,ensure_ascii=False,indent=2)+'\n')
    corrected_idx['corrected_pin_sha256']=sha(NEW_PIN.read_bytes())
    NEW_INDEX.write_text(json.dumps(corrected_idx,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text(
        '# B148 | B147 original source repaired metadata, no solver rewrite\n\n'
        'Actual solver spot LMP_CO_BB, A-high flop As9h2d, full 100bb GTO. '
        'Exact flop action x b50 c; BB checks turn; CO hero IP acts at x b50 c/x. '
        'Frozen rank **46**.\n\n'
        'Original B147 indexing mislabeled rank=71 and IP turn as OOP river. '
        'Upstream source, GTO root and gz SHA remain **unaltered**; corrections '
        'are recorded as new versioned files with upstream pin/index SHA.\n\n'
        'Legal actor-IP checked-turn nodes: '+str(len(strict))+
        ', strict combos: '+str(strict_combos)+'. This is genuine GTO source, '
        '**not** observed NL2 private-card conditional action frequencies. '
        'Limp 169-class preflop distributions are **assumed**. '
        'A fresh true actor-IP EXP source on this same board/turn remains required '
        'to validate a third flop and optionally promote rank46. '
        'V30 remains **142 CERT /250 APPROX**, 554 named board proofs, '
        '2475/2475 river audit, PR2 Draft and NEVER MERGE.\n')
    print(json.dumps(dict(status='PASS',rank=RANK,flop=FLOP,
           original_run=old['run_id'],strict_actor_ip_nodes=len(strict),
           strict_actor_ip_combos=strict_combos,
           upstream_source_sha256=sha(raw),upstream_index_sha256=sha(INDEX.read_bytes()),
           corrected_pin_sha256=sha(NEW_PIN.read_bytes()),CERT=142,APPROX=250),ensure_ascii=False))
if __name__=='__main__': main()
