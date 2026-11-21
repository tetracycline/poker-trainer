#!/usr/bin/env python3
"""Independent NL2 100bb multiboard CFR source, pot, rake, action, SPR,
convergence, full-street per-combo frequency reach and locked-pool provenance
audit. Creates no generic GTO certification by itself.
"""
import argparse,base64,collections,hashlib,json,pathlib,re,sys
REPO_SPOTS={
'BTN_BB':('SRP',5.5,97.5),
'CO_BB':('SRP',5.5,97.5),
'SB_BB':('SRP',6.0,97.0),
'UTG_CO':('SRP',6.5,97.5),
'BB3_BTN':('3BP',20.5,90.0),
'SB3_BTN':('3BP',21.0,90.0),
'CO3_BTN':('3BP',16.5,92.5),
'ISO_BTN_CO':('ISO',9.5,96.0),
'LMP_CO_BB':('LMP',2.5,99.0)}
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for z in iter(lambda:f.read(1024*1024),b''):h.update(z)
    return h.hexdigest()
def authorized_b149_rank46_exact_gto_parent(m):
    """Only one SHA-fixed B147 original GTO plus independently corrected B148
    pin/index can authorize a fresh B149 actor-IP turn-only Rust child.

    The original B147 source gz/manifest/root/job never changes. A stale
    producer rank71 or OOP river label must NOT authorize private-card NL2
    evidence, GTO texture extrapolation, or a model CERT by itself.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop')=='As9h2d' and
            m.get('selected_lines')==['x b50 c'] and
            m.get('selected_turn_lines')==['x x'] and
            m.get('gto_parent_source_run_id')==44853428350):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b148_rank46_as9h2d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B148_R46_AS9H2D_GTO_VERIFIED.index.json'
    source_gz=d/'solver_evidence/NL2_MULTIBOARD_B147_R46_AS9H2D_GTO.json.gz'
    oldindex=d/'solver_evidence/NL2_MULTIBOARD_B147_R46_AS9H2D_GTO.index.json'
    try:
        p=json.loads(pinfile.read_text())
        i=json.loads(indexfile.read_text())
        return (p['schema']=='NL2_HU_B148_RANK46_LMP_AS9H2D_CORRECTED_GTO_PARENT_PIN_V1' and
            i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
            i['batch']=='B148_R46_AS9H2D_GTO_VERIFIED' and
            (p['source_run_id'],i['run_id'])==(44853428350,44853428350) and
            (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
                'LMP_CO_BB','As9h2d','x b50 c','x x') and
            p['target_rank']==46 and p['model_id']=='ln-iso-lmp_t_model-17z0wyl' and
            p['acting_seat']==1 and p['acting_position']=='CO_IP' and
            p['target_exact_actor_IP_turn_nodes']>0 and
            p['target_exact_actor_IP_turn_strict_combos']>0 and
            p['original_full_100bb_lmp_gto_not_recomputed'] is True and
            p['observed_preflop_ranges'] is False and
            p['assumed_limped_169class'] is True and
            p['no_generic_model_certification'] is True and
            p['source_gto_job_id'] is None and
            p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
            p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
            p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
            p['original_gto_evidence_sha256']==i['source_sha256'] and
            p['original_gto_gzip_sha256']==i['gzip_sha256'] and
            i['corrected_pin_sha256']==sha(pinfile) and
            i['original_upstream_index_sha256']==sha(oldindex) and
            p['original_upstream_pin_sha256']==sha(d/'nl2_hu_b147_rank46_lmp_low64_gto_parent_pin.json') and
            i['frozen_high_frequency_rank']==46 and
            i['acting_seat']==1 and
            i['exact_actor_IP_checked_turn_nodes']>0 and
            i['exact_actor_IP_checked_turn_strict_combos']>0 and
            i['original_upstream_rank_label']==71 and
            sha(source_gz)==i['gzip_sha256'])
    except (OSError,KeyError,TypeError,ValueError):
        return False

def authorized_b160_rank71_exact_true_gto_parent(m):
    """Only original individually successful B156 full GTO and its independently
    SHA-audited source/index can authorize true downstream exp_oop NL2.
    The original LMP 169-class preflop is ASSUMED. Zero legal GTO
    actor-OOP river combos fails closed; never manufacture a texture CERT.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_oop' and
            m.get('flop')=='Ks7h2d' and
            m.get('selected_lines')==['b50 c'] and
            m.get('selected_turn_lines')==['x b50 c'] and
            m.get('gto_parent_source_run_id')==44860317844):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b156_rank71_lmp_ks7h2d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B156_R71_KS7H2D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B156_R71_KS7H2D_GTO.json.gz'
    try:
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        import gzip
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B156_RANK71_LMP_KS7H2D_GTO_PARENT_PIN_V1' and
          p['source_run_id']==44860317844 and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','Ks7h2d','b50 c','x b50 c') and
          p['target_rank']==71 and p['model_id']=='ln-iso-lmp_r_model-vlgh2t' and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['target_exact_actor_OOP_river_nodes']>0 and
          p['target_exact_actor_OOP_strict_combos']>0 and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B156_R71_KS7H2D_GTO' and
          (i['run_id'],i['gto_cases'],i['locked_cases'],i['verified_cases'])==(
             44860317844,1,0,1) and
          i['exact_target_actor_OOP_river_nodes']>0 and
          i['exact_target_actor_OOP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'])
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False

def authorized_b181_rank71_exact_B180_gto_parent(m):
    """Only original individually successful B180 full GTO and its independently
    SHA-audited source/index can authorize true downstream exp_oop NL2.
    The original LMP 169-class preflop is ASSUMED. Zero legal GTO
    actor-OOP river combos fails closed; never manufacture a texture CERT.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_oop' and
            m.get('flop')=='7s7h2d' and
            m.get('selected_lines')==['b50 c'] and
            m.get('selected_turn_lines')==['x b50 c'] and
            m.get('gto_parent_source_run_id')==44871805331):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b180_rank71_lmp_7s7h2d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B180_R71_7S7H2D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B180_R71_7S7H2D_GTO.json.gz'
    try:
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        import gzip
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B180_RANK71_LMP_7S7H2D_GTO_PARENT_PIN_V1' and
          p['source_run_id']==44871805331 and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','7s7h2d','b50 c','x b50 c') and
          p['target_rank']==71 and p['model_id']=='ln-iso-lmp_r_model-vlgh2t' and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['target_exact_actor_OOP_river_nodes']>0 and
          p['target_exact_actor_OOP_strict_combos']>0 and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B180_R71_7S7H2D_GTO' and
          (i['run_id'],i['gto_cases'],i['locked_cases'],i['verified_cases'])==(
             44871805331,1,0,1) and
          i['exact_target_actor_OOP_river_nodes']>0 and
          i['exact_target_actor_OOP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'])
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False

def authorized_b163_rank313_exact_true_gto_parent(m):
    """Only original individually successful B158 full GTO and its independently
    SHA-audited source/index can authorize true downstream exp_ip NL2.
    The original LMP 169-class preflop is ASSUMED. Zero legal GTO
    actor-IP river combos fails closed; never manufacture a texture CERT.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop')=='Ks7h2d' and
            m.get('selected_lines')==['b75 r c'] and
            m.get('selected_turn_lines')==['x b50 c'] and
            m.get('gto_parent_source_run_id')==44860436462):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b158_rank313_lmp_ks7h2d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B158_R313_KS7H2D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B158_R313_KS7H2D_GTO.json.gz'
    try:
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        import gzip
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B158_RANK313_LMP_KS7H2D_GTO_PARENT_PIN_V1' and
          p['source_run_id']==44860436462 and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','Ks7h2d','b75 r c','x b50 c') and
          p['target_rank']==313 and p['model_id']=='ln-iso-lmp_r_model-wpg493' and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['target_exact_actor_IP_river_nodes']>0 and
          p['target_exact_actor_IP_strict_combos']>0 and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B158_R313_KS7H2D_GTO' and
          (i['run_id'],i['gto_cases'],i['locked_cases'],i['verified_cases'])==(
             44860436462,1,0,1) and
          i['exact_target_actor_IP_river_nodes']>0 and
          i['exact_target_actor_IP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'])
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False

