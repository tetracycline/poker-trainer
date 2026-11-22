#!/usr/bin/env python3
"""B353: original B2 true UTG_CO historical Ks7h2d/9d GTO + NL2 CO-IP
real Rust source verified on precise turn x-check, model SPR7 and 40/70.
B2 aggregate run failed unrelated SB3 job; verify original archive SHA case.
"""
import gzip,hashlib,json,pathlib
D=pathlib.Path('data')
ARCHIVE=D/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.json.gz'
INDEX=D/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.index.json'
FLOP='Ks7h2d';TURN='9d';LINE='b50 c/x';SPOT='UTG_CO'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    idx=json.loads(INDEX.read_text());raw=gzip.decompress(ARCHIVE.read_bytes());a=json.loads(raw)
    assert idx['run_id']==a['source_run_id']==44666290556
    assert (idx['actual_spot_flop_version_jobs'],idx['verified_cases'],idx['gto_cases'],idx['locked_cases'])==(17,231,65,166)
    assert idx['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert idx['gzip_sha256']==sha(ARCHIVE)
    assert idx['failed_source_job']=='SB3_BTN/8s8h3d/GTO excluded; not counted'
    assert not a['errors'] and len(a['artifacts'])==17
    cases={}
    for v in ('gto','exp_ip'):
        hits=[(z,c) for z in a['artifacts'] if (z['spot'],z['flop'],z['version'])==(SPOT,FLOP,v)
              for c in z['cases'] if (c['flop_line'],c['turn'])==('b50 c',TURN)]
        assert len(hits)==1,('B2 missing exact original case',v,len(hits))
        art,c=hits[0]
        assert not art['errors']
        assert c['run_id']==idx['run_id'] and c['empirical_scope']=='PINNED_PREFLOP_CFR'
        assert (c['flop_root_pot_bb'],c['flop_root_stack_bb'])==(6.5,97.5)
        assert abs(c['real_flop_parent_spr']-7.0)/7.0<=.05
        assert c['gto_exploitability_pct']<=.5
        assert len(c['source_sha256'])==64
        if v=='exp_ip':assert c['locked_hero_gap_pct']<=.5
        nodes=[n for n in c['nodes'] if
             n['exact_node_line']==LINE and n['acting_seat']==1 and
             len(n['public_board'])==8 and n['strictly_reachable_combos']>0
             and abs(n['node_spr']-7)/7<=.05]
        assert len(nodes)==1,(v,len(nodes))
        assert nodes[0]['source_reachable_combos']>=nodes[0]['strictly_reachable_combos']>0
        cases[v]=dict(actual_turn_public_board=nodes[0]['public_board'],
            exact_original_source_sha256=c['source_sha256'],
            strict_CO_IP_actor_40_70_legal_combos=nodes[0]['strictly_reachable_combos'],
            exact_spr=nodes[0]['node_spr'],source_GTO_gap_pct=c['gto_exploitability_pct'],
            source_pattern_lock_scope=c['villain_lock_scope'] if v=='exp_ip' else None,
            full_100bb_original_preflop_CFR=True)
    assert cases['gto']['actual_turn_public_board']==cases['exp_ip']['actual_turn_public_board']
    assert abs(cases['gto']['exact_spr']-cases['exp_ip']['exact_spr'])<.01
    v45=D/'nl2_hu_multiboard_status_v45_b345_rank71.json'
    status=json.loads(v45.read_text())
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(157,235,0,392)
    mod=status['records']['ln-ipc-t_model-1cla93g']
    assert mod['frequency_rank']==79 and mod['label']=='APPROX'
    assert mod['assumed_model_node_spr']==7 and mod['solver_profile']==SPOT
    out=dict(schema='NL2_HU_B353_R79_HISTORIC_B2_KS7H2D_9D_GTO_PLUS_REAL_NL2_CO_IP_V1',
      original_B2_run_id=idx['run_id'],original_B2_archive_sha256=sha(ARCHIVE),
      original_B2_source_index_sha256=sha(INDEX),
      original_B2_aggregate_run_failed_unrelated_SB3_but_raw_source_individually_verified=True,
      actor='CO_IP',spot=SPOT,flop=FLOP,turn=TURN,exact_line=LINE,
      original_100bb_pot_bb=6.5,original_spr_model=7,
      original_GTO=cases['gto'],genuine_real_NL2_actor_IP_partial_source=cases['exp_ip'],
      true_3flop_Cert_requires_two_new_distinct_authentic_actor_matched_sources=True,
      no_generic_whole_texture_GTO=True,no_hole_card_conditional_NL2_empirical_claim=True,
      V45_status_sha256=sha(v45),CURRENT_CERT=157,CURRENT_APPROX=235,CURRENT_EST=0,
      PR2_Draft_NEVER_MERGE=True)
    p=D/'nl2_hu_b353_rank79_historic_B2_original_gto_real_nl2_ip_source.json'
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('PASS B353 historical B2 original GTO plus real NL2 COIP Ks7h2d/9d strict',
       cases['gto']['strict_CO_IP_actor_40_70_legal_combos'],
       cases['exp_ip']['strict_CO_IP_actor_40_70_legal_combos'])
if __name__=='__main__':main()
