#!/usr/bin/env python3
"""B351: frozen two UTG_CO 100bb original full flop GTO+authentic NL2 CO-IP
sources for rank79. Never certify a third board without original B2 and exact
actor/SPR full 40/70 source gates. NL2 pooled frequency = street/size marginal.
"""
import pathlib,argparse,json,hashlib,gzip
from hu_sequential_cfr_reach import accepted,game_reach
D=pathlib.Path(__file__).resolve().parents[1]/'data'
FLOPS=('8s8h3d','Js9h4d')
VERSIONS=('gto','exp_ip')
SPOT='UTG_CO'
LINE='b50 c/x'
SPR=7.0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--downloads',type=pathlib.Path,required=True)
    ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    args=ap.parse_args()
    idxpath=D/'solver_evidence/NL2_MULTIBOARD_B351_R79_UTGCO_TWO.index.json'
    gzpath=D/'solver_evidence/NL2_MULTIBOARD_B351_R79_UTGCO_TWO.json.gz'
    idx=json.loads(idxpath.read_text())
    raw=gzip.decompress(gzpath.read_bytes());evidence=json.loads(raw)
    assert idx['run_id']==args.run==evidence['source_run_id']
    assert (idx['actual_spot_flop_version_jobs'],len(evidence['artifacts']))==(4,4)
    assert idx['source_sha256']==hashlib.sha256(raw).hexdigest() and idx['gzip_sha256']==sha(gzpath)
    assert not evidence['errors'] and evidence['no_generic_texture_certification']
    assert {(z['spot'],z['flop'],z['version']) for z in evidence['artifacts']}=={
         (SPOT,f,v) for f in FLOPS for v in VERSIONS}
    source=[]
    for flop in FLOPS:
        pair={}
        for v in VERSIONS:
            folder=args.downloads/f'nl2-multiboard-B351_R79_UTGCO_TWO-{SPOT}-{flop}-{v}'
            manifest=folder/f'evidence/{SPOT}-{flop}-{v}.json'
            root=folder/f'solver/postflop/out/{SPOT}/{v}/{flop}_multiboard.json'
            job=root.with_suffix('.job.json')
            assert all(p.is_file() for p in (manifest,root,job))
            m=json.loads(manifest.read_text());fr=json.loads(root.read_text());j=json.loads(job.read_text())
            assert (m['spot'],m['flop'],m['version'])==(SPOT,flop,v)
            assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
            assert (m['flop_size_profile'],m['restricted_tree_assumption'])==('full',False)
            assert m['selected_lines']==['b50 c'] and not m['failures']
            assert m['solved_cases']==1 and len(m['cases'])==1
            assert (m['root_pot_bb'],m['root_remaining_bb'])==(6.5,97.5)
            assert (fr['flop'],fr['pot'],fr['stack'])==(flop,650,9750)
            assert j['pot']==650 and j['stack']==9750
            assert m['file_flop_sha256']==sha(root)
            assert fr['info']['gto_expl_pct']<=.5
            roots=[n for n in fr['nodes'] if n['line']=='' and n['player']==0 and len(n['board'])==6]
            assert len(roots)==1 and 'b50' in roots[0]['acts']
            legal=accepted(roots[0],fr['hands'],'b50')
            case=m['cases'][0]
            assert (case['line'],case['turn'])==('b50 c',m['turns'][0])
            sub=folder/'solver/postflop'/case['source_path']
            assert sub.is_file() and case['source_sha256']==sha(sub)
            su=json.loads(sub.read_text())
            assert (su['line0'],su['turn'])==('b50 c',case['turn'])
            assert su['info']['gto_expl_pct']<=.5
            if v=='exp_ip':assert su['info']['hero_gap_pct']<=.5
            nodes,stats=game_reach(fr,su)
            target=[z['count'] for k,z in nodes.items() if '|b50 c/x|1' in k]
            assert target,(flop,'missing exact turn IP actor in real Rust source')
            assert abs(case['real_flop_parent_spr']-SPR)/SPR<=.05
            assert abs(case['flop_parent_pot_bb']-13.0)<.01
            assert abs(case['flop_parent_effective_remaining_bb']-94.25)<.01
            pair[v]=dict(flop=flop,turn=case['turn'],version=v,
                original_flop_five_action_menu_full=True,
                original_flop_OOP_b50_legal_root_combos=len(legal),
                exact_CO_IP_7SPR_40_70_turn_combos=sum(target),
                exact_CO_IP_turn_legal_nodes=sum(x>0 for x in target),
                source_manifest_sha256=sha(manifest),source_flop_root_sha256=sha(root),
                source_job_sha256=sha(job),source_turn_river_sha256=sha(sub),
                original_source_preflop_pin_sha256=m['preflop_ranges']['full_sha256'],
                exact_reach_source_node_totals=dict(stats),
                original_NL2_pool_source_hand_count=m['n_NL2_hands'],
                aggregate_lock_patterns=m['locks'],
                no_observed_conditional_per_private_card_NL2=True)
        assert pair['gto']['turn']==pair['exp_ip']['turn']
        source.append(dict(flop=flop,turn=pair['gto']['turn'],
            genuine_original_GTO=pair['gto'],genuine_NL2_Rust_partial_CO_IP_lock=pair['exp_ip'],
            positive_actor_matching_40_70_GTO_and_NL2=(
                pair['gto']['exact_CO_IP_7SPR_40_70_turn_combos']>0 and
                pair['exp_ip']['exact_CO_IP_7SPR_40_70_turn_combos']>0),
            no_new_CERT_without_historic_B2_parent_and_two_textures=True))
    result=dict(schema='NL2_HU_B351_R79_UTGCO_TWO_ORIGINAL_100BB_GTO_AND_NL2_IP_ACTOR_SOURCE_V1',
       source_run_id=args.run,
       source_index_sha256=sha(idxpath),source_archive_sha256=sha(gzpath),
       frozen_target_rank=79,model_id='ln-ipc-t_model-1cla93g',
       actor='CO_IP',spot=SPOT,exact_line=LINE,model_SPR=SPR,
       original_case_pairs=4,
       fresh_original_and_real_NL2_exact_flops=source,
       legal_rank79_exact_new_pair_flops=[z['flop'] for z in source if z['positive_actor_matching_40_70_GTO_and_NL2']],
       original_existing_B2_Ks7h2d_required_for_any_promotion=True,
       no_new_3flop_CERT_without_separate_exact_source_gate=True,
       source_Rust_full_flop_game_not_restricted_LMP50=True,
       NL2_measured_only_street_and_size_marginals=True,
       no_private_card_conditional_rates_observed=True,
       current_V45_CERT=157,current_V45_APPROX=235,current_EST=0,
       PR2_Draft_NEVER_MERGE=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('PASS B351 genuine original GTO + independently Rust NL2 CO IP actor source',[
        (z['flop'],z['genuine_original_GTO']['original_flop_OOP_b50_legal_root_combos'],
         z['genuine_original_GTO']['exact_CO_IP_7SPR_40_70_turn_combos'],
         z['genuine_NL2_Rust_partial_CO_IP_lock']['exact_CO_IP_7SPR_40_70_turn_combos'])
        for z in source])
if __name__=='__main__':main()