def authorized_b167_rank80_exact_true_gto_parent(m):
    """Fail-closed new B165 original 7s5h3d LMP IP river GTO parent.

    Only its exact SHA-pinned B165 original GTO source, verified positive
    actor CO-IP full-street combo reach, and b33-call/x-x/x partial tree
    may be accepted. No texture/general model CERT from this predicate.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop')=='7s5h3d' and
            m.get('selected_lines')==['b33 c'] and
            m.get('selected_turn_lines')==['x x'] and
            m.get('turn_line_policy')=='xxonly' and
            m.get('flop_line_policy')=='oop-b33only' and
            m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
            m.get('gto_parent_source_run_id')==44862108987 and
            m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B165_TRUE_GTO' and
            m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
            m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS'):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b165_rank80_lmp_7s5h3d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B165_R80_7S5H3D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B165_R80_7S5H3D_GTO.json.gz'
    try:
        import gzip
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B165_RANK80_LMP_7S5H3D_GTO_PARENT_PIN_V1' and
          (p['source_run_id'],i['run_id'])==(44862108987,44862108987) and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','7s5h3d','b33 c','x x') and
          p['turn']=='6c' and
          p['target_rank']==80 and p['model_id']=='ln-iso-lmp_r_model-17pklmg' and
          p['target_exact_actor_IP_river_nodes']>0 and
          p['target_exact_actor_IP_strict_combos']>0 and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B165_R80_7S5H3D_GTO' and
          (i['gto_cases'],i['locked_cases'],i['verified_cases'])==(1,0,1) and
          i['exact_target_actor_IP_river_nodes']>0 and
          i['exact_target_actor_IP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'] and
          m.get('original_B167_parent_pin_sha256')==sha(pinfile))
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False


def authorized_b176_rank138_exact_b2_co_ip_xx(m):
    """Only original successful B2 CO_BB Js9h4d full GTO root for rank138.

    Never permit a generic check-check board without exact source SHA,
    original successful B2 job, frozen positive GTO combo reach, same
    actor/line/SPR and a genuine separately solved EXP_IP child.
    """
    if not (m.get('spot')=='CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop')=='Js9h4d' and
            m.get('selected_lines')==['x x'] and
            m.get('selected_turn_lines')==['x x'] and
            m.get('turns')==['Ts'] and
            m.get('flop_line_policy')=='checkcheck' and
            m.get('turn_line_policy')=='xxonly' and
            m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
            m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B2_RANK138_TRUE_GTO' and
            m.get('gto_parent_source_run_id')==44666290556 and
            m.get('preflop_ranges',{}).get('source')=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
            m.get('original_B2_GTO_flop_byte_identical_not_recomputed') is True):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pfile=d/'nl2_hu_b176_rank138_js9h4d_b2_gto_parent_pin.json'
    bz=d/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.json.gz'
    index=bz.with_suffix('').with_suffix('.index.json')
    prior=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    old=d/'nl2_hu_b107_co_js9h4d_b2_gto_parent_pin.json'
    try:
        import gzip
        p=json.loads(pfile.read_text())
        i=json.loads(index.read_text())
        a=json.loads(prior.read_text())
        o=json.loads(old.read_text())
        row=next(z for z in a['rows'] if z['rank']==138)
        authentic=[z for z in row['exact_authentic_gto_source_proofs'] if
          z['flop']=='Js9h4d' and z['turn']=='Ts' and
          z['source_run']==44666290556 and
          z['source_sha']==p['original_GTO_sample_sha256'] and
          z['exact_line']=='x x/x x/x' and z['actor']==1 and
          z['strict_legal_combos']>0 and z['GTO_gap_pct']<=0.5 and
          z['SPR_error_pct']<=5 and not z['true_NL2_actor_locked']]
        return (a['schema']=='NL2_HU_B175_V32_ALL_248_GENUINE_GTO_RUN_ACTOR_TURN_SHA_PROVENANCE_V1' and
          (a['CERT_MULTIBOARD'],a['APPROX'],a['EST'])==(144,248,0) and
          p['schema']=='NL2_HU_B176_RANK138_CO_BB_JS9H4D_B2_GTO_PARENT_PIN_V1' and
          p['original_source_run_id']==i['run_id']==44666290556 and
          p['target_rank']==138 and p['target_model_id']=='ln-ipfr-r_model-hqu5je' and
          p['public_flop']=='Js9h4d' and p['turn']=='Ts' and
          p['flop_line']=='x x' and p['turn_line']=='x x' and
          p['strict_hero_IP_river_combos']>0 and bool(authentic) and
          i['source_sha256']==hashlib.sha256(gzip.decompress(bz.read_bytes())).hexdigest() and
          i['gzip_sha256']==sha(bz) and
          p['B2_PARTIAL_source_archive_SHA256']==i['gzip_sha256'] and
          o['original_GTO_flop_SHA256']==p['original_GTO_flop_SHA256']==m.get('gto_parent_source_sha256') and
          o['original_GTO_job_SHA256']==p['original_GTO_job_SHA256']==m.get('flop_root_jobfile_sha256') and
          o['original_manifest_SHA256']==p['original_manifest_SHA256']==m.get('gto_parent_source_manifest_sha256') and
          m.get('original_B176_rank138_b2_GTO_pin_sha256')==sha(pfile))
    except (OSError,KeyError,TypeError,ValueError,EOFError,StopIteration):
        return False


def authorized_b178_rank138_b04_co_ip_xx(m):
    """Only original run44653774402 CO_BB 8s8h3d/5s legacy GTO source.
    Freeze exact original job/root/manifest SHA, actor-IP legal combos and
    original historical restricted bet menu. No board texture expansion.
    """
    if not (m.get('spot')=='CO_BB' and m.get('version')=='exp_ip' and
      m.get('flop')=='8s8h3d' and m.get('selected_lines')==['x x'] and
      m.get('selected_turn_lines')==['x x'] and m.get('turns')==['5s'] and
      m.get('flop_line_policy')=='checkcheck' and
      m.get('turn_line_policy')=='xxonly' and
      m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
      m.get('pinned_official_legacy_source_id')==44653774402 and
      m.get('gto_parent_source_run_id')==44653774402 and
      m.get('flop_size_profile')=='legacy-official-pinned' and
      m.get('restricted_original_GTO_tree') is True and
      m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B04_RANK138_LEGACY_GTO'):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    file=d/'nl2_hu_b177_rank138_co_bb_8s8h3d_b04_gto_parent_pin.json'
    old=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    arc=d/'nl2_hu_exact_boards_b04.json.gz'
    ix=d/'nl2_hu_exact_boards_b04.index.json'
    try:
        p=json.loads(file.read_text())
        a=json.loads(old.read_text())
        z=json.loads(ix.read_text())
        row=next(q for q in a['rows'] if q['rank']==138)
        genuine=[q for q in row['exact_authentic_gto_source_proofs'] if
           q['flop']=='8s8h3d' and q['turn']=='5s' and q['actor']==1 and
           q['exact_line']=='x x/x x/x' and q['source_run']==44653774402 and
           q['source_sha']==p['source_original_GTO_case_SHA256'] and
           q['strict_legal_combos']>0 and q['GTO_gap_pct']<=.5 and
           q['SPR_error_pct']<=5 and not q['true_NL2_actor_locked']]
        return (p['schema']=='NL2_HU_B177_RANK138_B04_CO_BB_8S8H3D_GTO_PARENT_PIN_V1' and
          p['original_run_id']==44653774402 and p['target_rank']==138 and
          p['target_model_id']=='ln-ipfr-r_model-hqu5je' and
          p['strict_original_GTO_combo_min']>0 and bool(genuine) and
          p['historical_restricted_tree_not_full_modern_GTO'] is True and
          p['original_flop_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          p['original_stage2_archive_sha256']==sha(arc)==z['gz_sha256'] and
          p['original_stage2_index_sha256']==sha(ix) and
          m.get('original_B177_rank138_GTO_pin_sha256')==sha(file) and
          m.get('flop_action_sizes')==dict(oop='',ip='33%,50%,75%',raise_sizes='3x,a'))
    except (OSError,KeyError,TypeError,ValueError,StopIteration):
        return False


def authorized_b189_rank199_202_B3_original_gto_IP_xb33_xb50(m):
    """Only exact original B3 8s8h3d or 9s6h3d GTO SHA for CO-IP hero.

    B175 source-blind proves actor and full street legal GTO combos; B188
    pins original root/job/manifest. New NL2 actor-IP Rust turn-river solve
    must remain an independent source; no other flop or action-line accepted.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop') in ('8s8h3d','9s6h3d') and
            m.get('selected_lines')==['x b33 c'] and
            m.get('selected_turn_lines')==['x b50 c'] and
            m.get('flop_line_policy')=='checked-b33only' and
            m.get('turn_line_policy')=='xb50only' and
            m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
            m.get('gto_parent_source_run_id')==44666294821 and
            m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B3_RANK199_202_GTO' and
            m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
            m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS'):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/('nl2_hu_b188_rank199_202_'+m['flop']+'_B3_gto_pin.json')
    idx=d/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
    arch=d/'solver_evidence/NL2_MULTIBOARD_B3.json.gz'
    b175=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    try:
        import gzip
        p=json.loads(pinfile.read_text())
        i=json.loads(idx.read_text())
        prov=json.loads(b175.read_text())
        assert p['schema']=='NL2_HU_B188_RANK199_202_B3_ORIGINAL_GTO_PARENT_PIN_V1'
        assert (p['spot'],p['flop'],p['original_GTO_flop_line'],p['target_turn_line'])==(
            'LMP_CO_BB',m['flop'],'x b33 c','x b50 c')
        assert p['rank_targets']==[199,202] and p['hero_actor']==1
        assert p['source_run_id']==i['run_id']==44666294821
        assert p['original_full_GTO_flop_not_recomputed'] is True
        assert p['assumed_limped_preflop_169class_not_observed'] is True
        assert p['original_B3_verified_archive_sha256']==i['gzip_sha256']==sha(arch)
        assert i['source_sha256']==hashlib.sha256(gzip.decompress(arch.read_bytes())).hexdigest()
        assert p['original_B3_index_sha256']==sha(idx)
        assert m['turns']==[p['turn']]
        assert m['original_B188_parent_pin_sha256']==sha(pinfile)
        assert m['gto_parent_source_sha256']==p['original_gto_root_sha256']
        assert m['flop_root_jobfile_sha256']==p['original_gto_job_sha256']
        assert m['gto_parent_source_manifest_sha256']==p['original_gto_manifest_sha256']
        for rank in (199,202):
            row=next(x for x in prov['rows'] if x['rank']==rank)
            assert any(q['flop']==p['flop'] and q['turn']==p['turn'] and
                q['source_run']==44666294821 and
                q['source_sha']==p['original_GTO_case_SHA256'] and
                q['exact_line']=='x b33 c/x b50 c/x' and
                q['actor']==1 and q['strict_legal_combos']>0 and
                q['GTO_gap_pct']<=.5 and q['SPR_error_pct']<=5
                for q in row['exact_authentic_gto_source_proofs'])
        return True
    except (OSError,KeyError,TypeError,ValueError,EOFError,StopIteration,AssertionError):
        return False


