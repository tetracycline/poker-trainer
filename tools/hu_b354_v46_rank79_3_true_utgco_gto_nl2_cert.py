#!/usr/bin/env python3
"""B354: V46 rank79 promotion requires 3 DISTINCT SHA-verifiable original 100bb
UTG_CO full-tree GTO + actor-matched genuine Rust NL2 CO-IP sources, 2+ textures,
exact b50 c/x IP-turn ancestry 40/70 and SPR7. Historic B353 stage2 + B351 new.
"""
import argparse,copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import texture
from hu_cert_lock_medium_coverage_matrix import create
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data');DOC=pathlib.Path('docs')
MID='ln-ipc-t_model-1cla93g';SPOT='UTG_CO';LINE='b50 c/x';SPR=7.0
PARENT=D/'nl2_hu_multiboard_status_v45_b345_rank71.json'
STATUS=D/'nl2_hu_multiboard_status_v46_b354_rank79.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v46_b354.json'
PROOF=D/'nl2_hu_b354_v46_rank79_3_original_GTO_real_NL2_source_gate.json'
B351=D/'nl2_hu_b351_rank79_two_full_GTO_real_NL2_COIP_source.json'
B353=D/'nl2_hu_b353_rank79_historic_stage2_original_gto_real_nl2_ip_source.json'
B175=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def archive(batch,run):
    ixp=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.index.json'
    gz=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.json.gz'
    ix=read(ixp);raw=gzip.decompress(gz.read_bytes())
    assert ix['run_id']==run and ix['gzip_sha256']==sha(gz)
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    a=json.loads(raw)
    assert a['source_run_id']==run and not a['errors']
    return a,dict(source_run_id=run,source_index_sha256=sha(ixp),source_archive_sha256=sha(gz))
def get_case(source,flop,turn,version):
    matches=[c for a in source['artifacts'] if
        (a['spot'],a['flop'],a['version'])==(SPOT,flop,version)
        for c in a['cases'] if c['flop_line']=='b50 c' and c['turn']==turn]
    assert len(matches)==1,('missing unambiguous actual 100bb GTO/NL2 case',flop,turn,version)
    c=matches[0]
    assert (c['flop_root_pot_bb'],c['flop_root_stack_bb'])==(6.5,97.5)
    assert c['empirical_scope']=='PINNED_PREFLOP_CFR'
    assert c['gto_exploitability_pct']<=.5 and abs(c['turn_spr']-SPR)/SPR<=.05
    assert len(c['source_sha256'])==64
    return c
def actor_nodes(c):
    return {n['public_board']:n for n in c['nodes'] if
        n['exact_node_line']==LINE and n['acting_seat']==1
        and len(n['public_board'])==8 and n['strictly_reachable_combos']>0
        and abs(n['node_spr']-SPR)/SPR<=.05}
def lock(run,rawsha,scope):
    assert run>0 and len(rawsha)==64
    return dict(version='exp_ip',run_id=run,sha256=rawsha,source_scope=scope,
        villain_observed_pattern_node_share_pct=None,
        source_not_real_per_combo_observation=True,
        unknown_history_frequency_filled_with_default=True,
        observed_marginal_source_nodes=None,assumed_default_source_nodes=None,
        unlocked_source_nodes=None,hero_model_gain_bb=None)
def newer(fl,turn,cg,ce,run):
    assert cg['run_id']==ce['run_id']==run
    assert ce['locked_hero_gap_pct'] is not None and ce['locked_hero_gap_pct']<=.5
    original,locked=actor_nodes(cg),actor_nodes(ce)
    shared=set(original)&set(locked)
    assert shared,('actor-correct positive GTO and NL2 full ancestry missing',fl,turn)
    pb=sorted(shared,key=lambda key:(-original[key]['strictly_reachable_combos'],key))[0]
    n,e=original[pb],locked[pb]
    assert n['strictly_reachable_combos']>0 and e['strictly_reachable_combos']>0
    assert n['source_actions'] and e['source_actions'] and abs(n['node_spr']-e['node_spr'])<=.01
    medium=int(n.get('medium_50pct_eligible_combos') or 0)
    research=bool(n.get('b50_nonpolarized_relative_equity_research_candidate',False))
    if research:assert medium>0
    return dict(flop=fl,turn=turn,public_board=pb,actual_exact_action_line=LINE,
       acting_seat=1,exact_flop_action='b50 c',
       actual_pot_bb=n['pot_bb'],actual_effective_stack_bb=n['remaining_bb'],
       actual_spr=n['node_spr'],model_assumed_spr=SPR,
       relative_spr_error_pct=round(100*abs(n['node_spr']-SPR)/SPR,5),
       genuine_gto_exploitability_pct=cg['gto_exploitability_pct'],
       source_run_id=run,source_sha256=cg['source_sha256'],
       source_kind='PINNED_PREFLOP_CFR',assumed_preflop_ranges=False,
       exact_combo_reachable=n['source_reachable_combos'],
       strict_full_street_combo_reachable=n['strictly_reachable_combos'],
       exact_node_actions=n['source_actions'],
       medium_50pct_eligible_combos=medium,
       b50_nonpolarized_relative_equity_research_candidate=research,
       flop_texture=texture(fl),nl2_locked_variants=[lock(
           run,ce['source_sha256'],
           'TRUE_ORIGINAL_100BB_UTGCO_NL2_CO_IP_PARTIAL_RUST_STREET_SIZE_POOL_MARGINAL_UNKNOWN_DENOMINATORS')])
