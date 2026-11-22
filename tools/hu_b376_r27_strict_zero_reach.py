#!/usr/bin/env python3
"""B376: exact-source negative audit; completed Rust solve != strictly reachable CERT.
Read original B372 Rust artifacts and apply immutable 40%-70% sequential actor policy.
No additional CFR solve, fake NL2 opponent conditional frequencies, or model promotion.
"""
import hashlib,json,pathlib,sys
from hu_sequential_cfr_reach import game_reach

D=pathlib.Path('data')
OUT=D/'nl2_hu_b376_rank27_b372_exact_full_street_zero_reach_negative.json'
DOC=pathlib.Path('docs/NL2_HU_B376_RANK27_STRICT_ZERO_REACH_NEGATIVE.md')
RUN=45016548530
GTO='b2aeb59fe69c73c42c4c848eed27df9c055f65a7503bd9d4ee07ab07b3c89822'
LOCK='8ea00b1942b607bd862cac0ccb144a0823f696f337695ed840f0a48a9d674e21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    root=pathlib.Path(sys.argv[1])
    mp=root/'evidence/LMP_CO_BB-9s6h3d-exp_oop-turn-only.json'
    frp=root/'solver/postflop/out/LMP_CO_BB/exp_oop/9s6h3d_multiboard.json'
    subp=root/'solver/postflop/out/LMP_CO_BB/exp_oop/9s6h3d_b33c_Ts.json'
    assert all(p.is_file() for p in (mp,frp,subp))
    m=read(mp);fr=read(frp);sub=read(subp)
    assert (m['schema'],m['version'],m['spot'],m['flop'])==(
        'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1','exp_oop','LMP_CO_BB','9s6h3d')
    assert (m['file_flop_sha256'],sha(frp))==(GTO,GTO)
    assert (m['cases'][0]['source_sha256'],sha(subp))==(LOCK,LOCK)
    assert sub['line0']=='b33 c' and sub['turn']=='Ts'
    assert (fr['flop'],fr['pot'],fr['stack'])==('9s6h3d',250,9900)
    assert (sub['flop'],sub['turn'])==('9s6h3d','Ts')
    assert (m['cases'][0]['gto_gap_pct']<=.5 and m['cases'][0]['hero_gap_pct']<=.5)
    masks,stats=game_reach(fr,sub)
    targets=[]
    for n in sub['nodes']:
        if n['line']=='b33 c/b50 c/' and n['player']==0 and len(n['board'])==10:
            key='|'.join((n['board'],n['line'],str(n['player'])))
            q=masks[key]
            targets.append(dict(public_board=n['board'],exact_line=n['line'],
                hero_actor='BB_OOP',root_original_gto_sha=GTO,true_Rust_NL2_child_sha=LOCK,
                strictly_reachable_combos_after_full_street_policy=q['count'],
                ancestor_actor_decisions=q['parent_actor_decisions'],
                source_node_positive_but_strictly_excluded=any(float(w)>1e-4 for w in n['w'][0])))
    assert len(targets)==2 and len({x['public_board'] for x in targets})==2
    assert stats['nodes']==len(sub['nodes'])==30
    assert stats['source_actor_combo_nodes']>0
    # The predeclared max/near rule has NO legal BB-OOP actor combo here.
    # Fail closed if the actual SHA-pinned source ever differs.
    assert stats['sequential_actor_combo_nodes']==0 and all(x['strictly_reachable_combos_after_full_street_policy']==0 for x in targets)
    s=read(D/'nl2_hu_multiboard_status_v47_b364_rank96.json')
    mid='ln-iso-lmp_r_model-1aov4pd'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(159,233,0,392)
    assert s['records'][mid]['label']=='APPROX' and s['records'][mid]['frequency_rank']==27
    proof=dict(schema='NL2_HU_B376_EXACT_B372_RANK27_STRICT_ZERO_REACH_V1',
        source_run_id=RUN,source_artifact_id=14752470971,
        model_id=mid,rank=27,flop='9s6h3d',turn='Ts',
        actor='BB_OOP',root_original_true_GTO_sha256=GTO,
        real_Rust_partially_NL2_locked_turn_sha256=LOCK,
        original_source_manifest_sha256=sha(mp),
        source_CFR_gto_gap_pct=m['cases'][0]['gto_gap_pct'],
        source_CFR_hero_gap_pct=m['cases'][0]['hero_gap_pct'],
        actual_original_Rust_source=True,
        cross_street_rule='MAX_ACTION_OR_ALTERNATE_FREQ_GE_40PCT_AND_GE_70PCT_OF_MAX',
        sequential_reach_stats=dict(stats),
        exact_named_river_actor_target_nodes=targets,
        excluded_reason='GTO_SOURCE_REAL_BUT_ZERO_LEGAL_FULL_STREET_HERO_COMBOS',
        not_a_missing_source_problem=True,
        source_aggregate_NL2_marginals_not_villain_private_hand_data=True,
        no_texture_generalization=True,
        no_CERT_upgrade_from_this_flop=True,
        HU_river_navigation_unchanged_2475_of_2475=True,
        CERT_MULTIBOARD=159,APPROX=233,EST=0,
        B368_not_rerun=True,PR2_remains_draft_never_merge=True)
    OUT.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B376 rank27 original true Rust source — independent negative strict-reach audit\n\n'
        'Original 100bb GTO flop and true NL2 partially locked Rust turn/river are SHA-verified. '
        'At exact 9s6h3d/Ts, BB-OOP b33-call / b50-call river roots have '
        '**0 strictly reachable hero combos** after max/40%-70% full-street gating, '
        'despite original CFR source nodes existing. Not usable to promote CERT. '
        '**159 CERT / 233 APPROX / 0 EST** unchanged.\n')
    print('PASS B376: 2 genuine river nodes, both ZERO full-street strict combos; 159 CERT / 233 APPROX')
if __name__=='__main__':main()