def authorized_b192_rank201_exact_original_B3_CO_IP_xb33_xb100(m):
    """Only original SHA-pinned B191 rank201 two B3 real GTO flops.

    B175 independently proves exact actor CO-IP and strictly positive
    full street combos for x b33 c / x b100 c / x. No other flop
    or preflop policy, no generic texture model certification.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
       m.get('flop') in ('8s8h3d','9s6h3d') and
       m.get('selected_lines')==['x b33 c'] and
       m.get('selected_turn_lines')==['x b100 c'] and
       m.get('flop_line_policy')=='checked-b33only' and
       m.get('turn_line_policy')=='xb100only' and
       m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
       m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B3_RANK201_XB33_XB100_GTO' and
       m.get('gto_parent_source_run_id')==44666294821 and
       m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS' and
       m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/('nl2_hu_b191_rank201_'+m['flop']+'_B3_original_gto_pin.json')
    b188=d/('nl2_hu_b188_rank199_202_'+m['flop']+'_B3_gto_pin.json')
    b175=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    archive=d/'solver_evidence/NL2_MULTIBOARD_B3.json.gz'
    index=d/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
    try:
        import gzip
        p=json.loads(pinfile.read_text())
        prev=json.loads(b188.read_text())
        gap=json.loads(b175.read_text())
        ix=json.loads(index.read_text())
        row=next(z for z in gap['rows'] if z['rank']==201)
        legal=[z for z in row['exact_authentic_gto_source_proofs'] if
           z['flop']==m['flop'] and z['turn']==p['turn'] and
           z['source_run']==44666294821 and z['source_sha']==p['original_GTO_case_SHA256']
           and z['exact_line']=='x b33 c/x b100 c/x' and
           z['actor']==1 and z['strict_legal_combos']>0 and
           z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5 and
           not z['true_NL2_actor_locked']]
        return (p['schema']=='NL2_HU_B191_RANK201_B3_ORIGINAL_XB33_XB100_GTO_PARENT_PIN_V1' and
           p['source_run_id']==44666294821 and p['target_rank']==201 and
           p['model_id']=='ln-iso-lmp_r_model-qsgdjf' and p['actor']==1 and
           p['spot']=='LMP_CO_BB' and p['original_GTO_flop_line']=='x b33 c' and
           p['target_turn_line']=='x b100 c' and p['exact_river_line']=='x b33 c/x b100 c/x' and
           p['original_assumed_preflop_169class_not_measured'] is True and
           p['original_full_GTO_flop_not_recomputed'] is True and
           p['minimum_strict_original_GTO_legal_IP_combos']>0 and bool(legal) and
           p['original_B188_parent_pin_sha256']==sha(b188) and
           p['original_gto_root_sha256']==prev['original_gto_root_sha256'] and
           p['original_gto_job_sha256']==prev['original_gto_job_sha256'] and
           p['original_gto_manifest_sha256']==prev['original_gto_manifest_sha256'] and
           p['original_B3_verified_archive_sha256']==ix['gzip_sha256']==sha(archive) and
           ix['source_sha256']==hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() and
           p['original_B3_index_sha256']==sha(index) and
           m.get('turns')==[p['turn']] and
           m.get('gto_parent_source_sha256')==p['original_gto_root_sha256'] and
           m.get('flop_root_jobfile_sha256')==p['original_gto_job_sha256'] and
           m.get('gto_parent_source_manifest_sha256')==p['original_gto_manifest_sha256'] and
           m.get('original_B191_parent_pin_sha256')==sha(pinfile))
    except (OSError,KeyError,TypeError,ValueError,EOFError,AssertionError,StopIteration):
        return False


def authorized_b195_rank159_original_SB_BB_BB_IP_xb100_xx(m):
    """Only original positive SB_BB BB-IP GTO parent As7h3d or Js9h4d.

    Preserve B1/B5 original independently verified source SHA, original CFR
    preflop ranges, exact actor BB IP / river action, and positive strict
    combo reach. NL2 hero lock child is separately genuine Rust turn-river.
    """
    if not (m.get('spot')=='SB_BB' and m.get('version')=='exp_ip' and
       m.get('flop') in ('As7h3d','Js9h4d') and
       m.get('selected_lines')==['x b100 c'] and
       m.get('selected_turn_lines')==['x x'] and
       m.get('flop_line_policy')=='checked-b100only' and
       m.get('turn_line_policy')=='xxonly' and
       m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
       m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B194_RANK159_SB_BB_GTO' and
       m.get('preflop_ranges',{}).get('source')=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
       m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/('nl2_hu_b194_rank159_'+m['flop']+'_original_SB_BB_gto_pin.json')
    b175=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    try:
        import gzip
        pin=json.loads(pinfile.read_text())
        prov=json.loads(b175.read_text())
        idx=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.index.json')
        arc=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.json.gz')
        ix=json.loads(idx.read_text())
        row=next(z for z in prov['rows'] if z['rank']==159)
        legal=[z for z in row['exact_authentic_gto_source_proofs'] if
          z['flop']==pin['flop'] and z['turn']==pin['turn'] and
          z['source_run']==pin['source_run_id'] and z['source_sha']==pin['original_case_sha256'] and
          z['exact_line']=='x b100 c/x x/x' and z['actor']==1 and
          z['strict_legal_combos']>0 and z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5 and
          not z['true_NL2_actor_locked']]
        return (
          pin['schema']=='NL2_HU_B194_RANK159_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1' and
          (pin['target_rank'],pin['model_id'])==(159,'ln-ipc-r_model-vvxn9n') and
          (pin['spot'],pin['acting_seat'],pin['acting_position'])==('SB_BB',1,'BB_IP') and
          pin['exact_river_line']=='x b100 c/x x/x' and
          pin['original_parent_GTO_not_recomputed'] is True and
          pin['minimum_strict_original_actor_IP_combos']>0 and
          pin['preflop_source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
          bool(legal) and m.get('turns')==[pin['turn']] and
          m.get('gto_parent_source_run_id')==pin['source_run_id']==ix['run_id'] and
          m.get('gto_parent_source_sha256')==pin['original_gto_root_sha256'] and
          m.get('flop_root_jobfile_sha256')==pin['original_gto_job_sha256'] and
          m.get('gto_parent_source_manifest_sha256')==pin['original_gto_manifest_sha256'] and
          m.get('original_B194_rank159_parent_pin_sha256')==sha(pinfile) and
          pin['original_archive_sha256']==ix['gzip_sha256']==sha(arc) and
          pin['original_index_sha256']==sha(idx) and
          ix['source_sha256']==hashlib.sha256(gzip.decompress(arc.read_bytes())).hexdigest())
    except (OSError,ValueError,KeyError,TypeError,EOFError,StopIteration,AssertionError):
        return False


def authorized_b200_rank188_original_SB_BB_BB_IP_xb100_xx(m):
    """Only original positive SB_BB BB-IP GTO parent 8s8h3d or 9s6h3d.

    Preserve B1/B5 original independently verified source SHA, original CFR
    preflop ranges, exact actor BB IP / river action, and positive strict
    combo reach. NL2 hero lock child is separately genuine Rust turn-river.
    """
    if not (m.get('spot')=='SB_BB' and m.get('version')=='exp_ip' and
       m.get('flop') in ('8s8h3d','9s6h3d') and
       m.get('selected_lines')==['x b50 c'] and
       m.get('selected_turn_lines')==['x b100 c'] and
       m.get('flop_line_policy')=='checked-b50only' and
       m.get('turn_line_policy')=='xb100only' and
       m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
       m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B199_RANK188_SB_BB_GTO' and
       m.get('preflop_ranges',{}).get('source')=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
       m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/('nl2_hu_b199_rank188_'+m['flop']+'_original_SB_BB_gto_pin.json')
    b175=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    try:
        import gzip
        pin=json.loads(pinfile.read_text())
        prov=json.loads(b175.read_text())
        idx=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.index.json')
        arc=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.json.gz')
        ix=json.loads(idx.read_text())
        row=next(z for z in prov['rows'] if z['rank']==188)
        legal=[z for z in row['exact_authentic_gto_source_proofs'] if
          z['flop']==pin['flop'] and z['turn']==pin['turn'] and
          z['source_run']==pin['source_run_id'] and z['source_sha']==pin['original_case_sha256'] and
          z['exact_line']=='x b50 c/x b100 c/x' and z['actor']==1 and
          z['strict_legal_combos']>0 and z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5 and
          not z['true_NL2_actor_locked']]
        return (
          pin['schema']=='NL2_HU_B199_RANK188_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1' and
          (pin['target_rank'],pin['model_id'])==(188,'ln-ipc-r_model-1s0a4ds') and
          (pin['spot'],pin['acting_seat'],pin['acting_position'])==('SB_BB',1,'BB_IP') and
          pin['exact_river_line']=='x b50 c/x b100 c/x' and
          pin['original_parent_GTO_not_recomputed'] is True and
          pin['minimum_strict_original_actor_IP_combos']>0 and
          pin['preflop_source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
          bool(legal) and m.get('turns')==[pin['turn']] and
          m.get('gto_parent_source_run_id')==pin['source_run_id']==ix['run_id'] and
          m.get('gto_parent_source_sha256')==pin['original_gto_root_sha256'] and
          m.get('flop_root_jobfile_sha256')==pin['original_gto_job_sha256'] and
          m.get('gto_parent_source_manifest_sha256')==pin['original_gto_manifest_sha256'] and
          m.get('original_B199_rank188_parent_pin_sha256')==sha(pinfile) and
          pin['original_archive_sha256']==ix['gzip_sha256']==sha(arc) and
          pin['original_index_sha256']==sha(idx) and
          ix['source_sha256']==hashlib.sha256(gzip.decompress(arc.read_bytes())).hexdigest())
    except (OSError,ValueError,KeyError,TypeError,EOFError,StopIteration,AssertionError):
        return False


def authorized_b204_rank190_original_SB_BB_BB_IP_xb75_xb100(m):
    """Only original positive SB_BB BB-IP GTO parent 8s8h3d or 9s6h3d.

    Preserve B1/B5 original independently verified source SHA, original CFR
    preflop ranges, exact actor BB IP / river action, and positive strict
    combo reach. NL2 hero lock child is separately genuine Rust turn-river.
    """
    if not (m.get('spot')=='SB_BB' and m.get('version')=='exp_ip' and
       m.get('flop') in ('8s8h3d','Js9h4d') and
       m.get('selected_lines')==['x b75 c'] and
       m.get('selected_turn_lines')==['x b100 c'] and
       m.get('flop_line_policy')=='checked-b75only' and
       m.get('turn_line_policy')=='xb100only' and
       m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
       m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B203_RANK190_SB_BB_GTO' and
       m.get('preflop_ranges',{}).get('source')=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
       m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/('nl2_hu_b203_rank190_'+m['flop']+'_original_SB_BB_gto_pin.json')
    b175=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    try:
        import gzip
        pin=json.loads(pinfile.read_text())
        prov=json.loads(b175.read_text())
        idx=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.index.json')
        arc=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.json.gz')
        ix=json.loads(idx.read_text())
        row=next(z for z in prov['rows'] if z['rank']==190)
        legal=[z for z in row['exact_authentic_gto_source_proofs'] if
          z['flop']==pin['flop'] and z['turn']==pin['turn'] and
          z['source_run']==pin['source_run_id'] and z['source_sha']==pin['original_case_sha256'] and
          z['exact_line']=='x b75 c/x b100 c/x' and z['actor']==1 and
          z['strict_legal_combos']>0 and z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5 and
          not z['true_NL2_actor_locked']]
        return (
          pin['schema']=='NL2_HU_B203_RANK190_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1' and
          (pin['target_rank'],pin['model_id'])==(190,'ln-ipc-r_model-dfikbd') and
          (pin['spot'],pin['acting_seat'],pin['acting_position'])==('SB_BB',1,'BB_IP') and
          pin['exact_river_line']=='x b75 c/x b100 c/x' and
          pin['original_parent_GTO_not_recomputed'] is True and
          pin['minimum_strict_original_actor_IP_combos']>0 and
          pin['preflop_source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
          bool(legal) and m.get('turns')==[pin['turn']] and
          m.get('gto_parent_source_run_id')==pin['source_run_id']==ix['run_id'] and
          m.get('gto_parent_source_sha256')==pin['original_gto_root_sha256'] and
          m.get('flop_root_jobfile_sha256')==pin['original_gto_job_sha256'] and
          m.get('gto_parent_source_manifest_sha256')==pin['original_gto_manifest_sha256'] and
          m.get('original_B203_rank190_parent_pin_sha256')==sha(pinfile) and
          pin['original_archive_sha256']==ix['gzip_sha256']==sha(arc) and
          pin['original_index_sha256']==sha(idx) and
          ix['source_sha256']==hashlib.sha256(gzip.decompress(arc.read_bytes())).hexdigest())
    except (OSError,ValueError,KeyError,TypeError,EOFError,StopIteration,AssertionError):
        return False


def authorized_b198_rank159_original_SB_BB_BB_IP_xb100_xx(m):
    """Only original positive SB_BB BB-IP GTO parent As9h2d or KsQh4d.

    Preserve B1/B5 original independently verified source SHA, original CFR
    preflop ranges, exact actor BB IP / river action, and positive strict
    combo reach. NL2 hero lock child is separately genuine Rust turn-river.
    """
    if not (m.get('spot')=='SB_BB' and m.get('version')=='exp_ip' and
       m.get('flop') in ('As9h2d','KsQh4d') and
       m.get('selected_lines')==['x b100 c'] and
       m.get('selected_turn_lines')==['x x'] and
       m.get('flop_line_policy')=='checked-b100only' and
       m.get('turn_line_policy')=='xxonly' and
       m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
       m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B197_RANK159_SB_BB_GTO' and
       m.get('preflop_ranges',{}).get('source')=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
       m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/('nl2_hu_b197_rank159_'+m['flop']+'_original_SB_BB_gto_pin.json')
    b175=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    try:
        import gzip
        pin=json.loads(pinfile.read_text())
        prov=json.loads(b175.read_text())
        idx=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.index.json')
        arc=d/('solver_evidence/NL2_MULTIBOARD_'+pin['source_batch']+'.json.gz')
        ix=json.loads(idx.read_text())
        row=next(z for z in prov['rows'] if z['rank']==159)
        legal=[z for z in row['exact_authentic_gto_source_proofs'] if
          z['flop']==pin['flop'] and z['turn']==pin['turn'] and
          z['source_run']==pin['source_run_id'] and z['source_sha']==pin['original_case_sha256'] and
          z['exact_line']=='x b100 c/x x/x' and z['actor']==1 and
          z['strict_legal_combos']>0 and z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5 and
          not z['true_NL2_actor_locked']]
        return (
          pin['schema']=='NL2_HU_B197_RANK159_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1' and
          (pin['target_rank'],pin['model_id'])==(159,'ln-ipc-r_model-vvxn9n') and
          (pin['spot'],pin['acting_seat'],pin['acting_position'])==('SB_BB',1,'BB_IP') and
          pin['exact_river_line']=='x b100 c/x x/x' and
          pin['original_parent_GTO_not_recomputed'] is True and
          pin['minimum_strict_original_actor_IP_combos']>0 and
          pin['preflop_source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and
          bool(legal) and m.get('turns')==[pin['turn']] and
          m.get('gto_parent_source_run_id')==pin['source_run_id']==ix['run_id'] and
          m.get('gto_parent_source_sha256')==pin['original_gto_root_sha256'] and
          m.get('flop_root_jobfile_sha256')==pin['original_gto_job_sha256'] and
          m.get('gto_parent_source_manifest_sha256')==pin['original_gto_manifest_sha256'] and
          m.get('original_B197_rank159_parent_pin_sha256')==sha(pinfile) and
          pin['original_archive_sha256']==ix['gzip_sha256']==sha(arc) and
          pin['original_index_sha256']==sha(idx) and
          ix['source_sha256']==hashlib.sha256(gzip.decompress(arc.read_bytes())).hexdigest())
    except (OSError,ValueError,KeyError,TypeError,EOFError,StopIteration,AssertionError):
        return False


def authorized_b282_rank46_new_GTO_IP_turn(m):
    """B282: ONLY prereg B279/B280/B284/B286 original 100bb LMP GTO with SHA pinned and
    strictly legal CO-IP x b50 c/x TURN combos can authorize a real Rust
    downstream NL2 partially locked child. No GTO-only or actor-zero source
    may authorize conditional private-hand NL2 rates or generic CERT.
    """
    specs={'KsJh4d':('B279',44937413659),'QsJh4d':('B280',44937484979),
           '7s5h3d':('B284',44938881037),'7s7h2d':('B286',44939456600)}
    flop=m.get('flop')
    if flop not in specs:return False
    batch,run=specs[flop]
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip'
        and m.get('selected_lines')==['x b50 c'] and
        m.get('selected_turn_lines')==['x x'] and
        m.get('flop_line_policy')=='checked-b50only' and
        m.get('turn_line_policy')=='xxonly' and
        m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
        m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B282_RANK46_GTO' and
        m.get('gto_parent_source_run_id')==run and
        m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
        m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS' and
        m.get('restricted_tree_assumption') is False and
        m.get('flop_size_profile')=='full'):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinpath=d/f'nl2_hu_{batch.lower()}_rank46_lmp_{flop}_gto_parent_pin.json'
    idxpath=d/f'solver_evidence/NL2_MULTIBOARD_{batch}_R46_{flop.upper()}_GTO.index.json'
    gz=d/f'solver_evidence/NL2_MULTIBOARD_{batch}_R46_{flop.upper()}_GTO.json.gz'
    try:
        import gzip
        p=json.loads(pinpath.read_text());ix=json.loads(idxpath.read_text())
        data=json.loads(gzip.decompress(gz.read_bytes()))
        assert p['schema']==f'NL2_HU_{batch}_RANK46_LMP_{flop.upper()}_GTO_PARENT_PIN_V1'
        assert (p['source_run_id'],ix['run_id'],data['source_run_id'])==(run,run,run)
        assert (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
            'LMP_CO_BB',flop,'x b50 c','x x')
        assert (p['target_rank'],p['model_id'])==(46,'ln-iso-lmp_t_model-17z0wyl')
        assert p['assumed_limped_169class'] is True and p['observed_preflop_ranges'] is False
        assert p['original_full_100bb_lmp_gto_not_recomputed'] is True
        assert p['direct_nl2_lock_source_present'] is False
        assert p['no_generic_model_certification'] is True
        assert p['target_exact_actor_IP_turn_nodes']>0
        assert p['target_exact_actor_IP_strict_combos']>0
        assert (ix['schema'],ix['batch'])==(
            'NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1',
            f'{batch}_R46_{flop.upper()}_GTO')
        assert (ix['gto_cases'],ix['locked_cases'],ix['verified_cases'])==(1,0,1)
        assert ix['target_line']=='x b50 c/x' and ix['turn']==p['turn']
        assert ix['frozen_high_frequency_rank']==46
        assert ix['exact_target_actor_IP_strict_combos']==p['target_exact_actor_IP_strict_combos']
        assert ix['no_generic_model_certification'] is True and ix['immediate_CERT_upgrades']==0
        assert ix['gzip_sha256']==sha(gz)
        assert ix['source_sha256']==hashlib.sha256(gzip.decompress(gz.read_bytes())).hexdigest()
        assert (ix['original_parent_GTO_root_SHA256'],
             ix['original_parent_GTO_job_SHA256'],
             ix['original_parent_GTO_manifest_SHA256'])==(
             p['original_gto_root_sha256'],
             p['original_gto_job_sha256'],
             p['original_gto_manifest_sha256'])
        assert data['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
        assert not data['errors'] and data['exact_board_gto_sources']==1
        assert data['imputed_pool_locked_sources']==0 and len(data['artifacts'])==1
        a=data['artifacts'][0]
        assert a['version']=='gto' and a['spot']=='LMP_CO_BB' and a['flop']==flop
        assert len(a['cases'])==1
        case=a['cases'][0]
        assert (case['flop_line'],case['turn'])==('x b50 c',p['turn'])
        assert case['gto_exploitability_pct'] is not None and case['gto_exploitability_pct']<=.5
        actual=[n for n in case['nodes'] if n['acting_seat']==1 and
            n['exact_node_line']=='x b50 c/x' and len(n['public_board'])==8 and
            n['strictly_reachable_combos']>0 and
            abs(n['node_spr']-19.55)/19.55<=.05]
        assert len(actual)>0
        assert sum(n['strictly_reachable_combos'] for n in actual)==p['target_exact_actor_IP_strict_combos']
        assert m.get('turns')==[p['turn']]
        assert m.get('original_B282_parent_pin_sha256')==sha(pinpath)
        assert (m.get('gto_parent_source_sha256'),
          m.get('flop_root_jobfile_sha256'),
          m.get('gto_parent_source_manifest_sha256'))==(
            p['original_gto_root_sha256'],
            p['original_gto_job_sha256'],
            p['original_gto_manifest_sha256'])
        return True
    except (OSError,KeyError,TypeError,ValueError,EOFError,AssertionError,StopIteration):
        return False


def authorized_b210_rank46_original_B3_LMP_CO_IP_xb50_x(m):
    """Rank46 only, exact 9s6h3d/Ts source-blind original B3 GTO SHA.

    Full 100bb limped GTO flop is byte-identical run44666294821;
    the actual fresh BB-villain NL2 pooled-marginal IP child uses exact
    x b50 c / x turn state only, with no inferred hole-card conditionals.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
        m.get('flop')=='9s6h3d' and m.get('selected_lines')==['x b50 c'] and
        m.get('selected_turn_lines')==['x x'] and
        m.get('flop_line_policy')=='checked-b50only' and
        m.get('turn_line_policy')=='xxonly' and
        m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
        m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B209_RANK46_B3_GTO' and
        m.get('gto_parent_source_run_id')==44666294821 and
        m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
        m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS'):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b209_rank46_lmp_9s6h3d_original_b3_gto_pin.json'
    archive=d/'solver_evidence/NL2_MULTIBOARD_B3.json.gz'
    idx=d/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
    ledger=d/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
    try:
        import gzip
        pin=json.loads(pinfile.read_text())
        index=json.loads(idx.read_text())
        b175=json.loads(ledger.read_text())
        row=next(q for q in b175['rows'] if q['rank']==46)
        exact=[q for q in row['exact_authentic_gto_source_proofs'] if
            q['flop']=='9s6h3d' and q['turn']=='Ts' and
            q['source_run']==44666294821 and
            q['source_sha']==pin['original_GTO_case_SHA256'] and
            q['exact_line']=='x b50 c/x' and q['actor']==1 and
            q['strict_legal_combos']>0 and q['GTO_gap_pct']<=.5 and
            q['SPR_error_pct']<=5 and not q['true_NL2_actor_locked']]
        return (
            pin['schema']=='NL2_HU_B209_RANK46_ORIGINAL_B3_9S6H3D_GTO_PARENT_PIN_V1' and
            pin['source_run_id']==index['run_id']==44666294821 and
            pin['target_rank']==46 and pin['model_id']=='ln-iso-lmp_t_model-17z0wyl' and
            pin['flop']=='9s6h3d' and pin['turn']=='Ts' and pin['actor']==1 and
            pin['spot']=='LMP_CO_BB' and pin['original_GTO_flop_line']=='x b50 c' and
            pin['exact_turn_line']=='x b50 c/x' and
            pin['strict_original_GTO_actor_IP_combos']>0 and bool(exact) and
            pin['original_full_GTO_flop_not_recomputed'] is True and
            pin['assumed_preflop_169class_not_observed'] is True and
            pin['original_B3_archive_sha256']==index['gzip_sha256']==sha(archive) and
            pin['original_B3_index_sha256']==sha(idx) and
            index['source_sha256']==hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() and
            m.get('turns')==['Ts'] and
            m.get('original_B209_parent_pin_sha256')==sha(pinfile) and
            m.get('gto_parent_source_sha256')==pin['original_gto_root_sha256'] and
            m.get('flop_root_jobfile_sha256')==pin['original_gto_job_sha256'] and
            m.get('gto_parent_source_manifest_sha256')==pin['original_gto_manifest_sha256'])
    except (OSError,ValueError,KeyError,TypeError,EOFError,StopIteration,AssertionError):
        return False