def historic(B353report,history,gd,ed):
    row=next(x for x in history['rows'] if x['rank']==79)
    assert row['model_id']==MID and row['distinct_GTO_plus_NL2_hero_flops']==['Ks7h2d']
    proofs=[x for x in row['exact_authentic_gto_source_proofs'] if
          (x['flop'],x['turn'],x['source_run'],x['actor'],x['exact_line'])==(
            'Ks7h2d','9d',44654973894,1,LINE)]
    assert len(proofs)==1 and proofs[0]['true_NL2_actor_locked']
    assert proofs[0]['strict_legal_combos']==18 and proofs[0]['SPR_error_pct']<=5
    assert proofs[0]['source_sha']==B353report['genuine_UTGCO_source_GTO']['actual_original_Rust_turn_source_sha256']
    assert proofs[0]['paired_lock_runs']==[44654973894]
    orig=B353report['genuine_UTGCO_source_GTO'];locked=B353report['genuine_UTGCO_real_NL2_CO_IP_source']
    assert B353report['original_40_70_B175_GTO_strict_combos']==18
    assert orig['true_actor_CO_IP_reached_combos']>=18 and locked['true_actor_CO_IP_reached_combos']>0
    assert orig['actual_board']==locked['actual_board']=='2d7hKs9d'
    assert abs(orig['actual_model_spr']-locked['actual_model_spr'])<=.01
    source={}
    for key,folder,anchor in [('gto',gd,orig),('exp_ip',ed,locked)]:
        manifest=folder/f'evidence/UTG_CO-{key}-Ks7h2d.json'
        assert manifest.is_file() and sha(manifest)==anchor['source_manifest_sha256']
        m=read(manifest)
        cs=[c for c in m['cases'] if (c['flop'],c['turn'],c['line'])==('Ks7h2d','9d','b50 c')]
        assert len(cs)==1
        case=cs[0]
        flop=folder/'solver/postflop'/case['flop_json']
        sub=folder/'solver/postflop'/case['sub_json']
        assert flop.is_file() and sub.is_file()
        assert sha(flop)==case['flop_sha256']==anchor['original_full_flop_root_sha256']
        assert sha(sub)==case['sub_sha256']==anchor['actual_original_Rust_turn_source_sha256']
        root=read(flop);child=read(sub)
        assert (root['flop'],root['pot'],root['stack'])==('Ks7h2d',650,9750)
        assert (child['flop'],child['turn'],child['line0'])==('Ks7h2d','9d','b50 c')
        assert child['info']['gto_expl_pct']<=.5
        nodes=[n for n in child['nodes'] if
               (n['board'],n['line'],n['player'])==('2d7hKs9d',LINE,1)]
        assert len(nodes)==1 and nodes[0]['acts'] and nodes[0]['pot']==1300
        assert abs(case['turn_node_spr']-SPR)/SPR<=.05
        assert abs(case['turn_node_spr']-anchor['actual_model_spr'])<.01
        source[key]=dict(node=nodes[0],case=case,source_sha=sha(sub))
    assert source['gto']['node']['acts']==source['exp_ip']['node']['acts']
    assert source['gto']['node']['acts']==['x','b50','b100']
    node=source['gto']['node'];case=source['gto']['case']
    spr=orig['actual_model_spr']
    assert abs(spr-7)/7<=.05
    # 18 GTO combos are ORIGINAL B175 strict 40/70 per-hand result, not
    # the 71 less-restrictive stage2 source overlay combo reach count.
    return dict(flop='Ks7h2d',turn='9d',public_board=orig['actual_board'],
        actual_exact_action_line=LINE,acting_seat=1,exact_flop_action='b50 c',
        actual_pot_bb=node['pot']/100,
        actual_effective_stack_bb=round((node['pot']/100)*spr,4),
        actual_spr=spr,model_assumed_spr=SPR,
        relative_spr_error_pct=round(100*abs(spr-SPR)/SPR,5),
        genuine_gto_exploitability_pct=case['sub_gto_expl_pct'],
        source_run_id=44654973894,source_sha256=source['gto']['source_sha'],
        source_kind='PINNED_PREFLOP_CFR',assumed_preflop_ranges=False,
        exact_combo_reachable=orig['true_actor_CO_IP_reached_combos'],
        strict_full_street_combo_reachable=proofs[0]['strict_legal_combos'],
        exact_node_actions=node['acts'],
        medium_50pct_eligible_combos=0,
        b50_nonpolarized_relative_equity_research_candidate=False,
        flop_texture=texture('Ks7h2d'),
        nl2_locked_variants=[lock(44654973894,source['exp_ip']['source_sha'],
            'HISTORICAL_ORIGINAL_STAGE2_AUTHENTIC_NL2_CO_IP_PARTIAL_RUST_SOURCE_UNKNOWN_NODE_DENOMINATOR')])
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--historic-gto',required=True,type=pathlib.Path)
    p.add_argument('--historic-exp',required=True,type=pathlib.Path)
    a=p.parse_args()
    old=read(PARENT)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V45_B345_RANK71'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(157,235,0,392)
    assert old['records'][MID]['label']=='APPROX' and old['records'][MID]['assumed_model_node_spr']==SPR
    b353=read(B353);h=read(B175);f=read(B351)
    assert b353['authenticated_original_stage2_run']==44654973894
    assert b353['original_source_stage2_conclusion_success']
    assert b353['V45_status_sha256']==sha(PARENT)
    assert f['schema']=='NL2_HU_B351_R79_UTGCO_TWO_ORIGINAL_100BB_GTO_AND_NL2_IP_ACTOR_SOURCE_V1'
    assert f['model_id']==MID and f['model_SPR']==SPR
    assert f['legal_rank79_exact_new_pair_flops']==['8s8h3d','Js9h4d']
    assert f['current_V45_CERT']==157 and f['current_V45_APPROX']==235
    assert len(f['fresh_original_and_real_NL2_exact_flops'])==2
    arch,anchor=archive('B351_R79_UTGCO_TWO',f['source_run_id'])
    boards=[historic(b353,h,a.historic_gto,a.historic_exp)]
    refs=[dict(flop='Ks7h2d',turn='9d',run=44654973894,
        GTO_SHA=boards[0]['source_sha256'],
        NL2_SHA=boards[0]['nl2_locked_variants'][0]['sha256'],
        source_b353_sha256=sha(B353),historical_rank79_GTO_strict=18)]
    for z in f['fresh_original_and_real_NL2_exact_flops']:
        flop=z['flop'];turn=z['turn']
        cg=get_case(arch,flop,turn,'gto');ce=get_case(arch,flop,turn,'exp_ip')
        assert cg['source_sha256']==z['genuine_original_GTO']['source_turn_river_sha256']
        assert ce['source_sha256']==z['genuine_NL2_Rust_partial_CO_IP_lock']['source_turn_river_sha256']
        b=newer(flop,turn,cg,ce,f['source_run_id'])
        assert b['strict_full_street_combo_reachable']==z['genuine_original_GTO']['exact_CO_IP_7SPR_40_70_turn_combos']
        boards.append(b)
        refs.append(dict(flop=flop,turn=turn,run=f['source_run_id'],
            GTO_SHA=cg['source_sha256'],NL2_SHA=ce['source_sha256'],
            original_archive_index_SHA=anchor['source_index_sha256'],
            original_archive_SHA=anchor['source_archive_sha256'],
            exact_rank79_turn_strict_GTO=b['strict_full_street_combo_reachable']))
    assert [b['flop'] for b in boards]==['Ks7h2d','8s8h3d','Js9h4d']
    assert len({b['flop'] for b in boards})==3
    textures={b['flop_texture'] for b in boards}
    assert len(textures)>=2
    assert all(b['acting_seat']==1 and b['actual_exact_action_line']==LINE and
       b['strict_full_street_combo_reachable']>0 and b['relative_spr_error_pct']<=5 and
       b['nl2_locked_variants'][0]['version']=='exp_ip' and not b['assumed_preflop_ranges'] for b in boards)
    newerstatus=copy.deepcopy(old)
    newerstatus['records'][MID].update(label='CERT-MULTIBOARD',
       high_frequency_preregistered=True,original_top24_high_frequency_preregistered=False,
       source_blind_expansion_rank=79,
       prereg_cohort='HISTORIC_STAGE2_KS7H2D_9D_ORIGINAL_GTO_NL2_PLUS_B351_TWO_FROZEN_DISTINCT_ORIGINAL_RUST_GTO_NL2_PAIR',
       certified_3_to_5_exact_flop_boards=boards,proven_exact_board_count=3,
       blocked_reason=None,
       source_credibility='3_DIFFERENT_AUTHENTIC_100BB_FULL_RUST_UTGCO_GTO_PLUS_NL2_IP_ACTOR_SHA_2PLUS_TEXTURE')
    assert {k for k in old['records'] if old['records'][k]!=newerstatus['records'][k]}=={MID}
    newerstatus.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79',
       CERT_MULTIBOARD=158,APPROX=234,EST=0,TOTAL=392,parent_v45_sha256=sha(PARENT),
       source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{79}),
       supplementary_cert_count=old['supplementary_cert_count']+1,
       B354_rank79_three_true_original_GTO_NL2_CO_IP_flops=dict(
          rank=79,model_id=MID,actor='CO_IP',spot=SPOT,exact_line=LINE,SPR=SPR,
          flops=[b['flop'] for b in boards],textures=sorted(textures),
          source_run_shas=refs,
          historic_source_original_run=44654973894,
          genuine_source_GTO_3_and_actor_NL2_3=True,
          no_observed_private_card_conditional_NL2_villain_rates=True,
          no_generic_texture_GTO=True))
    assert sum(m['label']=='CERT-MULTIBOARD' for m in newerstatus['records'].values())==158
    assert sum(m['label']=='APPROX' for m in newerstatus['records'].values())==234
    matrix=create(newerstatus)
    assert (len(matrix['boards']),len(matrix['models']))==(603,158)
    assert matrix['strict_aggregate']['named_board_proofs']==603
    assert matrix['strict_aggregate']['hero_lock_variants']==695
    aud=audit(newerstatus)
    assert (aud['cert_multiboard'],aud['approx'],aud['EST'])==(158,234,0)
    assert (aud['aggregate']['named_board_proofs'],aud['aggregate']['paired_hero_locked_source_variants'])==(603,695)
    assert aud['not_generalized_handclass_GTO'] and aud['not_actual_NL2_earnings']
    STATUS.write_text(json.dumps(newerstatus,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V46_B354',
       parent_v46_status_sha256=sha(STATUS),
       partial_NL2_locks_are_not_whole_flop_GTO=True,
       NL2_private_combo_conditional_rates_not_observed=True,
       only_exact_board_b50_nonpolarized_research=True,
       unknown_source_denominators_are_not_zero_or_empirical=True,
       PR2_Draft_NEVER_MERGE=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    PROOF.write_text(json.dumps(dict(schema='NL2_HU_B354_V46_RANK79_3_TRUE_UTGCO_GTO_NL2_IP_SOURCE_CERT_V1',
       parent_V45_status_sha256=sha(PARENT),historical_B353_proof_sha256=sha(B353),
       genuine_B351_source_sha256=sha(B351),
       V46_status_sha256=sha(STATUS),V46_matrix_sha256=sha(MATRIX),
       three_distinct_flops=[b['flop'] for b in boards],
       multiple_textures=sorted(textures),source_verified_real_GTO_NL2_actors=refs,
       original_stage2_run_success=True,
       exact_100bb_preflop_CFR=True,source_is_full_four_size_GTO=True,
       no_observed_NL2_private_card_conditional_rates=True,
       CERT=158,APPROX=234,EST=0,TOTAL=392,
       named_GTO_NL2_actor_boards=603,real_NL2_actor_lock_variants=695,
       HU2475_Actions_independent_audit_required_before_commit=True,PR2_Draft_NEVER_MERGE=True),
       ensure_ascii=False,indent=2)+'\n')
    DOC.mkdir(parents=True,exist_ok=True)
    (DOC/'NL2_HU_B354_V46_RANK79_THREE_ORIGINAL_GTO_REAL_NL2_IP_CERT.md').write_text(
       '# B354 V46 rank79 three authentic original 100bb UTGCO GTO and real NL2 IP Rust partial lock cert\n\n'
       'Exact public flops: '+', '.join(b['flop']+'/'+b['turn'] for b in boards)+'. '
       'Actor CO-IP, target line b50 c/x, SPR7 +/-5%, max/40/70 prior original CFR action ancestors, '
       'SHA-pinned successful original stage2 44654973894 and independently B351 four 100bb Rust source jobs, '
       'across genuine distinct flop textures; exactly named boards only. '
       'Original full flop 33/50/75/100 size tree, pinned real preflop CFR, genuine partial NL2 lock; '
       'NL2 player-pool frequencies only street/size marginals or disclosed assumptions, NOT observed private-hole-card conditionals. '
       'V46 158 CERT/234 APPROX/0 EST, 603 exact named board source and 695 genuine actor NL2 partial locks. '
       'HU 2475/2475 independent audit required before commit, PR2 Draft never merge/force push.\n')
    print('PASS B354 V46 rank79 three source-gated original full GTO+real NL2 IP',len(boards),
        'CERT 158/APPROX234, 603 named, 695 genuine locks')
if __name__=='__main__':main()
