#!/usr/bin/env python3
"""B352: pair immutable original B233/B234 GTO source with NEW true UTG_CO
NL2 CO-IP original Rust exp_ip under same 100bb full-size tree and exact turn.
Never call pooled street-size marginals empirical private-hole-card decisions.
"""
import argparse,gzip,hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parents[1]/'data'
ROWS=(('4s4h2d','8s','B233',44894288118,76),
      ('7s5h3d','6c','B234',44894366667,70))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_archive(batch,run):
    i=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.index.json'
    z=D/f'solver_evidence/NL2_MULTIBOARD_{batch}.json.gz'
    idx=json.loads(i.read_text());raw=gzip.decompress(z.read_bytes())
    assert idx['run_id']==run and idx['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert idx['gzip_sha256']==sha(z)
    data=json.loads(raw);assert data['source_run_id']==run and not data['errors']
    return idx,data,dict(index_sha256=sha(i),archive_sha256=sha(z))
def case(data,flop,turn,version):
    hit=[c for a in data['artifacts'] if
         (a['spot'],a['flop'],a['version'])==('UTG_CO',flop,version)
         for c in a['cases'] if c['flop_line']=='b50 c' and c['turn']==turn]
    assert len(hit)==1,(flop,turn,version,len(hit))
    c=hit[0]
    assert c['run_id']==data['source_run_id']
    assert c['empirical_scope']=='PINNED_PREFLOP_CFR'
    assert abs(c['turn_spr']-7)/7<=.05
    assert (c['flop_root_pot_bb'],c['flop_root_stack_bb'])==(6.5,97.5)
    assert c['gto_exploitability_pct']<=.5 and len(c['source_sha256'])==64
    return c
def target(c):
    return [n for n in c['nodes'] if n['acting_seat']==1
      and n['exact_node_line']=='b50 c/x' and len(n['public_board'])==8
      and n['strictly_reachable_combos']>0 and abs(n['node_spr']-7)/7<=.05]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run',required=True,type=int)
    ap.add_argument('--out',required=True,type=pathlib.Path)
    a=ap.parse_args()
    ix,data,newmeta=read_archive('B352_R79_TWO_REAL_NL2_IP',a.run)
    assert ix['actual_spot_flop_version_jobs']==2 and len(data['artifacts'])==2
    assert {z['version'] for z in data['artifacts']}=={'exp_ip'}
    frozen=json.loads((D/'nl2_hu_b350_rank79_8_original_utgco_gto_turn_legality.json').read_text())
    assert frozen['schema']=='NL2_HU_B350_R79_EIGHT_ORIGINAL_UTG_CO_FULL_ROOT_40_70_IP_TURN_SOURCE_SCAN_V1'
    source=[]
    for flop,turn,batch,run,oldcount in ROWS:
        oldix,old,oldmeta=read_archive(f'{batch}_R30_{flop.upper()}_GTO',run)
        assert (oldix['verified_cases'],oldix['gto_cases'],oldix['locked_cases'])==(1,1,0)
        original=case(old,flop,turn,'gto')
        locked=case(data,flop,turn,'exp_ip')
        assert locked['locked_hero_gap_pct'] is not None and locked['locked_hero_gap_pct']<=.5
        gn=target(original);nn=target(locked)
        assert gn and sum(z['strictly_reachable_combos'] for z in gn)==oldcount
        assert nn and all(abs(x['node_spr']-gn[0]['node_spr'])<=.01 for x in nn)
        assert {x['public_board'] for x in gn}&{x['public_board'] for x in nn}
        hist=next(x for x in frozen['original_gto_source_rows'] if x['flop']==flop)
        assert hist['run_id']==run and hist['original_GTO_case_sha256']==original['source_sha256']
        assert hist['rank79_CO_IP_turn_strict_SPR_40_70_combos']==oldcount
        assert hist['rank79_CO_IP_turn_reachable_real_original_GTO']
        source.append(dict(flop=flop,turn=turn,original_GTO_run_id=run,
            genuine_new_NL2_Rust_run_id=a.run,original_GTO_source_sha256=original['source_sha256'],
            true_NL2_Rust_IP_partial_source_sha256=locked['source_sha256'],
            original_source=oldmeta,new_NL2_source=newmeta,
            original_gto_actor_exact_40_70_SPR7_combos=oldcount,
            new_NL2_actor_exact_40_70_SPR7_combos=sum(z['strictly_reachable_combos'] for z in nn),
            matching_exact_public_turn_actor_source_nodes=sorted({x['public_board'] for x in gn}&{x['public_board'] for x in nn}),
            new_NL2_actor_lock_scope=locked['villain_lock_scope'],
            same_100bb_full_size_tree_and_UTG_CO_preflop_CFR=True,
            authentic_original_GTO_parent_not_replaced_by_NL2_flop=True,
            source_rate_is_pooled_street_size_marginal_not_per_hole_card=True))
    assert len(source)==2 and len({z['flop'] for z in source})==2
    out=dict(schema='NL2_HU_B352_R79_TWO_EXISTING_GTO_PLUS_NEW_REAL_RUST_NL2_COIP_SOURCE_V1',
       target_rank=79,model_id='ln-ipc-t_model-1cla93g',
       exact_line='b50 c/x',actor='CO_IP',model_spr=7,
       true_new_Rust_exp_ip_jobs=2,
       original_full_100bb_preflop_CFR_not_assumed_LMP=True,
       original_authentic_source_pairs=source,
       another_historical_Ks7h2d_GTO_plus_true_NL2_source_still_must_be_checked_for_3_flop_CERT=True,
       existing_V45_CERT=157,existing_V45_APPROX=235,EST=0,
       no_GTO_only_or_source_unverified_promotion=True,
       no_actual_observed_private_card_NL2_conditionals=True,
       PR2_Draft_NEVER_MERGE=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('PASS B352 original GTO+real NL2 exact actor turn pairing',
       [(z['flop'],z['original_gto_actor_exact_40_70_SPR7_combos'],z['new_NL2_actor_exact_40_70_SPR7_combos']) for z in source])
if __name__=='__main__':main()