def authorized_b294_rank71_new_exact_GTO_OOP_child(m):
    """Only a fully SHA-pinned, positive legal BB-OOP actor RIVER original
    100bb GTO on B290/B293/B296/B298 exact FLOP/TURN can authorize a genuine NL2
    downstream-only Rust partial OOP lock, never a generic model CERT.
    """
    specs={'As7h3d':('B290',44948738190),'QsJh4d':('B293',44951459377),'Js8h3d':('B296',44951459385),'5s5h3d':('B298',44950943882)}
    flop=m.get('flop')
    if flop not in specs:return False
    batch,run=specs[flop]
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_oop'
      and m.get('selected_lines')==['b50 c'] and
      m.get('selected_turn_lines')==['x b50 c'] and
      m.get('flop_line_policy')=='oop-b50only' and
      m.get('turn_line_policy')=='xb50only' and
      m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
      m.get('NL2_hero_lock_scope')=='TURN_RIVER_ONLY_FROM_SHA_PINNED_B294_RANK71_GTO' and
      m.get('gto_parent_source_run_id')==run and
      m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
      m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS' and
      m.get('restricted_tree_assumption') is False and
      m.get('flop_size_profile')=='full'):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinpath=d/f'nl2_hu_{batch.lower()}_rank71_lmp_{flop}_gto_parent_pin.json'
    idxpath=d/f'solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.index.json'
    srcgz=d/f'solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.json.gz'
    try:
        import gzip
        p=json.loads(pinpath.read_text());idx=json.loads(idxpath.read_text())
        raw=gzip.decompress(srcgz.read_bytes());g=json.loads(raw)
        assert p['schema']==f'NL2_HU_{batch}_RANK71_LMP_{flop.upper()}_GTO_PARENT_PIN_V1'
        assert (p['source_run_id'],idx['run_id'],g['source_run_id'])==(run,run,run)
        assert (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
          'LMP_CO_BB',flop,'b50 c','x b50 c')
        assert (p['target_rank'],p['model_id'])==(71,'ln-iso-lmp_r_model-vlgh2t')
        assert p['observed_preflop_ranges'] is False and p['assumed_limped_169class'] is True
        assert p['original_full_100bb_lmp_gto_not_recomputed'] is True
        assert p['direct_nl2_lock_source_present'] is False
        assert p['target_exact_actor_OOP_river_nodes']>0
        assert p['target_exact_actor_OOP_strict_combos']>0
        assert idx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
        assert idx['batch']==f'{batch}_R71_{flop.upper()}_GTO'
        assert (idx['gto_cases'],idx['locked_cases'],idx['verified_cases'])==(1,0,1)
        assert idx['no_generic_model_certification'] and idx['immediate_CERT_upgrades']==0
        assert idx['target_line']=='b50 c/x b50 c/'
        assert idx['turn']==p['turn']
        assert idx['exact_target_actor_OOP_strict_combos']==p['target_exact_actor_OOP_strict_combos']
        assert idx['exact_target_actor_OOP_river_nodes']==p['target_exact_actor_OOP_river_nodes']
        assert idx['source_sha256']==hashlib.sha256(raw).hexdigest()
        assert idx['gzip_sha256']==sha(srcgz)
        assert (idx['original_parent_GTO_root_SHA256'],
          idx['original_parent_GTO_job_SHA256'],
          idx['original_parent_GTO_manifest_SHA256'])==(
          p['original_gto_root_sha256'],p['original_gto_job_sha256'],
          p['original_gto_manifest_sha256'])
        assert g['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
        assert not g['errors'] and g['exact_board_gto_sources']==1
        assert g['imputed_pool_locked_sources']==0 and len(g['artifacts'])==1
        a=g['artifacts'][0]
        assert a['spot']=='LMP_CO_BB' and a['flop']==flop and a['version']=='gto'
        assert len(a['cases'])==1
        case=a['cases'][0]
        assert (case['flop_line'],case['turn'])==('b50 c',p['turn'])
        assert case['gto_exploitability_pct'] is not None and case['gto_exploitability_pct']<=.5
        assert case['empirical_scope'].startswith('ASSUMED')
        positive=[n for n in case['nodes'] if n['exact_node_line']=='b50 c/x b50 c/'
             and n['acting_seat']==0 and len(n['public_board'])==10
             and n['strictly_reachable_combos']>0
             and abs(n['node_spr']-9.916)/9.916<=.05]
        assert positive and sum(n['strictly_reachable_combos'] for n in positive)==p['target_exact_actor_OOP_strict_combos']
        assert m.get('turns')==[p['turn']]
        assert m.get('original_B294_parent_pin_sha256')==sha(pinpath)
        assert (m.get('gto_parent_source_sha256'),m.get('flop_root_jobfile_sha256'),
          m.get('gto_parent_source_manifest_sha256'))==(
          p['original_gto_root_sha256'],p['original_gto_job_sha256'],
          p['original_gto_manifest_sha256'])
        return True
    except (OSError,KeyError,TypeError,ValueError,EOFError,AssertionError,StopIteration):
        return False


def authorized_b212_rank71_exact_B207_gto_parent(m):
    """Only original individually successful B207 full GTO and its independently
    SHA-audited source/index can authorize true downstream exp_oop NL2.
    The original LMP 169-class preflop is ASSUMED. Zero legal GTO
    actor-OOP river combos fails closed; never manufacture a texture CERT.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_oop' and
            m.get('flop')=='6s4h2d' and
            m.get('selected_lines')==['b50 c'] and
            m.get('selected_turn_lines')==['x b50 c'] and
            m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
            m.get('flop_line_policy')=='oop-b50only' and
            m.get('turn_line_policy')=='xb50only' and
            m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
            m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS' and
            m.get('gto_parent_source_run_id')==44882288427):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b207_rank71_lmp_6s4h2d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B207_R71_6S4H2D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B207_R71_6S4H2D_GTO.json.gz'
    try:
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        import gzip
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B207_RANK71_LMP_6S4H2D_GTO_PARENT_PIN_V1' and
          p['source_run_id']==44882288427 and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','6s4h2d','b50 c','x b50 c') and
          p['target_rank']==71 and p['model_id']=='ln-iso-lmp_r_model-vlgh2t' and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['target_exact_actor_OOP_river_nodes']>0 and
          p['target_exact_actor_OOP_strict_combos']>0 and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B207_R71_6S4H2D_GTO' and
          (i['run_id'],i['gto_cases'],i['locked_cases'],i['verified_cases'])==(
             44882288427,1,0,1) and
          i['exact_target_actor_OOP_river_nodes']>0 and
          i['exact_target_actor_OOP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'] and
          m.get('original_B212_parent_pin_sha256')==sha(pinfile))
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False

def authorized_b213_rank313_exact_B208_gto_parent(m):
    """Only original individually successful B208 full GTO and its independently
    SHA-audited source/index can authorize true downstream exp_ip NL2.
    The original LMP 169-class preflop is ASSUMED. Zero legal GTO
    actor-IP river combos fails closed; never manufacture a texture CERT.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop')=='8s7h4d' and
            m.get('selected_lines')==['b75 r c'] and
            m.get('selected_turn_lines')==['x b50 c'] and
            m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
            m.get('flop_line_policy')=='oop-b75raisecall' and
            m.get('turn_line_policy')=='xb50only' and
            m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
            m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS' and
            m.get('gto_parent_source_run_id')==44882298058):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b208_rank313_lmp_8s7h4d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B208_R313_8S7H4D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B208_R313_8S7H4D_GTO.json.gz'
    try:
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        import gzip
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B208_RANK313_LMP_8S7H4D_GTO_PARENT_PIN_V1' and
          p['source_run_id']==44882298058 and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','8s7h4d','b75 r c','x b50 c') and
          p['target_rank']==313 and p['model_id']=='ln-iso-lmp_r_model-wpg493' and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['target_exact_actor_IP_river_nodes']>0 and
          p['target_exact_actor_IP_strict_combos']>0 and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B208_R313_8S7H4D_GTO' and
          (i['run_id'],i['gto_cases'],i['locked_cases'],i['verified_cases'])==(
             44882298058,1,0,1) and
          i['exact_target_actor_IP_river_nodes']>0 and
          i['exact_target_actor_IP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'] and
          m.get('original_B213_parent_pin_sha256')==sha(pinfile))
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False

