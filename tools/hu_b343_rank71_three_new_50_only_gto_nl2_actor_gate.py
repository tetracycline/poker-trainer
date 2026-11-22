#!/usr/bin/env python3
"""B343: original restricted LMP-50 CFR + independently solved NL2 OOP locks.
Only exact public boards and canonical highest-or-40/70 ancestry; never generic CERT.
"""
import argparse, hashlib, gzip, json, pathlib, sys
from hu_sequential_cfr_reach import accepted, game_reach

FLOPS=('3s3h2d','3s4h5d','2s3h4d')
VERSIONS=('gto','exp_oop')
D=pathlib.Path(__file__).resolve().parents[1]/'data'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',required=True,type=pathlib.Path)
    p.add_argument('--run',required=True,type=int)
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    idxpath=D/'solver_evidence/NL2_MULTIBOARD_B343_LMP50_LEGAL.index.json'
    gzpath=D/'solver_evidence/NL2_MULTIBOARD_B343_LMP50_LEGAL.json.gz'
    ix=json.loads(idxpath.read_text())
    raw=gzip.decompress(gzpath.read_bytes()); v=json.loads(raw)
    assert (ix['run_id'],ix['actual_spot_flop_version_jobs'])==(a.run,6)
    assert 0<=ix['gto_cases']<=3 and 0<=ix['locked_cases']<=3 and ix['verified_cases']<=6
    assert sha(gzpath)==ix['gzip_sha256']
    assert hashlib.sha256(raw).hexdigest()==ix['source_sha256']
    assert not v['errors'] and len(v['artifacts'])==6
    assert {(x['flop'],x['version']) for x in v['artifacts']}=={(f,ver) for f in FLOPS for ver in VERSIONS}
    reports=[]
    for flop in FLOPS:
        versions={}
        for version in VERSIONS:
            base=a.downloads/f'nl2-multiboard-B343_LMP50_LEGAL-LMP_CO_BB-{flop}-{version}'
            manifest=base/f'evidence/LMP_CO_BB-{flop}-{version}.json'
            root=base/f'solver/postflop/out/LMP_CO_BB/{version}/{flop}_multiboard.json'
            assert manifest.is_file() and root.is_file()
            mf=json.loads(manifest.read_text());fr=json.loads(root.read_text())
            assert (mf['spot'],mf['flop'],mf['version'])==('LMP_CO_BB',flop,version)
            assert mf['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
            assert (mf['flop_size_profile'],mf['restricted_tree_assumption'])==('lmp-50-only',True)
            assert mf['selected_lines']==['b50 c'] and mf['solved_cases']==1 and not mf['failures']
            assert mf['file_flop_sha256']==sha(root)
            assert (fr['pot'],fr['stack'])==(250,9900) and fr['info']['gto_expl_pct']<=.5
            roots=[n for n in fr['nodes'] if n['line']=='' and n['player']==0 and len(n['board'])==6]
            assert len(roots)==1 and roots[0]['acts']==['x','b50']
            original_legal=accepted(roots[0],fr['hands'],'b50')
            turn=mf['turns'][0]
            case=mf['cases'][0]
            assert (case['line'],case['turn'])==('b50 c',turn)
            sub=base/'solver/postflop'/case['source_path']
            assert sub.is_file() and sha(sub)==case['source_sha256']
            sj=json.loads(sub.read_text())
            assert sj['line0']=='b50 c' and sj['turn']==turn
            assert sj['info']['gto_expl_pct']<=.5
            nodes,stats=game_reach(fr,sj)
            strict=[x['count'] for key,x in nodes.items() if '|b50 c/x b50 c/|0' in key]
            assert strict and abs(case['real_flop_parent_spr']-19.55)<.01
            versions[version]=dict(
                restricted_root_actions=['x','b50'],flop_b50_original_strict_combo_count=len(original_legal),
                rank71_exact_river_actor_OOP_strict_combos=sum(strict),
                rank71_river_actor_OOP_positive_nodes=sum(q>0 for q in strict),
                turn=turn,manifest_sha256=sha(manifest),full_flop_root_sha256=sha(root),
                actual_rust_turn_river_sha256=sha(sub),source_reach_stats=dict(stats),
                NL2_pool_source_scope=mf['unknown_action_frequency_policy'],
                private_hand_conditional_NL2_rates_measured=False)
        assert versions['gto']['turn']==versions['exp_oop']['turn']
        reports.append(dict(flop=flop,
          texture='PAIRED' if flop=='3s3h2d' else 'LOW',
          GTO=versions['gto'],authentic_partial_NL2_OOP_lock=versions['exp_oop'],
          third_flop_candidate=bool(versions['gto']['rank71_exact_river_actor_OOP_strict_combos'] and
                                    versions['exp_oop']['rank71_exact_river_actor_OOP_strict_combos']),
          no_unmatched_turn_or_source_promoted=True))
    result=dict(schema='NL2_HU_B343_ORIGINAL_RESTRICTED_50_GTO_PLUS_REAL_NL2_BB_OOP_V1',
      original_GTO_run_id=a.run,
      original_restricted_game_tree_identical_to_B19_B26=True,
      true_source_GTO_and_real_partial_NL2_jobs=6,
      authenticated_independent_new_named_flops=3,
      tested=reports,
      new_rank71_legal_genuine_GTO_NL2_pair_flops=[x['flop'] for x in reports if x['third_flop_candidate']],
      original_V44_CERT=156,original_V44_APPROX=236,
      GTO_only_never_certifies=True,no_new_generic_texture_policy=True,
      no_actual_private_card_conditional_NL2_villain_rate_observed=True,
      PR2_Draft_NEVER_MERGE=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'legal_candidate_flops':result['new_rank71_legal_genuine_GTO_NL2_pair_flops'],
       'flop_counts':[(x['flop'],x['GTO']['flop_b50_original_strict_combo_count'],
                       x['GTO']['rank71_exact_river_actor_OOP_strict_combos'],
                       x['authentic_partial_NL2_OOP_lock']['rank71_exact_river_actor_OOP_strict_combos']) for x in reports]}))

if __name__=='__main__':main()