def authorized_b263_rank313_exact_B250_gto_parent(m):
    """Only original independently successful B250 full GTO and its independently
    SHA-audited source/index can authorize true downstream exp_ip NL2.
    The original LMP 169-class preflop is ASSUMED. Zero legal GTO
    actor-IP river combos fails closed; never manufacture a texture CERT.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop')=='6s5h3d' and
            m.get('selected_lines')==['b75 r c'] and
            m.get('selected_turn_lines')==['x b50 c'] and
            m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
            m.get('flop_line_policy')=='oop-b75raisecall' and
            m.get('turn_line_policy')=='xb50only' and
            m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
            m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS' and
            m.get('gto_parent_source_run_id')==44901784001):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b250_rank313_lmp_6s5h3d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B250_R313_6S5H3D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B250_R313_6S5H3D_GTO.json.gz'
    try:
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        import gzip
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B250_RANK313_LMP_6S5H3D_GTO_PARENT_PIN_V1' and
          p['source_run_id']==44901784001 and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','6s5h3d','b75 r c','x b50 c') and
          p['target_rank']==313 and p['model_id']=='ln-iso-lmp_r_model-wpg493' and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['target_exact_actor_IP_river_nodes']>0 and
          p['target_exact_actor_IP_strict_combos']>0 and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B250_R313_6S5H3D_GTO' and
          (i['run_id'],i['gto_cases'],i['locked_cases'],i['verified_cases'])==(
             44901784001,1,0,1) and
          i['exact_target_actor_IP_river_nodes']>0 and
          i['exact_target_actor_IP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'] and
          m.get('original_B263_parent_pin_sha256')==sha(pinfile))
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False

def authorized_b214_rank46_exact_B211_gto_parent(m):
    """Only original individually successful B211 full GTO and its independently
    SHA-audited source/index can authorize true downstream exp_oop NL2.
    The original LMP 169-class preflop is ASSUMED. Zero legal GTO
    actor-OOP river combos fails closed; never manufacture a texture CERT.
    """
    if not (m.get('spot')=='LMP_CO_BB' and m.get('version')=='exp_ip' and
            m.get('flop')=='As9h2d' and
            m.get('selected_lines')==['x b50 c'] and
            m.get('selected_turn_lines')==['x x'] and
            m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK' and
            m.get('flop_line_policy')=='checked-b50only' and
            m.get('turn_line_policy')=='xxonly' and
            m.get('original_full_GTO_flop_byte_identical_not_recomputed') is True and
            m.get('preflop_ranges',{}).get('source')=='ASSUMED_EXPLICIT_169CLASS' and
            m.get('gto_parent_source_run_id')==44882967346):
        return False
    d=pathlib.Path(__file__).resolve().parents[1]/'data'
    pinfile=d/'nl2_hu_b211_rank46_lmp_As9h2d_gto_parent_pin.json'
    indexfile=d/'solver_evidence/NL2_MULTIBOARD_B211_R46_AS9H2D_GTO.index.json'
    sourcegz=d/'solver_evidence/NL2_MULTIBOARD_B211_R46_AS9H2D_GTO.json.gz'
    try:
        p=json.loads(pinfile.read_text());i=json.loads(indexfile.read_text())
        import gzip
        raw=gzip.decompress(sourcegz.read_bytes())
        return (
          p['schema']=='NL2_HU_B211_RANK46_LMP_AS9H2D_GTO_PARENT_PIN_V1' and
          p['source_run_id']==44882967346 and
          p['source_gto_job_id'] is None and
          (p['spot'],p['flop'],p['flop_line'],p['turn_line'])==(
             'LMP_CO_BB','As9h2d','x b50 c','x') and
          p['target_rank']==46 and p['model_id']=='ln-iso-lmp_t_model-17z0wyl' and
          p['original_full_100bb_lmp_gto_not_recomputed'] is True and
          p['observed_preflop_ranges'] is False and
          p['assumed_limped_169class'] is True and
          p['target_exact_actor_IP_turn_nodes']>0 and
          p['target_exact_actor_IP_strict_combos']>0 and
          p['no_generic_model_certification'] is True and
          i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1' and
          i['batch']=='B211_R46_AS9H2D_GTO' and
          (i['run_id'],i['gto_cases'],i['locked_cases'],i['verified_cases'])==(
             44882967346,1,0,1) and
          i['exact_target_actor_IP_turn_nodes']>0 and
          i['exact_target_actor_IP_strict_combos']>0 and
          i['no_generic_model_certification'] is True and
          i['source_sha256']==hashlib.sha256(raw).hexdigest() and
          i['gzip_sha256']==sha(sourcegz) and
          p['original_gto_root_sha256']==m.get('gto_parent_source_sha256') and
          p['original_gto_job_sha256']==m.get('flop_root_jobfile_sha256') and
          p['original_gto_manifest_sha256']==m.get('gto_parent_source_manifest_sha256') and
          i['original_parent_GTO_root_SHA256']==p['original_gto_root_sha256'] and
          i['original_parent_GTO_job_SHA256']==p['original_gto_job_sha256'] and
          i['original_parent_GTO_manifest_SHA256']==p['original_gto_manifest_sha256'] and
          m.get('original_B214_parent_pin_sha256')==sha(pinfile))
    except (OSError,KeyError,TypeError,ValueError,EOFError):
        return False

def strict_medium_evidence(n,raw,seq_mask):
    """Re-evaluate b50 relative-equity distribution ONLY after every past
    hero action was legal under max/near-mix and blockers.
    No empirical private-card NL2 frequencies are invented.
    """
    actions=n['acts']
    if 'b50' not in actions:return dict(eligible=0,preferred=0,candidate=False,status='NO_50PCT_ACTION')
    i=actions.index('b50');actor=n['player'];nh=len(raw['hands'][actor])
    if len(n['w'][actor])!=nh or len(n['eq'])!=nh or len(n['ev'])!=nh*len(actions):
        raise ValueError('Missing equity/EV/w source for strict medium-size proof')
    masks=base64.b64decode(seq_mask,validate=True)
    if len(masks)!=nh:raise ValueError('Sequential mask length changed')
    allhands=[];bet=[];p50=0
    for k,m in enumerate(masks):
        if not m or float(n['w'][actor][k])<=1e-4:continue
        equity=float(n['eq'][k]);weight=float(n['w'][actor][k])
        if not 0<=equity<=1.001:raise ValueError('Invalid source equity')
        allhands.append((equity,weight))
        if m & (1<<i):
            raw_ev=[float(n['ev'][j*nh+k]) for j in range(len(actions))]
            preferred=int(i==max(range(len(raw_ev)),key=lambda x:raw_ev[x]))
            p50+=preferred
            bet.append((equity,weight))
    if not bet:return dict(eligible=0,preferred=0,candidate=False,status='B50_UNREACHABLE_AFTER_PREVIOUS_STREET')
    total=sum(w for _,w in allhands);ordered=sorted(allhands)
    def quantile(frac):
        target=total*frac;acc=0
        for eq,w in ordered:
            acc+=w
            if acc>=target:return eq
        return ordered[-1][0]
    qlo,qhi=quantile(1/3),quantile(2/3)
    low=mid=high=0
    lw=mw=hw=0.
    for eq,w in bet:
        if eq<qlo:low+=1;lw+=w
        elif eq>qhi:high+=1;hw+=w
        else:mid+=1;mw+=w
    eligible=len(bet);fraction=mw/(lw+mw+hw)
    candidate=eligible>=20 and mid>=10 and fraction>=0.20 and (high>=5 or low>=5)
    return dict(eligible=eligible,preferred=p50,
        best_ev_b50_fraction_pct=round(100*p50/eligible,3),
        low_count=low,middle_count=mid,high_count=high,
        mid_reach_mass_fraction_pct=round(100*fraction,3),candidate=bool(candidate),
        status='EXACT_BOARD_STRICT_PATH_NONPOLARIZED_RESEARCH_CANDIDATE_NOT_GENERIC_BET_RECOMMENDATION')
def source_nodes(d,seq):
    out=[]
    for n in d['nodes']:
        k='|'.join((n['board'],n['line'],str(n['player'])))
        strict=seq['nodes'].get(k)
        if strict is None:raise ValueError('No sequential mask for '+k)
        reach=sum(w>1e-4 for w in n['w'][n['player']])
        if reach==0 or strict['count']==0:continue
        spr=(d['stack']-max(n['bets']))/n['pot']
        if spr<0:raise ValueError('Negative SPR')
        medium=strict_medium_evidence(n,d,strict['mask'])

        actor=n['player'];hands=d['hands'][actor];nh=len(hands)
        actions=n['acts'];strictmask=base64.b64decode(strict['mask'],validate=True)
        if len(strictmask)!=nh or len(n['ev'])!=len(actions)*nh or len(n['strat'])!=len(actions)*nh:
            raise ValueError('Missing original CFR EV/strategy dimensions')
        bestlegal=bytearray([255]*nh);bestunrestricted=bytearray([255]*nh)
        weighted=[0.]*len(actions);total=0.
        for k,m in enumerate(strictmask):
            if not m:continue
            prob=[max(0.,float(n['strat'][z*nh+k])) for z in range(len(actions))]
            den=sum(prob)
            if den<=0:raise ValueError('Reachable actor with zero strategy sum')
            prob=[z/den for z in prob]
            ev=[float(n['ev'][z*nh+k]) for z in range(len(actions))]
            permitted=[z for z in range(len(actions)) if m&(1<<z)]
            if not permitted:raise ValueError('Reachable hand but no permissible action')
            bestlegal[k]=max(permitted,key=lambda z:ev[z])
            bestunrestricted[k]=max(range(len(actions)),key=lambda z:ev[z])
            weight=float(n['w'][actor][k]);total+=weight
            for z,pct in enumerate(prob):weighted[z]+=weight*pct
        per_action={act:round(100*weighted[i]/total,3) if total else 0
                    for i,act in enumerate(actions)}
        out.append(dict(public_board=n['board'],exact_node_line=n['line'],
          acting_seat=n['player'],pot_bb=n['pot']/100,
          remaining_bb=(d['stack']-max(n['bets']))/100,
          node_spr=round(spr,6),source_reachable_combos=reach,
          strictly_reachable_combos=strict['count'],
          strictly_reachable_masks_b64=strict['mask'],
          source_actions=n['acts'],
          action_frequency_weighted_pct=per_action,
          strict_legal_best_ev_action_indices_b64=base64.b64encode(bestlegal).decode('ascii'),
          strict_unconstrained_best_ev_action_indices_b64=base64.b64encode(bestunrestricted).decode('ascii'),
          best_ev_scope='CONDITIONAL_RUST_CFR_ACTION_EV_WITHIN_ACTUAL_EXACT_POT_AND_BOARD',
          medium_50pct_eligible_combos=medium['eligible'],
          b50_nonpolarized_relative_equity_research_candidate=medium['candidate'],
          medium_50pct_strict_evidence=medium))
    return out
def lock_scope(d,patterns,version):
    if version=='gto':
        return dict(villain_decision_nodes=0,pattern_matched_nodes=0,
            observed_marginal_source_nodes=0,imputed_assumption_nodes=0,
            unmatched_nodes=0,coverage_pct=None,all_villain_nodes_locked=False)
    villain=1 if version=='exp_oop' else 0
    candidates=[]
    for n in d['nodes']:
        if n['player']!=villain or len(n['acts'])<2:continue
        if not any(float(w)>1e-4 for w in n['w'][villain]):continue
        candidates.append(n)
    observed=imputed=matched=0
    samples=[]
    for n in candidates:
        hits=[item for item in patterns if re.search(item['pat'],n['line'])]
        if not hits:continue
        matched+=1
        # A coarse empirical marginal is NOT a direct conditional observation
        # of this exact bet-size, board, SPR and prior action history.
        first=hits[0]
        scope=first.get('scope','PINNED_MEASURED_NL2_SOURCE')
        if scope.startswith('ASSUMED') or first.get('n',0)<500:
            imputed+=1
        else:observed+=1
        if len(samples)<12:
            samples.append(dict(line=n['line'],board=n['board'],
                first_pattern=first['pat'],source=first.get('source'),
                source_observed_count=first.get('n'),scope=scope))
    total=len(candidates)
    return dict(villain_decision_nodes=total,pattern_matched_nodes=matched,
        observed_marginal_source_nodes=observed,imputed_assumption_nodes=imputed,
        unmatched_nodes=total-matched,
        coverage_pct=round(100*matched/total,3) if total else None,
        all_villain_nodes_locked=bool(total and matched==total),
        matching_examples=samples,
        caveat='Regex/source bucket matching does not prove the Rust driver locked every combo nor its conditional opponent behavior.')

def locked_model_gain(d,version):
    if version=='gto':return None
    info=d.get('info',{})
    before=info.get('ev_gto_vs_pool');after=info.get('ev_exploit')
    seat=1 if version=='exp_ip' else 0
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after)==2:
        return round((float(after[seat])-float(before[seat]))/100,5)
    return None

def verify(root,source_pin,run_id):
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
    from hu_sequential_cfr_reach import game_reach
    src=source_pin.resolve()
    expected_pool=sha(src/'inputs/pool_stats.json')
    reports=[]
    rejects=[]
    accum=collections.Counter()
    for ad in sorted(root.iterdir()):
        if not ad.is_dir() or not (ad.name.startswith('nl2-stage3-') or ad.name.startswith('nl2-multiboard-')):
            continue
        manifest=list((ad/'evidence').glob('*.json'))
        if len(manifest)!=1:
            rejects.append(dict(artifact=ad.name,reason='Expected one actual solver manifest'))
            continue
        m=json.loads(manifest[0].read_text())
        info=dict(artifact=ad.name,spot=m['spot'],version=m['version'],flop=m['flop'],cases=[],
            excludes=m.get('skipped',[]),errors=m.get('failures',[]))
        try:
            if m['schema']!='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1' or m['no_generic_certification'] is not True:
                raise ValueError('Not a genuine auditable multi-board solver record')
            if m['spot'] not in REPO_SPOTS or m['version'] not in ('gto','exp_ip','exp_oop'):
                raise ValueError('Unexpected source profile or version')
            if m.get('turn_sizing_mode','default') not in ('default','river-gaps','exact-b66-only'):
                raise ValueError('Unregistered turn subgame size menu')
            permitted_flop_lines={'oop-b33only':'b33 c','oop-b50only':'b50 c',
                'checked-b33only':'x b33 c',
                'oop-b75only':'b75 c','oop-b75raisecall':'b75 r c','checked-b50only':'x b50 c',
                'checked-b75only':'x b75 c',
                'checked-b100only':'x b100 c','checkcheck':'x x'}
            policy=m.get('flop_line_policy','all')
            if policy in permitted_flop_lines:
                if m.get('selected_lines')!=[permitted_flop_lines[policy]]:
                    raise ValueError('Focused flop policy not identical to source action line')
            if m.get('turn_line_policy','default') not in ('default','b100only','b66only','xxonly','xb100only','xb50only','b50only'):
                raise ValueError('Unregistered focused turn continuation')
            fam,pot,stack=REPO_SPOTS[m['spot']]
            if m['pot_family']!=fam or abs(m['root_pot_bb']-pot)>1e-6 or abs(m['root_remaining_bb']-stack)>1e-6:
                raise ValueError('Root pot/SPR assumption mismatch')
            if abs(m['root_spr']-stack/pot)>1e-4:
                raise ValueError('Root SPR mismatch')
            if m['pool_source_sha256']!=expected_pool:
                raise ValueError('NL2 statistical pool source hash mismatch')
            if m['spot'] in ('ISO_BTN_CO','LMP_CO_BB'):
                r=m['preflop_ranges']
                if r['source']!='ASSUMED_EXPLICIT_169CLASS':
                    raise ValueError('Assumed pool mislabeled empirical')
                for seat in ('oop_169','ip_169'):
                    if len(r[seat])!=169 or any(not 0<=float(x)<=1 for x in r[seat].values()) or not sum(r[seat].values()):
                        raise ValueError('Frozen assumed 169 class range invalid')
            else:
                if m.get('pinned_official_legacy_source_id') in (44654973894,44525865923,44653774402):
                    r=m['preflop_ranges']
                    if r.get('source')!='PINNED_LEGACY_OFFICIAL_GTO_FLOP_WEIGHTS':
                        raise ValueError('Official source GTO parent mislabeled as current preflop CFR')
                    pinned_origins={
                      (44654973894,'SB_BB','Ks7h2d'):(
                        'beef22e291953c2d7ecfef8b1eecf2c66495507c5a3ac02e69a8ba8ec6f13ab8',
                        '8765d6b5ddfc47fdb29ac38c3675941e6fcaf51371b8f569c59ed3c3c5065897',
                        '87ab0e76fde687c0cd51d5358b7b97acc1fe35f15b5af8581510f1d59b47cfb0'),
                      (44525865923,'BTN_BB','Ks7s2s'):(
                        '543ee8b77cd22e27488c9d2f491259990f7743013f9843a6486c04864e819925',
                        '50216984f138dc4404f206547ee9c07c05dc4f1e4e9e3af655235bc75ebc74d5',
                        'e0d38da008131f1b9a6d6ce679b08167f160f541a1d9b0e2079fd583e6f3c774'),
                      (44525865923,'BTN_BB','9s6h3d'):(
                        'dad046881f9837e3b3c62fd3c0298db426f0ab731456ecde57651312d527841c',
                        '259105deb64e55228bb6f85b1a3a479c54c4b3f149b697cd74e22bf0a7a18321',
                        '00987298491613f9728d3b97bb6ae28352ff9582bb3e8f3dca725b8d6911d2ce'),
                      (44653774402,'BTN_BB','KsQh4d'):(
                        'f79497797d728792b829f771ac2827d73a71ba777429691c7a0c62afea3bae51',
                        '95a482291bcfd8a826dd1a447a903e1d16096b73eb76c4d7741fe0c74a9f9a6c',
                        'e22e1437ee32cb29555c4fca7bb129e0260c54148ebd4e66b02cad88802ead1d'),
                      (44653774402,'BTN_BB','Js9h4d'):(
                        'c6bdcce708415f34195b7582d35f6dcd5820f90a45339ab3bb647afcc772ffed',
                        '707e525006628c2fda778bf6e8cc6950773f59c3c212f6fc3f79e5ab814082f7',
                        'e4e65078adc3883d0993f947a38fe482e9573553ac847450eda53a3f3f259949')}
                    # B178 original historical B04 CO_BB 8s8h3d, exact root and
                    # full source pin: no blanket new historical spot exemption.
                    if (m.get('spot'),m.get('flop'),m.get('version'),
                        m.get('selected_lines'),m.get('selected_turn_lines'))==(
                          'CO_BB','8s8h3d','exp_ip',['x x'],['x x']):
                        b178pin=json.loads((pathlib.Path(__file__).resolve().parents[1]/
                          'data/nl2_hu_b177_rank138_co_bb_8s8h3d_b04_gto_parent_pin.json').read_text())
                        assert b178pin['schema']=='NL2_HU_B177_RANK138_B04_CO_BB_8S8H3D_GTO_PARENT_PIN_V1'
                        assert b178pin['original_run_id']==44653774402
                        assert b178pin['strict_original_GTO_combo_min']>0
                        pinned_origins[(44653774402,'CO_BB','8s8h3d')]=(
                          b178pin['original_manifest_sha256'],
                          b178pin['original_flop_root_sha256'],
                          b178pin['original_job_sha256'])
                    key=(m['pinned_official_legacy_source_id'],m['spot'],m['flop'])
                    original=pinned_origins.get(key)
                    if original is None:raise ValueError('Original historical GTO source not preregistered')
                    if (r.get('original_official_manifest_sha256'),
                        r.get('original_official_root_sha256'),
                        r.get('original_official_root_job_sha256'))!=original:
                        raise ValueError('Original GTO parent SHA differs from audited B28/B31 pins')
                    if m.get('gto_parent_source_run_id')!=key[0]:
                        raise ValueError('Original source GitHub run differs')
                    if m['spot']=='SB_BB':
                        if m['version']!='exp_oop' or m.get('selected_lines') not in (
                            ['b50 c'],['b75 c'],['x x']):
                            raise ValueError('Wrong original SB_BB actor/line')
                    else:
                        if (m['version'] not in ('exp_oop','exp_ip') or
                            m.get('selected_lines') not in (['x x'],['x b50 c']) or
                            m.get('selected_lines')==['x b50 c'] and m['version']!='exp_oop'):
                            raise ValueError('Wrong original BTN_BB hero actor/action')
                    if r.get('do_not_claim_same_preflop_tree_as_current') is not True:
                        raise ValueError('Missing disclosure that historical preflop source differs')
                    if not isinstance(r.get('legacy_dependency_mismatches'),list) or not r['legacy_dependency_mismatches']:
                        raise ValueError('Mismatch report inconsistent with original pinned legacy source')
                else:
                    if m['preflop_ranges']['source']!='PINNED_POKER_SOLVER_PREFLOP_CFR':
                        raise ValueError('Known SRP/3BP profile without real preflop CFR')
                    if m['preflop_ranges']['full_sha256']!=sha(src/'v8_build/build/pf_data.json'):
                        raise ValueError('Preflop combo weights underlying file changed')
            if m['failures'] or m['solved_cases']!=len(m['cases']) or not m['cases']:
                raise ValueError('Original solver source incomplete')
            base=ad/'solver/postflop'
            flopfile=base/m['file_flop']
            if sha(flopfile)!=m['file_flop_sha256']:
                raise ValueError('Raw flop source sha256 mismatch')
            jobfile=flopfile.with_suffix('.job.json')
            if not jobfile.is_file():raise ValueError('Missing authentic Rust driver flop config')
            j=json.loads(jobfile.read_text());fr=json.loads(flopfile.read_text())
            if fr.get('flop')!=m['flop'] or fr['pot']!=round(100*pot) or fr['stack']!=round(100*stack):
                raise ValueError('Authentic flop model does not match assumed 100bb pot')
            if j['pot']!=round(100*pot) or j['stack']!=round(100*stack):
                raise ValueError('Rust job actual pot/stack inconsistent')
            if m.get('flop_line_policy') in permitted_flop_lines:
                actual_flop_extract=[e.get('prefix',[]) for e in j.get('extract',[]) if e.get('prefix',[])]
                expected_flop=permitted_flop_lines[m['flop_line_policy']].split()
                if m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK':
                    # The previously verified GTO flop solves a larger action
                    # set; the new EXP proof solves ONLY the declared downstream
                    # continuation. The GTO parent must contain our requested line.
                    if not any(p[:len(expected_flop)]==expected_flop for p in actual_flop_extract) and not any(
                            n.get('line')==' '.join(expected_flop)+'/' and n.get('wr')
                            for n in fr.get('nodes',[])):
                        raise ValueError('Exact requested line absent from pinned GTO flop parent')
                # Match the complete declared prefix: x b100 c has THREE tokens,
                # not two. Length-2 policies retain their original strict gate.
                elif not actual_flop_extract or not all(p[:len(expected_flop)]==expected_flop for p in actual_flop_extract):
                    raise ValueError('Actual flop job has unexpected or missing focused action extraction')
            if abs(j['rake_rate']-0.05)>1e-8 or j['rake_cap']!=1000:
                raise ValueError('Unstated rake vs expected NL2 5% max10bb')
            partial_gto_parent=m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK'
            fp=m.get('flop_size_profile','full')
            if fp=='lmp-50-only':
                if m['spot']!='LMP_CO_BB' or m.get('flop_line_policy')!='oop-b50only':
                    raise ValueError('LMP restricted flop tree mismatched declared exact b50 c')
                if j.get('flop_oop')!='50%' or j.get('flop_ip')!='50%' or m.get('flop_action_sizes')!=['50%']:
                    raise ValueError('False 50pct restricted-game claim vs actual Rust menu')
                if m.get('restricted_tree_assumption') is not True:
                    raise ValueError('Missing restricted-tree warning on solver source')
            elif fp=='full':
                if not all(x in j.get('flop_oop','') for x in ('33%','50%','75%','100%')):
                    raise ValueError('Missing actual OOP lead sizes')
                if not all(x in j.get('flop_ip','') for x in ('33%','50%','75%','100%')):
                    raise ValueError('Missing actual IP bet sizes')
            elif fp=='legacy-official-pinned':
                if m.get('pinned_official_legacy_source_id') not in (44654973894,44525865923,44653774402) or not partial_gto_parent:
                    raise ValueError('Historical bet menu not authorized for current GTO tree')
                actual={'oop':j.get('flop_oop'),'ip':j.get('flop_ip'),
                        'raise_sizes':j.get('flop_raise')}
                if m.get('flop_action_sizes')!=actual or m.get('restricted_original_GTO_tree') is not True:
                    raise ValueError('Old GTO flop source bet menu does not match SHA-pinned original Rust job')
                if m.get('pinned_official_legacy_source_id') in (44525865923,44653774402):
                    # Independently SHA-pinned original BTN_BB GTO source run
                    # 44525865923 may have NO OOP lead menu at the flop.
                    # Do not invent one. Actual ip/raise options are required,
                    # and the complete original job is checked byte-for-byte
                    # against the precommitted B31 original job SHA above.
                    if not (isinstance(actual['ip'],str) and actual['ip'] and
                            isinstance(actual['raise_sizes'],str) and actual['raise_sizes'] and
                            isinstance(actual['oop'],str)):
                        raise ValueError('Historical BTN_BB original IP/raise menu missing')
                elif not all(isinstance(actual[x],str) and actual[x] for x in ('oop','ip','raise_sizes')):
                    raise ValueError('Missing original historical flop sizing options')
            else: raise ValueError('Unknown flop size proof profile')
            if m['version']=='gto' and j.get('hero') is not None:
                raise ValueError('GTO job unexpectedly locks a hero')
            if partial_gto_parent:
                if m['version']=='gto' or j.get('hero') is not None or j.get('locks'):
                    raise ValueError('Copied GTO flop root mislabeled as locked flop')
                if m.get('flop_root_jobfile_sha256')!=sha(jobfile):
                    raise ValueError('Pinned GTO root Rust job SHA changed')
                if m.get('gto_parent_source_sha256')!=sha(flopfile):
                    raise ValueError('Pinned GTO parent raw flop SHA changed')
                if int(m.get('gto_parent_source_run_id',0))<=0:
                    raise ValueError('Missing immutable original GTO run ID')
                if m.get('turn_line_policy') not in ('b100only','b66only','xxonly','xb100only','xb50only','b50only'):
                    raise ValueError('Partial GTO parent lock requires fixed turn continuation')
            else:
                if m['version']!='gto' and j.get('hero')!=(1 if m['version']=='exp_ip' else 0):
                    raise ValueError('Locked hero seat is wrong')
                if m['version']!='gto' and not j.get('locks'):
                    raise ValueError('Pool locked variant has no lock patterns')
            for c in m['cases']:
                rawfile=base/c['source_path']
                if sha(rawfile)!=c['source_sha256']:
                    raise ValueError('Subgame SHA mismatch '+c['source_path'])
                turn_policy=m.get('turn_line_policy')
                if turn_policy in ('b100only','b66only','xxonly','xb100only','xb50only','b50only'):
                    token=(['x','x'] if turn_policy=='xxonly' else
                           ['x','b50','c'] if turn_policy=='xb50only' else
                           ['x','b100','c'] if turn_policy=='xb100only' else
                           ['b66','c'] if turn_policy=='b66only' else
                           ['b50','c'] if turn_policy=='b50only' else ['b100','c'])
                    if turn_policy=='b50only' and not (
                        m['spot']=='SB3_BTN' and m['version']=='exp_oop' and
                        m['flop']=='Jh9d6s' and m.get('selected_lines')==['b33 c'] and
                        m.get('selected_turn_lines')==['b50 c'] and
                        m.get('gto_parent_source_run_id')==44837416843 and
                        m.get('gto_parent_source_sha256')=='51d421761aa0cfc81f3c951b6c9854e56cecbe53f9fe084439da19151a4ea9a2' and
                        m.get('flop_root_jobfile_sha256')=='6e6c91ff9841c7662f1b36b39933631dcf22de602f66749e698ef3991641ba1b' and
                        m.get('gto_parent_source_manifest_sha256')=='ab08f31291ed6feb19bdca412c56f8adc9ee5bc06ff43fe6ae6303b0660c2b3f'):
                        raise ValueError('Focused b50-call turn allowed ONLY from byte-identical B117 SB3 Jh9d6s actor OOP GTO parent')
                    if turn_policy=='xxonly' and not (
                        # B214 only if B211 original As9h2d rank46 GTO
                        # proven actor CO-IP x-b50 c/x legal with strict SHA.
                        authorized_b214_rank46_exact_B211_gto_parent(m)
                        or
                        # B210 rank46: only original B209 B3 authentic 9s6h3d
                        # x b50 c/x turn actor-IP positive source 100bb GTO.
                        authorized_b210_rank46_original_B3_LMP_CO_IP_xb50_x(m)
                        or
                        # B282 only if new individually pinned positive actor-IP
                        # original B279/B280 100bb GTO SHA and legal 40/70 combos.
                        authorized_b282_rank46_new_GTO_IP_turn(m)
                        or
                        # B198: only original B197 SB_BB As9h2d/KsQh4d
                        # exact BB IP x b100 c / x x / x from frozen B1/B5.
                        authorized_b198_rank159_original_SB_BB_BB_IP_xb100_xx(m)
                        or
                        # B195 only: SHA-pinned B194 original SB_BB two real
                        # BB-IP x b100 c / x x / x GTO actor-positive sources.
                        authorized_b195_rank159_original_SB_BB_BB_IP_xb100_xx(m)
                        or
                        # B178 historical B04 CO IP 8s8h3d/5s x-x/x-x only.
                        authorized_b178_rank138_b04_co_ip_xx(m)
                        or
                        # B176 rank138 only: B2 independently-successful original
                        # Js9h4d full GTO parent x-x / x-x CO IP run+SHA.
                        authorized_b176_rank138_exact_b2_co_ip_xx(m)
                        or
                        # B167: independently verified exact B165 7s5h3d
                        # GTO parent, IP CO after b33-call/x-x, fixed SHAs.
                        authorized_b167_rank80_exact_true_gto_parent(m)
                        or
                        # B164: individually SUCCESS original B9 genuine
                        # 100bb LMP full-sized GTO flop 4s4h2d, BB OOP
                        # bet33-call, turn 8s OOP check, CO hero IP x-x
                        # locked ONLY from original SHA-pinned flop.
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_ip' and
                         m['flop']=='4s4h2d' and m.get('selected_lines')==['b33 c'] and
                         m.get('selected_turn_lines')==['x x'] and
                         m.get('gto_parent_source_run_id')==44740512245 and
                         m.get('gto_parent_source_sha256')=='227b4fd8d6ff2aa4f5ba394398a98d2b4d29f050191bbfd3d4fb43ebdbecaa54' and
                         m.get('flop_root_jobfile_sha256')=='5293fffecddfe2b86310c5b3a634441ac3b51c4a5d61edabb69693d024f3fcd0' and
                         m.get('gto_parent_source_manifest_sha256')=='bc1a559e0e635d58ef5a44d96a5474f403d784605e2e01c507b86e5b44b1b7d1')
                        or
                        # B149: original independently SHA-audited B147 A-high
                        # 100bb GTO, corrected actor-IP rank46 metadata only.
                        # A true new Rust NL2 partial source is still required.
                        authorized_b149_rank46_exact_gto_parent(m)
                        or
                        # B146 frozen rank46: only genuine B3 9s6h3d GTO
                        # root and exact CO-IP 50%-stab/call flop -> BB check
                        # turn; true Rust NL2 actor-IP turn-only source.
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_ip' and
                         m['flop']=='9s6h3d' and m.get('selected_lines')==['x b50 c'] and
                         m.get('selected_turn_lines')==['x x'] and
                         m.get('gto_parent_source_run_id')==44666294821 and
                         m.get('gto_parent_source_sha256')=='2856dcd71a0d8b4f2f2597ffb5e62cc8b31aeefa3017cbf6f263bcc733716909' and
                         m.get('flop_root_jobfile_sha256')=='5e0dd09079d0e7c63cb92206c705a37686abecfbc65870a37894c91d7e681246' and
                         m.get('gto_parent_source_manifest_sha256')=='e1928c60767bd27371029f56f3d53f0f3471f74d955108cf808ff3090bc85d13')
                        or
                        # B144 frozen rank47: original B3 individually-successful
                        # *full* 100bb limped GTO parent, actor IP CO at turn
                        # after flop BB check/CO b33/BB call; turn BB check.
                        # Only these two exact original roots and fixed SHA/jobs.
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_ip' and
                         m['flop']=='8s8h3d' and m.get('selected_lines')==['x b33 c'] and
                         m.get('selected_turn_lines')==['x x'] and
                         m.get('gto_parent_source_run_id')==44666294821 and
                         m.get('gto_parent_source_sha256')=='c5861d2bbcc0361f095b13a8ed3e393785c48ec2a517cee1cafb7c52567ed61c' and
                         m.get('flop_root_jobfile_sha256')=='bbed120f68c2e295febc4715fc2a8f987bf46d2d2802a7e410809fea66ca7907' and
                         m.get('gto_parent_source_manifest_sha256')=='f6922cc27956249d6d69e1c4a184956dc356f67ba8b577194a88a2eccebd3bb7')
                        or
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_ip' and
                         m['flop']=='9s6h3d' and m.get('selected_lines')==['x b33 c'] and
                         m.get('selected_turn_lines')==['x x'] and
                         m.get('gto_parent_source_run_id')==44666294821 and
                         m.get('gto_parent_source_sha256')=='2856dcd71a0d8b4f2f2597ffb5e62cc8b31aeefa3017cbf6f263bcc733716909' and
                         m.get('flop_root_jobfile_sha256')=='5e0dd09079d0e7c63cb92206c705a37686abecfbc65870a37894c91d7e681246' and
                         m.get('gto_parent_source_manifest_sha256')=='e1928c60767bd27371029f56f3d53f0f3471f74d955108cf808ff3090bc85d13')
                        or
                        (m['spot']=='BTN_BB' and m['version']=='exp_oop' and
                         m.get('selected_lines')==['x b50 c'] and
                         m.get('pinned_official_legacy_source_id') in (44525865923,44653774402))
                        or
                        # B98 pinned *full original* B3 GTO LMP root. This is
                        # one source-run+SHA+actor+line exemption, NOT an
                        # authorization to relabel other check-check locks.
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_oop' and
                         m['flop']=='8s8h3d' and m.get('selected_lines')==['x x'] and
                         m.get('gto_parent_source_run_id')==44666294821 and
                         m.get('gto_parent_source_sha256')=='c5861d2bbcc0361f095b13a8ed3e393785c48ec2a517cee1cafb7c52567ed61c' and
                         m.get('flop_root_jobfile_sha256')=='bbed120f68c2e295febc4715fc2a8f987bf46d2d2802a7e410809fea66ca7907' and
                         m.get('gto_parent_source_manifest_sha256')=='f6922cc27956249d6d69e1c4a184956dc356f67ba8b577194a88a2eccebd3bb7')
                        or
                        # B101: single B5 original full-size SB_BB As7h3d GTO
                        # parent, actor OOP. Original EXP timeout is NOT reused.
                        (m['spot']=='SB_BB' and m['version']=='exp_oop' and
                         m['flop']=='As7h3d' and m.get('selected_lines')==['b50 c'] and
                         m.get('gto_parent_source_run_id')==44736420272 and
                         m.get('gto_parent_source_sha256')=='af894c256528d482110eea24682467970fdb2d90cafec6de677cfd46a664b0d3' and
                         m.get('flop_root_jobfile_sha256')=='b86009ee8f620defbf9645bc5219c24b128e103ca6d95bf483b2748735b8ea44' and
                         m.get('gto_parent_source_manifest_sha256')=='af789ac9a2811e81672c59690913ac380bc47124fb9060be5466ce179f73a8f9')
                        or
                        # B104 only: unmodified authentic B1 BTN_BB As9h2d
                        # GTO full-size flop, actor IP. No other source accepted.
                        (m['spot']=='BTN_BB' and m['version']=='exp_ip' and
                         m['flop']=='As9h2d' and m.get('selected_lines')==['x b100 c'] and
                         m.get('gto_parent_source_run_id')==44666285424 and
                         m.get('gto_parent_source_sha256')=='80cbf4e9c56d01f6fb56400006b02029088de5114d3e70d848c3a233157e7a8e' and
                         m.get('flop_root_jobfile_sha256')=='f23084dbc9a1f9539c5d52ab57d91d62253c794e000fb96b87321e274e888a19' and
                         m.get('gto_parent_source_manifest_sha256')=='385c2fc4341b185633345d617638ea71c1a922b5cfe6297625c0a44cb6678fbb7')
                        or
                        # B129: exact B124 BTN_BB As7h3d pinned original GTO
                        # and fresh NL2 IP turn-only genuine Rust continuation.
                        (m['spot']=='BTN_BB' and m['version']=='exp_ip' and
                         m['flop']=='As7h3d' and m.get('selected_lines')==['b33 c'] and
                         m.get('selected_turn_lines')==['x x'] and
                         m.get('gto_parent_source_run_id')==44839543260 and
                         m.get('gto_parent_source_sha256')=='afc78d90660b563671bad694f20e9de4eb9aa4b7c38101a7136b926a3b6e80c1' and
                         m.get('flop_root_jobfile_sha256')=='f76c10266568e783726d05aeed4107c0db9295bc7dfe1cd9a055526d38fea036' and
                         m.get('gto_parent_source_manifest_sha256')=='009a322dc392543e9675a3c03582fa9cd2bda5e7ef48aafcc8bff8f1450945f0')):
                        raise ValueError('x-x extraction outside individually SHA-pinned B98/B101/B104/B129/B164/B167 actor parents')
                    if turn_policy=='xb100only' and not (
                        # B204 original B203 rank190 B1 true GTO BB-IP exactly
                        # 8s8h3d/Js9h4d x b75 c / x b100 c / x only.
                        authorized_b204_rank190_original_SB_BB_BB_IP_xb75_xb100(m)
                        or
                        # B200: exact original B199 B1/B4 SB_BB true GTO
                        # 8s8h3d/9s6h3d BB IP x b50 c / x b100 c / x only.
                        authorized_b200_rank188_original_SB_BB_BB_IP_xb100_xx(m)
                        or
                        # B192 only: B191 SHA original B3 rank201 8s8h3d/9s6h3d
                        # exact x b33 c / x b100 c / x CO IP legal combo.
                        authorized_b192_rank201_exact_original_B3_CO_IP_xb33_xb100(m)
                        or
                        m['spot']=='CO_BB' and m['version']=='exp_ip' and
                        m['flop']=='Js9h4d' and m.get('selected_lines')==['x b33 c'] and
                        m.get('selected_turn_lines')==['x b100 c'] and
                        m.get('gto_parent_source_run_id')==44666290556 and
                        m.get('gto_parent_source_sha256')=='1e55a710787d36d684eaa03a5c3f7a5abc89eb85b0df4c7906cc27a76922b47d' and
                        m.get('flop_root_jobfile_sha256')=='1411f3b3f44d1f2aa2186c3d3ca6bc67042d790bd0be8f3667e0a5f7a8eb39ac' and
                        m.get('gto_parent_source_manifest_sha256')=='113506aa83161e8a3ad8dd98875023c75f8ec4a51e610ba02ea7ab5485fcee52'):
                        raise ValueError('Focused x-b100-call turn allowed ONLY from B107 individually SHA-pinned original B2 CO_BB IP GTO root')
                    if turn_policy=='xb50only' and not (
                        # B213 only original positive B208 GTO 8s7h4d
                        # SHA, rank313, exact actor and source line.
                        authorized_b263_rank313_exact_B250_gto_parent(m)
                        or
                        authorized_b213_rank313_exact_B208_gto_parent(m)
                        or
                        # B212 only original positive B207 GTO 6s4h2d
                        # SHA, rank71, exact actor and source line.
                        authorized_b212_rank71_exact_B207_gto_parent(m)
                        or
                        # B294 only if independent original B290 or B293 100bb
                        # LMP GTO SHA + BB OOP river 40/70 combos strictly positive.
                        authorized_b294_rank71_new_exact_GTO_OOP_child(m)
                        or
                        # B189: exact B188 SHA-pinned B3 original LMP CO-IP
                        # x b33 c / x b50 c, only on two original true GTO flops.
                        authorized_b189_rank199_202_B3_original_gto_IP_xb33_xb50(m)
                        or
                        # B181: only B180 positive legal actor-BB-OOP, exact 7s7h2d
                        # GTO pinned job/root/manifest SHA; never texture generalization.
                        authorized_b181_rank71_exact_B180_gto_parent(m)
                        or
                        # B160: only individually source-proven B156 full GTO
                        # and positive exact BB OOP strict river sequence.
                        authorized_b160_rank71_exact_true_gto_parent(m)
                        or
                        # B163 requires exact positive B158 b75-raise-call
                        # GTO original and true actor CO-IP terminal river.
                        authorized_b163_rank313_exact_true_gto_parent(m)
                        or
                        m['spot']=='UTG_CO' and m['version']=='exp_ip' and
                        m['flop']=='9s6h3d' and m.get('selected_lines')==['b75 c'] and
                        m.get('selected_turn_lines')==['x b50 c'] and
                        m.get('gto_parent_source_run_id')==44806967313 and
                        m.get('gto_parent_source_sha256')=='efd7295c361a9a0cb559a004b77f16d2a9ed2e73a19d1c6125659f7a451c6ee6' and
                        m.get('flop_root_jobfile_sha256')=='8c58597e5114bd178abeb880f3fe4d6912cba8b1fa7b6788853096df6a5d2c62' and
                        m.get('gto_parent_source_manifest_sha256')=='a8fc7e0d02b5badaa82c56faa54e985ff11075eff023519836034e7ed101812e'
                        or
                        # B121 source: B114 CO_BB GTO has finished with a
                        # verified verbatim root/job/manifest SHA. The genuine
                        # Rust EXP_IP task solves ONLY the exact turn child.
                        # Never reuse its GTO flop file as an EXP flop solve.
                        (m['spot']=='CO_BB' and m['version']=='exp_ip' and
                         m['flop']=='8s8h3d' and m.get('selected_lines')==['x x'] and
                         m.get('selected_turn_lines')==['x b50 c'] and
                         m.get('gto_parent_source_run_id')==44836834970 and
                         m.get('gto_parent_source_sha256')=='af2fcbadbf848208f4046b4098b60dce01618863d76deaaecb35648f7b139741' and
                         m.get('flop_root_jobfile_sha256')=='9d1d6fc120154cb70881f2bda9c0d29fd0d7ddc219b154c25d02c932a9cbbafb' and
                         m.get('gto_parent_source_manifest_sha256')=='2e908a15bba6701cd7fa3bb1079d99a3a985cb05ef586b95eef9f00805c0d2fe')
                        or
                        # B126 only: exact SHA-pinned original B116 LMP root
                        # (ASSUMED_EXPLICIT_169CLASS limped preflop), actor
                        # OOP BB hero lock in the true turn/river child.
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_oop' and
                         m['flop']=='As7h3d' and m.get('selected_lines')==['b50 c'] and
                         m.get('selected_turn_lines')==['x b50 c'] and
                         m.get('gto_parent_source_run_id')==44837377803 and
                         m.get('gto_parent_source_sha256')=='7a66b9e3495aaa1a113136bec64181f50b3b87046e351a0d5a73826eda3f1601' and
                         m.get('flop_root_jobfile_sha256')=='92a3ee4289cd1a85e7f9766e770d940eb70e3e3c35b437691395abaefaa1c10b' and
                         m.get('gto_parent_source_manifest_sha256')=='7199156c5b98fd7f51f732cc721a1eaefb718013ca50e4d29ed3a35b1159f433')
                        or
                        # B128 source: B119 authentic original b75-raise-call
                        # GTO flop parent; LMP assumed 169-class preflop,
                        # downstream actor-IP NL2 turn+river is an actual
                        # fresh Rust source, never an inferred GTO texture.
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_ip' and
                         m['flop']=='As7h3d' and m.get('selected_lines')==['b75 r c'] and
                         m.get('selected_turn_lines')==['x b50 c'] and
                         m.get('gto_parent_source_run_id')==44837834984 and
                         m.get('gto_parent_source_sha256')=='3531438b93c5185182fa7bb0ab4d95dd1025e7e1fe5da3d18b58cee4eec87573' and
                         m.get('flop_root_jobfile_sha256')=='b6cc92f2dd7d5995b8e26f959420a0a5677769b9f1918208a2ea4e4f99d6653e' and
                         m.get('gto_parent_source_manifest_sha256')=='e7a2817f866609cafd48d3dc20f34372b87fb77522d45facda8c5088f67a49ca')
                        or
                        # B138: individually successful B134 LMP_CO_BB
                        # 9s6h3d genuine GTO source (original B134 run overall
                        # cancelled due EXP_OOP). A fresh Rust EXP_OOP turn
                        # child reuses ONLY the byte-identical GTO parent.
                        # All 169 limped ranges remain explicitly ASSUMED.
                        (m['spot']=='LMP_CO_BB' and m['version']=='exp_oop' and
                         m['flop']=='9s6h3d' and m.get('selected_lines')==['b50 c'] and
                         m.get('selected_turn_lines')==['x b50 c'] and
                         m.get('gto_parent_source_run_id')==44841724661 and
                         m.get('gto_parent_source_sha256')=='cab2bcdadebdaafc1dcacd0a9b1eb9c656b8864f486f2542b1abe39ebe6c2eb6' and
                         m.get('flop_root_jobfile_sha256')=='3f7c036d8aac871a2cabc5ddffc94c42ce51d43520d9cdee620add8dbe6072bf' and
                         m.get('gto_parent_source_manifest_sha256')=='2ec67f19079a7946bb0b771d5a865372cc90a645c350663bda352ad8e5bb569c')):
                        raise ValueError('Focused x-b50-call turn requires exact SHA-pinned B113/B121/B126/B128/B138 parent')
                    if m.get('selected_turn_lines')!=[' '.join(token)]:
                        raise ValueError('Focused turn extraction differs from predeclared line')
                    subjobfile=rawfile.with_suffix('.job.json')
                    if not subjobfile.is_file():
                        raise ValueError('Missing true focused turn Rust job config')
                    subjob=json.loads(subjobfile.read_text())
                    sub_extract=[e.get('prefix',[]) for e in subjob.get('extract',[]) if e.get('prefix',[])]
                    if not sub_extract or not all(p[:len(token)]==token for p in sub_extract):
                        raise ValueError('Actual Rust focused turn action extraction mismatch')
                if m.get('turn_sizing_mode')=='river-gaps':
                    real_job=rawfile.with_suffix('.job.json')
                    if not real_job.exists():raise ValueError('No exact turn-river solver config')
                    j2=json.loads(real_job.read_text())
                    if j2.get('turn_oop')!='33%,66%,75%' or j2.get('turn_ip')!='33%,66%,75%':
                        raise ValueError('Actual solved turn sizes differ from predeclared river-gaps menu')
                if m.get('turn_sizing_mode')=='exact-b66-only':
                    if (m['spot']!='SB_BB' or
                        (m['version']!='gto' and not partial_gto_parent) or
                        m.get('selected_lines')!=['x x'] or
                        m.get('selected_turn_lines')!=['b66 c']):
                        raise ValueError('Exact 66% source requires predeclared SB_BB x-x and genuine original GTO flop parent')
                    exact_job=rawfile.with_suffix('.job.json')
                    if not exact_job.is_file():raise ValueError('Missing exact b66 Rust turn job')
                    cfg=json.loads(exact_job.read_text())
                    if cfg.get('turn_oop')!='66%' or cfg.get('turn_ip')!='66%':
                        raise ValueError('Actual Rust menu not exclusive 66%, may merge with 75')
                    ex=[z.get('prefix',[]) for z in cfg.get('extract',[]) if z.get('prefix',[])]
                    if not ex or not all(z[:2]==['b66','c'] for z in ex):
                        raise ValueError('Exact b66 river extraction missing')
                if partial_gto_parent:
                    actual_subjob=rawfile.with_suffix('.job.json')
                    if not actual_subjob.is_file():raise ValueError('No genuine downstream Rust EXP job')
                    sj=json.loads(actual_subjob.read_text())
                    hero=1 if m['version']=='exp_ip' else 0
                    if sj.get('hero')!=hero or not sj.get('locks'):
                        raise ValueError('Turn-only lock lacks correct hero/real subgame locks')
                    if abs(sj.get('rake_rate',-1)-0.05)>1e-8 or sj.get('rake_cap')!=1000:
                        raise ValueError('Turn-only true Rust job rake differs from NL2')
                d=json.loads(rawfile.read_text())
                if m.get('turn_sizing_mode')=='exact-b66-only':
                    if not any(n['line']=='x x/' and 'b66' in n.get('acts',[]) for n in d['nodes']):
                        raise ValueError('Actual Rust root lacks distinct b66 action')
                    if not any(n['line']=='x x/b66 c/' and len(n['board'])==10 for n in d['nodes']):
                        raise ValueError('Actual Rust river lacks exact b66 call branch')
                if d['flop']!=m['flop'] or d['turn']!=c['turn'] or d['line0']!=c['line']:
                    raise ValueError('Wrong flop-to-turn lineage')
                parent=next((n for n in fr['nodes'] if n['line']==c['line']+'/' and n['board'][-2:]==c['turn']),None)
                if parent is None:raise ValueError('No exact flop parent '+c['line'])
                pp=parent['pot']/100;rem=(fr['stack']-max(parent['bets']))/100
                if abs(pp-c['flop_parent_pot_bb'])>1e-5 or abs(rem-c['flop_parent_effective_remaining_bb'])>1e-5 or abs(rem/pp-c['real_flop_parent_spr'])>1e-5:
                    raise ValueError('Parent authentic SPR inconsistent')
                gg=d['info'].get('gto_expl_pct')
                hh=d['info'].get('hero_gap_pct')
                if gg is None or gg>0.5:
                    raise ValueError('GTO equilibrium gap >0.5% '+str(gg))
                if m['version']!='gto' and (hh is None or hh>0.5):
                    raise ValueError('Locked hero gap >0.5% '+str(hh))
                if c['true_river_nodes']!=sum(len(n['board'])==10 for n in d['nodes']):
                    raise ValueError('Declared river CFR node count wrong')
                sequential,proof=game_reach(fr,d)
                if not proof['sequential_actor_combo_nodes']:
                    # Real CFR solved the game, but this branch is impossible
                    # under the user-mandated max/near action policy.
                    # Never publish an unreachable exact-board GTO example.
                    info['excludes'].append(dict(line=c['line'],turn=c['turn'],
                        source_sha256=c['source_sha256'],
                        reason='SOLVED_CFR_BUT_ALL_COMBOS_UNREACHABLE_AFTER_STRICT_MULTISTREET_POLICY'))
                    accum['authentic_cfr_cases_excluded_by_reachability']+=1
                    continue
                nodes=source_nodes(d,dict(nodes=sequential))
                locked=lock_scope(d,m['locks'],m['version'])
                gain=locked_model_gain(d,m['version'])
                if not nodes:
                    info['excludes'].append(dict(line=c['line'],turn=c['turn'],
                        source_sha256=c['source_sha256'],
                        reason='SOLVED_CFR_BUT_NO_STRICT_ACTOR_COMBOS'))
                    accum['authentic_cfr_cases_excluded_by_reachability']+=1
                    continue
                source=dict(run_id=run_id,artifact=ad.name,
                  pot_family=fam,spot=m['spot'],version=m['version'],flop=m['flop'],
                  turn=c['turn'],flop_line=c['line'],flop_root_pot_bb=pot,
                  flop_root_stack_bb=stack,flop_source_sha256=m['file_flop_sha256'],
                  root_spr=m['root_spr'],turn_spr=c['real_flop_parent_spr'],
                  source_sha256=c['source_sha256'],gto_exploitability_pct=gg,
                  locked_hero_gap_pct=hh,flop_size_menu=(
                      [p.strip() for p in j['flop_oop'].split(',')]
                      if m.get('pinned_official_legacy_source_id') in (44654973894,44525865923,44653774402)
                      else ['33%','50%','75%','100%']),
                  NL2_pool_source_sha256=expected_pool,
                  lock_patterns=m['locks'] if m['version']!='gto' else [],
                  lock_coverage_pct=locked['coverage_pct'],
                  villain_lock_scope=locked,
                  hero_model_gain_bb=gain,
                  rust_source_lock_stats=d['info'].get('lock_stats',{}),
                  medium50_strict_eligible_total=sum(n['medium_50pct_eligible_combos'] for n in nodes),
                  medium50_strict_merged_research_nodes=sum(bool(n['b50_nonpolarized_relative_equity_research_candidate']) for n in nodes),
                  assumed_missing_rate_policy=m['unknown_action_frequency_policy'],
                  empirical_scope=('ASSUMED_PREFLOP_RANGES' if fam in ('ISO','LMP')
                      else 'PINNED_LEGACY_OFFICIAL_GTO_FLOP_WEIGHTS' if m.get('pinned_official_legacy_source_id') in (44654973894,44525865923,44653774402)
                      else 'PINNED_PREFLOP_CFR'),
                  certified_scope=('EXACT_BOARD_ONLY_GTO' if m['version']=='gto'
                      else 'TURN_ONLY_NL2_MARGINAL_LOCK_FROM_PINNED_GTO_FLOP_PARENT'
                      if partial_gto_parent else 'PARTIALLY_LOCKED_NL2_MARGINAL_PROXY'),
                  hands_by_seat=d['hands'],
                  strict_combo_path_summary=dict(proof),nodes=nodes)
                info['cases'].append(source)
                accum['verified_cases']+=1
                accum['gto' if m['version']=='gto' else 'pool_locked_experimental']+=1
                accum['sequential_actor_combo_nodes']+=proof['sequential_actor_combo_nodes']
                accum['individually_proved_nodes']+=len(nodes)
                accum['medium50_strict_eligible_combo_nodes']+=sum(n['medium_50pct_eligible_combos'] for n in nodes)
                accum['medium50_strict_research_candidate_nodes']+=sum(bool(n['b50_nonpolarized_relative_equity_research_candidate']) for n in nodes)
                accum['vil_observed_marginal_lock_match_nodes']+=locked['observed_marginal_source_nodes']
                accum['vil_assumed_default_lock_match_nodes']+=locked['imputed_assumption_nodes']
                accum['vil_unlocked_nodes']+=locked['unmatched_nodes']
        except Exception as exc:
            info['errors'].append(str(exc))
            rejects.append(dict(artifact=ad.name,reason=str(exc)))
        reports.append(info)
    if not reports:rejects.append(dict(reason='No authentic multi-board artifacts found'))
    return dict(schema='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',
      source_run_id=run_id,actual_NL2_stake_hands=2334487,
      source_poker_solver_pin='abe310c3aad02dd4a7c77fb2831801fd490cf51b',
      authentic_rust_engine_pin='9d1509fe5077d019825f833eed04b16d342dfda1',
      no_generic_texture_certification=True,
      new_authentic_board_cases=accum['verified_cases'],
      exact_board_gto_sources=accum['gto'],
      imputed_pool_locked_sources=accum['pool_locked_experimental'],
      verified_source_nodes=accum['individually_proved_nodes'],
      strictly_reachable_combo_nodes=accum['sequential_actor_combo_nodes'],
      medium50_strict_eligible_combo_nodes=accum['medium50_strict_eligible_combo_nodes'],
      medium50_strict_nonpolarized_research_candidate_nodes=accum['medium50_strict_research_candidate_nodes'],
      villain_nodes_with_measured_NL2_marginal_lock_source=accum['vil_observed_marginal_lock_match_nodes'],
      villain_nodes_matched_assumed_default=accum['vil_assumed_default_lock_match_nodes'],
      villain_nodes_unlocked=accum['vil_unlocked_nodes'],
      errors=rejects,artifacts=reports)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',required=True,type=pathlib.Path)
    p.add_argument('--solver-root',required=True,type=pathlib.Path)
    p.add_argument('--run-id',type=int,required=True)
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    d=verify(a.downloads,a.solver_root,a.run_id)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in d.items() if k not in ('artifacts','errors')},ensure_ascii=False))
    if d['errors']:
        print('STRICT_SOURCE_REJECTIONS',json.dumps(d['errors'][:12],ensure_ascii=False),flush=True)
    if d['errors'] or d['new_authentic_board_cases']<1:raise SystemExit(1)
if __name__=='__main__':main()
